#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo 1 — criar os recursos base no Azure
#
#   Grupo de recursos ................ rg-aula-05
#   Conta de armazenamento + blob .... stdeva3<sufixo> / deteccoes
#   Recurso de visão ................. cv-deva3-<sufixo>
#   Registro de containers ........... acrdeva3<sufixo>
#   Ambiente de Container Apps ....... cae-aula-05
#
# Uso:  SUFIXO=fiap01 bash infra/01-criar-recursos.sh
#
# ⚠️ Este script CRIA recursos que geram custo na sua assinatura.
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_az
mostrar_alvo

amarelo "Este script vai criar recursos que geram custo. Continuar? (digite: sim)"
read -r resposta
[[ "$resposta" == "sim" ]] || { echo "Cancelado."; exit 0; }

# ── 0. Pré-requisitos da assinatura ──────────────────────────────────────
azul "[0/6] Registrando provedores e extensão de Container Apps..."
az extension add --name containerapp --upgrade --only-show-errors
az provider register -n Microsoft.App --wait
az provider register -n Microsoft.OperationalInsights --wait
az provider register -n Microsoft.ContainerRegistry --wait
az provider register -n Microsoft.CognitiveServices --wait

# ── 1. Grupo de recursos ─────────────────────────────────────────────────
azul "[1/6] Criando o grupo ${GRUPO}..."
az group create \
  --name "$GRUPO" \
  --location "$REGIAO" \
  --tags disciplina=cloud aula=05 projeto=deva3 responsavel="isaias" \
  --only-show-errors -o none

# ── 2. Conta de armazenamento + container de blobs ───────────────────────
azul "[2/6] Criando a conta de armazenamento ${CONTA_ARMAZENAMENTO}..."
az storage account create \
  --name "$CONTA_ARMAZENAMENTO" \
  --resource-group "$GRUPO" \
  --location "$REGIAO" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --only-show-errors -o none

CONEXAO_ARMAZENAMENTO=$(az storage account show-connection-string \
  --name "$CONTA_ARMAZENAMENTO" --resource-group "$GRUPO" \
  --query connectionString -o tsv)

azul "      Criando o container '${CONTAINER_BLOB}' (privado)..."
az storage container create \
  --name "$CONTAINER_BLOB" \
  --connection-string "$CONEXAO_ARMAZENAMENTO" \
  --public-access off \
  --only-show-errors -o none

# ── 3. Recurso de visão ──────────────────────────────────────────────────
azul "[3/6] Criando o recurso de visão ${RECURSO_VISAO} (nível ${NIVEL_VISAO})..."
az cognitiveservices account create \
  --name "$RECURSO_VISAO" \
  --resource-group "$GRUPO" \
  --location "$REGIAO" \
  --kind ComputerVision \
  --sku "$NIVEL_VISAO" \
  --custom-domain "$RECURSO_VISAO" \
  --yes \
  --only-show-errors -o none

VISAO_ENDPOINT=$(az cognitiveservices account show \
  --name "$RECURSO_VISAO" --resource-group "$GRUPO" \
  --query properties.endpoint -o tsv)
VISAO_CHAVE=$(az cognitiveservices account keys list \
  --name "$RECURSO_VISAO" --resource-group "$GRUPO" \
  --query key1 -o tsv)

# A Azure devolve o endpoint com barra no final; a nossa API não aceita.
VISAO_ENDPOINT="${VISAO_ENDPOINT%/}"

# ── 4. Registro de containers ────────────────────────────────────────────
azul "[4/6] Criando o registro de containers ${ACR}..."
az acr create \
  --name "$ACR" \
  --resource-group "$GRUPO" \
  --location "$REGIAO" \
  --sku Basic \
  --admin-enabled true \
  --only-show-errors -o none

# ── 5. Ambiente de Container Apps ────────────────────────────────────────
azul "[5/6] Criando o ambiente de Container Apps ${AMBIENTE_APPS}..."
az containerapp env create \
  --name "$AMBIENTE_APPS" \
  --resource-group "$GRUPO" \
  --location "$REGIAO" \
  --only-show-errors -o none

# ── 6. Arquivo .env local ────────────────────────────────────────────────
azul "[6/6] Gravando o arquivo .env local..."
cat > .env <<ARQUIVO
# Gerado por infra/01-criar-recursos.sh em $(date -u +"%Y-%m-%d %H:%M UTC")
# ⚠️ Este arquivo contém segredos. Ele está no .gitignore. Não versione.
AMBIENTE=local

VISAO_ENDPOINT=${VISAO_ENDPOINT}
VISAO_CHAVE=${VISAO_CHAVE}
VISAO_API_VERSAO=2024-02-01

FACE_ENDPOINT=
FACE_CHAVE=
FACE_MODELO_DETECCAO=detection_03

ARMAZENAMENTO_CONEXAO=${CONEXAO_ARMAZENAMENTO}
ARMAZENAMENTO_CONTAINER=${CONTAINER_BLOB}
PERSISTIR_IMAGENS=true

TAMANHO_MAXIMO_MB=4
LIMIAR_CONFIANCA=0.60
TEMPO_LIMITE_SEGUNDOS=30
ORIGENS_PERMITIDAS=*

API_URL=http://localhost:8000
ARQUIVO

verde ""
verde "✔ Recursos criados no grupo ${GRUPO}."
verde "  Endpoint de visão : ${VISAO_ENDPOINT}"
verde "  Registro          : ${ACR}.azurecr.io"
verde "  Blob              : ${CONTA_ARMAZENAMENTO}/${CONTAINER_BLOB}"
verde ""
verde "  O arquivo .env foi gravado. Teste localmente com:  docker compose up --build"
verde "  Depois publique com:                               bash infra/02-publicar-imagens.sh"
