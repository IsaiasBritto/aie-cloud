# Scripts Python — Aula 2

Scripts que populam e exploram as bases provisionadas pelo Terraform da Aula 2. Todos usam o **boto3**, que no CloudShell autentica sozinho com a credencial da sessão do Learner Lab (LabRole) — nenhuma chave no código.

| Script | Atividade | O que faz |
|--------|-----------|-----------|
| [popular_produtos.py](popular_produtos.py) | L₂ | Lê a connection string do Secrets Manager e o CSV do S3; cria e popula `t_produtos` no RDS PostgreSQL |
| [popular_reviews.py](popular_reviews.py) | L₃-A | Insere 30 reviews fictícias no DynamoDB e faz Query na partição `produto_id = 5` |
| [indexar_produtos.py](indexar_produtos.py) | L₃-B | Gera embeddings (MiniLM, 384 dims) e cria a busca vetorial com pgvector no RDS |
| [popular_reviews_mongo.py](popular_reviews_mongo.py) | L₃-C | Mesmas 30 reviews no MongoDB da EC2, com a senha lida do Secrets Manager |

## Dependências

```bash
pip install --user -r requirements.txt
# ou só o que cada atividade pede (ver guia)
```

## Variáveis de ambiente

| Script | Variáveis |
|--------|-----------|
| `popular_produtos.py` | `SECRET_ID`, `BUCKET_NAME` |
| `popular_reviews.py` | `DYNAMO_TABLE` |
| `indexar_produtos.py` | `SECRET_ID` (ou `DB_HOST` + `DB_PASSWORD`), `BUCKET_NAME` |
| `popular_reviews_mongo.py` | `MONGO_IP`, `MONGO_SECRET_ID` (ou `SECRET_ID`) |

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
export BUCKET_NAME=$(terraform output -raw bucket_name)
export SECRET_ID=$(terraform output -raw secret_id)
export MONGO_SECRET_ID=$(terraform output -raw mongo_secret_id)
export DYNAMO_TABLE=$(terraform output -raw dynamodb_table)
export DB_HOST=$(terraform output -raw db_endpoint)
export MONGO_IP=$(terraform output -raw mongodb_public_ip)
```

## Como executar

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 popular_produtos.py
python3 popular_reviews.py
python3 indexar_produtos.py
python3 popular_reviews_mongo.py
```

> **Lição de segurança:** a credencial nunca aparece no código. No CloudShell ela vem da sessão; numa Lambda ou tarefa ECS, da execution/task role; no seu notebook, do `aws configure` ou de SSO. O código é o mesmo nos três lugares.
