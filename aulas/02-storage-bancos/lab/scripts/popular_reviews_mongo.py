"""
Aula 2 / Lab 3C (alternativa) — Inserir 30 reviews fictícias da QC no MongoDB (EC2).

Alternativa ao popular_reviews.py (DynamoDB). Mesma estrutura de dados e mesmo
random seed — facilita comparar os dois bancos NoSQL lado a lado.

A senha do MongoDB vem do Secrets Manager (nada de senha no código).

Variáveis de ambiente:
    MONGO_IP         — IP público da EC2 (terraform output -raw mongodb_public_ip)
    MONGO_SECRET_ID  — segredo do Mongo (terraform output -raw mongo_secret_id)
                       Se ausente, é derivado do SECRET_ID (troca /postgres por /mongo).

Dependências:
    pip install --user boto3 pymongo
"""

import json
import os
import random
import sys
import time
from urllib.parse import quote_plus

import boto3
from pymongo import MongoClient, errors

MONGO_IP = os.environ.get("MONGO_IP")
if not MONGO_IP:
    print("Exporte MONGO_IP com o IP da EC2:")
    print("  export MONGO_IP=$(terraform output -raw mongodb_public_ip)")
    sys.exit(1)

secret_id = os.environ.get("MONGO_SECRET_ID") or os.environ.get("SECRET_ID", "").replace("/postgres", "/mongo")
if not secret_id:
    print("Exporte MONGO_SECRET_ID (ou SECRET_ID):")
    print("  export MONGO_SECRET_ID=$(terraform output -raw mongo_secret_id)")
    sys.exit(1)

# Mesmo TEMPLATES e random.seed do popular_reviews.py — dados idênticos nos dois bancos.
TEMPLATES = [
    ("Adorei! Chegou rápido e funcionou perfeitamente.", 5),
    ("Produto excelente, recomendo demais.", 5),
    ("Cumpre o que promete, vale a pena pelo preço.", 4),
    ("Bom produto, mas a embalagem chegou amassada.", 4),
    ("Funciona ok, nada de especial.", 3),
    ("Esperava mais pelo valor pago.", 2),
    ("Decepcionante, não recomendo.", 1),
    ("Veio com defeito, tive que trocar.", 1),
    ("Maravilhoso, superou expectativas!", 5),
    ("Compraria de novo, ótimo custo-benefício.", 5),
]

# 1. Ler credenciais do Secrets Manager (LabRole do CloudShell)
print(f"→ Lendo credenciais de {secret_id}...")
cred = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=secret_id)["SecretString"])
URI = (
    f"mongodb://{quote_plus(cred['username'])}:{quote_plus(cred['password'])}"
    f"@{MONGO_IP}:27017/?authSource=admin"
)
print("✓ Credenciais obtidas (não vamos imprimi-las)")

# 2. Conectar — a EC2 leva ~2 min para baixar as imagens no primeiro boot
print(f"Conectando ao MongoDB em {MONGO_IP}:27017...")
for tentativa in range(12):
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✓ MongoDB pronto!")
        break
    except errors.ServerSelectionTimeoutError:
        print(f"  Aguardando MongoDB... (tentativa {tentativa + 1}/12)")
        time.sleep(10)
else:
    print("✗ MongoDB não respondeu após 2 min. Confira a EC2 e o security group (seu IP mudou?).")
    sys.exit(1)

db = client["qc-db"]
col = db["reviews"]

# Limpar reviews existentes (idempotente)
col.delete_many({})

print(f"→ Inserindo 30 reviews em {MONGO_IP}/qc-db.reviews...")

random.seed(42)
docs = []
for i in range(1, 31):
    produto_id = random.randint(1, 20)
    texto, score = random.choice(TEMPLATES)
    docs.append(
        {
            "review_id": f"r-{i:03d}",
            "produto_id": produto_id,
            "score": score,
            "texto": texto,
            "cliente": f"cliente-{random.randint(100, 999)}",
        }
    )

result = col.insert_many(docs)
print(f"✓ {len(result.inserted_ids)} reviews inseridas")

# Query: reviews positivas do produto 5 (mesma query do popular_reviews.py)
print("\n=== Reviews 4+ do produto 5 ===")
for r in col.find({"produto_id": 5, "score": {"$gte": 4}}, {"_id": 0}):
    print(f"  [score {r['score']}] {r['texto']}")

print(f"\nExplore visualmente: http://{MONGO_IP}:8081  (usuário qcadmin)")

client.close()
