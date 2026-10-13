#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo 99 — apagar tudo
#
# Remove serviço, cluster, repositórios (com as imagens), logs e o bucket —
# inclusive as fotos que alguém autorizou guardar. É o "jeito de apagar" que a
# LGPD exige, e é também o controle de custo mais eficaz que existe.
#
# Uso:  bash infra/99-remover-tudo.sh
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_ferramentas
mostrar_alvo

amarelo "Isto apaga o bucket com TODAS as imagens e resultados, e as imagens do ECR."
read -r -p "Digite 'apagar' para confirmar: " RESPOSTA
[ "$RESPOSTA" = "apagar" ] || { echo "Cancelado."; exit 0; }

tf destroy -input=false -auto-approve

verde "Tudo removido. Confira no Tag Editor (tag projeto = deva3) que nada sobrou."
