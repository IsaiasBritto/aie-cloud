#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Descobre em quais regiões CADA serviço do lab pode ser criado NESTA assinatura
# e escreve o terraform.tfvars com o resultado.
#
#   bash check_regions.sh                  # mostra a matriz e grava o tfvars
#   bash check_regions.sh --so-mostrar     # só mostra, não escreve arquivo
#
# Substitui check_regions_cosmos.sh, check_regions_search.sh e
# check_regions_sqlserver.sh, que tinham dois problemas:
#
#   1. Testavam uma lista fixa de 19 regiões do mundo inteiro, ignorando a
#      policy "Allowed resource deployment regions" da assinatura. O aluno
#      recebia como "disponível" região onde o deploy é barrado por política.
#
#   2. Chamavam subcomandos que não existem no az ("az cosmosdb
#      list-region-capacity"). Com "2>/dev/null" o erro sumia e TODAS as
#      regiões apareciam como indisponíveis, sem nenhuma pista do motivo.
#
# O que este script NÃO consegue prever, por design:
#   400 InsufficientResourcesAvailable  -> cota do SKU free esgotada agora
#   503 ServiceUnavailable              -> capacidade da Azure esgotada agora
# Os dois são transitórios e dependem do minuto. Se aparecerem no apply, a
# resposta é repetir; só troque de região se persistir.
# ---------------------------------------------------------------------------
set -uo pipefail

SO_MOSTRAR=0
[ "${1:-}" = "--so-mostrar" ] && SO_MOSTRAR=1

TFVARS="${TFVARS:-terraform/terraform.tfvars}"

# Serviço | namespace do provider | tipo de recurso
SERVICOS=(
  "storage|Microsoft.Storage|storageAccounts"
  "keyvault|Microsoft.KeyVault|vaults"
  "cosmos|Microsoft.DocumentDB|databaseAccounts"
  "sql|Microsoft.Sql|servers"
  "search|Microsoft.Search|searchServices"
  "aci|Microsoft.ContainerInstance|containerGroups"
)

# Normaliza para comparar "Brazil South" com "brazilsouth".
norm() { tr '[:upper:]' '[:lower:]' | tr -d '[:space:]-_'; }

SUB_ID="$(az account show --query id -o tsv)" || {
  echo "Não consegui ler a assinatura. Rode 'az login' antes." >&2
  exit 1
}
echo "==> Assinatura: $SUB_ID"

# --- 1. regiões permitidas pela policy --------------------------------------
# ATENÇÃO: "az ... -o tsv" devolve array numa ÚNICA linha separada por TAB.
# Sem o "tr" abaixo, as cinco regiões viram um único elemento e todo o resto
# do script compara contra uma string gigante que nunca casa.
mapfile -t PERMITIDAS < <(
  az policy assignment list \
    --scope "/subscriptions/$SUB_ID" --disable-scope-strict-match \
    --query "[?contains(displayName,'regions')].parameters.listOfAllowedLocations.value" \
    -o tsv 2>/dev/null | tr '\t' '\n' | tr -d '\r' | sed '/^[[:space:]]*$/d'
)

