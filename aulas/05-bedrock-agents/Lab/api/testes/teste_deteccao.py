"""Testes do Deva3.

Não chamam a AWS: usam respostas no formato do Rekognition. O objetivo é
garantir que a interpretação do payload (proporção → pixels, 0–100 → 0–1) e as
regras de limiar continuem certas depois de qualquer mudança.

    python -m pytest api/testes -v
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from api.erros import ImagemGrandeDemais, ImagemInvalida
from api.modelos import CaixaDelimitadora
from api.principal import _para_formato_do_rekognition, _validar_imagem
from api.servicos.detector_pessoas import ServicoPessoasRekognition, caixa_em_pixels
from api.servicos.detector_rostos import ServicoRostosRekognition

# ── respostas no formato da documentação do Rekognition ──────────────────

RESPOSTA_PESSOAS = {
    "Labels": [
        {
            "Name": "Person",
            "Confidence": 99.2,
            "Instances": [
                {"BoundingBox": {"Width": 0.3167, "Height": 0.8182, "Left": 0.0, "Top": 0.1775},
                 "Confidence": 94.74},
                {"BoundingBox": {"Width": 0.2333, "Height": 0.6494, "Left": 0.4333, "Top": 0.2597},
                 "Confidence": 42.12},
            ],
        }
    ],
    "LabelModelVersion": "3.0",
}

RESPOSTA_ROSTOS = {
    "FaceDetails": [
        {"BoundingBox": {"Width": 0.13, "Height": 0.26, "Left": 0.6567, "Top": 0.2338},
         "Confidence": 99.98,
         "Quality": {"Brightness": 81.2, "Sharpness": 92.2}}
    ]
}


def _imagem_valida(largura: int = 120, altura: int = 90) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (largura, altura), (20, 21, 26)).save(buffer, format="PNG")
    return buffer.getvalue()


# ── interpretação do payload de pessoas ──────────────────────────────────

def teste_pessoas_converte_proporcao_em_pixels_e_confianca():
    servico = ServicoPessoasRekognition(regiao="us-east-1")
    achados, dimensoes = servico._interpretar(RESPOSTA_PESSOAS, 300, 231)

    assert dimensoes == (300, 231)
    assert len(achados) == 2

    caixa, confianca = achados[0]
    assert isinstance(caixa, CaixaDelimitadora)
    assert (caixa.x, caixa.y, caixa.largura, caixa.altura) == (0, 41, 95, 189)
    assert confianca == pytest.approx(0.9474, abs=1e-4)  # 94.74 / 100


def teste_pessoas_ordena_da_maior_para_a_menor_confianca():
    servico = ServicoPessoasRekognition(regiao="us-east-1")
    achados, _ = servico._interpretar(RESPOSTA_PESSOAS, 300, 231)
    confiancas = [confianca for _, confianca in achados]
    assert confiancas == sorted(confiancas, reverse=True)


def teste_pessoas_ignora_outros_rotulos_e_lista_vazia():
    servico = ServicoPessoasRekognition(regiao="us-east-1")
    achados, _ = servico._interpretar({"Labels": [{"Name": "Chair", "Instances": [
        {"BoundingBox": {"Width": 0.5, "Height": 0.5, "Left": 0, "Top": 0}, "Confidence": 99}]}]}, 10, 10)
    assert achados == []
    assert servico._interpretar({}, 10, 10)[0] == []


def teste_caixa_nunca_sai_da_imagem():
    caixa = caixa_em_pixels({"Width": 0.5, "Height": 0.5, "Left": 0.8, "Top": -0.1}, 100, 100)
    assert caixa.x == 80 and caixa.y == 0
    assert caixa.x + caixa.largura <= 100


# ── interpretação do payload de rostos ───────────────────────────────────

def teste_rostos_tem_confianca_real():
    servico = ServicoRostosRekognition(regiao="us-east-1")
    achados, _ = servico._interpretar(RESPOSTA_ROSTOS, 600, 300)

    caixa, nota = achados[0]
    assert (caixa.x, caixa.y, caixa.largura, caixa.altura) == (394, 70, 78, 78)
    assert nota == pytest.approx(0.9998, abs=1e-4)


def teste_rostos_sem_confianca_devolve_nulo():
    servico = ServicoRostosRekognition(regiao="us-east-1")
    achados, _ = servico._interpretar(
        {"FaceDetails": [{"BoundingBox": {"Width": 0.1, "Height": 0.1, "Left": 0, "Top": 0}}]}, 10, 10)
    _, nota = achados[0]
    assert nota is None


# ── conversão de formato ─────────────────────────────────────────────────

def teste_png_passa_direto_e_bmp_vira_png():
    png = _imagem_valida()
    assert _para_formato_do_rekognition(png, "image/png") is png

    buffer = io.BytesIO()
    Image.new("RGB", (100, 100), (1, 2, 3)).save(buffer, format="BMP")
    convertido = _para_formato_do_rekognition(buffer.getvalue(), "image/bmp")
    assert convertido[:8] == b"\x89PNG\r\n\x1a\n"


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
