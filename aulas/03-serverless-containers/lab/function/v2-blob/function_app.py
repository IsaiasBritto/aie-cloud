"""
Function HTTP da Quantum Commerce — versão L₂.

Lê produtos.csv do Blob Storage do catálogo (criado nesta aula) via Managed Identity.
SEM credenciais no código — autenticação via DefaultAzureCredential que detecta
a Managed Identity SystemAssigned do Function App em runtime.

Variável de ambiente esperada (configurada pelo Terraform):
    STORAGE_ACCOUNT_CATALOGO — nome do Storage Account com o container 'catalogo'
"""
import csv
import json
import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

STORAGE_ACCOUNT = os.environ["STORAGE_ACCOUNT_CATALOGO"]
CONTAINER       = "catalogo"
BLOB_NAME       = "produtos.csv"

_credential = DefaultAzureCredential()
_blob_service = BlobServiceClient(
    f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=_credential,
)

@app.route(route="fretes", methods=["POST"])
def calcular_frete(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/fretes"""
    logging.info("Endpoint /fretes chamado")

    body = req.get_json()

    cep_origem = body.get("cep_origem")
    cep_destino = body.get("cep_destino")
    peso_kg = body.get("peso_kg")

    # Tem que fazer o codigo do calculo do frete

    try:
        if not cep_origem or not cep_destino or peso_kg is None:
            return func.HttpResponse(
                json.dumps({
                    "erro": "cep_origem, cep_destino e peso_kg são obrigatórios"
                }),
                mimetype="application/json",
                status_code=400
            )

        peso_kg = float(peso_kg)

        if peso_kg <= 0:
            return func.HttpResponse(
                json.dumps({
                    "erro": "peso_kg deve ser maior que zero"
                }),
                mimetype="application/json",
                status_code=400
            )

        resposta = {
                "cep_origem": cep_origem,
                "cep_destino": cep_destino,
                "peso_kg": peso_kg,
                "distancia_estimada_km": 0.0,
                "valor_frete": 0.0,
                "tempo_estimado_entrega_dias": 0
            }

        return func.HttpResponse(
                    json.dumps(resposta, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=200
        )
    
    except Exception as e:
        logging.exception("Falha ao calcular frete")
        return func.HttpResponse(
            json.dumps({"erro": f"falha ao acessar storage: {e!s}"}),
            mimetype="application/json",
            status_code=500,
        )

    



def carregar_produtos() -> list[dict]:
    """Baixa produtos.csv do Blob e converte em lista de dicts."""
    blob_client = _blob_service.get_blob_client(container=CONTAINER, blob=BLOB_NAME)
    csv_content = blob_client.download_blob().readall().decode("utf-8")
    rows = list(csv.DictReader(csv_content.splitlines()))
    for r in rows:
        r["id"]      = int(r["id"])
        r["preco"]   = float(r["preco"])
        r["estoque"] = int(r["estoque"])
    return rows


@app.route(route="produtos", methods=["GET"])
def listar_produtos(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/produtos?categoria=moveis&nome=cadeira"""
    logging.info("Endpoint /produtos chamado")

    try:
        produtos = carregar_produtos()
    except Exception as e:
        logging.exception("Falha ao carregar produtos do Blob")
        return func.HttpResponse(
            json.dumps({"erro": f"falha ao acessar storage: {e!s}"}),
            mimetype="application/json",
            status_code=500,
        )

    categoria = (req.params.get("categoria") or "").lower().strip()
    nome      = (req.params.get("nome")      or "").lower().strip()

    resultado = produtos
    if categoria:
        resultado = [p for p in resultado if p["categoria"].lower() == categoria]
    if nome:
        resultado = [p for p in resultado if nome in p["nome"].lower()]

    return func.HttpResponse(
        json.dumps({"total": len(resultado), "produtos": resultado}, ensure_ascii=False),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "service": "qc-catalogo", "source": "blob"}),
        mimetype="application/json",
    )
