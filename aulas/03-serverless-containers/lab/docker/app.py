"""
Versão FastAPI da API de produtos QC — mesmo comportamento da Lambda v2-s3.

Empacotada num container Docker para rodar no Amazon ECS (Fargate). A credencial
vem da task role da tarefa (no Learner Lab, a LabRole): o boto3 a encontra
sozinho pelo endpoint de credenciais do ECS — nada de chave no código.
"""
import csv
import os

import boto3
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Quantum Commerce — Catálogo API", version="1.0")

BUCKET = os.environ["BUCKET_NAME"]
CSV_KEY = os.environ.get("CSV_KEY", "catalogo/produtos.csv")

_s3 = boto3.client("s3")


def carregar_produtos() -> list[dict]:
    obj = _s3.get_object(Bucket=BUCKET, Key=CSV_KEY)
    rows = list(csv.DictReader(obj["Body"].read().decode("utf-8").splitlines()))
    for r in rows:
        r["id"] = int(r["id"])
        r["preco"] = float(r["preco"])
        r["estoque"] = int(r["estoque"])
    return rows


@app.get("/health")
def health():
    return {"status": "ok", "service": "qc-catalogo", "source": "s3", "runtime": "container"}


@app.get("/produtos")
def listar_produtos(categoria: str | None = None, nome: str | None = None):
    try:
        produtos = carregar_produtos()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"falha ao acessar o S3: {e!s}") from e

    cat = (categoria or "").lower().strip()
    nm = (nome or "").lower().strip()

    resultado = produtos
    if cat:
        resultado = [p for p in resultado if p["categoria"].lower() == cat]
    if nm:
        resultado = [p for p in resultado if nm in p["nome"].lower()]

    return {"total": len(resultado), "produtos": resultado}
