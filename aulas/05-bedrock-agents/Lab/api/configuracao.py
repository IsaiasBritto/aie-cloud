"""Configuração da aplicação Deva3.

Todas as opções vêm de variáveis de ambiente. Em desenvolvimento elas são lidas
do arquivo `.env`; em produção, das variáveis do Azure Container App.

Nada de segredo escrito no código. Nunca.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _texto(nome: str, padrao: str = "") -> str:
    return os.getenv(nome, padrao).strip()


def _booleano(nome: str, padrao: bool = False) -> bool:
    valor = os.getenv(nome, str(padrao)).strip().lower()
    return valor in {"1", "true", "sim", "yes", "on"}


def _inteiro(nome: str, padrao: int) -> int:
    try:
        return int(os.getenv(nome, str(padrao)))
    except ValueError:
        return padrao


@dataclass(frozen=True)
class Configuracao:
    """Reúne, num objeto só, tudo que a aplicação precisa saber do ambiente."""

    # ── Identificação ────────────────────────────────────────────────────
    nome_aplicacao: str = "Deva3 · API de Validação Biométrica Básica"
    versao: str = "1.0.0"
    ambiente: str = field(default_factory=lambda: _texto("AMBIENTE", "local"))

    # ── Azure AI Vision (modo "pessoas") ─────────────────────────────────
    endpoint_visao: str = field(default_factory=lambda: _texto("VISAO_ENDPOINT"))
    chave_visao: str = field(default_factory=lambda: _texto("VISAO_CHAVE"))
    versao_api_visao: str = field(
        default_factory=lambda: _texto("VISAO_API_VERSAO", "2024-02-01")
    )

    # ── Azure AI Face (modo "rostos") — opcional, exige Acesso Limitado ──
    endpoint_face: str = field(default_factory=lambda: _texto("FACE_ENDPOINT"))
    chave_face: str = field(default_factory=lambda: _texto("FACE_CHAVE"))
    modelo_deteccao_face: str = field(
        default_factory=lambda: _texto("FACE_MODELO_DETECCAO", "detection_03")
    )

    # ── Armazenamento (Blob) ─────────────────────────────────────────────
    conexao_armazenamento: str = field(
        default_factory=lambda: _texto("ARMAZENAMENTO_CONEXAO")
    )
    container_blob: str = field(
        default_factory=lambda: _texto("ARMAZENAMENTO_CONTAINER", "deteccoes")
    )
    persistir_imagens: bool = field(
        default_factory=lambda: _booleano("PERSISTIR_IMAGENS", True)
    )

    # ── Limites operacionais ─────────────────────────────────────────────
    tamanho_maximo_bytes: int = field(
        default_factory=lambda: _inteiro("TAMANHO_MAXIMO_MB", 4) * 1024 * 1024
    )
    limiar_confianca: float = field(
        default_factory=lambda: float(os.getenv("LIMIAR_CONFIANCA", "0.60"))
    )
    tempo_limite_segundos: int = field(
        default_factory=lambda: _inteiro("TEMPO_LIMITE_SEGUNDOS", 30)
    )
    origens_permitidas: str = field(
        default_factory=lambda: _texto("ORIGENS_PERMITIDAS", "*")
    )

    # ── Verificações ─────────────────────────────────────────────────────
    @property
    def visao_configurada(self) -> bool:
        return bool(self.endpoint_visao and self.chave_visao)

    @property
    def face_configurada(self) -> bool:
        return bool(self.endpoint_face and self.chave_face)

    @property
    def armazenamento_configurado(self) -> bool:
        return bool(self.conexao_armazenamento)

    @property
    def modos_disponiveis(self) -> list[str]:
        modos = []
        if self.visao_configurada:
            modos.append("pessoas")
        if self.face_configurada:
            modos.append("rostos")
        return modos

    def lista_origens(self) -> list[str]:
        if self.origens_permitidas.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.origens_permitidas.split(",") if o.strip()]


@lru_cache(maxsize=1)
def obter_configuracao() -> Configuracao:
    """Devolve sempre a mesma instância de configuração (carregada uma vez)."""
    return Configuracao()
