"""Contratos do Serviço de Continuidade do Deva.

Tudo em português porque o payload é material didático: o aluno abre o JSON e lê.

Duas ideias moram aqui:

1. **Memória** — uma linha de aprendizado tem sempre origem, data e texto. Uma linha
   *proposta* tem, além disso, quem propôs (o agente) e o documento que a motivou.
2. **Fila** — um documento tem um estado, e a lista de estados é fechada. Sem estado
   explícito não existe processo contínuo; existe repetição.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Memória
# ─────────────────────────────────────────────────────────────────────────────

class SecaoDaMemoria(str, Enum):
    """As seções do MEMORY.md. Lista fechada de propósito.

    Memória sem seção vira lista infinita, e lista infinita ninguém revisa.
    """

    CLASSIFICACAO = "classificacao"
    INTERPRETACAO_DE_POLITICA = "interpretacao_de_politica"
    FORNECEDORES = "fornecedores"
    OPERACAO = "operacao"


class SituacaoDaProposta(str, Enum):
    PENDENTE = "pendente"
    APROVADA = "aprovada"
    DESCARTADA = "descartada"


class LinhaDeMemoria(BaseModel):
    """Uma regra já aprovada, vivendo no MEMORY.md."""

    secao: SecaoDaMemoria
    origem: str = Field(description="Quem disse. Nome do auditor humano, nunca 'Deva'.")
    data: date
    texto: str
    aprovada_por: str | None = None
    aprovada_em: datetime | None = None

    def para_markdown(self) -> str:
        return f"- [{self.origem} · {self.data.isoformat()}] {self.texto}"


class PropostaDeMemoria(BaseModel):
    """Uma regra que o agente QUER aprender. Ainda não vale nada.

    O campo `evidencia` é o que separa aprendizado de alucinação: se o agente não
    consegue apontar o documento e a conversa que motivaram a regra, a proposta não
    deveria existir.
    """

    identificador: str
    secao: SecaoDaMemoria
    texto: str
    evidencia: str = Field(
        description="Qual documento e qual correção do auditor motivaram esta proposta.")
    proposta_por: str = Field(default="deva")
    proposta_em: datetime
    situacao: SituacaoDaProposta = SituacaoDaProposta.PENDENTE
    decidida_por: str | None = None
    decidida_em: datetime | None = None
    motivo_do_descarte: str | None = None

    def para_markdown(self) -> str:
        return (f"- [{self.identificador}] ({self.secao.value}) {self.texto}\n"
                f"  · evidência: {self.evidencia}\n"
                f"  · proposta em {self.proposta_em.date().isoformat()}")


class EntradaDeProposta(BaseModel):
    """O que o agente envia. Repare no que NÃO existe aqui: situação, aprovador, data
    de decisão. O agente não tem como se auto-aprovar porque o contrato não permite."""

    secao: SecaoDaMemoria
    texto: str = Field(min_length=15, max_length=400)
    evidencia: str = Field(min_length=10, max_length=400)


class DecisaoSobreProposta(BaseModel):
    auditor: str = Field(min_length=3, description="Nome de quem está decidindo.")
    motivo: str | None = None


class Memoria(BaseModel):
    """A resposta de GET /memoria — o que o agente lê no início de toda sessão."""

    atualizada_em: datetime
    total_de_linhas: int
    linhas: list[LinhaDeMemoria]
    markdown: str


# ─────────────────────────────────────────────────────────────────────────────
# Fila de documentos
# ─────────────────────────────────────────────────────────────────────────────

class EstadoDoDocumento(str, Enum):
    """A máquina de estados. É ela que transforma pergunta-e-resposta em processo."""

    RECEBIDO = "recebido"
    EXTRAIDO = "extraido"
    AUDITADO = "auditado"
    CONFORME = "conforme"
    EXCECAO = "excecao"
    ILEGIVEL = "ilegivel"
    DUPLICADO = "duplicado"


#: Para onde cada estado pode ir. Transição fora daqui é erro, não criatividade.
TRANSICOES_PERMITIDAS: dict[EstadoDoDocumento, set[EstadoDoDocumento]] = {
    EstadoDoDocumento.RECEBIDO: {EstadoDoDocumento.EXTRAIDO, EstadoDoDocumento.ILEGIVEL},
    EstadoDoDocumento.EXTRAIDO: {EstadoDoDocumento.AUDITADO, EstadoDoDocumento.DUPLICADO,
                                 EstadoDoDocumento.ILEGIVEL},
    EstadoDoDocumento.AUDITADO: {EstadoDoDocumento.CONFORME, EstadoDoDocumento.EXCECAO},
    EstadoDoDocumento.CONFORME: set(),
    EstadoDoDocumento.EXCECAO: {EstadoDoDocumento.CONFORME},   # o humano pode liberar
    EstadoDoDocumento.ILEGIVEL: {EstadoDoDocumento.RECEBIDO},  # reenvio de arquivo melhor
    EstadoDoDocumento.DUPLICADO: set(),
}

#: Estados em que o documento já saiu da esteira.
ESTADOS_FINAIS = {EstadoDoDocumento.CONFORME, EstadoDoDocumento.DUPLICADO}


class Documento(BaseModel):
    identificador: str
    arquivo: str
    recebido_em: datetime
    estado: EstadoDoDocumento = EstadoDoDocumento.RECEBIDO
    atualizado_em: datetime
    fornecedor: str | None = None
    valor_total: float | None = None
    categoria: str | None = None
    regra_aplicada: str | None = None
    confianca: Literal["alta", "media", "baixa"] | None = None
    justificativa: str | None = None
    precisa_de_humano: bool = False
    historico: list[str] = Field(default_factory=list)


class EntradaDeDocumento(BaseModel):
    arquivo: str = Field(min_length=1)
    fornecedor: str | None = None
    valor_total: float | None = None


class AtualizacaoDeDocumento(BaseModel):
    estado: EstadoDoDocumento
    fornecedor: str | None = None
    valor_total: float | None = None
    categoria: str | None = None
    regra_aplicada: str | None = None
    confianca: Literal["alta", "media", "baixa"] | None = None
    justificativa: str | None = None


class ResumoDaFila(BaseModel):
    """A resposta que o agente lê para saber o que fazer sem ninguém mandar."""

    gerado_em: datetime
    total: int
    por_estado: dict[str, int]
    aguardando_o_agente: list[str] = Field(
        description="Identificadores em estado que o agente ainda pode avançar.")
    aguardando_humano: list[str] = Field(
        description="Identificadores parados em exceção. O agente NÃO resolve estes.")
    propostas_pendentes: int


class EstadoDeSaude(BaseModel):
    servico: str = "servico-de-continuidade-do-deva"
    versao: str
    armazenamento: str
    memoria_acessivel: bool
    total_de_linhas_na_memoria: int
    propostas_pendentes: int


def agora() -> datetime:
    return datetime.now(timezone.utc)
