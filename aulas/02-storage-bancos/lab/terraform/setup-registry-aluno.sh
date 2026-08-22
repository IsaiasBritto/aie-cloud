#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Cria o ACR do lab NA SUA PROPRIA assinatura e importa as imagens do MongoDB.
# Rode ANTES do "terraform apply". Nao depende do professor.
#
# Forma recomendada (uma linha, ja deixa as variaveis na sessao):
#
#   source setup-registry-aluno.sh
#
# Tambem funciona executado, mas ai o "source" vira passo separado:
#
#   bash setup-registry-aluno.sh
#   source ~/.qc-registry.env
#
# A REGIAO E AUTOMATICA: le "location_aci" do terraform.tfvars gerado pelo
# check_regions.sh (Passo 0). Passe LOCAL= so para sobrescrever.
#
# Por que existe:
#   O Azure Container Instances puxa a imagem do Docker Hub por IPs de saida
#   compartilhados da regiao. O limite anonimo (100 pulls/6h por IP) estoura
#   quando a turma roda junto, e o apply falha com:
#     409 RegistryErrorResponse: An error response is received from the docker
#     registry 'index.docker.io'. Please retry later.
#   Com um registry proprio, o pull sai do backbone da Azure e o problema some.
#
# Custo: ACR Basic ~ US$ 0,17/dia. O passo de limpeza no fim do lab remove.
# ---------------------------------------------------------------------------

# NAO use "set -e": carregado com "source", este arquivo roda no shell do aluno,
# e um erro qualquer fecharia o terminal dele. Os comandos que importam sao
# checados um a um.
set -uo pipefail

# "${BASH_SOURCE[0]}" e o caminho do arquivo; "$0" e o do processo. Sao
# diferentes exatamente quando o arquivo foi carregado com "source".
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
  _QC_SOURCED=1
else
  _QC_SOURCED=0
fi

# Le 'chave = "valor"' do terraform.tfvars, ignorando comentarios.
_qc_ler_tfvars() {
  local chave="$1" arquivo="$2"
  [ -f "$arquivo" ] || return 1
  sed -n "s/^[[:space:]]*${chave}[[:space:]]*=[[:space:]]*\"\([^\"]*\)\".*/\1/p" "$arquivo" | head -1
}

