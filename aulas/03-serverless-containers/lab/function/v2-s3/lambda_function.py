"""
Lambda HTTP da Quantum Commerce — versão L₂.

Lê catalogo/produtos.csv do bucket S3 desta aula. SEM credenciais no código:
o boto3 usa a credencial temporária da execution role da função (no Learner
Lab, a LabRole), entregue pela própria Lambda em variáveis de ambiente.

Variáveis de ambiente (configuradas pelo Terraform):
    BUCKET_NAME — bucket do catálogo
    CSV_KEY     — chave do CSV (padrão: catalogo/produtos.csv)
"""
import csv
import json
import logging
import os

import boto3  # já vem no runtime Python da Lambda — não precisa empacotar

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET = os.environ["BUCKET_NAME"]
CSV_KEY = os.environ.get("CSV_KEY", "catalogo/produtos.csv")

# Cliente criado FORA do handler: reaproveitado entre invocações "quentes"
_s3 = boto3.client("s3")


def resposta(corpo: dict, status: int = 200) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(corpo, ensure_ascii=False),
    }


def carregar_produtos() -> list[dict]:
    """Baixa o CSV do S3 e converte em lista de dicts."""
    obj = _s3.get_object(Bucket=BUCKET, Key=CSV_KEY)
    rows = list(csv.DictReader(obj["Body"].read().decode("utf-8").splitlines()))
    for r in rows:
        r["id"] = int(r["id"])
        r["preco"] = float(r["preco"])
        r["estoque"] = int(r["estoque"])
    return rows


def listar_produtos(params: dict) -> dict:
    """GET /produtos?categoria=moveis&nome=cadeira"""
    logger.info("Endpoint /produtos chamado")
    try:
        produtos = carregar_produtos()
    except Exception as e:  # noqa: BLE001 — devolve o erro em JSON para o lab
        logger.exception("Falha ao carregar produtos do S3")
        return resposta({"erro": f"falha ao acessar o S3: {e!s}"}, 500)

    categoria = (params.get("categoria") or "").lower().strip()
    nome = (params.get("nome") or "").lower().strip()

    resultado = produtos
    if categoria:
        resultado = [p for p in resultado if p["categoria"].lower() == categoria]
    if nome:
        resultado = [p for p in resultado if nome in p["nome"].lower()]
    return resposta({"total": len(resultado), "produtos": resultado})


def lambda_handler(event, context):
    caminho = event.get("rawPath", "/")
    params = event.get("queryStringParameters") or {}

    if caminho == "/health":
        return resposta({"status": "ok", "service": "qc-catalogo", "source": "s3"})
    if caminho in ("/", "/produtos"):
        return listar_produtos(params)
    return resposta({"erro": f"rota {caminho} não existe", "rotas": ["/produtos", "/health"]}, 404)
