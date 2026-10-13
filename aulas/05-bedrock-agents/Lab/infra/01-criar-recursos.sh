#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo 1 — criar os recursos (sem o serviço ECS)
#
#   S3 (bucket com retenção LGPD) · ECR (api e web) · cluster ECS · logs · SG
#
# O serviço só nasce no passo 3: ele precisa das imagens, que nascem no 2.
# Uso:  bash infra/01-criar-recursos.sh
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_ferramentas
mostrar_alvo

azul "terraform init..."
tf init -input=false -upgrade >/dev/null

azul "terraform apply (servico_ativo=false)..."
tf apply -input=false -auto-approve -var servico_ativo=false "$@"

verde "Recursos criados."
echo
echo "Para rodar a API na SUA máquina gravando no S3, coloque no .env:"
echo "  ARMAZENAMENTO_BUCKET=$(saida bucket)"
echo
echo "Próximo passo:  bash infra/02-publicar-imagens.sh"
