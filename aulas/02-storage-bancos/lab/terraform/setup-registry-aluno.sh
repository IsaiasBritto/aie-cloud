#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Cria o ACR do lab NA SUA PROPRIA assinatura e importa as imagens do MongoDB.
# Rode ANTES do "terraform apply". Nao depende do professor.
#
#   bash setup-registry-aluno.sh
#   source ~/.qc-registry.env
#
# Por que existe:
#   O Azure Container Instances puxa a imagem do Docker Hub por IPs de saida
#   compartilhados da regiao. O limite anonimo (100 pulls/6h por IP) estoura
#   quando a turma roda junto, e o apply falha com:
#     409 RegistryErrorResponse: An error response is received from the docker
#     registry 'index.docker.io'. Please retry later.
#   Com um ACR proprio, o pull sai do backbone da Azure e o problema some.
#
# Custo: ACR Basic ~ US$ 0,17/dia. O passo de limpeza no fim do lab remove.
#
# Variaveis opcionais:
#   LOCAL=brazilsouth bash setup-registry-aluno.sh   # regiao do ACR
# ---------------------------------------------------------------------------
set -euo pipefail

RG="${RG:-rg-qc-registry}"
LOCAL="${LOCAL:-eastus2}"
ENV_FILE="${ENV_FILE:-$HOME/.qc-registry.env}"

# Nome do ACR precisa ser unico no mundo inteiro. Derivamos da sua subscription
# para ser deterministico: rodar duas vezes gera o mesmo nome e reaproveita o
# registry em vez de criar outro.
SUB_ID="$(az account show --query id -o tsv)"
ACR="${ACR:-acrqc$(echo "$SUB_ID" | tr -d '-' | cut -c1-12)}"

echo "==> Assinatura: $SUB_ID"
echo "==> Registry:   $ACR  (regiao: $LOCAL)"
echo

# --- valida a regiao contra a policy da assinatura --------------------------
PERMITIDAS="$(az policy assignment list \
  --scope "/subscriptions/$SUB_ID" --disable-scope-strict-match \
  --query "[?contains(displayName,'regions')].parameters.listOfAllowedLocations.value" \
  -o tsv 2>/dev/null || true)"

if [ -n "$PERMITIDAS" ] && ! echo "$PERMITIDAS" | grep -qw "$LOCAL"; then
  echo "ERRO: a regiao '$LOCAL' nao esta permitida na sua assinatura."
  echo "Permitidas: $(echo "$PERMITIDAS" | tr '\n' ' ')"
  echo "Rode de novo escolhendo uma delas, por exemplo:"
  echo "  LOCAL=$(echo "$PERMITIDAS" | head -1) bash $0"
  exit 1
fi

# --- resource group separado ------------------------------------------------
# Proposital: fora do RG do lab. Se o ACR ficasse no mesmo RG, o
# "terraform destroy" falharia com "the Resource Group still contains Resources",
# porque o Terraform nao conhece o registry.
echo "==> Resource Group: $RG"
az group create -n "$RG" -l "$LOCAL" -o none

# --- registry ---------------------------------------------------------------
if az acr show -n "$ACR" -g "$RG" -o none 2>/dev/null; then
  echo "==> Registry ja existe, reaproveitando"
else
  echo "==> Criando registry (~30s)"
  az acr create -g "$RG" -n "$ACR" --sku Basic -l "$LOCAL" -o none
fi

az acr update -n "$ACR" --admin-enabled true -o none

# --- imagens ----------------------------------------------------------------
# O "library/" e obrigatorio para imagens oficiais do Docker Hub. Sem ele a
# Azure procura um repositorio de usuario chamado "mongo-express", que nao
# existe, e o import falha com 401 UNAUTHORIZED.
echo "==> Importando imagens (via backbone da Azure, sem rate limit do seu IP)"
for IMG in "library/mongo:7.0" "library/mongo-express:1.0.2"; do
  DEST="${IMG#library/}"
  if az acr repository show -n "$ACR" --image "$DEST" -o none 2>/dev/null; then
    echo "    $DEST ja esta no registry"
  else
    echo "    importando $DEST"
    az acr import -n "$ACR" --source "docker.io/$IMG" --image "$DEST" --force -o none
  fi
done

echo
az acr repository list -n "$ACR" -o table

# --- grava as variaveis -----------------------------------------------------
cat > "$ENV_FILE" <<EOF
# Gerado por setup-registry-aluno.sh em $(date -u +%Y-%m-%dT%H:%M:%SZ)
export TF_VAR_registry_server="$(az acr show -n "$ACR" --query loginServer -o tsv)"
export TF_VAR_registry_user="$(az acr credential show -n "$ACR" --query username -o tsv)"
export TF_VAR_registry_password="$(az acr credential show -n "$ACR" --query 'passwords[0].value' -o tsv)"
EOF
chmod 600 "$ENV_FILE"

echo
echo "======================================================================"
echo "Pronto. Carregue as variaveis na sua sessao:"
echo
echo "    source $ENV_FILE"
echo
echo "Se a sessao do Cloud Shell cair, rode o source de novo. Se o arquivo"
echo "tambem tiver sumido, rode este script outra vez - ele reaproveita o"
echo "registry existente e leva poucos segundos."
echo "======================================================================"