_qc_setup_registry() {
  # ATENCAO aos nomes com "_" no inicio.
  # As variaveis que o aluno sobrescreve pelo ambiente (LOCAL, RG, ACR,
  # ENV_FILE, TFVARS) NAO podem aparecer num "local": bash cria a local vazia e
  # descarta o valor herdado, e "LOCAL=brazilsouth bash setup-registry-aluno.sh"
  # passaria a ser ignorado em silencio. Por isso lemos para nomes internos.
  local dir sub_id permitidas origem
  local reg_local reg_rg reg_acr reg_envfile reg_tfvars
  local img dest server user pass

  dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  reg_tfvars="${TFVARS:-$dir/terraform.tfvars}"
  reg_local="${LOCAL:-}"
  reg_rg="${RG:-rg-qc-registry}"
  reg_envfile="${ENV_FILE:-$HOME/.qc-registry.env}"

  sub_id="$(az account show --query id -o tsv 2>/dev/null)" || {
    echo "ERRO: nao consegui ler a assinatura. Rode 'az login' antes." >&2
    return 1
  }

  # --- de onde vem a regiao -------------------------------------------------
  # Ordem: LOCAL do ambiente > location_aci do tfvars > location do tfvars >
  #        primeira permitida pela policy > eastus2.
  # O registry acompanha o ACI de proposito: e o ACI quem puxa a imagem.
  if [ -n "$reg_local" ]; then
    origem="variavel LOCAL"
  elif reg_local="$(_qc_ler_tfvars location_aci "$reg_tfvars")" && [ -n "$reg_local" ]; then
    origem="location_aci de $(basename "$reg_tfvars")"
  elif reg_local="$(_qc_ler_tfvars location "$reg_tfvars")" && [ -n "$reg_local" ]; then
    origem="location de $(basename "$reg_tfvars")"
  else
    reg_local=""
    origem="padrao"
  fi

  # --- regioes permitidas pela policy ---------------------------------------
  # "az ... -o tsv" devolve o array numa UNICA linha separada por TAB; sem o
  # "tr" a comparacao nunca casa.
  permitidas="$(az policy assignment list \
    --scope "/subscriptions/$sub_id" --disable-scope-strict-match \
    --query "[?contains(displayName,'regions')].parameters.listOfAllowedLocations.value" \
    -o tsv 2>/dev/null | tr '\t' '\n' | tr -d '\r' | sed '/^[[:space:]]*$/d')"

  if [ -z "$reg_local" ]; then
    if [ -n "$permitidas" ]; then
      reg_local="$(printf '%s\n' "$permitidas" | head -1)"
      origem="primeira permitida pela policy"
    else
      reg_local="eastus2"
      origem="padrao"
    fi
  fi

  if [ -n "$permitidas" ] && ! printf '%s\n' "$permitidas" | grep -qx "$reg_local"; then
    echo "ERRO: a regiao '$reg_local' ($origem) nao esta permitida na sua assinatura." >&2
    echo "Permitidas: $(printf '%s' "$permitidas" | tr '\n' ' ')" >&2
    echo "Rode o Passo 0 de novo (bash ../check_regions.sh) ou force:" >&2
    echo "  LOCAL=$(printf '%s\n' "$permitidas" | head -1) source ${BASH_SOURCE[0]}" >&2
    return 1
  fi

  # Nome de registry e unico no mundo inteiro. Derivamos da subscription para
  # ser deterministico: rodar duas vezes gera o mesmo nome e reaproveita.
  reg_acr="${ACR:-acrqc$(echo "$sub_id" | tr -d '-' | cut -c1-12)}"

  echo "==> Assinatura: $sub_id"
  echo "==> Regiao:     $reg_local   ($origem)"
  echo "==> Registry:   $reg_acr"
  echo

  # --- resource group separado ----------------------------------------------
  # Proposital: fora do resource group do lab. Se o registry ficasse la, o
  # "terraform destroy" falharia com "the Resource Group still contains
  # Resources", porque o Terraform nao conhece esse recurso.
  echo "==> Resource Group: $reg_rg"
  az group create -n "$reg_rg" -l "$reg_local" -o none || {
    echo "ERRO: falha ao criar o resource group em '$reg_local'." >&2
    return 1
  }

  # --- registry --------------------------------------------------------------
  if az acr show -n "$reg_acr" -g "$reg_rg" -o none 2>/dev/null; then
    echo "==> Registry ja existe, reaproveitando"
  else
    echo "==> Criando registry (~30s)"
    az acr create -g "$reg_rg" -n "$reg_acr" --sku Basic -l "$reg_local" -o none || {
      echo "ERRO: falha ao criar o registry '$reg_acr'." >&2
      return 1
    }
  fi

  az acr update -n "$reg_acr" --admin-enabled true -o none || return 1

  # --- imagens ---------------------------------------------------------------
  # O "library/" e obrigatorio para imagens oficiais do Docker Hub. Sem ele a
  # Azure procura um repositorio de usuario chamado "mongo-express", que nao
  # existe, e o import falha com 401 UNAUTHORIZED.
  echo "==> Importando imagens (via backbone da Azure, sem rate limit do seu IP)"
  for img in "library/mongo:7.0" "library/mongo-express:1.0.2"; do
    dest="${img#library/}"
    if az acr repository show -n "$reg_acr" --image "$dest" -o none 2>/dev/null; then
      echo "    $dest ja esta no registry"
    else
      echo "    importando $dest"
      az acr import -n "$reg_acr" --source "docker.io/$img" --image "$dest" --force -o none || {
        echo "ERRO: falha ao importar $dest." >&2
        return 1
      }
    fi
  done

  echo
  az acr repository list -n "$reg_acr" -o table

  # --- grava as variaveis ----------------------------------------------------
  server="$(az acr show -n "$reg_acr" --query loginServer -o tsv)"
  user="$(az acr credential show -n "$reg_acr" --query username -o tsv)"
  pass="$(az acr credential show -n "$reg_acr" --query 'passwords[0].value' -o tsv)"

  # Senha de registry tem ~50 caracteres. Vindo curta, o valor foi truncado, e o
  # apply so falharia bem depois com InaccessibleImage — erro que nao aponta
  # para ca. Melhor parar agora.
  if [ "${#pass}" -lt 20 ]; then
    echo "ERRO: a senha do registry veio com ${#pass} caracteres (esperado ~50)." >&2
    echo "Rode de novo; se persistir, confira 'az acr credential show -n $reg_acr'." >&2
    return 1
  fi

  umask 077
  cat > "$reg_envfile" <<EOF
# Gerado por setup-registry-aluno.sh em $(date -u +%Y-%m-%dT%H:%M:%SZ)
export TF_VAR_registry_server="$server"
export TF_VAR_registry_user="$user"
export TF_VAR_registry_password="$pass"
EOF
  chmod 600 "$reg_envfile"

  echo
  echo "======================================================================"
  if [ "$_QC_SOURCED" = "1" ]; then
    # shellcheck source=/dev/null
    . "$reg_envfile"
    echo "Pronto. Variaveis ja carregadas NESTA sessao:"
    echo
    echo "    registry=[$TF_VAR_registry_server]"
    echo "    usuario =[$TF_VAR_registry_user]   senha=[${#TF_VAR_registry_password} chars]"
    echo
    echo "Pode seguir direto para o terraform apply."
  else
    echo "Pronto. Carregue as variaveis na sua sessao:"
    echo
    echo "    source $reg_envfile"
    echo
    echo "(Da proxima vez use 'source setup-registry-aluno.sh' e este passo some.)"
  fi
  echo
  echo "Se a sessao do Cloud Shell cair, repita o source. Se o arquivo tambem"
  echo "tiver sumido, rode este script outra vez — ele reaproveita o registry"
  echo "existente e leva poucos segundos."
  echo "======================================================================"
}

_qc_setup_registry
_QC_RC=$?

if [ "$_QC_SOURCED" = "1" ]; then
  unset -f _qc_setup_registry _qc_ler_tfvars
  unset _QC_SOURCED
  # "return" so vale em arquivo carregado com source — nao troque por "exit",
  # ou o terminal do aluno fecha.
  return $_QC_RC
else
  exit $_QC_RC
fi
