"""Serviço de detecção de rostos usando o Azure AI Face.

⚠️ ATENÇÃO DIDÁTICA — leia antes de usar em sala:

1. O serviço **Face é de Acesso Limitado**. Criar o recurso exige preencher o
   formulário de cadastro da Microsoft e ser aprovado. Se a turma não tem
   aprovação, use o modo `pessoas` (Image Analysis) — ele funciona na hora.

2. A detecção do Face **não devolve pontuação de confiança**. Ela devolve o
   retângulo do rosto e ponto. Para ter algo comparável a uma confiança, pedimos
   o atributo `qualityForRecognition` (baixa/média/alta) e o `blur`, e
   convertemos isso numa nota de 0 a 1 — deixando claro no payload que é uma
   nota **derivada**, não a confiança do detector.

Contrato da chamada (documentação em 30/08/2026):

    POST {endpoint}/face/v1.2/detect
         ?detectionModel=detection_03&recognitionModel=recognition_04
         &returnFaceId=false&returnFaceLandmarks=false
         &returnFaceAttributes=qualityForRecognition,blur
    Cabeçalhos: Ocp-Apim-Subscription-Key, Content-Type: application/octet-stream

Resposta:

    [ { "faceRectangle": {"top":54,"left":394,"width":78,"height":78},
        "faceAttributes": {"qualityForRecognition":"high",
                           "blur":{"blurLevel":"low","value":0.06}} } ]
"""

from __future__ import annotations

import httpx

from api.erros import FalhaDeIntegracao, ServicoNaoConfigurado
from api.modelos import CaixaDelimitadora

# Conversão da qualidade categórica em nota numérica, para a interface conseguir
# desenhar uma barra. É uma convenção NOSSA, e o payload diz isso.
NOTA_POR_QUALIDADE = {"high": 0.95, "medium": 0.70, "low": 0.35}


class ServicoFaceAzure:
    """Encapsula a chamada ao Azure AI Face."""

    NOME = "Azure AI Face · /face/v1.2/detect"

    def __init__(self, endpoint: str, chave: str,
                 modelo_deteccao: str = "detection_03", tempo_limite: int = 30) -> None:
        if not endpoint or not chave:
            raise ServicoNaoConfigurado(
                servico="Azure AI Face",
                como_resolver=(
                    "Este modo é opcional e exige um recurso Face aprovado no programa "
                    "de Acesso Limitado. Sem ele, use o modo 'pessoas'. "
                    "Se você tem o recurso, defina FACE_ENDPOINT e FACE_CHAVE no .env."
                ),
            )
        self.endpoint = endpoint.rstrip("/")
        self.chave = chave
        self.modelo_deteccao = modelo_deteccao
        self.tempo_limite = tempo_limite

    @property
    def url(self) -> str:
        return f"{self.endpoint}/face/v1.2/detect"

    async def detectar(self, imagem: bytes) -> tuple[
        list[tuple[CaixaDelimitadora, float | None]], tuple[int, int]
    ]:
        parametros = {
            "detectionModel": self.modelo_deteccao,
            "recognitionModel": "recognition_04",
            "returnFaceId": "false",
            "returnFaceLandmarks": "false",
            "returnFaceAttributes": "qualityForRecognition,blur",
        }
        cabecalhos = {
            "Ocp-Apim-Subscription-Key": self.chave,
            "Content-Type": "application/octet-stream",
        }

        try:
            async with httpx.AsyncClient(timeout=self.tempo_limite) as cliente:
                resposta = await cliente.post(
                    self.url, params=parametros, headers=cabecalhos, content=imagem
                )
        except httpx.HTTPError as erro:
            raise FalhaDeIntegracao(
                servico=self.NOME,
                mensagem="Não foi possível falar com o serviço de rostos.",
                detalhe=str(erro),
                como_resolver="Confira FACE_ENDPOINT e a conectividade de saída do container.",
            ) from erro

        self._verificar_resposta(resposta)
        return self._interpretar(resposta.json())

    # ── auxiliares ───────────────────────────────────────────────────────
    def _verificar_resposta(self, resposta: httpx.Response) -> None:
        if resposta.status_code == 200:
            return

        dicas = {
            401: "Chave inválida para o recurso Face.",
            403: (
                "Acesso negado. Quase sempre é o Acesso Limitado do Face: a assinatura "
                "precisa estar aprovada. Use o modo 'pessoas' enquanto isso."
            ),
            400: "A imagem pode estar fora dos limites (1 KB a 6 MB, JPEG/PNG/GIF/BMP).",
            429: "Cota estourada. Espere um minuto e tente de novo.",
        }
        raise FalhaDeIntegracao(
            servico=self.NOME,
            mensagem=f"O serviço de rostos devolveu HTTP {resposta.status_code}.",
            detalhe=resposta.text[:600],
            como_resolver=dicas.get(resposta.status_code, "Leia o campo detalhe."),
        )

    def _interpretar(self, corpo: list) -> tuple[
        list[tuple[CaixaDelimitadora, float | None]], tuple[int, int]
    ]:
        achados: list[tuple[CaixaDelimitadora, float | None]] = []
        for rosto in corpo or []:
            retangulo = rosto.get("faceRectangle") or {}
            caixa = CaixaDelimitadora(
                x=int(retangulo.get("left", 0)),
                y=int(retangulo.get("top", 0)),
                largura=int(retangulo.get("width", 0)),
                altura=int(retangulo.get("height", 0)),
            )
            atributos = rosto.get("faceAttributes") or {}
            qualidade = (atributos.get("qualityForRecognition") or "").lower()
            nota = NOTA_POR_QUALIDADE.get(qualidade)
            achados.append((caixa, nota))

        # O Face não informa as dimensões da imagem; quem calcula é a API.
        return achados, (0, 0)
