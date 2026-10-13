"""Serviço de detecção de pessoas usando o Azure AI Vision (Image Analysis 4.0).

Este é o modo padrão do Deva3, porque funciona com qualquer chave de Vision:
não depende de aprovação de Acesso Limitado.

Contrato da chamada (confirmado na documentação em 30/08/2026):

    POST {endpoint}/computervision/imageanalysis:analyze
         ?api-version=2024-02-01&features=people
    Cabeçalhos: Ocp-Apim-Subscription-Key, Content-Type: application/octet-stream
    Corpo: os bytes da imagem

Resposta:

    {
      "modelVersion": "2024-02-01",
      "metadata": { "width": 300, "height": 231 },
      "peopleResult": {
        "values": [ { "boundingBox": {"x":0,"y":41,"w":95,"h":189},
                      "confidence": 0.947 } ]
      }
    }
"""

from __future__ import annotations

import httpx

from api.erros import FalhaDeIntegracao, ServicoNaoConfigurado
from api.modelos import CaixaDelimitadora


class ServicoVisaoAzure:
    """Encapsula a chamada ao Image Analysis 4.0."""

    NOME = "Azure AI Vision · Image Analysis 4.0 (features=people)"

    def __init__(self, endpoint: str, chave: str, versao_api: str = "2024-02-01",
                 tempo_limite: int = 30) -> None:
        if not endpoint or not chave:
            raise ServicoNaoConfigurado(
                servico="Azure AI Vision",
                como_resolver=(
                    "Defina VISAO_ENDPOINT e VISAO_CHAVE no arquivo .env "
                    "(ou nas variáveis de ambiente do Container App)."
                ),
            )
        self.endpoint = endpoint.rstrip("/")
        self.chave = chave
        self.versao_api = versao_api
        self.tempo_limite = tempo_limite

    @property
    def url(self) -> str:
        return f"{self.endpoint}/computervision/imageanalysis:analyze"

    async def detectar(self, imagem: bytes) -> tuple[list[tuple[CaixaDelimitadora, float]],
                                                     tuple[int, int]]:
        """Envia a imagem e devolve as caixas com confiança e as dimensões da imagem.

        Retorna uma tupla: ([(caixa, confiança), ...], (largura, altura)).
        """
        parametros = {"api-version": self.versao_api, "features": "people"}
        cabecalhos = {
            "Ocp-Apim-Subscription-Key": self.chave,
            "Content-Type": "application/octet-stream",
        }

        try:
            async with httpx.AsyncClient(timeout=self.tempo_limite) as cliente:
                resposta = await cliente.post(
                    self.url, params=parametros, headers=cabecalhos, content=imagem
                )
        except httpx.TimeoutException as erro:
            raise FalhaDeIntegracao(
                servico=self.NOME,
                mensagem="O serviço de visão não respondeu dentro do tempo limite.",
                detalhe=str(erro),
                como_resolver=(
                    "Tente uma imagem menor ou aumente TEMPO_LIMITE_SEGUNDOS no .env."
                ),
            ) from erro
        except httpx.HTTPError as erro:
            raise FalhaDeIntegracao(
                servico=self.NOME,
                mensagem="Não foi possível falar com o serviço de visão.",
                detalhe=str(erro),
                como_resolver=(
                    "Confira se VISAO_ENDPOINT está completo, começando com https:// "
                    "e terminando em .cognitiveservices.azure.com"
                ),
            ) from erro

        self._verificar_resposta(resposta)
        return self._interpretar(resposta.json())

    # ── auxiliares ───────────────────────────────────────────────────────
    def _verificar_resposta(self, resposta: httpx.Response) -> None:
        if resposta.status_code == 200:
            return

        dicas = {
            401: "A chave está errada ou é de outro recurso. Copie de novo em Chaves e Ponto de Extremidade.",
            403: "A chave é válida mas não tem permissão para este recurso ou região.",
            404: "O endpoint está errado. Ele termina em .cognitiveservices.azure.com, sem barra no fim.",
            413: "A imagem é grande demais para o serviço. Reduza para menos de 4 MB.",
            415: "O formato não é aceito. Use JPEG, PNG ou BMP.",
            429: "Você estourou a cota do nível gratuito F0 (20 chamadas por minuto). Espere um minuto.",
        }
        raise FalhaDeIntegracao(
            servico=self.NOME,
            mensagem=f"O serviço de visão devolveu HTTP {resposta.status_code}.",
            detalhe=resposta.text[:600],
            como_resolver=dicas.get(
                resposta.status_code,
                "Leia o campo detalhe: a Azure costuma dizer exatamente o que faltou.",
            ),
        )

    def _interpretar(self, corpo: dict) -> tuple[list[tuple[CaixaDelimitadora, float]],
                                                 tuple[int, int]]:
        metadados = corpo.get("metadata", {}) or {}
        dimensoes = (int(metadados.get("width", 0)), int(metadados.get("height", 0)))

        valores = ((corpo.get("peopleResult") or {}).get("values")) or []
        achados: list[tuple[CaixaDelimitadora, float]] = []
        for valor in valores:
            retangulo = valor.get("boundingBox") or {}
            caixa = CaixaDelimitadora(
                x=int(retangulo.get("x", 0)),
                y=int(retangulo.get("y", 0)),
                largura=int(retangulo.get("w", 0)),
                altura=int(retangulo.get("h", 0)),
            )
            achados.append((caixa, float(valor.get("confidence", 0.0))))

        achados.sort(key=lambda item: item[1], reverse=True)
        return achados, dimensoes
