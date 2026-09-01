#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-variaveis.sh"
cd "$(dirname "$0")/.."

# az acr build constrói NA NUVEM: não precisa de Docker na máquina do aluno.
az acr build --registry "$REGISTRO" --image "$IMAGEM_API" --file api/Dockerfile .
echo "✓ imagem da API publicada"

az acr build --registry "$REGISTRO" --image "$IMAGEM_WEB" --file web/Dockerfile .
echo "✓ imagem da tela publicada"
