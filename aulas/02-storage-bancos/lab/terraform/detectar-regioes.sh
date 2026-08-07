#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Descobre em quais regioes CADA servico do lab realmente provisiona nesta
# assinatura, e escreve o terraform.tfvars com o resultado.
#
#   bash detectar-regioes.sh
#
# Por que existe:
#   Regiao permitida pela policy NAO garante que o servico provisiona. Cada um
#   pode falhar por um motivo proprio:
#     403 RequestDisallowedByAzure        -> regiao fora da policy
#     403 ProvisioningDisabled            -> servico bloqueado nessa regiao
#     400 InsufficientResourcesAvailable  -> regiao ok, sem cota no momento
#   Sondar leva ~3 min e evita descobrir isso no meio do apply.
#
# O script cria recursos de teste minusculos e os APAGA em seguida.
# ---------------------------------------------------------------------------
set -uo pipefail

SUB_ID="$(az account show --query id -o tsv)"
RG_PROBE="rg-probe-regioes-$RANDOM"
TFVARS="${TFVARS:-terraform.tfvars}"

echo "==> Assinatura: $SUB_ID"

# --- 1. regioes permitidas pela policy --------------------------------------
mapfile -t PERMITIDAS < <(az policy assignment list \
  --scope "/subscriptions/$SUB_ID" --disable-scope-strict-match \
  --query "[?contains(displayName,'regions')].parameters.listOfAllowedLocations.value" \
  -o tsv 2>/dev/null)

if [ ${#PERMITIDAS[@]} -eq 0 ]; then
  echo "Nenhuma policy de regiao encontrada. Usando lista padrao."
  PERMITIDAS=(eastus2 brazilsouth canadacentral southcentralus northcentralus)
fi

echo "==> Regioes permitidas: ${PERMITIDAS[*]}"
echo

# Preferencia: Brasil primeiro (latencia), depois o resto.
ORDENADAS=()
for L in brazilsouth "${PERMITIDAS[@]}"; do
  case " ${PERMITIDAS[*]} " in *" $L "*) ;; *) continue ;; esac
  case " ${ORDENADAS[*]:-} " in *" $L "*) continue ;; esac
  ORDENADAS+=("$L")
done

# --- RG temporario para as sondas -------------------------------------------
limpar() {
  echo
  echo "==> Removendo recursos de teste"
  az group delete -n "$RG_PROBE" --yes --no-wait -o none 2>/dev/null || true
}
trap limpar EXIT

az group create -n "$RG_PROBE" -l "${ORDENADAS[0]}" -o none

# --- 2. sondas ---------------------------------------------------------------
sonda_storage() {   # regiao geral: RG, Storage, Key Vault, Cosmos
  az storage account create -g "$RG_PROBE" -n "stprobe$RANDOM$RANDOM" \
    -l "$1" --sku Standard_LRS -o none 2>/dev/null
}

sonda_sql() {
  az sql server create -g "$RG_PROBE" -n "sqlprobe$RANDOM" -l "$1" \
    -u probeadmin -p "Pr0be${RANDOM}Xyz#9" -o none 2>/dev/null
}

sonda_search() {
  az search service create -g "$RG_PROBE" -n "srchprobe$RANDOM" -l "$1" \
    --sku free -o none 2>/dev/null
}

descobrir() {   # $1 = rotulo, $2 = nome da funcao de sonda
  local rotulo="$1" fn="$2"
  for L in "${ORDENADAS[@]}"; do
    printf "    %-16s %s ... " "$rotulo" "$L"
    if "$fn" "$L"; then
      echo "OK"
      echo "$L"
      return 0
    fi
    echo "falhou"
  done
  echo ""
  return 1
}

echo "==> Sondando (cada recurso de teste e apagado no final)"
LOC_GERAL="$(descobrir  "geral"  sonda_storage | tail -1)"
LOC_SQL="$(descobrir    "sql"    sonda_sql     | tail -1)"
LOC_SEARCH="$(descobrir "search" sonda_search  | tail -1)"

# O ACI nao e restritivo por regiao: o problema historico dele era rate limit
# do Docker Hub, resolvido pelo registry proprio. Segue a regiao geral.
LOC_ACI="$LOC_GERAL"

echo
if [ -z "$LOC_GERAL" ] || [ -z "$LOC_SQL" ] || [ -z "$LOC_SEARCH" ]; then
  echo "ERRO: algum servico nao provisionou em nenhuma regiao permitida."
  echo "  geral=[$LOC_GERAL] sql=[$LOC_SQL] search=[$LOC_SEARCH]"
  echo "Abra um chamado (Service and subscription limits) ou tente mais tarde:"
  echo "cota de SKU free varia ao longo do dia."
  exit 1
fi

# --- 3. escreve o tfvars -----------------------------------------------------
[ -f "$TFVARS" ] && cp "$TFVARS" "$TFVARS.bak"

cat > "$TFVARS" <<EOF
# Gerado por detectar-regioes.sh em $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Assinatura: $SUB_ID
#
# Regioes permitidas pela policy desta assinatura:
#   ${PERMITIDAS[*]}
#
# Estas foram VALIDADAS por sonda: cada servico foi realmente criado e
# apagado na regiao indicada. Regiao permitida pela policy nao garante que
# o servico provisiona - por isso a separacao por servico.

location        = "$LOC_GERAL"
location_sql    = "$LOC_SQL"
location_search = "$LOC_SEARCH"
location_aci    = "$LOC_ACI"

# A senha do SQL NAO fica aqui. Passe por variavel de ambiente:
#   export TF_VAR_sql_admin_password="\$(openssl rand -base64 24)"
#
# Registry das imagens do ACI (rode setup-registry-aluno.sh):
#   source ~/.qc-registry.env
EOF

echo "==> $TFVARS atualizado:"
echo
cat "$TFVARS" | grep "^location"
echo
echo "Backup do anterior em $TFVARS.bak"
