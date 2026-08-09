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
# ATENCAO: "az ... -o tsv" devolve array numa UNICA linha separada por TAB.
# Sem o "tr" abaixo, o mapfile joga as cinco regioes em PERMITIDAS[0] e o
# "az group create" recebe a string inteira como se fosse uma regiao.
mapfile -t PERMITIDAS < <(
  az policy assignment list \
    --scope "/subscriptions/$SUB_ID" --disable-scope-strict-match \
    --query "[?contains(displayName,'regions')].parameters.listOfAllowedLocations.value" \
    -o tsv 2>/dev/null | tr '\t' '\n' | tr -d '\r' | sed '/^[[:space:]]*$/d'
)

if [ ${#PERMITIDAS[@]} -eq 0 ]; then
  echo "Nenhuma policy de regiao encontrada. Usando lista padrao."
  PERMITIDAS=(eastus2 brazilsouth canadacentral southcentralus northcentralus)
fi

echo "==> Regioes permitidas (${#PERMITIDAS[@]}):"
printf '      - %s\n' "${PERMITIDAS[@]}"
echo

# Preferencia: Brasil primeiro (latencia), depois a ordem da policy.
ORDENADAS=()
for L in brazilsouth "${PERMITIDAS[@]}"; do
  [[ " ${PERMITIDAS[*]} " == *" $L "* ]] || continue
  [[ " ${ORDENADAS[*]:-} " == *" $L "* ]] && continue
  ORDENADAS+=("$L")
done

# --- RG temporario para as sondas -------------------------------------------
limpar() {
  echo >&2
  echo "==> Removendo recursos de teste" >&2
  az group delete -n "$RG_PROBE" --yes --no-wait -o none 2>/dev/null || true
}
trap limpar EXIT

echo "==> Criando resource group temporario em ${ORDENADAS[0]}"
if ! az group create -n "$RG_PROBE" -l "${ORDENADAS[0]}" -o none; then
  echo "ERRO: nao foi possivel criar o resource group de sondagem."
  exit 1
fi

# --- 2. sondas ---------------------------------------------------------------
# Cada sonda cria o recurso mais barato/rapido que representa o servico.
sonda_storage() {   # regiao geral: RG, Storage, Key Vault, Cosmos
  az storage account create -g "$RG_PROBE" -n "stprb${RANDOM}${RANDOM}" \
    -l "$1" --sku Standard_LRS -o none 2>/dev/null
}

sonda_sql() {
  az sql server create -g "$RG_PROBE" -n "sqlprb${RANDOM}${RANDOM}" -l "$1" \
    -u probeadmin -p "Pr0be${RANDOM}Xyz#9" -o none 2>/dev/null
}

sonda_search() {
  az search service create -g "$RG_PROBE" -n "srchprb${RANDOM}${RANDOM}" -l "$1" \
    --sku free -o none 2>/dev/null
}

# IMPORTANTE: todo log vai para stderr (>&2). O stdout carrega apenas o
# resultado, que e capturado por $( ).
descobrir() {   # $1 = rotulo, $2 = funcao de sonda
  local rotulo="$1" fn="$2" L
  for L in "${ORDENADAS[@]}"; do
    printf "    %-8s %-16s ... " "$rotulo" "$L" >&2
    if "$fn" "$L"; then
      echo "OK" >&2
      printf '%s' "$L"
      return 0
    fi
    echo "falhou" >&2
  done
  return 1
}

echo
echo "==> Sondando (os recursos de teste sao apagados no final)"
LOC_GERAL="$(descobrir  "geral"  sonda_storage)"
LOC_SQL="$(descobrir    "sql"    sonda_sql)"
LOC_SEARCH="$(descobrir "search" sonda_search)"

# O ACI nao e restritivo por regiao: o problema historico dele era rate limit
# do Docker Hub, resolvido pelo registry proprio. Segue a regiao geral.
LOC_ACI="$LOC_GERAL"

echo
if [ -z "$LOC_GERAL" ] || [ -z "$LOC_SQL" ] || [ -z "$LOC_SEARCH" ]; then
  echo "ERRO: algum servico nao provisionou em nenhuma regiao permitida."
  echo "  geral=[$LOC_GERAL]  sql=[$LOC_SQL]  search=[$LOC_SEARCH]"
  echo
  echo "Se foi o search: cota do SKU free varia ao longo do dia - tente mais tarde."
  echo "Se foi o sql: pode ser bloqueio da assinatura. Abra um chamado com o"
  echo "tipo 'Service and subscription limits'."
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
# As regioes abaixo foram VALIDADAS por sonda: cada servico foi realmente
# criado e apagado na regiao indicada. Estar na lista de permitidas nao
# garante que o servico provisiona - por isso a separacao por servico.

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
grep "^location" "$TFVARS" | sed 's/^/      /'
echo
echo "Backup do anterior em $TFVARS.bak"
