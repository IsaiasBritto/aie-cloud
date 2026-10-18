"""Teste de ponta a ponta do POST /detectar, sem AWS.

Troca o cliente boto3 por um falso que devolve respostas gravadas e guarda o
que foi pedido. Assim dá para conferir o contrato inteiro: a chamada ao
Rekognition, a conversão para pixels, o limiar e a regra de consentimento do S3.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import configuracao
from api.servicos import armazenamento, detector_pessoas, detector_rostos
from api.testes.teste_deteccao import RESPOSTA_PESSOAS, RESPOSTA_ROSTOS


class ClienteFalso:
    def __init__(self) -> None:
        self.gravados: list[str] = []

    def detect_labels(self, **kwargs):
        assert kwargs["Settings"]["GeneralLabels"]["LabelInclusionFilters"] == ["Person"]
        return RESPOSTA_PESSOAS

    def detect_faces(self, **kwargs):
        return RESPOSTA_ROSTOS

    def put_object(self, **kwargs):
        self.gravados.append(kwargs["Key"])
        return {}


@pytest.fixture
def ambiente(monkeypatch):
    falso = ClienteFalso()
    for modulo in (detector_pessoas, detector_rostos, armazenamento):
        monkeypatch.setattr(modulo, "cliente", lambda *a, **k: falso)
    monkeypatch.setenv("ARMAZENAMENTO_BUCKET", "bucket-de-teste")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "teste")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "teste")
    configuracao.obter_configuracao.cache_clear()
    from api.principal import aplicacao

    yield TestClient(aplicacao), falso
    configuracao.obter_configuracao.cache_clear()


def _png(largura=300, altura=231) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (largura, altura), (40, 40, 40)).save(buffer, format="PNG")
    return buffer.getvalue()


def teste_detectar_pessoas_sem_consentimento_grava_so_o_json(ambiente):
    cliente, falso = ambiente
    resposta = cliente.post("/detectar?modo=pessoas",
                            files={"imagem": ("foto.png", _png(), "image/png")})
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["total_detectado"] == 2
    assert corpo["total_acima_do_limiar"] == 1
    assert corpo["deteccoes"][0]["caixa"] == {"x": 0, "y": 41, "largura": 95, "altura": 189}
    assert corpo["imagem_persistida"] is False
    assert corpo["caminho_armazenamento"].startswith("s3://bucket-de-teste/deteccoes/")
    assert [k.rsplit("/", 1)[1] for k in falso.gravados] == ["resultado.json"]


def teste_detectar_rostos_com_consentimento_grava_imagem(ambiente):
    cliente, falso = ambiente
    resposta = cliente.post("/detectar?modo=rostos&consentimento=true",
                            files={"imagem": ("foto.png", _png(600, 300), "image/png")})
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["servico"] == "Amazon Rekognition · DetectFaces"
    assert corpo["imagem_persistida"] is True
    assert sorted(k.rsplit("/", 1)[1] for k in falso.gravados) == ["original.png", "resultado.json"]


def teste_saude_lista_os_dois_modos(ambiente):
    cliente, _ = ambiente
    corpo = cliente.get("/saude").json()
    assert corpo["modos_disponiveis"] == ["pessoas", "rostos"]
    assert corpo["armazenamento_configurado"] is True
