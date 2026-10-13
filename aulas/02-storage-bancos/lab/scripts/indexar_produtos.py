"""
Aula 2 / Lab 3B — Busca vetorial dos produtos da QC com pgvector no RDS PostgreSQL.

Passos:
1. Cria a extensão vector, a tabela produtos_vetor e um índice HNSW.
2. Baixa catalogo/produtos.csv do S3.
3. Gera embeddings (MiniLM multilíngue, 384 dimensões) AQUI no CloudShell
   e grava cada produto já com o seu vetor.
4. Demonstra: busca por palavra × busca por significado × filtro + vetor.

Por que os embeddings são gerados no CloudShell: o Learner Lab não libera o
Amazon Bedrock. Em produção, o mesmo papel seria de um modelo de embedding
no Bedrock (ou do Bedrock Knowledge Bases, que faz o RAG inteiro).

Variáveis de ambiente:
    SECRET_ID    — segredo com a connection string (terraform output -raw secret_id)
    BUCKET_NAME  — bucket com catalogo/produtos.csv (terraform output -raw bucket_name)
    (alternativa ao SECRET_ID: DB_HOST + DB_PASSWORD)

Dependências:
    pip install --user boto3 "psycopg[binary]" pgvector fastembed
"""

import csv
import os
import sys

import boto3
import psycopg
from fastembed import TextEmbedding
from pgvector.psycopg import register_vector

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIMENSOES = 384
# O $HOME do CloudShell tem só 1 GB: o modelo (~220 MB) fica no /tmp
CACHE_MODELO = os.environ.get("FASTEMBED_CACHE", "/tmp/fastembed")


def connection_string():
    if os.environ.get("SECRET_ID"):
        sm = boto3.client("secretsmanager")
        return sm.get_secret_value(SecretId=os.environ["SECRET_ID"])["SecretString"]
    host, senha = os.environ.get("DB_HOST"), os.environ.get("DB_PASSWORD")
    if host and senha:
        return f"postgresql://qcadmin:{senha}@{host}:5432/qcdb?sslmode=require"
    sys.exit("Exporte SECRET_ID (ou DB_HOST + DB_PASSWORD) — veja o guia.")


def main():
    bucket = os.environ.get("BUCKET_NAME") or sys.exit("Exporte BUCKET_NAME — veja o guia.")

    # 1. Produtos do S3
    print(f"→ Baixando s3://{bucket}/catalogo/produtos.csv...")
    corpo = boto3.client("s3").get_object(Bucket=bucket, Key="catalogo/produtos.csv")["Body"]
    rows = list(csv.DictReader(corpo.read().decode("utf-8").splitlines()))
    print(f"✓ {len(rows)} produtos lidos")

    # 2. Modelo de embedding (baixa na 1ª vez, ~1 min)
    print(f"→ Carregando o modelo {MODELO} (cache em {CACHE_MODELO})...")
    modelo = TextEmbedding(model_name=MODELO, cache_dir=CACHE_MODELO)
    textos = [f"{r['nome']}. {r['descricao']}. Categoria: {r['categoria']}" for r in rows]
    vetores = list(modelo.embed(textos))
    print(f"✓ {len(vetores)} embeddings gerados ({len(vetores[0])} dimensões)")

    with psycopg.connect(connection_string(), connect_timeout=15, autocommit=True) as conn:
        # 3. Extensão + tabela + índice HNSW (distância de cosseno)
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        conn.execute("DROP TABLE IF EXISTS produtos_vetor")
        conn.execute(
            f"""
            CREATE TABLE produtos_vetor (
                id         INTEGER PRIMARY KEY,
                nome       TEXT NOT NULL,
                descricao  TEXT,
                categoria  TEXT,
                preco      NUMERIC(10,2),
                estoque    INTEGER,
                embedding  vector({DIMENSOES})
            )
            """
        )
        conn.execute(
            "CREATE INDEX produtos_vetor_hnsw ON produtos_vetor "
            "USING hnsw (embedding vector_cosine_ops)"
        )
        print("✓ Tabela produtos_vetor + índice HNSW criados")

        # 4. Gravar cada produto JÁ com o seu vetor
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO produtos_vetor VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    (int(r["id"]), r["nome"], r["descricao"], r["categoria"],
                     float(r["preco"]), int(r["estoque"]), v)
                    for r, v in zip(rows, vetores)
                ],
            )
        print(f"✓ {len(rows)} produtos indexados")

        # 5. Demonstrações
        print("\n=== Busca por PALAVRA (ILIKE): 'trabalhar em pé' ===")
        achou = conn.execute(
            "SELECT nome FROM produtos_vetor WHERE descricao ILIKE %s OR nome ILIKE %s",
            ("%trabalhar em pé%", "%trabalhar em pé%"),
        ).fetchall()
        print("  (nenhum resultado — nenhuma descrição tem essa frase)" if not achou
              else "\n".join(f"  {n}" for (n,) in achou))

        consulta = "algo para trabalhar em pé"
        q = next(modelo.embed([consulta]))
        print(f"\n=== Busca por SIGNIFICADO (pgvector): '{consulta}' ===")
        for nome, desc, dist in conn.execute(
            "SELECT nome, descricao, embedding <=> %s AS distancia "
            "FROM produtos_vetor ORDER BY distancia LIMIT 3",
            (q,),
        ):
            print(f"  [similaridade {1 - dist:.2f}] {nome} — {desc[:60]}...")

        print("\n=== Filtro 'moveis' + significado 'conforto para as costas' ===")
        q2 = next(modelo.embed(["conforto para as costas"]))
        for nome, preco in conn.execute(
            "SELECT nome, preco FROM produtos_vetor WHERE categoria = %s "
            "ORDER BY embedding <=> %s LIMIT 3",
            ("moveis", q2),
        ):
            print(f"  R$ {preco:>8} - {nome}")

    print("\n✓ Pronto. Explore no psql: SELECT nome FROM produtos_vetor ORDER BY embedding <=> ... ")


if __name__ == "__main__":
    main()
