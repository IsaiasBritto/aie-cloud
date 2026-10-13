#!/usr/bin/env bash
# custo.sh — custo estimado da Eva a partir da telemetria no CloudWatch Logs.
#
# Por que este script, e não o Cost Explorer:
#   1. O Learner Lab não libera Cost Explorer nem Budgets.
#   2. Mesmo numa conta comum, a fatura chega com até 24 h de atraso e não
#      sabe o que é um "turno". A telemetria da Eva sabe: cada chamada ao
#      modelo carrega turno_id, tokens e custo estimado.
#   3. O Logs Insights é assíncrono: start-query devolve um ID e o resultado
#      precisa ser buscado depois. O laço abaixo faz isso por você.
#
# Uso (de dentro desta pasta, depois do deploy):
#   bash custo.sh            # últimas 24 h
#   bash custo.sh 2          # últimas 2 h
#   LOG_GROUP=/eva/turnos bash custo.sh 720   # outro log group (ex.: amostra da Aula 6)
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HORAS="${1:-24}"
LOG_GROUP="${LOG_GROUP:-$(cd "$AQUI/terraform" && terraform output -raw log_group_name)}"
CONSULTA=$(grep -v '^#' "$AQUI/consulta-custo.logsinsights")

FIM=$(date +%s)
INICIO=$((FIM - HORAS * 3600))

echo "Log group: $LOG_GROUP · janela: últimas ${HORAS} h"
ID=$(aws logs start-query --log-group-name "$LOG_GROUP" \
       --start-time "$INICIO" --end-time "$FIM" \
       --query-string "$CONSULTA" --query queryId --output text)

for _ in $(seq 1 30); do
  STATUS=$(aws logs get-query-results --query-id "$ID" --query status --output text)
  case "$STATUS" in
    Complete) break ;;
    Failed|Cancelled|Timeout) echo "Consulta terminou com status $STATUS" >&2; exit 1 ;;
  esac
  sleep 2
done

aws logs get-query-results --query-id "$ID" \
  --query 'results[0][].{campo: field, valor: value}' --output table

echo
echo "Custo zerado? Os preços estão em 0 na task definition."
echo "Ajuste preco_entrada_por_1m / preco_saida_por_1m no terraform.tfvars e rode o deploy de novo."
