"""
Aula 2 / Lab 2 — Popular a tabela t_produtos no Amazon RDS for PostgreSQL.

O script demonstra como NÃO hardcodar segredos:
1. Lê a connection string do AWS Secrets Manager (não do código).
2. Lê os produtos de um CSV no S3 (prefixo catalogo/).
3. Cria a tabela t_produtos no RDS e insere os 20 produtos.

Autenticação: boto3 usa a credencial do CloudShell (LabRole) — nenhuma chave no código.

Variáveis de ambiente:
    SECRET_ID    — nome do segredo (terraform output -raw secret_id)
    BUCKET_NAME  — bucket com catalogo/produtos.csv (terraform output -raw bucket_name)

Dependências:
    pip install --user boto3 "psycopg[binary]"
"""

import csv
import os
import sys

import boto3
import psycopg


def main():
    secret_id = os.environ["SECRET_ID"]
    bucket = os.environ["BUCKET_NAME"]

    sm = boto3.client("secretsmanager")  # usa a LabRole do CloudShell
    s3 = boto3.client("s3")

    # 1. Ler connection string do Secrets Manager
    print(f"→ Lendo connection string de {secret_id}...")
    secret = sm.get_secret_value(SecretId=secret_id)
    conn_str = secret["SecretString"]
    print("✓ Connection string obtida (não vamos imprimi-la)")

    # 2. Baixar CSV do S3
    print(f"→ Baixando s3://{bucket}/catalogo/produtos.csv...")
    obj = s3.get_object(Bucket=bucket, Key="catalogo/produtos.csv")
    csv_content = obj["Body"].read().decode("utf-8")
    rows = list(csv.DictReader(csv_content.splitlines()))
    print(f"✓ {len(rows)} produtos lidos do S3")

    # 3. Conectar no RDS via psycopg (TLS exigido pelo sslmode=require do segredo)
    print("→ Conectando no RDS PostgreSQL...")
    with psycopg.connect(conn_str, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            # 4. Criar tabela (drop se existir, para idempotência do lab)
            cur.execute("DROP TABLE IF EXISTS t_produtos")
            cur.execute(
                """
                CREATE TABLE t_produtos (
                    id          INTEGER PRIMARY KEY,
                    nome        VARCHAR(200) NOT NULL,
                    descricao   VARCHAR(1000),
                    categoria   VARCHAR(100),
                    preco       NUMERIC(10,2),
                    estoque     INTEGER
                )
                """
            )
            print("✓ Tabela t_produtos criada")

            # 5. Inserir produtos (parâmetros %s — nunca concatene SQL)
            cur.executemany(
                "INSERT INTO t_produtos VALUES (%s, %s, %s, %s, %s, %s)",
                [
                    (
                        int(r["id"]),
                        r["nome"],
                        r["descricao"],
                        r["categoria"],
                        float(r["preco"]),
                        int(r["estoque"]),
                    )
                    for r in rows
                ],
            )
            conn.commit()
            print(f"✓ {len(rows)} produtos inseridos")

            # 6. Verificar
            cur.execute("SELECT COUNT(*) FROM t_produtos")
            total = cur.fetchone()[0]
            cur.execute("SELECT id, nome, preco FROM t_produtos ORDER BY preco DESC LIMIT 3")
            top = cur.fetchall()

    print("\n=== Resultado ===")
    print(f"Total de produtos: {total}")
    print("Top 3 mais caros:")
    for pid, nome, preco in top:
        print(f"  #{pid} - {nome} - R$ {preco}")


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"\n✗ Variável de ambiente ausente: {e}. Veja o guia (export ...).", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
