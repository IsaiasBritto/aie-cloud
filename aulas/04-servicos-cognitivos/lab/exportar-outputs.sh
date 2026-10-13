#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Exporta os outputs do Terraform da Aula 4 para a sessão atual.
#
#   source exportar-outputs.sh
#
# Precisa ser carregado com "source": rodar com "bash" cria outro processo e as
# variáveis morrem junto com ele.
#
# Por que existe: o CloudShell encerra a sessão depois de ~20 min sem uso, e
# abrir uma aba nova começa do zero. Os exports somem — e os erros depois não
# dizem isso (MONGO_IP vazio, URL "None"...). Rode sempre que abrir um terminal.
# ---------------------------------------------------------------------------

_qc_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/terraform"

if [ ! -d "$_qc_dir" ]; then
  echo "ERRO: não achei a pasta terraform em $_qc_dir" >&2
  return 1 2>/dev/null || exit 1
fi

_qc_out() { terraform -chdir="$_qc_dir" output -raw "$1" 2>/dev/null; }

DATA_BUCKET="$(_qc_out data_bucket_name)"
FUNC_NAME="$(_qc_out lambda_name)"
FUNC_URL="$(_qc_out function_url)"
MONGO_IP="$(_qc_out mongodb_public_ip)"
MONGO_SECRET_ID="$(_qc_out mongo_secret_id)"
export DATA_BUCKET FUNC_NAME FUNC_URL MONGO_IP MONGO_SECRET_ID

unset -f _qc_out
unset _qc_dir

echo "Bucket de dados : ${DATA_BUCKET:-VAZIO}"
echo "Lambda          : ${FUNC_NAME:-VAZIO}"
echo "Function URL    : ${FUNC_URL:-VAZIO}"
echo "MongoDB         : ${MONGO_IP:-VAZIO}:27017"
echo "Mongo Express   : http://${MONGO_IP:-VAZIO}:8081  (qcadmin / QCview2024!)"

if [ -z "${DATA_BUCKET:-}" ] || [ -z "${MONGO_IP:-}" ]; then
  echo
  echo "AVISO: algum output veio vazio. Rode 'terraform output' na pasta terraform" >&2
  echo "       para ver o que falta — provavelmente o apply não completou." >&2
fi
