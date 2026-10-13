#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo 3 — implantar (ou atualizar) os dois Container Apps
#
#   ca-deva3-api  → porta 8000, entrada externa, guarda os segredos
#   ca-deva3-web  → porta 8501, entrada externa, aponta para a API
#
# Uso:  SUFIXO=fiap01 VERSAO=v1 bash infra/03-implantar-apps.sh
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_az
mostrar_alvo

# ── recuperar os valores dos recursos já criados ─────────────────────────
azul "Lendo endpoint e chaves dos recursos existentes..."
VISAO_ENDPOINT=$(az cognitiveservices account show \
  --name "$RECURSO_VISAO" --resource-group "$GRUPO" \
  --query properties.endpoint -o tsv); VISAO_ENDPOINT="${VISAO_ENDPOINT%/}"
VISAO_CHAVE=$(az cognitiveservices account keys list \
  --name "$RECURSO_VISAO" --resource-group "$GRUPO" --query key1 -o tsv)
CONEXAO_ARMAZENAMENTO=$(az storage account show-connection-string \
  --name "$CONTA_ARMAZENAMENTO" --resource-group "$GRUPO" \
  --query connectionString -o tsv)

USUARIO_ACR=$(az acr credential show --name "$ACR" --query username -o tsv)
SENHA_ACR=$(az acr credential show --name "$ACR" --query "passwords[0].value" -o tsv)

existe_app() {
  az containerapp show -n "$1" -g "$GRUPO" >/dev/null 2>&1
}

# ── API ──────────────────────────────────────────────────────────────────
azul "Implantando ${APP_API}..."
if existe_app "$APP_API"; then
  az containerapp update \
    --name "$APP_API" --resource-group "$GRUPO" \
    --image "${ACR}.azurecr.io/deva3-api:${VERSAO}" \
    --only-show-errors -o none
else
  az containerapp create \
    --name "$APP_API" \
    --resource-group "$GRUPO" \
    --environment "$AMBIENTE_APPS" \
    --image "${ACR}.azurecr.io/deva3-api:${VERSAO}" \
    --registry-server "${ACR}.azurecr.io" \
    --registry-username "$USUARIO_ACR" \
    --registry-password "$SENHA_ACR" \
    --target-port 8000 \
    --ingress external \
    --min-replicas 0 --max-replicas 2 \
    --cpu 0.5 --memory 1.0Gi \
    --secrets "visao-chave=${VISAO_CHAVE}" \
              "armazenamento-conexao=${CONEXAO_ARMAZENAMENTO}" \
    --env-vars "AMBIENTE=azure" \
               "VISAO_ENDPOINT=${VISAO_ENDPOINT}" \
               "VISAO_CHAVE=secretref:visao-chave" \
               "ARMAZENAMENTO_CONEXAO=secretref:armazenamento-conexao" \
               "ARMAZENAMENTO_CONTAINER=${CONTAINER_BLOB}" \
               "PERSISTIR_IMAGENS=true" \
               "LIMIAR_CONFIANCA=0.60" \
    --only-show-errors -o none
fi

URL_API=$(az containerapp show -n "$APP_API" -g "$GRUPO" \
  --query properties.configuration.ingress.fqdn -o tsv)

# ── Interface ────────────────────────────────────────────────────────────
azul "Implantando ${APP_WEB} apontando para https://${URL_API}..."
if existe_app "$APP_WEB"; then
  az containerapp update \
    --name "$APP_WEB" --resource-group "$GRUPO" \
    --image "${ACR}.azurecr.io/deva3-web:${VERSAO}" \
    --set-env-vars "API_URL=https://${URL_API}" \
    --only-show-errors -o none
else
  az containerapp create \
    --name "$APP_WEB" \
    --resource-group "$GRUPO" \
    --environment "$AMBIENTE_APPS" \
    --image "${ACR}.azurecr.io/deva3-web:${VERSAO}" \
    --registry-server "${ACR}.azurecr.io" \
    --registry-username "$USUARIO_ACR" \
    --registry-password "$SENHA_ACR" \
    --target-port 8501 \
    --ingress external \
    --min-replicas 0 --max-replicas 2 \
    --cpu 0.5 --memory 1.0Gi \
    --env-vars "API_URL=https://${URL_API}" \
    --only-show-errors -o none
fi

URL_WEB=$(az containerapp show -n "$APP_WEB" -g "$GRUPO" \
  --query properties.configuration.ingress.fqdn -o tsv)

# ── verificação ──────────────────────────────────────────────────────────
azul "Verificando a saúde da API..."
sleep 12
curl -s "https://${URL_API}/saude" || amarelo "Ainda subindo. Tente de novo em 30 s."

verde ""
verde "✔ Implantação concluída."
verde "  API ......... https://${URL_API}"
verde "  Documentação  https://${URL_API}/docs"
verde "  Interface ... https://${URL_WEB}"
verde ""
verde "  No fim da aula, apague tudo:  bash infra/99-remover-tudo.sh"
