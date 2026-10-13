"""
Telemetria — uma linha JSON por chamada ao modelo, direto para o CloudWatch Logs.

Responde a três perguntas que toda aplicação de IA em produção precisa
responder, e que nenhum log de texto livre responde bem:

    Quanto demora?   (latência por chamada)
    Quanto custa?    (tokens de entrada e saída, e o custo estimado)
    O que quebrou?   (erros, com o contexto da chamada)

Como funciona: cada chamada vira UMA linha JSON no stdout. No ECS Fargate, o
driver `awslogs` da task definition entrega o stdout ao CloudWatch Logs — sem
SDK, sem agente, sem permissão extra na aplicação. Lá, o Logs Insights lê os
campos do JSON sozinho:

    filter evento = "eva.chamada_modelo"
    | stats sum(custo_estimado_usd) as custo_turno, count(*) as iteracoes by turno_id

A linha carrega o `turno_id`: um turno (uma pergunta do usuário) pode custar
VÁRIAS chamadas ao modelo — uma por volta do loop de ferramentas. Custo por
chamada engana; custo por turno é o número que vai para a reunião.

Ligar/desligar: EVA_TELEMETRIA=stdout liga (é o que a task definition faz).
Vazio = desligada — a aplicação roda igual na sua máquina, só não emite nada.
"""

from __future__ import annotations

import contextlib
import datetime
import json
import logging
import os
import sys
import time
import uuid

log = logging.getLogger("eva.telemetria")

DESTINO = os.getenv("EVA_TELEMETRIA", "").strip().lower()

# Preço por 1 milhão de tokens, para o custo estimado.
# ATENÇÃO: preencha com os valores do SEU modelo e da SUA região, na página de
# preços do Amazon Bedrock (ou da OpenAI). Deixei 0 de propósito — número
# inventado em painel de custo é pior que painel nenhum.
PRECO_ENTRADA_1M = float(os.getenv("EVA_PRECO_ENTRADA_POR_1M", "0"))
PRECO_SAIDA_1M = float(os.getenv("EVA_PRECO_SAIDA_POR_1M", "0"))

EVENTO = "eva.chamada_modelo"

_ligado = False
_servico = "eva"


def ligado() -> bool:
    return _ligado


def iniciar(nome_servico: str = "eva-agente") -> bool:
    """Liga a telemetria. Seguro chamar mais de uma vez.

    Devolve True se as linhas JSON vão ser emitidas.
    """
    global _ligado, _servico
    _servico = nome_servico
    if _ligado:
        return True
    if DESTINO != "stdout":
        log.info("EVA_TELEMETRIA vazia — telemetria desligada.")
        return False
    _ligado = True
    return True


def novo_turno() -> str:
    """Um ID curto por pergunta do usuário. Todas as chamadas do turno o carregam."""
    return uuid.uuid4().hex[:12]


def custo_estimado(tokens_entrada: int, tokens_saida: int) -> float:
    """Custo em dólares, a partir da tabela de preços configurada."""
    return (tokens_entrada / 1_000_000) * PRECO_ENTRADA_1M + (
        tokens_saida / 1_000_000
    ) * PRECO_SAIDA_1M


@contextlib.contextmanager
def medir_chamada(modelo: str, streaming: bool = False, turno_id: str | None = None,
                  iteracao: int = 1, provedor: str = "bedrock"):
    """Envolve UMA chamada ao modelo, medindo tempo e registrando o resultado.

    Uso:

        with telemetria.medir_chamada(modelo, turno_id=turno, iteracao=1) as m:
            resposta = cliente.converse(...)
            m.registrar_uso(entrada=resposta["usage"]["inputTokens"],
                            saida=resposta["usage"]["outputTokens"])

    Se a telemetria estiver desligada, o `with` continua funcionando — só não
    emite nada. A aplicação nunca quebra por causa de telemetria.
    """
    medicao = _Medicao(modelo, streaming, turno_id or novo_turno(), iteracao, provedor)
    inicio = time.perf_counter()
    try:
        yield medicao
    except Exception as exc:
        _emitir(medicao, (time.perf_counter() - inicio) * 1000, erro=type(exc).__name__)
        raise
    else:
        _emitir(medicao, (time.perf_counter() - inicio) * 1000)


class _Medicao:
    """O que a chamada reporta de volta para a telemetria."""

    def __init__(self, modelo, streaming, turno_id, iteracao, provedor) -> None:
        self.modelo = modelo
        self.streaming = streaming
        self.turno_id = turno_id
        self.iteracao = iteracao
        self.provedor = provedor
        self.tokens_entrada = 0
        self.tokens_saida = 0
        self.duracao_ms = 0.0

    def registrar_uso(self, entrada: int = 0, saida: int = 0) -> None:
        self.tokens_entrada += int(entrada or 0)
        self.tokens_saida += int(saida or 0)

    @property
    def custo(self) -> float:
        return custo_estimado(self.tokens_entrada, self.tokens_saida)


def _emitir(m: _Medicao, duracao_ms: float, erro: str | None = None) -> None:
    """Escreve a linha JSON. Falha aqui nunca sobe para a aplicação."""
    m.duracao_ms = duracao_ms
    if not _ligado:
        return
    registro = {
        "evento": EVENTO,
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds"),
        "servico": _servico,
        "turno_id": m.turno_id,
        "iteracao": m.iteracao,
        "provedor": m.provedor,
        "modelo": m.modelo,
        "streaming": m.streaming,
        "duracao_ms": round(duracao_ms, 1),
        "tokens_entrada": m.tokens_entrada,
        "tokens_saida": m.tokens_saida,
        "custo_estimado_usd": round(m.custo, 8),
        "erro": erro,
        # Numérico de propósito: vira métrica por filtro (metricValue=$.falhou)
        # sem depender de como cada ferramenta trata null.
        "falhou": 1 if erro else 0,
    }
    try:
        sys.stdout.write(json.dumps(registro, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    except Exception as exc:  # noqa: BLE001
        log.debug("Falha ao emitir telemetria: %s", exc)


def resumo() -> dict[str, object]:
    """Estado da telemetria — a interface mostra isso."""
    return {
        "ligada": _ligado,
        "destino": "stdout → CloudWatch Logs" if DESTINO == "stdout" else "desligada",
        "preco_entrada_1M": PRECO_ENTRADA_1M,
        "preco_saida_1M": PRECO_SAIDA_1M,
        "precos_definidos": bool(PRECO_ENTRADA_1M or PRECO_SAIDA_1M),
    }
