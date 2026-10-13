"""Configuração da aplicação Deva3.

Todas as opções vêm de variáveis de ambiente. Em desenvolvimento elas são lidas
do arquivo `.env`; em produção, das variáveis da task definition do ECS.

Nada de segredo escrito no código. Nunca. E, na AWS, nem no ambiente: a
credencial do Rekognition e do S3 vem da role da tarefa (no Learner Lab, a
LabRole), entregue pelo próprio ECS.
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

    # ── AWS — Rekognition (modos "pessoas" e "rostos") ───────────────────
    regiao: str = field(
        default_factory=lambda: _texto("AWS_REGION") or _texto("AWS_DEFAULT_REGION", "us-east-1")
    )
    # Confiança mínima (0–100) pedida ao DetectLabels. Abaixo dela o Rekognition
    # nem devolve a caixa. É DIFERENTE do limiar de decisão (LIMIAR_CONFIANCA):
    # este filtra ruído; o limiar decide aprovar ou revisar.
    confianca_minima_rekognition: float = field(
        default_factory=lambda: float(os.getenv("REKOGNITION_CONFIANCA_MINIMA", "50"))
    )

    # ── Armazenamento (S3) ───────────────────────────────────────────────
    bucket: str = field(default_factory=lambda: _texto("ARMAZENAMENTO_BUCKET"))
    prefixo_armazenamento: str = field(
        default_factory=lambda: _texto("ARMAZENAMENTO_PREFIXO", "deteccoes")
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
    def credencial_aws(self) -> bool:
        """Há credencial AWS alcançável? (env, perfil ou role da tarefa)"""
        try:
            import boto3

            return boto3.Session().get_credentials() is not None
        except Exception:  # noqa: BLE001
            return False

    @property
    def armazenamento_configurado(self) -> bool:
        return bool(self.bucket)

    @property
    def modos_disponiveis(self) -> list[str]:
        # No Rekognition os dois modos usam a mesma credencial e nenhum exige
        # aprovação prévia (ao contrário do Face da Azure, de Acesso Limitado).
        return ["pessoas", "rostos"] if self.credencial_aws else []

    def lista_origens(self) -> list[str]:
        if self.origens_permitidas.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.origens_permitidas.split(",") if o.strip()]


@lru_cache(maxsize=1)
def obter_configuracao() -> Configuracao:
    """Devolve sempre a mesma instância de configuração (carregada uma vez)."""
    return Configuracao()
