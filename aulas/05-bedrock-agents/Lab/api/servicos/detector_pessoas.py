"""Detecção de pessoas com o Amazon Rekognition (DetectLabels, rótulo Person).

É o modo padrão do Deva3: devolve uma caixa por pessoa encontrada, com a
confiança do detector.

Contrato da chamada:

    rekognition.detect_labels(
        Image={"Bytes": <bytes da imagem>},
        Features=["GENERAL_LABELS"],
        Settings={"GeneralLabels": {"LabelInclusionFilters": ["Person"]}},
        MinConfidence=50,
    )

Resposta (trecho):

    {"Labels": [{"Name": "Person", "Confidence": 99.1,
                 "Instances": [{"BoundingBox": {"Width": 0.31, "Height": 0.82,
                                                "Left": 0.0,  "Top": 0.17},
                                "Confidence": 94.7}]}]}

Duas diferenças em relação ao Azure AI Vision, e as duas caem em prova:

1. A caixa vem em PROPORÇÃO da imagem (0 a 1), não em pixels. Quem converte
   somos nós — por isso este serviço precisa das dimensões da imagem.
2. A confiança vem de 0 a 100, não de 0 a 1. Dividimos por 100 para manter
   o contrato da API (e o limiar) iguais.
"""

from __future__ import annotations

import asyncio

from api.modelos import CaixaDelimitadora
from api.servicos._aws import cliente, traduzir_erro


def caixa_em_pixels(proporcao: dict, largura: int, altura: int) -> CaixaDelimitadora:
    """BoundingBox do Rekognition (0–1) → caixa em pixels, presa dentro da imagem."""
    x = max(0, round(float(proporcao.get("Left", 0)) * largura))
    y = max(0, round(float(proporcao.get("Top", 0)) * altura))
    w = round(float(proporcao.get("Width", 0)) * largura)
    h = round(float(proporcao.get("Height", 0)) * altura)
    return CaixaDelimitadora(x=x, y=y, largura=max(0, min(w, largura - x)),
                             altura=max(0, min(h, altura - y)))


class ServicoPessoasRekognition:
    """Encapsula a chamada ao DetectLabels filtrada para pessoas."""

    NOME = "Amazon Rekognition · DetectLabels (Person)"

    def __init__(self, regiao: str, confianca_minima: float = 50.0,
                 tempo_limite: int = 30) -> None:
        self.regiao = regiao
        self.confianca_minima = confianca_minima
        self.tempo_limite = tempo_limite

    async def detectar(self, imagem: bytes, largura: int, altura: int) -> tuple[
        list[tuple[CaixaDelimitadora, float]], tuple[int, int]
    ]:
        """Devolve ([(caixa, confiança 0–1), ...], (largura, altura))."""
        rekognition = cliente("rekognition", self.regiao, self.tempo_limite)
        try:
            corpo = await asyncio.to_thread(
                rekognition.detect_labels,
                Image={"Bytes": imagem},
                Features=["GENERAL_LABELS"],
                Settings={"GeneralLabels": {"LabelInclusionFilters": ["Person"]}},
                MinConfidence=self.confianca_minima,
            )
        except Exception as erro:  # noqa: BLE001 — vira erro com "como resolver"
            raise traduzir_erro(self.NOME, erro) from erro
        return self._interpretar(corpo, largura, altura)

    def _interpretar(self, corpo: dict, largura: int, altura: int) -> tuple[
        list[tuple[CaixaDelimitadora, float]], tuple[int, int]
    ]:
        achados: list[tuple[CaixaDelimitadora, float]] = []
        for rotulo in corpo.get("Labels") or []:
            if rotulo.get("Name") != "Person":
                continue
            for instancia in rotulo.get("Instances") or []:
                caixa = caixa_em_pixels(instancia.get("BoundingBox") or {}, largura, altura)
                achados.append((caixa, round(float(instancia.get("Confidence", 0)) / 100, 4)))

        achados.sort(key=lambda item: item[1], reverse=True)
        return achados, (largura, altura)
