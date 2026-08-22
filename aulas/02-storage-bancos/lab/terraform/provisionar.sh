#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Provisiona o lab inteiro com UM comando, recuperando sozinho dos erros de
# região que só aparecem na hora de criar.
#
#   bash provisionar.sh
#
# Por que existe:
#   Três erros do Azure NÃO são detectáveis antes de tentar criar o recurso.
#   O check_regions.sh pega o que é declarável (policy e serviço não oferecido
#   na região); estes aqui só aparecem no apply, e dependem do minuto e da
#   assinatura:
#
#     403 ProvisioningDisabled            -> a assinatura não provisiona esse
#                                            serviço nessa região
#     503 ServiceUnavailable              -> capacidade da Azure esgotada agora
#     400 InsufficientResourcesAvailable  -> cota do SKU free esgotada agora
#
#   Sem este wrapper, o aluno trava no meio da aula lendo um erro de 40 linhas.
#   Com ele, o script troca a região DAQUELE serviço e repete.
#
#   Há ainda um quarto caso, consequência dos anteriores:
#     409 InvalidResourceLocation / already exists
#   Criação que falha deixa Cosmos e SQL Server ocupando o nome. A tentativa
#   seguinte morre com 409 em vez do erro real — mais confuso ainda. O script
#   apaga esse fantasma antes de repetir.
#
# Variáveis opcionais:
#   MAX_TENTATIVAS=6 bash provisionar.sh
# ---------------------------------------------------------------------------
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TFVARS="$DIR/terraform.tfvars"
LOG="$DIR/.provisionar.log"
MAX_TENTATIVAS="${MAX_TENTATIVAS:-5}"

# Ordem de preferência por serviço, aprendida na prática em contas Students.
# A lista final é sempre a interseção com o que a policy da assinatura permite.
PREF_sql="canadacentral southcentralus chilecentral brazilsouth"
PREF_cosmos="eastus2 canadacentral southcentralus brazilsouth"
PREF_search="brazilsouth eastus2 southcentralus canadacentral"
PREF_aci="eastus2 southcentralus brazilsouth canadacentral"
PREF_geral="brazilsouth eastus2 canadacentral southcentralus"

# --------------------------------------------------------------- utilidades ---

log() { echo "$*" | tee -a "$LOG"; }

ler_tfvars() {
  sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\"\([^\"]*\)\".*/\1/p" "$TFVARS" 2>/dev/null | head -1
}

escrever_tfvars() {
  local chave="$1" valor="$2"
  if grep -q "^[[:space:]]*${chave}[[:space:]]*=" "$TFVARS" 2>/dev/null; then
    sed -i "s|^[[:space:]]*${chave}[[:space:]]*=.*|${chave} = \"${valor}\"|" "$TFVARS"
  else
    printf '%s = "%s"\n' "$chave" "$valor" >> "$TFVARS"
  fi
}

# Candidatas para um serviço: preferência conhecida primeiro, depois o resto
# das permitidas, sempre sem repetir e sem a região que acabou de falhar.
candidatas() {
  local servico="$1" excluir="$2" pref var L
  eval "pref=\${PREF_${servico}}"
  for L in $pref $PERMITIDAS; do
    [[ " $PERMITIDAS " == *" $L "* ]] || continue      # tem que ser permitida
    [[ " $excluir " == *" $L "* ]] && continue          # já falhou aqui
    [[ " ${vistas:-} " == *" $L "* ]] && continue
    vistas="${vistas:-} $L"
    printf '%s\n' "$L"
  done
}

proxima_regiao() {  # $1 = servico, $2 = regioes ja tentadas
  local vistas=""
  candidatas "$1" "$2" | head -1
}

# ------------------------------------------------------------- classificação ---
# Descobre, a partir da saída do terraform, QUAIS serviços falharam e por quê.
# Terraform imprime, em cada erro, uma linha "with azurerm_<tipo>.<nome>,".

servico_do_recurso() {
  case "$1" in
    azurerm_mssql_server|azurerm_mssql_database|azurerm_mssql_firewall_rule) echo sql ;;
    azurerm_cosmosdb_*)       echo cosmos ;;
    azurerm_search_service)   echo search ;;
    azurerm_container_group)  echo aci ;;
    azurerm_key_vault_secret) echo segredo ;;
    *)                        echo geral ;;
  esac
}

