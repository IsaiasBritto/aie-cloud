#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Aula 6 · Lab 3 — carrega o log de amostra da Eva no CloudWatch Logs
#
# Cria o log group /eva/turnos (retenção 7 dias, tag projeto=eva) e envia
# eva-amostra.jsonl: ~200 chamadas ao modelo, ~125 turnos, medidas pela Eva do
# professor (Aula 5, 03-agente-Eva-aws). Cada linha vira um evento JSON — o
# MESMO formato que a telemetria.py da Eva escreve no stdout do ECS.
#
# Os preços NÃO vêm no arquivo: o carregador calcula custo_estimado_usd na hora,
# com os valores que VOCÊ informar. Sem preço, o custo sai zero — de propósito:
#
#   export EVA_PRECO_ENTRADA_POR_1M=0.06    # Nova Lite, USD por 1M tokens de entrada
#   export EVA_PRECO_SAIDA_POR_1M=0.24      # Nova Lite, USD por 1M tokens de saída
#   bash finops/carregar-amostra.sh
#
# Os horários são deslocados para terminar AGORA: o CloudWatch recusa eventos
# com mais de 14 dias, e o Logs Insights precisa deles dentro da janela de busca.
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AMOSTRA="${AMOSTRA:-$AQUI/eva-amostra.jsonl}"
export LOG_GROUP="${LOG_GROUP:-/eva/turnos}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
export EVA_PRECO_ENTRADA_POR_1M="${EVA_PRECO_ENTRADA_POR_1M:-0}"
export EVA_PRECO_SAIDA_POR_1M="${EVA_PRECO_SAIDA_POR_1M:-0}"

aws sts get-caller-identity >/dev/null 2>&1 || {
  echo "Sem credencial AWS. O Learner Lab está ligado (bolinha verde)?" >&2; exit 1; }

python3 - <<'PY'
import json, os, time
import boto3

grupo = os.environ["LOG_GROUP"]
p_in = float(os.environ["EVA_PRECO_ENTRADA_POR_1M"])
p_out = float(os.environ["EVA_PRECO_SAIDA_POR_1M"])
logs = boto3.client("logs", region_name=os.environ["AWS_REGION"])

try:
    logs.create_log_group(logGroupName=grupo, tags={"projeto": "eva", "aula": "6"})
    print(f"✓ Log group {grupo} criado")
except logs.exceptions.ResourceAlreadyExistsException:
    print(f"· Log group {grupo} já existe — os eventos vão para um stream novo")
logs.put_retention_policy(logGroupName=grupo, retentionInDays=7)

linhas = [json.loads(l) for l in open(os.environ["AMOSTRA"], encoding="utf-8") if l.strip()]
fim = max(l["offset_s"] for l in linhas)
agora_ms = int(time.time() * 1000) - 60_000  # um minuto atrás: nada no "futuro"

eventos = []
for l in linhas:
    ts = agora_ms - int((fim - l.pop("offset_s")) * 1000)
    l["custo_estimado_usd"] = round(l["tokens_entrada"] / 1e6 * p_in + l["tokens_saida"] / 1e6 * p_out, 8)
    l["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts / 1000))
    eventos.append({"timestamp": ts, "message": json.dumps(l, ensure_ascii=False)})
eventos.sort(key=lambda e: e["timestamp"])

stream = f"amostra-{time.strftime('%Y%m%d-%H%M%S')}"
logs.create_log_stream(logGroupName=grupo, logStreamName=stream)
for i in range(0, len(eventos), 500):  # lotes bem abaixo do limite de 1 MB
    logs.put_log_events(logGroupName=grupo, logStreamName=stream, logEvents=eventos[i:i + 500])

turnos = len({json.loads(e["message"])["turno_id"] for e in eventos})
custo = sum(json.loads(e["message"])["custo_estimado_usd"] for e in eventos)
print(f"✓ {len(eventos)} chamadas · {turnos} turnos → {grupo} / {stream}")
print(f"  Preços: entrada {p_in} · saída {p_out} USD/1M  →  custo total estimado US$ {custo:.6f}")
if not (p_in or p_out):
    print("  ⚠️  Preços em 0: o custo vai sair zerado. Exporte EVA_PRECO_* e rode de novo.")
print("\nPróximo passo: CloudWatch → Logs Insights → log group", grupo)
PY