if [ ${#PERMITIDAS[@]} -eq 0 ]; then
  echo "==> Nenhuma policy de região encontrada — usando todas as regiões da assinatura."
  mapfile -t PERMITIDAS < <(az account list-locations --query "[].name" -o tsv | tr -d '\r')
else
  echo "==> Regiões permitidas pela policy (${#PERMITIDAS[@]}): ${PERMITIDAS[*]}"
fi
echo

# Preferência: Brasil primeiro (latência), depois a ordem da policy.
ORDENADAS=()
for L in brazilsouth "${PERMITIDAS[@]}"; do
  [[ " ${PERMITIDAS[*]} " == *" $L "* ]] || continue
  [[ " ${ORDENADAS[*]:-} " == *" $L "* ]] && continue
  ORDENADAS+=("$L")
done

# --- 2. onde cada serviço é oferecido nesta assinatura -----------------------
# "az provider show" devolve os locations em NOME DE EXIBIÇÃO ("Brazil South"),
# não em código ("brazilsouth") — por isso a normalização.
declare -A DISPONIVEL

for entrada in "${SERVICOS[@]}"; do
  IFS='|' read -r nome ns tipo <<< "$entrada"
  # Progresso vai para stdout junto com o resto: misturar stdout e stderr aqui
  # embaralha a ordem das linhas quando a saída é redirecionada para arquivo.
  printf "    consultando %-9s (%s)... " "$nome" "$ns"

  locs="$(az provider show --namespace "$ns" \
    --query "resourceTypes[?resourceType=='$tipo'].locations | [0]" -o tsv 2>/dev/null \
    | tr '\t' '\n' | tr -d '\r')"

  if [ -z "$locs" ]; then
    echo "sem resposta (provider não registrado?)"
    continue
  fi

  n=0
  while IFS= read -r loc; do
    [ -z "$loc" ] && continue
    DISPONIVEL["$nome|$(printf '%s' "$loc" | norm)"]=1
    n=$((n + 1))
  done <<< "$locs"
  echo "$n regiões"
done
echo

# --- 3. matriz -------------------------------------------------------------
printf "%-16s" "REGIAO"
for entrada in "${SERVICOS[@]}"; do printf "%-10s" "${entrada%%|*}"; done
echo

for L in "${ORDENADAS[@]}"; do
  printf "%-16s" "$L"
  chave="$(printf '%s' "$L" | norm)"
  for entrada in "${SERVICOS[@]}"; do
    nome="${entrada%%|*}"
    if [ "${DISPONIVEL[$nome|$chave]:-0}" = "1" ]; then printf "%-10s" "sim"; else printf "%-10s" "-"; fi
  done
  echo
done
echo

# --- 4. escolhe a primeira região válida por serviço ------------------------
primeira() {
  local servico="$1" L
  for L in "${ORDENADAS[@]}"; do
    if [ "${DISPONIVEL[$servico|$(printf '%s' "$L" | norm)]:-0}" = "1" ]; then
      printf '%s' "$L"
      return 0
    fi
  done
  return 1
}

# A região "geral" precisa servir Storage, Key Vault e Resource Group ao mesmo
# tempo — por isso é a interseção dos dois, não o primeiro de um só.
LOC_GERAL=""
for L in "${ORDENADAS[@]}"; do
  k="$(printf '%s' "$L" | norm)"
  if [ "${DISPONIVEL[storage|$k]:-0}" = "1" ] && [ "${DISPONIVEL[keyvault|$k]:-0}" = "1" ]; then
    LOC_GERAL="$L"
    break
  fi
done

LOC_SQL="$(primeira sql)"       || LOC_SQL="$LOC_GERAL"
LOC_SEARCH="$(primeira search)" || LOC_SEARCH="$LOC_GERAL"
LOC_ACI="$(primeira aci)"       || LOC_ACI="$LOC_GERAL"
LOC_COSMOS="$(primeira cosmos)" || LOC_COSMOS="$LOC_GERAL"

if [ -z "$LOC_GERAL" ]; then
  echo "ERRO: nenhuma região permitida oferece Storage + Key Vault." >&2
  echo "Confirme com o professor se a policy da sua assinatura está correta." >&2
  exit 1
fi

# Alternativas para trocar à mão quando der 503/400 (transitórios).
ALTERNATIVAS=""
for L in "${ORDENADAS[@]}"; do
  [ "$L" = "$LOC_COSMOS" ] && continue
  [ "${DISPONIVEL[cosmos|$(printf '%s' "$L" | norm)]:-0}" = "1" ] && ALTERNATIVAS="$ALTERNATIVAS $L"
done

echo "==> Escolhido:"
echo "    location        = $LOC_GERAL"
echo "    location_sql    = $LOC_SQL"
echo "    location_search = $LOC_SEARCH"
echo "    location_aci    = $LOC_ACI"
echo "    location_cosmos = $LOC_COSMOS"
echo

if [ "$SO_MOSTRAR" = "1" ]; then
  echo "(--so-mostrar: nada foi gravado)"
  exit 0
fi

mkdir -p "$(dirname "$TFVARS")"
[ -f "$TFVARS" ] && cp "$TFVARS" "$TFVARS.bak"

cat > "$TFVARS" <<EOF
# Gerado por check_regions.sh em $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Assinatura: $SUB_ID
#
# Regiões permitidas pela policy desta assinatura:
#   ${PERMITIDAS[*]}
#
# As regiões abaixo são as primeiras, em ordem de preferência, em que o provider
# declara oferecer cada serviço NESTA assinatura. Isso elimina os erros de
# policy e de serviço indisponível na região — mas NÃO garante capacidade no
# momento do apply.
#
# Se o apply falhar com um destes, é transitório: repita antes de trocar região.
#   400 InsufficientResourcesAvailable  -> cota de SKU free esgotada agora
#   503 ServiceUnavailable              -> capacidade da Azure esgotada agora

location        = "$LOC_GERAL"
location_sql    = "$LOC_SQL"
location_search = "$LOC_SEARCH"
location_aci    = "$LOC_ACI"
location_cosmos = "$LOC_COSMOS"

# Alternativas de região para o Cosmos, se o 503 persistir:
#  ${ALTERNATIVAS:- (nenhuma outra região permitida oferece Cosmos)}
#
# Trocar só o Cosmos não recria nada — a conta não precisa ficar na mesma
# região do Resource Group:
#   terraform apply -auto-approve -var="location_cosmos=<outra>"

# A senha do SQL NÃO fica aqui. Passe por variável de ambiente:
#   export TF_VAR_sql_admin_password="\$(openssl rand -base64 24)"
#
# Registry das imagens do ACI (rode setup-registry-aluno.sh):
#   source ~/.qc-registry.env
EOF

echo "==> $TFVARS gravado."
# O "&&" sozinho na última linha faria o script sair com código 1 quando o .bak
# não existe — e um exit code espúrio quebra qualquer uso em pipeline ou CI.
if [ -f "$TFVARS.bak" ]; then
  echo "    (versão anterior em $TFVARS.bak)"
fi

echo
echo "Próximo passo:"
echo "    cd terraform && terraform init && terraform plan"