var_do_servico() {
  case "$1" in
    sql)    echo location_sql ;;
    cosmos) echo location_cosmos ;;
    search) echo location_search ;;
    aci)    echo location_aci ;;
    *)      echo location ;;
  esac
}

# ------------------------------------------------------------------ fantasma ---
# Criação que falha deixa o recurso registrado ocupando o nome. Só Cosmos e SQL
# Server têm esse comportamento no lab. Escopo estrito: apenas o RG do lab.
limpar_fantasma() {
  local servico="$1" rg
  rg="$(ler_tfvars resource_group_name)"
  [ -z "$rg" ] && rg="$(terraform -chdir="$DIR" output -raw resource_group_name 2>/dev/null)"
  [ -z "$rg" ] && return 0

  case "$servico" in
    sql)
      local s
      for s in $(az sql server list -g "$rg" --query "[].name" -o tsv 2>/dev/null); do
        log "    removendo SQL Server fantasma: $s"
        az sql server delete -g "$rg" -n "$s" --yes -o none 2>/dev/null
      done
      ;;
    cosmos)
      local ids
      ids="$(az resource list -g "$rg" --resource-type Microsoft.DocumentDB/databaseAccounts \
             --query "[].id" -o tsv 2>/dev/null)"
      for s in $ids; do
        log "    removendo conta Cosmos fantasma: $(basename "$s")"
        az resource delete --ids "$s" -o none 2>/dev/null
      done
      ;;
    segredo)
      # Key Vault tem SOFT DELETE. Apagar o vault e recriá-lo com o mesmo nome
      # faz a Azure RESTAURAR o vault anterior, segredos inclusive — com valores
      # velhos, apontando para recursos que já não existem. O Terraform então
      # para com "already exists - needs to be imported into the State".
      #
      # Só o "delete" não resolve: o segredo fica em estado deleted e o nome
      # continua reservado. Precisa do "purge".
      local kv seg
      kv="$(terraform -chdir="$DIR" output -raw key_vault_name 2>/dev/null)"
      [ -z "$kv" ] && return 0
      for seg in sql-connection-string cosmos-primary-key; do
        if az keyvault secret show --vault-name "$kv" --name "$seg" -o none 2>/dev/null; then
          log "    removendo segredo restaurado pelo soft delete: $seg"
          az keyvault secret delete --vault-name "$kv" --name "$seg" -o none 2>/dev/null
          sleep 10
          az keyvault secret purge --vault-name "$kv" --name "$seg" -o none 2>/dev/null
        fi
      done
      ;;
  esac
}

# ------------------------------------------------------------------ preflight ---

: > "$LOG"
log "== Provisionamento do lab — Aula 2 =="
log

command -v terraform >/dev/null || { log "ERRO: terraform não encontrado."; exit 1; }
az account show -o none 2>/dev/null || { log "ERRO: rode 'az login' antes."; exit 1; }

SUB_ID="$(az account show --query id -o tsv)"
log "Assinatura: $SUB_ID"

PERMITIDAS="$(az policy assignment list \
  --scope "/subscriptions/$SUB_ID" --disable-scope-strict-match \
  --query "[?contains(displayName,'regions')].parameters.listOfAllowedLocations.value" \
  -o tsv 2>/dev/null | tr '\t' '\n' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tr '\n' ' ')"

if [ -z "${PERMITIDAS// /}" ]; then
  PERMITIDAS="$(az account list-locations --query "[].name" -o tsv | tr '\n' ' ')"
  log "Sem policy de região; usando todas as regiões da assinatura."
else
  log "Regiões permitidas: $PERMITIDAS"
fi

# tfvars — gera se não existir
if [ ! -f "$TFVARS" ]; then
  log "terraform.tfvars não existe; rodando check_regions.sh..."
  bash "$DIR/../check_regions.sh" >> "$LOG" 2>&1 || {
    log "ERRO: check_regions.sh falhou. Veja $LOG"
    exit 1
  }
fi

# senha do SQL — gera se faltar, e mostra UMA vez
if [ -z "${TF_VAR_sql_admin_password:-}" ]; then
  export TF_VAR_sql_admin_password="$(openssl rand -base64 24)"
  log
  log "Senha do SQL gerada (ANOTE, ela não é gravada em disco):"
  log "    $TF_VAR_sql_admin_password"
  log
fi

