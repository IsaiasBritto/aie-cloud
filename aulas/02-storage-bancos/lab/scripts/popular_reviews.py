"""
Aula 2 / Lab 3A — Inserir 30 reviews fictícias da QC no Amazon DynamoDB.

Demonstra:
- Cliente boto3 autenticado pela LabRole do CloudShell (sem chave no código).
- Escrita em lote (batch_writer) numa tabela com chave de partição.
- Query por partição (produto_id) — a leitura barata do DynamoDB.

Variáveis de ambiente:
    DYNAMO_TABLE — nome da tabela (terraform output -raw dynamodb_table)

Dependências:
    pip install --user boto3
"""

import os
import random
import sys

import boto3
from boto3.dynamodb.conditions import Attr, Key

# Templates de reviews — variados por sentimento
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


def main():
    nome_tabela = os.environ.get("DYNAMO_TABLE")
    if not nome_tabela:
        print("Exporte DYNAMO_TABLE:  export DYNAMO_TABLE=$(terraform output -raw dynamodb_table)")
        sys.exit(1)

    tabela = boto3.resource("dynamodb").Table(nome_tabela)
    print(f"→ Inserindo 30 reviews em {nome_tabela}...")

    random.seed(42)
    with tabela.batch_writer() as batch:  # agrupa em lotes de 25 automaticamente
        for i in range(1, 31):
            produto_id = random.randint(1, 20)
            texto, score = random.choice(TEMPLATES)
            batch.put_item(
                Item={
                    "produto_id": produto_id,  # chave de partição (N)
                    "review_id": f"r-{i:03d}",  # chave de ordenação (S)
                    "score": score,
                    "texto": texto,
                    "cliente": f"cliente-{random.randint(100, 999)}",
                }
            )
    print("✓ 30 reviews inseridas")

    # Query: reviews positivas do produto 5 — lê UMA partição só
    print("\n=== Reviews 4+ do produto 5 ===")
    resp = tabela.query(
        KeyConditionExpression=Key("produto_id").eq(5),
        FilterExpression=Attr("score").gte(4),
    )
    for r in resp["Items"]:
        print(f"  [score {r['score']}] {r['texto']}")
    print(f"\n(capacidade consumida: a query leu só a partição produto_id=5 — {resp['ScannedCount']} itens)")


if __name__ == "__main__":
    main()
