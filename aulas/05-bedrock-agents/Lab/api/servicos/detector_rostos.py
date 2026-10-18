"""Detecção de rostos com o Amazon Rekognition (DetectFaces).

Diferente do Azure AI Face, aqui NÃO há Acesso Limitado: o DetectFaces
funciona na hora, inclusive no AWS Academy Learner Lab. E devolve a confiança
de detecção de verdade — não é preciso derivar nota de atributo de qualidade.

⚖️ O que esta chamada faz e o que ela NÃO faz:

- DetectFaces responde "há um rosto aqui, com esta confiança". Só isso.
- Não identifica ninguém. Identificar exigiria CompareFaces, SearchFacesByImage
  ou uma Collection com IndexFaces — que guarda um vetor biométrico do rosto.
  O Deva3 não chama nenhuma dessas, de propósito.

Contrato da chamada:

    rekognition.detect_faces(Image={"Bytes": ...}, Attributes=["DEFAULT"])

Resposta (trecho):

    {"FaceDetails": [{"BoundingBox": {"Width": 0.12, "Height": 0.20,
                                      "Left": 0.61, "Top": 0.18},
                      "Confidence": 99.98,
                      "Quality": {"Brightness": 81.2, "Sharpness": 92.2}}]}
"""

from __future__ import annotations

import asyncio

from api.modelos import CaixaDelimitadora
from api.servicos._aws import cliente, traduzir_erro
from api.servicos.detector_pessoas import caixa_em_pixels


class ServicoRostosRekognition:
    """Encapsula a chamada ao DetectFaces."""

    NOME = "Amazon Rekognition · DetectFaces"

    def __init__(self, regiao: str, tempo_limite: int = 30) -> None:
        self.regiao = regiao
        self.tempo_limite = tempo_limite

    async def detectar(self, imagem: bytes, largura: int, altura: int) -> tuple[
        list[tuple[CaixaDelimitadora, float | None]], tuple[int, int]
    ]:
        rekognition = cliente("rekognition", self.regiao, self.tempo_limite)
        try:
            corpo = await asyncio.to_thread(
                rekognition.detect_faces, Image={"Bytes": imagem}, Attributes=["DEFAULT"]
            )
        except Exception as erro:  # noqa: BLE001
            raise traduzir_erro(self.NOME, erro) from erro
        return self._interpretar(corpo, largura, altura)

    def _interpretar(self, corpo: dict, largura: int, altura: int) -> tuple[
        list[tuple[CaixaDelimitadora, float | None]], tuple[int, int]
    ]:
        achados: list[tuple[CaixaDelimitadora, float | None]] = []
        for rosto in corpo.get("FaceDetails") or []:
            caixa = caixa_em_pixels(rosto.get("BoundingBox") or {}, largura, altura)
            confianca = rosto.get("Confidence")
            achados.append((caixa, round(float(confianca) / 100, 4) if confianca is not None else None))

        achados.sort(key=lambda item: item[1] or 0, reverse=True)
        return achados, (largura, altura)
