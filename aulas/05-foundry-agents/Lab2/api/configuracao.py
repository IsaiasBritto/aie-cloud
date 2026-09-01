"""Configuração isolada num lugar só.

Nenhum `os.getenv` espalhado pelo código. Quando o aluno perguntar "onde configura
isso?", a resposta é sempre este arquivo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

VERSAO = "1.0.0"


@dataclass(frozen=True)
class Configuracao:
    # Onde a memória e a fila vivem.
    cadeia_de_conexao_do_blob: str = ""
    container_do_blob: str = "memoria-do-deva"
    pasta_local: Path = Path("dados")

    # Quem pode aprovar. Sem isto, o serviço sobe em modo aberto (só para aula local).
    segredo_do_auditor: str = ""

    # Limite de propostas pendentes. Fila de aprendizado que ninguém revisa é dívida.
    maximo_de_propostas_pendentes: int = 50

    @property
    def usa_blob(self) -> bool:
        return bool(self.cadeia_de_conexao_do_blob)

    @property
    def armazenamento(self) -> str:
        return "blob" if self.usa_blob else f"arquivo local ({self.pasta_local})"

    @property
    def exige_segredo(self) -> bool:
        return bool(self.segredo_do_auditor)


@lru_cache(maxsize=1)
def obter_configuracao() -> Configuracao:
    return Configuracao(
        cadeia_de_conexao_do_blob=os.getenv("DEVA_BLOB_CONEXAO", "").strip(),
        container_do_blob=os.getenv("DEVA_BLOB_CONTAINER", "memoria-do-deva").strip(),
        pasta_local=Path(os.getenv("DEVA_PASTA_LOCAL", "dados")),
        segredo_do_auditor=os.getenv("DEVA_SEGREDO_AUDITOR", "").strip(),
        maximo_de_propostas_pendentes=int(os.getenv("DEVA_MAX_PROPOSTAS", "50")),
    )
