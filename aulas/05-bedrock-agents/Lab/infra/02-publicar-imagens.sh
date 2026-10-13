#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo 2 — construir as duas imagens e enviar ao ECR
#
# O build roda no CloudShell (tem Docker). O login no ECR usa a credencial da
# sua sessão: nenhuma senha de registro fica guardada em lugar nenhum — ao
# contrário do `az acr credential show` da versão Azure.
#
# Uso:  VERSAO=v1 bash infra/02-publicar-imagens.sh
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_ferramentas
command -v docker >/dev/null 2>&1 || { vermelho "Docker não encontrado. Use o CloudShell."; exit 1; }

ECR_API=$(saida ecr_api)
ECR_WEB=$(saida ecr_web)
REGISTRO="${ECR_API%%/*}"

azul "Login no ECR (${REGISTRO})..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRO"

azul "Construindo deva3-api:${VERSAO}..."
docker build -f "$RAIZ/api/Dockerfile" -t "${ECR_API}:${VERSAO}" "$RAIZ"
azul "Construindo deva3-web:${VERSAO}..."
docker build -f "$RAIZ/web/Dockerfile" -t "${ECR_WEB}:${VERSAO}" "$RAIZ"

azul "Enviando..."
docker push "${ECR_API}:${VERSAO}"
docker push "${ECR_WEB}:${VERSAO}"

verde "Imagens publicadas com a etiqueta ${VERSAO}."
echo "Próximo passo:  VERSAO=${VERSAO} bash infra/03-implantar-apps.sh"
