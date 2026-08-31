"""Serviço de armazenamento no Azure Blob Storage.

Grava, para cada análise, dois arquivos no container `deteccoes`:

    AAAA/MM/DD/<identificador>/original.<ext>   ← a imagem enviada
    AAAA/MM/DD/<identificador>/resultado.json   ← o payload devolvido

⚖️ LGPD, para dizer em aula: imagem de rosto é **dado pessoal sensível**
(dado biométrico, art. 5º, II da LGPD). Guardar exige base legal, consentimento
informado, prazo de retenção e um jeito de apagar. Por isso:

- a interface pede consentimento explícito antes de enviar;
- `PERSISTIR_IMAGENS=false` desliga a gravação da imagem sem quebrar nada;
- o script `99-remover-tudo.sh` apaga o grupo de recursos inteiro no fim da aula.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from azure.core.exceptions import AzureError
from azure.storage.blob.aio import BlobServiceClient

from api.erros import FalhaDeArmazenamento

EXTENSAO_POR_TIPO = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/bmp": "bmp",
    "image/webp": "webp",
}


class ServicoArmazenamentoBlob:
    """Grava imagem e resultado no Blob Storage."""

    NOME = "Azure Blob Storage"

    def __init__(self, conexao: str, container: str = "deteccoes") -> None:
        self.conexao = conexao
        self.container = container

    def montar_prefixo(self, identificador: str,
                       momento: datetime | None = None) -> str:
        agora = momento or datetime.now(timezone.utc)
        return f"{agora:%Y/%m/%d}/{identificador}"

    async def guardar(self, identificador: str, imagem: bytes | None,
                      tipo_conteudo: str, resultado: dict,
                      momento: datetime | None = None) -> str:
        """Grava os arquivos e devolve o prefixo usado no container."""
        prefixo = self.montar_prefixo(identificador, momento)
        try:
            async with BlobServiceClient.from_connection_string(self.conexao) as servico:
                container = servico.get_container_client(self.container)

                if imagem is not None:
                    extensao = EXTENSAO_POR_TIPO.get(tipo_conteudo, "bin")
                    await container.upload_blob(
                        name=f"{prefixo}/original.{extensao}",
                        data=imagem,
                        overwrite=True,
                    )

                await container.upload_blob(
                    name=f"{prefixo}/resultado.json",
                    data=json.dumps(resultado, ensure_ascii=False, indent=2,
                                    default=str).encode("utf-8"),
                    overwrite=True,
                )
        except AzureError as erro:
            raise FalhaDeArmazenamento(
                mensagem="Não foi possível gravar no Blob Storage.",
                detalhe=str(erro),
                como_resolver=(
                    "Confira ARMAZENAMENTO_CONEXAO (string de conexão completa, com "
                    "AccountKey) e se o container 'deteccoes' existe na conta."
                ),
            ) from erro

        return prefixo

    async def container_existe(self) -> bool:
        try:
            async with BlobServiceClient.from_connection_string(self.conexao) as servico:
                container = servico.get_container_client(self.container)
                return await container.exists()
        except AzureError:
            return False
