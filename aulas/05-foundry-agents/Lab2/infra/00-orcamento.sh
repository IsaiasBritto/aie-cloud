#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva contínuo · Passo 0 — criar o orçamento da assinatura
#
# Num módulo em que o agente ACORDA SOZINHO, o orçamento não é opcional:
# é o que faz alguém descobrir o gasto no segundo dia, e não na fatura.
#
# Uso:   bash infra/00-orcamento.sh
#
# Ajustes opcionais, por variável de ambiente:
#   VALOR=10                    teto em US$
#   MESES=3                     por quantos meses o orçamento vale
#   NOME_ORCAMENTO=orc-aula-05-continuo
#   EMAIL=voce@exemplo.com      padrão: o e-mail da sua conta no `az login`
#
# Este script NÃO cria recurso que gera custo e NÃO depende do 00-variaveis.sh:
# roda antes de você escolher sufixo, região ou grupo.
#
# Por que `az rest` e não `az consumption budget create`?
#   O grupo de comandos `consumption` está em preview e o payload que a CLI
#   monta está fora de sincronia com o serviço — devolve
#   "(400) Invalid budget configuration, please use filter interface with
#   2019-05-01-preview version". Bug aberto: Azure/azure-cli#29950.
#   Aqui falamos direto com a API de budgets, na versão 2024-08-01.
# ─────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── utilitários de saída ─────────────────────────────────────────────────
azul()    { printf "\033[1;36m%s\033[0m\n" "$*"; }
verde()   { printf "\033[1;32m%s\033[0m\n" "$*"; }
amarelo() { printf "\033[1;33m%s\033[0m\n" "$*"; }
vermelho(){ printf "\033[1;31m%s\033[0m\n" "$*"; }

# ── o que você pode ajustar ──────────────────────────────────────────────
VALOR="${VALOR:-10}"
MESES="${MESES:-3}"
NOME_ORCAMENTO="${NOME_ORCAMENTO:-orc-aula-05-continuo}"
API="2024-08-01"

# o arquivo temporário fica no diretório atual de propósito: no Git Bash,
# caminhos que começam com / são reescritos antes de chegar no az.exe
TEMP_JSON="./.orcamento.$$.json"
trap 'rm -f "$TEMP_JSON"' EXIT

# ── 0. pré-requisitos ────────────────────────────────────────────────────
command -v az >/dev/null 2>&1 || {
  vermelho "A CLI do Azure (az) não está instalada."
  echo "Instale em: https://learn.microsoft.com/cli/azure/install-azure-cli"
  exit 1
}
az account show >/dev/null 2>&1 || {
  vermelho "Você não está autenticado. Rode:  az login"
  exit 1
}

ASSINATURA_NOME=$(az account show --query name -o tsv)
ASSINATURA_ID=$(az account show --query id -o tsv)

# o e-mail do alerta sai do próprio login — assim o mesmo script serve
# para a turma inteira, e cada aluno recebe o próprio aviso
EMAIL="${EMAIL:-$(az account show --query user.name -o tsv)}"
case "$EMAIL" in
  *@*) ;;
  *)   vermelho "Não consegui descobrir um e-mail a partir do seu login."
       echo "Rode de novo informando um:  EMAIL=voce@exemplo.com bash infra/00-orcamento.sh"
       exit 1 ;;
esac

# ── 1. datas: primeiro dia deste mês, e de daqui a N meses ───────────────
# `date -d` é GNU (Linux, WSL, Git Bash); `date -v` é BSD (macOS).
INICIO="$(date +%Y-%m-01)"
if date -d "+1 month" >/dev/null 2>&1; then
  FIM="$(date -d "+${MESES} months" +%Y-%m-01)"
else
  FIM="$(date -v+"${MESES}"m +%Y-%m-01)"
fi

azul "───────────────────────────────────────────────────────────"
azul " Assinatura ...... ${ASSINATURA_NOME}"
azul " Orçamento ....... ${NOME_ORCAMENTO}"
azul " Teto ............ US\$ ${VALOR} por mês"
azul " Vigência ........ ${INICIO}  →  ${FIM}"
azul " Alertas para .... ${EMAIL}  (50%, 80%, 100%)"
azul "───────────────────────────────────────────────────────────"

# ── 2. o corpo da requisição ─────────────────────────────────────────────
# `category` precisa ser exatamente "Cost". A notificação exige pelo menos
# um contactEmails quando o escopo é a assinatura.
cat > "$TEMP_JSON" <<JSON
{
  "properties": {
    "category": "Cost",
    "amount": ${VALOR},
    "timeGrain": "Monthly",
    "timePeriod": {
      "startDate": "${INICIO}T00:00:00Z",
      "endDate": "${FIM}T00:00:00Z"
    },
    "notifications": {
      "Aviso_50": {
        "enabled": true, "operator": "GreaterThanOrEqualTo",
        "threshold": 50, "thresholdType": "Actual",
        "contactEmails": ["${EMAIL}"]
      },
      "Aviso_80": {
        "enabled": true, "operator": "GreaterThanOrEqualTo",
        "threshold": 80, "thresholdType": "Actual",
        "contactEmails": ["${EMAIL}"]
      },
      "Aviso_100": {
        "enabled": true, "operator": "GreaterThanOrEqualTo",
        "threshold": 100, "thresholdType": "Actual",
        "contactEmails": ["${EMAIL}"]
      }
    }
  }
}
JSON

# ── 3. criar (ou atualizar) o orçamento ──────────────────────────────────
# É um PUT: rodar de novo sobrescreve, não duplica. Pode repetir à vontade.
URL="https://management.azure.com/subscriptions/${ASSINATURA_ID}/providers/Microsoft.Consumption/budgets/${NOME_ORCAMENTO}?api-version=${API}"

azul "[1/2] Criando o orçamento..."
if ! az rest --method put --url "$URL" --body "@${TEMP_JSON}" -o none; then
  echo
  vermelho "Não deu para criar o orçamento pela API."
  amarelo "Não insista no terminal — crie pelo portal, leva um minuto:"
  echo "  Gerenciamento de Custos → Orçamentos → Adicionar"
  echo "  Nome: ${NOME_ORCAMENTO} · Valor: US\$ ${VALOR} · Redefinição: Mensal"
  echo "  Alertas: 50%, 80% e 100% para ${EMAIL}"
  echo
  vermelho "O que NÃO pode é seguir para o Módulo 1 sem orçamento."
  exit 1
fi

# ── 4. conferir ──────────────────────────────────────────────────────────
azul "[2/2] Conferindo..."
az rest --method get --url "$URL" \
  --query "properties.{valor:amount, grao:timeGrain, inicio:timePeriod.startDate, fim:timePeriod.endDate}" \
  -o table

echo
verde "✔ Orçamento ativo. Pode seguir para o Módulo 1."
verde ""
verde "  O orçamento AVISA, não freia: o Azure não tem limite rígido de gasto."
verde "  O freio de verdade é a cota (TPM) da implantação do modelo."
verde ""
verde "  Para apagar depois:"
verde "    az rest --method delete --url \"${URL}\""
