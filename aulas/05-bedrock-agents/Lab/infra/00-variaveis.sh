#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · variáveis e utilitários compartilhados pelos scripts de infra.
#
# Não execute este arquivo sozinho: os outros scripts o carregam com `source`.
#
# Diferente da versão Azure, não há SUFIXO para escolher: o Terraform sorteia
# um (random_string) e guarda no estado. Nome de bucket é único no mundo, e o
# sorteio evita a colisão entre colegas da mesma turma.
# ─────────────────────────────────────────────────────────────────────────

set -euo pipefail

INFRA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export INFRA
export TF_DIR="$INFRA/terraform"
export RAIZ="$INFRA/.."                     # contexto do docker build (pasta Lab)
export AWS_REGION="${AWS_REGION:-us-east-1}"
export VERSAO="${VERSAO:-v1}"               # etiqueta das imagens. Nunca 'latest'
export TF_VAR_versao="$VERSAO"

# ── utilitários de saída ─────────────────────────────────────────────────
azul()    { printf "\033[1;36m%s\033[0m\n" "$*"; }
verde()   { printf "\033[1;32m%s\033[0m\n" "$*"; }
amarelo() { printf "\033[1;33m%s\033[0m\n" "$*"; }
vermelho(){ printf "\033[1;31m%s\033[0m\n" "$*"; }

exigir_ferramentas() {
  command -v aws >/dev/null 2>&1 || { vermelho "AWS CLI não encontrada. Use o CloudShell."; exit 1; }
  command -v terraform >/dev/null 2>&1 || {
    vermelho "Terraform não encontrado."
    echo "Rode: bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh && source ~/.bashrc"
    exit 1
  }
  aws sts get-caller-identity >/dev/null 2>&1 || {
    vermelho "Sem credencial AWS. O Learner Lab está ligado (bolinha verde)?"
    exit 1
  }
}

mostrar_alvo() {
  local conta arn
  conta=$(aws sts get-caller-identity --query Account --output text)
  arn=$(aws sts get-caller-identity --query Arn --output text)
  azul "───────────────────────────────────────────────────────────"
  azul " Conta ........... ${conta}"
  azul " Identidade ...... ${arn}"
  azul " Região .......... ${AWS_REGION}"
  azul " Versão .......... ${VERSAO}"
  azul "───────────────────────────────────────────────────────────"
}

tf() { terraform -chdir="$TF_DIR" "$@"; }
saida() { tf output -raw "$1"; }
