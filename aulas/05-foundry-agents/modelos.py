"""Modelos de dados da API — o contrato que a interface e os alunos vão ler.

Todos os campos em português, porque o payload é material didático:
quem abre o JSON precisa entender sem tradutor.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ModoDeteccao(str, Enum):
    """Qual serviço cognitivo será chamado."""

    PESSOAS = "pessoas"   # Azure AI Vision · Image Analysis 4.0 · feature `people`
    ROSTOS = "rostos"     # Azure AI Face · /face/v1.2/detect (Acesso Limitado)


class CaixaDelimitadora(BaseModel):
    """Retângulo, em pixels, de onde a detecção aconteceu."""

    x: int = Field(..., description="Distância da borda esquerda até o retângulo, em pixels")
    y: int = Field(..., description="Distância do topo até o retângulo, em pixels")
    largura: int = Field(..., description="Largura do retângulo, em pixels")
    altura: int = Field(..., description="Altura do retângulo, em pixels")

    @property
    def area(self) -> int:
        return self.largura * self.altura


class Deteccao(BaseModel):
    """Uma detecção individual devolvida pelo serviço cognitivo."""

    indice: int = Field(..., description="Ordem da detecção no resultado, começando em 1")
    caixa: CaixaDelimitadora
    confianca: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Pontuação de 0 a 1 devolvida pelo serviço. "
            "O modo 'rostos' não devolve confiança — nesse caso vem nulo."
        ),
    )
    acima_do_limiar: bool = Field(
        ...,
        description="Se a confiança atingiu o limiar configurado. Nulo conta como False.",
    )
    proporcao_da_imagem: float = Field(
        ..., description="Percentual da área da imagem ocupado pela caixa (0 a 1)"
    )


class DimensoesImagem(BaseModel):
    largura: int
    altura: int


class ResultadoDeteccao(BaseModel):
    """Resposta completa do endpoint de detecção."""

    identificador: str = Field(..., description="Identificador único desta análise")
    momento: datetime = Field(..., description="Quando a análise foi feita (UTC)")
    modo: ModoDeteccao
    servico: str = Field(..., description="Nome do serviço da Azure efetivamente chamado")
    arquivo: str = Field(..., description="Nome do arquivo enviado")
    tamanho_bytes: int
    dimensoes: DimensoesImagem
    limiar_confianca: float
    total_detectado: int
    total_acima_do_limiar: int
    deteccoes: list[Deteccao]
    duracao_ms: int = Field(..., description="Tempo total da análise, em milissegundos")
    imagem_persistida: bool = Field(
        ..., description="Se a imagem foi gravada no Blob Storage"
    )
    caminho_blob: str | None = Field(
        None, description="Caminho do arquivo no container do Blob Storage"
    )
    avisos: list[str] = Field(
        default_factory=list,
        description="Mensagens que o aluno precisa ler (limiar, consentimento, degradação)",
    )


class EstadoSaude(BaseModel):
    """Resposta do endpoint de saúde — o primeiro lugar onde se olha quando dá erro."""

    situacao: Literal["saudavel", "degradado"] = "saudavel"
    aplicacao: str
    versao: str
    ambiente: str
    modos_disponiveis: list[str]
    armazenamento_configurado: bool
    persistir_imagens: bool
    limiar_confianca: float


class Falha(BaseModel):
    """Formato único de erro. Toda falha da API sai assim."""

    erro: str = Field(..., description="Código curto e estável do erro")
    mensagem: str = Field(..., description="Explicação em português, para humano")
    detalhe: str | None = Field(None, description="Detalhe técnico, quando existir")
    como_resolver: str | None = Field(
        None, description="A ação concreta que resolve — o campo que salva a aula"
    )
