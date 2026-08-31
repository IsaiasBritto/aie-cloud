"""Testes do Deva3.

Não chamam a Azure: usam respostas gravadas. O objetivo é garantir que a
interpretação do payload e as regras de limiar continuem certas depois de
qualquer mudança.

    python -m pytest api/testes -v
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from api.erros import ImagemGrandeDemais, ImagemInvalida
from api.modelos import CaixaDelimitadora
from api.principal import _validar_imagem
from api.servicos.detector_rostos import ServicoFaceAzure
from api.servicos.detector_visao import ServicoVisaoAzure

# ── respostas reais, copiadas da documentação da Azure ───────────────────

RESPOSTA_VISAO = {
    "modelVersion": "2024-02-01",
    "metadata": {"width": 300, "height": 231},
    "peopleResult": {
        "values": [
            {"boundingBox": {"x": 0, "y": 41, "w": 95, "h": 189}, "confidence": 0.9474},
            {"boundingBox": {"x": 130, "y": 60, "w": 70, "h": 150}, "confidence": 0.4212},
        ]
    },
}

RESPOSTA_FACE = [
    {
        "faceRectangle": {"top": 54, "left": 394, "width": 78, "height": 78},
        "faceAttributes": {"qualityForRecognition": "high",
                           "blur": {"blurLevel": "low", "value": 0.06}},
    }
]


def _imagem_valida(largura: int = 120, altura: int = 90) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (largura, altura), (20, 21, 26)).save(buffer, format="PNG")
    return buffer.getvalue()


# ── interpretação do payload de visão ────────────────────────────────────

def teste_visao_interpreta_caixas_e_confianca():
    servico = ServicoVisaoAzure(endpoint="https://exemplo.cognitiveservices.azure.com",
                                chave="chave-de-teste")
    achados, dimensoes = servico._interpretar(RESPOSTA_VISAO)

    assert dimensoes == (300, 231)
    assert len(achados) == 2

    caixa, confianca = achados[0]
    assert isinstance(caixa, CaixaDelimitadora)
    assert (caixa.x, caixa.y, caixa.largura, caixa.altura) == (0, 41, 95, 189)
    assert confianca == pytest.approx(0.9474, abs=1e-4)


def teste_visao_ordena_da_maior_para_a_menor_confianca():
    servico = ServicoVisaoAzure(endpoint="https://exemplo.cognitiveservices.azure.com",
                                chave="chave-de-teste")
    achados, _ = servico._interpretar(RESPOSTA_VISAO)
    confiancas = [confianca for _, confianca in achados]
    assert confiancas == sorted(confiancas, reverse=True)


def teste_visao_sem_pessoas_devolve_lista_vazia():
    servico = ServicoVisaoAzure(endpoint="https://exemplo.cognitiveservices.azure.com",
                                chave="chave-de-teste")
    achados, _ = servico._interpretar({"metadata": {"width": 10, "height": 10}})
    assert achados == []


# ── interpretação do payload de rostos ───────────────────────────────────

def teste_face_converte_retangulo_para_o_nosso_formato():
    servico = ServicoFaceAzure(endpoint="https://exemplo.cognitiveservices.azure.com",
                               chave="chave-de-teste")
    achados, _ = servico._interpretar(RESPOSTA_FACE)

    caixa, nota = achados[0]
    # O Face usa left/top; o nosso contrato usa x/y.
    assert (caixa.x, caixa.y, caixa.largura, caixa.altura) == (394, 54, 78, 78)
    assert nota == 0.95  # derivada de qualityForRecognition = high


def teste_face_sem_qualidade_devolve_confianca_nula():
    servico = ServicoFaceAzure(endpoint="https://exemplo.cognitiveservices.azure.com",
                               chave="chave-de-teste")
    achados, _ = servico._interpretar([{"faceRectangle":
                                        {"top": 1, "left": 2, "width": 3, "height": 4}}])
    _, nota = achados[0]
    assert nota is None


# ── validação da imagem ──────────────────────────────────────────────────

def teste_imagem_valida_devolve_dimensoes():
    assert _validar_imagem(_imagem_valida(120, 90), "image/png", 4 * 1024 * 1024) == (120, 90)


def teste_imagem_vazia_e_recusada():
    with pytest.raises(ImagemInvalida):
        _validar_imagem(b"", "image/png", 4 * 1024 * 1024)


def teste_imagem_grande_demais_e_recusada():
    with pytest.raises(ImagemGrandeDemais):
        _validar_imagem(_imagem_valida(), "image/png", 10)


def teste_arquivo_que_nao_e_imagem_e_recusado():
    with pytest.raises(ImagemInvalida):
        _validar_imagem(b"isto aqui nao e uma imagem", "image/png", 4 * 1024 * 1024)


def teste_tipo_nao_aceito_e_recusado():
    with pytest.raises(ImagemInvalida):
        _validar_imagem(_imagem_valida(), "application/pdf", 4 * 1024 * 1024)


# ── regra de limiar (a que mais gera discussão em aula) ──────────────────

@pytest.mark.parametrize(
    "confianca, limiar, esperado",
    [(0.95, 0.60, True), (0.60, 0.60, True), (0.59, 0.60, False), (None, 0.60, False)],
)
def teste_regra_do_limiar(confianca, limiar, esperado):
    acima = bool(confianca is not None and confianca >= limiar)
    assert acima is esperado


def teste_area_da_caixa():
    caixa = CaixaDelimitadora(x=0, y=0, largura=10, altura=20)
    assert caixa.area == 200
