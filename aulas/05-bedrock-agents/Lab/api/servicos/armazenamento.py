"""Serviço de armazenamento no Amazon S3.

Grava, para cada análise, dois objetos no bucket, sob o prefixo `deteccoes/`:

    deteccoes/AAAA/MM/DD/<identificador>/original.<ext>   ← a imagem enviada
    deteccoes/AAAA/MM/DD/<identificador>/resultado.json   ← o payload devolvido

⚖️ LGPD, para dizer em aula: imagem de rosto é **dado pessoal sensível**
(dado biométrico, art. 5º, II da LGPD). Guardar exige base legal, consentimento
informado, prazo de retenção e um jeito de apagar. Por isso:

- a interface pede consentimento explícito antes de enviar;
- `PERSISTIR_IMAGENS=false` desliga a gravação da imagem sem quebrar nada;
- o bucket tem regra de ciclo de vida: tudo em `deteccoes/` expira sozinho
  (padrão: 7 dias) — retenção escrita em código, não em promessa;
- o bucket bloqueia acesso público e criptografa em repouso;
- o `99-remover-tudo.sh` apaga o bucket inteiro no fim da aula.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from api.erros import FalhaDeArmazenamento
from api.servicos._aws import cliente, traduzir_erro

EXTENSAO_POR_TIPO = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/bmp": "bmp",
    "image/webp": "webp",
}


class ServicoArmazenamentoS3:
    """Grava imagem e resultado no S3."""

    NOME = "Amazon S3"

    def __init__(self, bucket: str, regiao: str, prefixo_raiz: str = "deteccoes") -> None:
        self.bucket = bucket
        self.regiao = regiao
        self.prefixo_raiz = prefixo_raiz.strip("/")

    def montar_prefixo(self, identificador: str,
                       momento: datetime | None = None) -> str:
        agora = momento or datetime.now(timezone.utc)
        return f"{self.prefixo_raiz}/{agora:%Y/%m/%d}/{identificador}"

    async def guardar(self, identificador: str, imagem: bytes | None,
                      tipo_conteudo: str, resultado: dict,
                      momento: datetime | None = None) -> str:
        """Grava os objetos e devolve o prefixo usado no bucket."""
        prefixo = self.montar_prefixo(identificador, momento)
        s3 = cliente("s3", self.regiao)
        try:
            if imagem is not None:
                extensao = EXTENSAO_POR_TIPO.get(tipo_conteudo, "bin")
                await asyncio.to_thread(
                    s3.put_object, Bucket=self.bucket, Key=f"{prefixo}/original.{extensao}",
                    Body=imagem, ContentType=tipo_conteudo,
                )
            await asyncio.to_thread(
                s3.put_object, Bucket=self.bucket, Key=f"{prefixo}/resultado.json",
                Body=json.dumps(resultado, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                ContentType="application/json",
            )
        except Exception as erro:  # noqa: BLE001
            traduzido = traduzir_erro(self.NOME, erro)
            raise FalhaDeArmazenamento(
                mensagem="Não foi possível gravar no S3.",
                detalhe=traduzido.detalhe,
                como_resolver=traduzido.como_resolver or (
                    "Confira ARMAZENAMENTO_BUCKET (output do Terraform) e a permissão "
                    "s3:PutObject da role."
                ),
            ) from erro

        return prefixo

    async def bucket_existe(self) -> bool:
        s3 = cliente("s3", self.regiao)
        try:
            await asyncio.to_thread(s3.head_bucket, Bucket=self.bucket)
            return True
        except Exception:  # noqa: BLE001
            return False
