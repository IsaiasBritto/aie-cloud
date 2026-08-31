#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo 2 — construir as imagens dentro do Azure Container Registry
#
# `az acr build` envia o contexto e constrói NA NUVEM: o aluno não precisa
# ter Docker instalado na máquina dele. É o atalho que salva a aula.
#
# Uso:  SUFIXO=fiap01 VERSAO=v1 bash infra/02-publicar-imagens.sh
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_az
mostrar_alvo

azul "Construindo deva3-api:${VERSAO} no registro ${ACR}..."
az acr build \
  --registry "$ACR" \
  --image "deva3-api:${VERSAO}" \
  --file api/Dockerfile \
  .

azul "Construindo deva3-web:${VERSAO} no registro ${ACR}..."
az acr build \
  --registry "$ACR" \
  --image "deva3-web:${VERSAO}" \
  --file web/Dockerfile \
  .

verde ""
verde "✔ Imagens publicadas:"
az acr repository show-tags --name "$ACR" --repository deva3-api -o table || true
az acr repository show-tags --name "$ACR" --repository deva3-web -o table || true
verde ""
verde "  Próximo passo:  bash infra/03-implantar-apps.sh"
