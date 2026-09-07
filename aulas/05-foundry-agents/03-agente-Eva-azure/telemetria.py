"""
Telemetria — Application Insights via OpenTelemetry.

Responde a três perguntas que toda aplicação de IA em produção precisa
responder, e que nenhum log de texto responde bem:

    Quanto demora?   (latência por chamada)
    Quanto custa?    (tokens de entrada e saída, e o custo estimado)
    O que quebrou?   (exceções, com o contexto da chamada)

Como funciona: `configure_azure_monitor()` liga o SDK do OpenTelemetry ao
Application Insights. Depois disso, spans e métricas são exportados sozinhos.
Se a connection string não estiver configurada, tudo aqui vira no-op — a
aplicação roda igual, só não emite telemetria. É o que permite o mesmo código
rodar na sua máquina sem Azure Monitor nenhum.
"""

from __future__ import annotations

import contextlib
import logging
import os
import time

log = logging.getLogger("eva.telemetria")

CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "").strip()

# Preço por 1 milhão de tokens, para o custo estimado.
# ATENÇÃO: preencha com os valores do SEU modelo e da SUA região, na página de
# preços do Azure OpenAI. Deixei 0 de propósito — número inventado em painel de
# custo é pior que painel nenhum.
PRECO_ENTRADA_1M = float(os.getenv("EVA_PRECO_ENTRADA_POR_1M", "0"))
PRECO_SAIDA_1M = float(os.getenv("EVA_PRECO_SAIDA_POR_1M", "0"))

_ligado = False
_tracer = None
_hist_latencia = None
_cont_tokens = None
_cont_custo = None
_cont_chamadas = None


def ligado() -> bool:
    return _ligado


def iniciar(nome_servico: str = "eva-agente") -> bool:
    """Liga a telemetria. Seguro chamar mais de uma vez.

    Devolve True se o Application Insights foi configurado de verdade.
    """
    global _ligado, _tracer, _hist_latencia, _cont_tokens, _cont_custo, _cont_chamadas

    if _ligado:
        return True
    if not CONNECTION_STRING:
        log.info("APPLICATIONINSIGHTS_CONNECTION_STRING ausente — telemetria desligada.")
        return False

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry import metrics, trace
    except ImportError:
        log.warning("Pacote azure-monitor-opentelemetry ausente — telemetria desligada.")
        return False

    try:
        configure_azure_monitor(
            connection_string=CONNECTION_STRING,
            resource_attributes={"service.name": nome_servico},
        )
    except Exception as exc:  # noqa: BLE001 — telemetria nunca derruba a aplicação
        log.warning("Não consegui configurar o Application Insights: %s", exc)
        return False

    _tracer = trace.get_tracer("eva")
    medidor = metrics.get_meter("eva")

    # Um histograma para latência (permite ver p50/p95, não só a média) e
    # contadores para tokens, custo e volume.
    _hist_latencia = medidor.create_histogram(
        "eva.chamada.duracao", unit="ms", description="Latência de cada chamada ao modelo"
    )
    _cont_tokens = medidor.create_counter(
        "eva.tokens", unit="{token}", description="Tokens consumidos"
    )
    _cont_custo = medidor.create_counter(
        "eva.custo.estimado", unit="USD", description="Custo estimado das chamadas"
    )
    _cont_chamadas = medidor.create_counter(
        "eva.chamadas", unit="{chamada}", description="Chamadas ao modelo"
    )

    _ligado = True
    log.info("Telemetria ligada (serviço=%s).", nome_servico)
    return True


def custo_estimado(tokens_entrada: int, tokens_saida: int) -> float:
    """Custo em dólares, a partir da tabela de preços configurada."""
    return (tokens_entrada / 1_000_000) * PRECO_ENTRADA_1M + (
        tokens_saida / 1_000_000
    ) * PRECO_SAIDA_1M


@contextlib.contextmanager
def medir_chamada(deployment: str, streaming: bool = False):
    """Envolve UMA chamada ao modelo, medindo tempo e registrando o resultado.

    Uso:

        with telemetria.medir_chamada("gpt-5.4-mini") as m:
            resposta = cliente.chat.completions.create(...)
            m.registrar_uso(entrada=..., saida=...)

    Se a telemetria estiver desligada, o `with` continua funcionando — só não
    exporta nada. A aplicação nunca quebra por causa de telemetria.
    """
    medicao = _Medicao(deployment, streaming)
    inicio = time.perf_counter()

    if not _ligado or _tracer is None:
        try:
            yield medicao
        finally:
            medicao.duracao_ms = (time.perf_counter() - inicio) * 1000
        return

    with _tracer.start_as_current_span("eva.chamada_modelo") as span:
        span.set_attribute("eva.deployment", deployment)
        span.set_attribute("eva.streaming", streaming)
        try:
            yield medicao
        except Exception as exc:
            span.record_exception(exc)
            span.set_attribute("eva.erro", type(exc).__name__)
            _registrar(medicao, (time.perf_counter() - inicio) * 1000, erro=type(exc).__name__)
            raise
        else:
            duracao = (time.perf_counter() - inicio) * 1000
            span.set_attribute("eva.duracao_ms", round(duracao, 1))
            span.set_attribute("eva.tokens.entrada", medicao.tokens_entrada)
            span.set_attribute("eva.tokens.saida", medicao.tokens_saida)
            span.set_attribute("eva.custo_estimado_usd", medicao.custo)
            _registrar(medicao, duracao)


class _Medicao:
    """O que a chamada reporta de volta para a telemetria."""

    def __init__(self, deployment: str, streaming: bool) -> None:
        self.deployment = deployment
        self.streaming = streaming
        self.tokens_entrada = 0
        self.tokens_saida = 0
        self.duracao_ms = 0.0

    def registrar_uso(self, entrada: int = 0, saida: int = 0) -> None:
        self.tokens_entrada += int(entrada or 0)
        self.tokens_saida += int(saida or 0)

    @property
    def custo(self) -> float:
        return custo_estimado(self.tokens_entrada, self.tokens_saida)


def _registrar(m: _Medicao, duracao_ms: float, erro: str | None = None) -> None:
    """Publica as métricas. Falha aqui nunca sobe para a aplicação."""
    m.duracao_ms = duracao_ms
    atributos = {"deployment": m.deployment, "streaming": m.streaming}
    if erro:
        atributos["erro"] = erro

    try:
        _hist_latencia.record(duracao_ms, atributos)
        _cont_chamadas.add(1, atributos)
        if m.tokens_entrada:
            _cont_tokens.add(m.tokens_entrada, {**atributos, "tipo": "entrada"})
        if m.tokens_saida:
            _cont_tokens.add(m.tokens_saida, {**atributos, "tipo": "saida"})
        if m.custo:
            _cont_custo.add(m.custo, atributos)
    except Exception as exc:  # noqa: BLE001
        log.debug("Falha ao registrar métrica: %s", exc)


def resumo() -> dict[str, object]:
    """Estado da telemetria — a interface mostra isso."""
    return {
        "ligada": _ligado,
        "connection_string": "configurada" if CONNECTION_STRING else "ausente",
        "preco_entrada_1M": PRECO_ENTRADA_1M,
        "preco_saida_1M": PRECO_SAIDA_1M,
        "precos_definidos": bool(PRECO_ENTRADA_1M or PRECO_SAIDA_1M),
    }
