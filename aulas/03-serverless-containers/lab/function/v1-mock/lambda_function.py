"""
Lambda HTTP da Quantum Commerce — versão L₁ (mock data).
Sem dependências externas, sem credenciais. Bom para validar que o deploy funciona.

Rotas (via Function URL):
    GET /                          → mesma coisa que /produtos
    GET /produtos?categoria=&nome= → lista filtrada
    GET /health                    → status

No L₂ plugamos no S3 do catálogo (versão em ../v2-s3/), com a LabRole como identidade.
"""
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Mock inicial — depois substituído pelo S3 na v2-s3/
PRODUTOS_MOCK = [
    {"id": 1, "nome": "Cadeira Ergonômica DXRacer", "categoria": "moveis",           "preco": 1499.90},
    {"id": 2, "nome": "Notebook Dell Inspiron 15",  "categoria": "eletronicos",      "preco": 4299.00},
    {"id": 3, "nome": "Cafeteira Nespresso Mini",   "categoria": "eletrodomesticos", "preco": 499.00},
    {"id": 4, "nome": "Tênis Nike Air Zoom Pegasus","categoria": "calcados",         "preco": 799.90},
    {"id": 5, "nome": "Smartphone Galaxy S24",      "categoria": "eletronicos",      "preco": 3999.00},
]


def resposta(corpo: dict, status: int = 200) -> dict:
    """Formato que a Function URL entende (o mesmo do API Gateway HTTP API v2)."""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(corpo, ensure_ascii=False),
    }


def listar_produtos(params: dict) -> dict:
    """GET /produtos?categoria=eletronicos&nome=galaxy"""
    logger.info("Endpoint /produtos chamado (mock)")
    categoria = (params.get("categoria") or "").lower().strip()
    nome = (params.get("nome") or "").lower().strip()

    resultado = PRODUTOS_MOCK
    if categoria:
        resultado = [p for p in resultado if p["categoria"] == categoria]
    if nome:
        resultado = [p for p in resultado if nome in p["nome"].lower()]
    return resposta({"total": len(resultado), "produtos": resultado})


def lambda_handler(event, context):
    caminho = event.get("rawPath", "/")
    params = event.get("queryStringParameters") or {}

    if caminho == "/health":
        return resposta({"status": "ok", "service": "qc-catalogo", "source": "mock"})
    if caminho in ("/", "/produtos"):
        return listar_produtos(params)
    return resposta({"erro": f"rota {caminho} não existe", "rotas": ["/produtos", "/health"]}, 404)
