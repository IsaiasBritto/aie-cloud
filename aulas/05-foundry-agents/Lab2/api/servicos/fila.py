"""A fila de documentos — o que transforma conversa em processo.

Um agente que só responde pergunta não precisa de fila. Um agente contínuo precisa saber,
sem ninguém dizer, **o que já fez, o que falta e o que não é dele**. É isso que esta
classe guarda.

A regra que mais importa está em `avancar`: um documento em `excecao` **não volta para o
agente**. Ele fica esperando gente. Sem essa regra, o agente entra em laço — tenta de
novo, falha de novo, gasta token de novo — e a fatura cresce sozinha durante a madrugada.
"""
from __future__ import annotations

import uuid

from ..erros import DocumentoNaoEncontrado, TransicaoProibida
from ..modelos import (ESTADOS_FINAIS, TRANSICOES_PERMITIDAS, AtualizacaoDeDocumento,
                       Documento, EntradaDeDocumento, EstadoDoDocumento, ResumoDaFila,
                       agora)
from .armazenamento import ARQUIVO_FILA, Armazenamento

#: Estados em que o agente ainda tem trabalho a fazer.
ESTADOS_DO_AGENTE = {EstadoDoDocumento.RECEBIDO, EstadoDoDocumento.EXTRAIDO,
                     EstadoDoDocumento.AUDITADO}

#: Estados que só uma pessoa resolve.
ESTADOS_DO_HUMANO = {EstadoDoDocumento.EXCECAO, EstadoDoDocumento.ILEGIVEL}


class ServicoDaFila:
    def __init__(self, armazenamento: Armazenamento):
        self.armazenamento = armazenamento

    def _carregar(self) -> list[Documento]:
        cru = self.armazenamento.ler_json(ARQUIVO_FILA, [])
        return [Documento(**item) for item in cru]

    def _salvar(self, documentos: list[Documento]) -> None:
        self.armazenamento.escrever_json(
            ARQUIVO_FILA, [d.model_dump(mode="json") for d in documentos])

    def listar(self, estado: EstadoDoDocumento | None = None) -> list[Documento]:
        documentos = self._carregar()
        if estado:
            documentos = [d for d in documentos if d.estado is estado]
        return sorted(documentos, key=lambda d: d.recebido_em, reverse=True)

    def obter(self, identificador: str) -> Documento:
        for d in self._carregar():
            if d.identificador == identificador:
                return d
        raise DocumentoNaoEncontrado(
            f"Não existe documento com identificador {identificador}.",
            como_resolver="Confira a lista em GET /fila.",
        )

    def receber(self, entrada: EntradaDeDocumento) -> Documento:
        """Chamado pelo gatilho quando um arquivo cai no armazenamento.

        É o ponto onde o agente deixa de depender de alguém digitar uma pergunta.
        """
        instante = agora()
        documento = Documento(
            identificador=f"doc-{uuid.uuid4().hex[:8]}",
            arquivo=entrada.arquivo,
            recebido_em=instante,
            atualizado_em=instante,
            fornecedor=entrada.fornecedor,
            valor_total=entrada.valor_total,
            historico=[f"{instante.isoformat(timespec='seconds')} · recebido"],
        )
        documentos = self._carregar()
        documentos.append(documento)
        self._salvar(documentos)
        return documento

    def avancar(self, identificador: str, atualizacao: AtualizacaoDeDocumento,
                por: str = "deva") -> Documento:
        documentos = self._carregar()
        documento = next((d for d in documentos if d.identificador == identificador), None)
        if documento is None:
            raise DocumentoNaoEncontrado(
                f"Não existe documento com identificador {identificador}.",
                como_resolver="Confira a lista em GET /fila.",
            )

        destino = atualizacao.estado
        permitidos = TRANSICOES_PERMITIDAS[documento.estado]
        if destino not in permitidos:
            legiveis = ", ".join(sorted(e.value for e in permitidos)) or "nenhum"
            raise TransicaoProibida(
                f"Um documento em '{documento.estado.value}' não pode ir para "
                f"'{destino.value}'.",
                detalhe=f"Destinos possíveis a partir daqui: {legiveis}.",
                como_resolver=(
                    "Máquina de estados existe justamente para impedir atalho. Se o "
                    "documento está em 'excecao', quem libera é uma pessoa pela tela — "
                    "o agente não retoma sozinho, e é por isso que ele não entra em laço."),
            )

        if documento.estado is EstadoDoDocumento.EXCECAO and por == "deva":
            raise TransicaoProibida(
                "Documento em exceção só é liberado por uma pessoa.",
                como_resolver=("Abra a aba Exceções na tela e decida. Se o agente pudesse "
                               "liberar a própria exceção, a revisão humana viraria "
                               "enfeite."),
            )

        instante = agora()
        for campo in ("fornecedor", "valor_total", "categoria", "regra_aplicada",
                      "confianca", "justificativa"):
            valor = getattr(atualizacao, campo)
            if valor is not None:
                setattr(documento, campo, valor)

        anterior = documento.estado
        documento.estado = destino
        documento.atualizado_em = instante
        documento.precisa_de_humano = destino in ESTADOS_DO_HUMANO
        documento.historico.append(
            f"{instante.isoformat(timespec='seconds')} · {anterior.value} → "
            f"{destino.value} (por {por})")

        self._salvar(documentos)
        return documento

    def resumir(self, propostas_pendentes: int = 0) -> ResumoDaFila:
        documentos = self._carregar()
        por_estado: dict[str, int] = {}
        for d in documentos:
            por_estado[d.estado.value] = por_estado.get(d.estado.value, 0) + 1
        return ResumoDaFila(
            gerado_em=agora(),
            total=len(documentos),
            por_estado=por_estado,
            aguardando_o_agente=[d.identificador for d in documentos
                                 if d.estado in ESTADOS_DO_AGENTE],
            aguardando_humano=[d.identificador for d in documentos
                               if d.estado in ESTADOS_DO_HUMANO],
            propostas_pendentes=propostas_pendentes,
        )

    def concluidos(self) -> list[Documento]:
        return [d for d in self._carregar() if d.estado in ESTADOS_FINAIS]
