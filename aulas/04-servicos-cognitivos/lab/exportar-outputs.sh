#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Exporta TODOS os outputs do Terraform da Aula 4 para a sessão atual.
#
#   source exportar-outputs.sh
#
# Precisa ser carregado com "source". Rodar com "bash" não adianta: o script
# roda em outro processo e as variáveis morrem junto com ele.
#
# Por que existe:
#   O Cloud Shell encerra a sessão após 20 min de inatividade, e abrir uma aba
#   nova também começa do zero. Quando isso acontece, TODOS os exports somem — e
#   os erros que aparecem depois não dizem isso:
#
#     export KEY_VAULT_NAME vazio  ->  az: "URL has an invalid label"
#     export MONGO_IP vazio        ->  o script Python pede o IP e sai
#     export AI_ENDPOINT vazio     ->  erro de conexão sem explicação
#
#   Rode isto sempre que abrir um terminal novo. É idempotente e leva segundos.
# ---------------------------------------------------------------------------

_qc_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/terraform"

if [ ! -d "$_qc_dir" ]; then
  echo "ERRO: não achei a pasta terraform em $_qc_dir" >&2
  return 1 2>/dev/null || exit 1
fi

_qc_out() { terraform -chdir="$_qc_dir" output -raw "$1" 2>/dev/null; }

export AI_ENDPOINT="$(_qc_out ai_endpoint)"
export AI_REGION="${AI_REGION:-eastus2}"
export KEY_VAULT_NAME="$(_qc_out key_vault_name)"
export DATA_STORAGE="$(_qc_out data_storage_account_name)"
export MONGO_IP="$(_qc_out mongodb_public_ip)"
export FUNC_NAME="$(_qc_out function_app_name)"

# NÃO use HOSTNAME: é variável do próprio bash (nome da máquina). Sobrescrever
# confunde prompt, logs e qualquer script que dependa dela.
export FUNC_HOSTNAME="$(_qc_out function_app_hostname)"

unset -f _qc_out
unset _qc_dir

echo "AI Services   : ${AI_ENDPOINT:-VAZIO}"
echo "Key Vault     : ${KEY_VAULT_NAME:-VAZIO}"
echo "Storage dados : ${DATA_STORAGE:-VAZIO}"
echo "MongoDB       : ${MONGO_IP:-VAZIO}:27017"
echo "Mongo Express : http://${MONGO_IP:-VAZIO}:8081"
echo "Function      : ${FUNC_NAME:-VAZIO}  ${FUNC_HOSTNAME:-}"

# Qualquer campo VAZIO significa que o Terraform não tem esse output no state —
# provavelmente o apply não terminou. Vale avisar em vez de deixar quebrar depois.
if [ -z "${KEY_VAULT_NAME:-}" ] || [ -z "${MONGO_IP:-}" ]; then
  echo
  echo "AVISO: algum output veio vazio. Rode 'terraform output' na pasta terraform" >&2
  echo "       para ver o que falta — provavelmente o apply não completou." >&2
fi