# registry do MongoDB — sem ele o ACI puxa do Docker Hub e pode dar 409
if [ -z "${TF_VAR_registry_server:-}" ]; then
  if [ -f "$HOME/.qc-registry.env" ]; then
    # shellcheck source=/dev/null
    . "$HOME/.qc-registry.env"
    log "Registry carregado de ~/.qc-registry.env: $TF_VAR_registry_server"
  else
    log "Registry não configurado; rodando setup-registry-aluno.sh..."
    # shellcheck source=/dev/null
    . "$DIR/setup-registry-aluno.sh" >> "$LOG" 2>&1 || {
      log "AVISO: não consegui preparar o registry. O lab segue puxando do"
      log "       Docker Hub, o que pode falhar com 409 se a turma rodar junto."
    }
  fi
fi

terraform -chdir="$DIR" init -input=false >> "$LOG" 2>&1 || {
  log "ERRO: terraform init falhou. Veja $LOG"
  exit 1
}

# ---------------------------------------------------------------------- loop ---

declare -A JA_TENTADAS   # servico -> regioes que já falharam

for (( tentativa = 1; tentativa <= MAX_TENTATIVAS; tentativa++ )); do
  log
  log "-- Tentativa $tentativa/$MAX_TENTATIVAS --"
  for v in location location_sql location_search location_aci location_cosmos; do
    log "   $v = $(ler_tfvars "$v")"
  done

  SAIDA="$(terraform -chdir="$DIR" apply -auto-approve -input=false 2>&1)"
  RC=$?
  printf '%s\n' "$SAIDA" >> "$LOG"

  if [ $RC -eq 0 ]; then
    log
    log "== Provisionado com sucesso na tentativa $tentativa =="
    terraform -chdir="$DIR" output
    log
    log "Log completo em $LOG"
    exit 0
  fi

  # --- que recursos falharam? ---
  RECURSOS="$(printf '%s\n' "$SAIDA" | sed -n 's/.*with \(azurerm_[a-z_]*\)\..*/\1/p' | sort -u)"
  if [ -z "$RECURSOS" ]; then
    log
    log "ERRO não reconhecido — não é problema de região. Últimas linhas:"
    printf '%s\n' "$SAIDA" | grep -E "^│ (Error|Message)" | head -5 | tee -a "$LOG"
    log "Log completo em $LOG"
    exit 1
  fi

  MUDOU=0
  for recurso in $RECURSOS; do
    servico="$(servico_do_recurso "$recurso")"
    var="$(var_do_servico "$servico")"
    atual="$(ler_tfvars "$var")"

    # Nome ocupado por criação anterior que falhou, ou por soft delete do Key
    # Vault. Limpa e repete NA MESMA região — trocar aqui só criaria um segundo
    # fantasma.
    if printf '%s' "$SAIDA" | grep -qE "InvalidResourceLocation|already exists|needs to be imported"; then
      log "  [$servico] nome ocupado por criação anterior que falhou"
      limpar_fantasma "$servico"
      MUDOU=1
      continue
    fi

    # 503 e 400 são transitórios: na primeira vez, repete na mesma região.
    if printf '%s' "$SAIDA" | grep -qE "ServiceUnavailable|InsufficientResourcesAvailable" \
       && [ -z "${JA_TENTADAS[$servico]:-}" ]; then
      log "  [$servico] erro transitório em '$atual' — repetindo na mesma região"
      JA_TENTADAS[$servico]="$atual"
      MUDOU=1
      continue
    fi

    JA_TENTADAS[$servico]="${JA_TENTADAS[$servico]:-} $atual"
    nova="$(proxima_regiao "$servico" "${JA_TENTADAS[$servico]}")"

    if [ -z "$nova" ]; then
      log "  [$servico] acabaram as regiões permitidas. Já tentei:${JA_TENTADAS[$servico]}"
      continue
    fi

    log "  [$servico] '$atual' não serve — trocando para '$nova'"
    limpar_fantasma "$servico"
    escrever_tfvars "$var" "$nova"
    MUDOU=1
  done

  if [ $MUDOU -eq 0 ]; then
    log
    log "Não há mais o que tentar automaticamente."
    log "Log completo em $LOG"
    exit 1
  fi
done

log
log "Esgotei $MAX_TENTATIVAS tentativas. Log completo em $LOG"
exit 1
