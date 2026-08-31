#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · variáveis compartilhadas por todos os scripts de infraestrutura.
#
# Não execute este arquivo sozinho: os outros scripts o carregam com `source`.
#
# O único valor que você PRECISA mudar é o SUFIXO — nome de conta de
# armazenamento e de registro de containers é único no mundo inteiro.
# ─────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── o que você escolhe ───────────────────────────────────────────────────
export SUFIXO="${SUFIXO:-fiap01}"          # 4 a 6 letras/números, minúsculas
export REGIAO="${REGIAO:-eastus}"
export GRUPO="${GRUPO:-rg-aula-05}"
export VERSAO="${VERSAO:-v1}"              # etiqueta das imagens. Nunca 'latest'

# ── nomes derivados (não precisa mexer) ──────────────────────────────────
export CONTA_ARMAZENAMENTO="stdeva3${SUFIXO}"      # sem hífen, minúsculas, até 24
export CONTAINER_BLOB="deteccoes"
export RECURSO_VISAO="cv-deva3-${SUFIXO}"
export ACR="acrdeva3${SUFIXO}"                     # sem hífen, minúsculas
export AMBIENTE_APPS="cae-aula-05"
export APP_API="ca-deva3-api"
export APP_WEB="ca-deva3-web"

# Nível do recurso de visão:
#   F0 = gratuito, 20 chamadas/minuto, UM por assinatura por região
#   S1 = pago por chamada (10 chamadas/segundo) — use no dia da aula com turma grande
export NIVEL_VISAO="${NIVEL_VISAO:-F0}"

# ── utilitários de saída ─────────────────────────────────────────────────
azul()    { printf "\033[1;36m%s\033[0m\n" "$*"; }
verde()   { printf "\033[1;32m%s\033[0m\n" "$*"; }
amarelo() { printf "\033[1;33m%s\033[0m\n" "$*"; }
vermelho(){ printf "\033[1;31m%s\033[0m\n" "$*"; }

exigir_az() {
  command -v az >/dev/null 2>&1 || {
    vermelho "A CLI do Azure (az) não está instalada."
    echo "Instale em: https://learn.microsoft.com/cli/azure/install-azure-cli"
    exit 1
  }
  az account show >/dev/null 2>&1 || {
    vermelho "Você não está autenticado. Rode: az login"
    exit 1
  }
}

mostrar_alvo() {
  local assinatura
  assinatura=$(az account show --query name -o tsv)
  azul "───────────────────────────────────────────────────────────"
  azul " Assinatura ...... ${assinatura}"
  azul " Grupo ........... ${GRUPO}"
  azul " Região .......... ${REGIAO}"
  azul " Sufixo .......... ${SUFIXO}"
  azul "───────────────────────────────────────────────────────────"
}
