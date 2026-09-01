#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-variaveis.sh"
: "${CONEXAO:?exporte CONEXAO com a cadeia de conexão do armazenamento (saída do script 01)}"

SEGREDO_AUDITOR="${SEGREDO_AUDITOR:-$(openssl rand -hex 12)}"
SERVIDOR=$(az acr show --name "$REGISTRO" --query loginServer -o tsv)
USUARIO=$(az acr credential show --name "$REGISTRO" --query username -o tsv)
SENHA=$(az acr credential show --name "$REGISTRO" --query "passwords[0].value" -o tsv)

# --min-replicas 0: fora da aula os containers dormem e não cobram.
az containerapp create --name "$APP_API" --resource-group "$GRUPO" \
  --environment "$AMBIENTE" --image "$SERVIDOR/$IMAGEM_API" \
  --registry-server "$SERVIDOR" --registry-username "$USUARIO" --registry-password "$SENHA" \
  --target-port 8000 --ingress external --min-replicas 0 --max-replicas 2 \
  --cpu 0.5 --memory 1.0Gi \
  --secrets "conexao=$CONEXAO" "segredo=$SEGREDO_AUDITOR" \
  --env-vars "DEVA_BLOB_CONEXAO=secretref:conexao" \
             "DEVA_BLOB_CONTAINER=$CONTAINER_MEMORIA" \
             "DEVA_SEGREDO_AUDITOR=secretref:segredo" \
  --output none
URL_API="https://$(az containerapp show --name "$APP_API" --resource-group "$GRUPO" \
  --query properties.configuration.ingress.fqdn -o tsv)"
echo "✓ API em $URL_API"

az containerapp create --name "$APP_WEB" --resource-group "$GRUPO" \
  --environment "$AMBIENTE" --image "$SERVIDOR/$IMAGEM_WEB" \
  --registry-server "$SERVIDOR" --registry-username "$USUARIO" --registry-password "$SENHA" \
  --target-port 8501 --ingress external --min-replicas 0 --max-replicas 1 \
  --cpu 0.5 --memory 1.0Gi \
  --secrets "segredo=$SEGREDO_AUDITOR" \
  --env-vars "DEVA_API=$URL_API" "DEVA_SEGREDO_AUDITOR=secretref:segredo" \
  --output none
URL_WEB="https://$(az containerapp show --name "$APP_WEB" --resource-group "$GRUPO" \
  --query properties.configuration.ingress.fqdn -o tsv)"

echo "✓ Tela em $URL_WEB"
echo
echo "Agora gere a especificação do agente apontando para a API:"
echo "  python gerar_openapi_do_agente.py   # e troque https://SUA-URL/ por $URL_API"
echo
echo "Guarde o segredo do auditor (a tela já está com ele): $SEGREDO_AUDITOR"
