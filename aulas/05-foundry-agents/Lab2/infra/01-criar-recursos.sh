#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-variaveis.sh"

echo
echo "Isto cria recursos que CUSTAM. Antes de continuar, confirme que você já criou o"
echo "orçamento com alerta (Módulo 0 do lab). Digite CRIAR para seguir:"
read -r confirmacao
[ "$confirmacao" = "CRIAR" ] || { echo "Cancelado."; exit 1; }

az group create --name "$GRUPO" --location "$REGIAO" --output none
echo "✓ grupo $GRUPO"

az storage account create --name "$ARMAZENAMENTO" --resource-group "$GRUPO" \
  --location "$REGIAO" --sku Standard_LRS --kind StorageV2 \
  --allow-blob-public-access false --output none
echo "✓ conta de armazenamento $ARMAZENAMENTO"

CONEXAO=$(az storage account show-connection-string --name "$ARMAZENAMENTO" \
  --resource-group "$GRUPO" --query connectionString -o tsv)

for c in "$CONTAINER_MEMORIA" "$CONTAINER_ENTRADA"; do
  az storage container create --name "$c" --connection-string "$CONEXAO" --output none
  echo "✓ container $c"
done

az acr create --name "$REGISTRO" --resource-group "$GRUPO" --sku Basic \
  --admin-enabled true --output none
echo "✓ registro de container $REGISTRO"

az containerapp env create --name "$AMBIENTE" --resource-group "$GRUPO" \
  --location "$REGIAO" --output none
echo "✓ ambiente de Container Apps $AMBIENTE"

echo
echo "Pronto. Guarde a cadeia de conexão para o próximo script:"
echo "export CONEXAO='$CONEXAO'"
