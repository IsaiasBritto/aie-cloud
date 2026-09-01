"""Onde a memória mora.

Dois modos, mesma interface:

* **Blob Storage** — é o modo da aula. Importa porque o aluno consegue abrir o
  `MEMORY.md` pelo portal do Azure, ver a data de modificação mudar e entender que
  memória de agente é **um arquivo com dono, permissão e retenção** — não mágica.
* **Arquivo local** — para rodar na máquina antes de provisionar qualquer coisa.

Decisão importante: guardamos os dados em JSON (para a aplicação) **e** publicamos o
markdown renderizado (para o ser humano). O JSON é a verdade; o `.md` é a janela. Os
dois são reescritos na mesma operação, então nunca divergem.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from ..configuracao import Configuracao
from ..erros import ArmazenamentoIndisponivel

ARQUIVO_MEMORIA = "memoria.json"
ARQUIVO_PROPOSTAS = "propostas.json"
ARQUIVO_FILA = "fila.json"
ARQUIVO_MEMORIA_MD = "MEMORY.md"
ARQUIVO_PENDENTE_MD = "memoria-pendente.md"


class Armazenamento:
    """Interface mínima: ler texto, escrever texto, ler JSON, escrever JSON."""

    def ler_texto(self, nome: str) -> str | None:
        raise NotImplementedError

    def escrever_texto(self, nome: str, conteudo: str) -> None:
        raise NotImplementedError

    def ler_json(self, nome: str, padrao):
        bruto = self.ler_texto(nome)
        if bruto is None or not bruto.strip():
            return padrao
        try:
            return json.loads(bruto)
        except json.JSONDecodeError as erro:
            raise ArmazenamentoIndisponivel(
                f"O arquivo {nome} está corrompido.",
                detalhe=str(erro),
                como_resolver=("Abra o arquivo no armazenamento e conserte o JSON, ou "
                               "apague-o para que o serviço recrie vazio. Um backup "
                               "automático não existe de propósito: em aula, o aluno "
                               "precisa ver que estado tem custo."),
            ) from erro

    def escrever_json(self, nome: str, dados) -> None:
        self.escrever_texto(nome, json.dumps(dados, ensure_ascii=False, indent=2,
                                             default=str))


class ArmazenamentoLocal(Armazenamento):
    def __init__(self, pasta: Path):
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)
        self._trava = threading.Lock()

    def ler_texto(self, nome: str) -> str | None:
        caminho = self.pasta / nome
        if not caminho.exists():
            return None
        return caminho.read_text(encoding="utf-8")

    def escrever_texto(self, nome: str, conteudo: str) -> None:
        with self._trava:
            destino = self.pasta / nome
            provisorio = destino.with_suffix(destino.suffix + ".tmp")
            provisorio.write_text(conteudo, encoding="utf-8")
            provisorio.replace(destino)   # troca atômica: nunca deixa arquivo pela metade


class ArmazenamentoEmBlob(Armazenamento):
    def __init__(self, cadeia_de_conexao: str, container: str):
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as erro:                      # pragma: no cover
            raise ArmazenamentoIndisponivel(
                "A biblioteca azure-storage-blob não está instalada.",
                detalhe=str(erro),
                como_resolver="pip install azure-storage-blob",
            ) from erro

        self._servico = BlobServiceClient.from_connection_string(cadeia_de_conexao)
        self._container = self._servico.get_container_client(container)
        try:
            self._container.create_container()
        except Exception:      # já existe — é o caso normal a partir da segunda execução
            pass

    def ler_texto(self, nome: str) -> str | None:
        try:
            return self._container.download_blob(nome).readall().decode("utf-8")
        except Exception:
            return None

    def escrever_texto(self, nome: str, conteudo: str) -> None:
        from azure.storage.blob import ContentSettings
        # text/markdown faz o portal do Azure exibir o arquivo em vez de baixá-lo.
        tipo = "text/markdown" if nome.endswith(".md") else "application/json"
        self._container.upload_blob(
            name=nome, data=conteudo.encode("utf-8"), overwrite=True,
            content_settings=ContentSettings(content_type=f"{tipo}; charset=utf-8"))


def montar_armazenamento(config: Configuracao) -> Armazenamento:
    if config.usa_blob:
        return ArmazenamentoEmBlob(config.cadeia_de_conexao_do_blob,
                                   config.container_do_blob)
    return ArmazenamentoLocal(config.pasta_local)
