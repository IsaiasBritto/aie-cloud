# Guia de Laboratório — Aula 2

**Tema:** Storage & Bancos de Dados na Nuvem
**Plataforma:** Amazon Web Services (AWS Academy Learner Lab)
**Ambiente:** **AWS CloudShell** — tudo no browser, sem instalar nada localmente
**Região:** `us-east-1`

---

## Visão geral do lab

```
Preparação — terraform apply de TODA a camada de dados            ~10 min
Atividade 1 — Bucket S3 + upload do CSV do catálogo                ~15 min  (L₁)
Atividade 2 — RDS PostgreSQL + Secrets Manager + Python            ~30 min  (L₂)
Atividade 3 — DynamoDB / MongoDB + busca vetorial (pgvector)       ~55 min  (L₃)
Wrap-up     — terraform destroy + verificação de custo             ~10 min
```

> **Regra de ouro:** sempre encerrar com `terraform destroy`.

### Por que `terraform apply` de uma vez só, antes das atividades?

A camada de dados da QC é uma **declaração única** — provisionar tudo de uma vez (~8 min, o RDS é o mais lento) reflete como IaC funciona na vida real. Enquanto o Terraform roda, você lê os arquivos `.tf` para entender o que está sendo construído.

---

## Pré-requisitos

- ✅ Aula 1 concluída (Learner Lab iniciado, CloudShell funcionando, Terraform instalado no `$HOME`)
- ✅ Esboço da arquitetura QC do grupo no repositório privado

---

## Preparação (15 min — antes do L₁)

### Passo 1 — Clone (ou atualize) o repositório e instale o Terraform

```bash
# Se já tinha clonado, apague e clone de novo (garante a versão da aula)
cd ~ && rm -rf aie-cloud
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/02-storage-bancos/lab/terraform

# Terraform no $HOME (só se ainda não instalou na Aula 1)
bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
export PATH="$HOME/bin:$PATH" TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"

# Pré-voo: a sessão tem acesso a S3, RDS, DynamoDB, Secrets Manager e EC2?
bash ../check_regions.sh
```

### Passo 2 — Provisione

```bash
# Senha do RDS — fica só na memória deste terminal (o RDS não aceita / @ " e espaço)
export DB_PASSWORD=$(openssl rand -hex 16)

terraform init
terraform apply -auto-approve -var="db_password=$DB_PASSWORD"
```

Enquanto o Terraform trabalha (~8 min), leia os arquivos:

| Arquivo | O que define |
|---------|--------------|
| [main.tf](terraform/main.tf) | Providers, sufixo aleatório, tags padrão, VPC padrão e o IP do CloudShell |
| [variables.tf](terraform/variables.tf) | `region`, `db_password` e as senhas do MongoDB |
| [outputs.tf](terraform/outputs.tf) | Nomes e endpoints consumidos pelos scripts Python |
| [storage.tf](terraform/storage.tf) | Bucket S3 + 3 prefixos (`catalogo/`, `imagens/`, `logs/`) + lifecycle |
| [rds.tf](terraform/rds.tf) | RDS PostgreSQL 16 `db.t3.micro` + security group (só o seu IP) |
| [secrets.tf](terraform/secrets.tf) | Secrets Manager: connection string do PostgreSQL e credenciais do Mongo |
| [dynamodb.tf](terraform/dynamodb.tf) | Tabela DynamoDB on-demand (`produto_id` + `review_id`) |
| [mongo.tf](terraform/mongo.tf) | EC2 com Docker: MongoDB 7.0 + Mongo Express (Lab 3C) |

### Passo 3 — Exporte os outputs

```bash
# Armazena em variáveis valores criados pelo terraform
export BUCKET_NAME=$(terraform output -raw bucket_name)
export SECRET_ID=$(terraform output -raw secret_id)
export MONGO_SECRET_ID=$(terraform output -raw mongo_secret_id)
export DYNAMO_TABLE=$(terraform output -raw dynamodb_table)
export DB_HOST=$(terraform output -raw db_endpoint)
export MONGO_IP=$(terraform output -raw mongodb_public_ip)

# Exibe em tela
echo "Bucket: $BUCKET_NAME"
echo "Secret: $SECRET_ID"
echo "DynamoDB: $DYNAMO_TABLE"
echo "RDS: $DB_HOST"
echo "MongoDB: $MONGO_IP:27017  |  Mongo Express: $(terraform output -raw mongo_express_url)"
```

### Se a sessão do CloudShell cair

As variáveis somem, mas o estado do Terraform fica no `$HOME`. Volte para a pasta, rode o Passo 3 de novo e, se o IP do CloudShell mudou (`terraform output meu_ip` × `curl -s https://checkip.amazonaws.com`), rode `terraform apply -var="db_password=..."` com **a mesma senha** para liberar o novo IP.

> Perdeu a senha? Ela está no segredo: `aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --query SecretString --output text`.

---

## Atividade 1 — Bucket S3 + upload do CSV (L₁)

### Passo 1 — Conferir o que foi provisionado

No console: **S3** → bucket `qc-aula02-xxxxxx` → prefixos `catalogo/`, `imagens/`, `logs/`. Aba **Management**: a regra `logs-lifecycle` (Standard → Standard-IA em 30 dias → Glacier em 90 → expira em 365).

### Passo 2 — Upload do CSV de produtos

```bash
# 1. Localize e explore o arquivo
ls ~/aie-cloud/aulas/02-storage-bancos/lab/data/
head -5 ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv

# 2. Confira a identidade (no Learner Lab, a LabRole já acessa o S3)
aws sts get-caller-identity

# 3. Upload para o prefixo catalogo/
aws s3 cp ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv \
  s3://$BUCKET_NAME/catalogo/produtos.csv

# 4. Confirme
aws s3 ls s3://$BUCKET_NAME/catalogo/
```

> **Para discutir:** quem autorizou o upload? A **LabRole** da sua sessão, via política IAM. Não existe "chave do bucket" que dê acesso total a quem a tiver — a permissão é sempre de uma identidade, e o CloudTrail registra qual identidade fez o quê.

**✅ Checkpoint L₁:** `produtos.csv` aparece em `catalogo/`?

---

## Atividade 2 — RDS PostgreSQL + Secrets Manager + Python (L₂)

### Passo 1 — Conferir o que foi provisionado

- **RDS** → Databases → `qc-aula02-xxxxxx` (PostgreSQL 16, `db.t3.micro`). Aba **Connectivity & security**: o security group só aceita a porta 5432 do IP do seu CloudShell.
- **Secrets Manager** → `qc-aula02-xxxxxx/postgres`. Clique em **Retrieve secret value** só para ver o formato — o script nunca imprime isso.

### Passo 2 — Rodar o script

O [`popular_produtos.py`](scripts/popular_produtos.py): lê a connection string do Secrets Manager → baixa o CSV do S3 → conecta no RDS via `psycopg` → cria `t_produtos` (drop se existir) → insere os 20 produtos.

```bash
# OPCIONAL: se perdeu a sessão e as variáveis
# export SECRET_ID=...   export BUCKET_NAME=...

pip install --user boto3 "psycopg[binary]"
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 popular_produtos.py
```

Saída esperada: `✓ 20 produtos inseridos` e o top 3 mais caros.

> **Erro comum — `connection timeout`:** o IP do CloudShell mudou desde o apply. Rode `terraform apply -var="db_password=$DB_PASSWORD"` de novo e repita.

### Passo 3 — Consultar pelo psql (opcional)

```bash
sudo dnf install -y postgresql16 >/dev/null 2>&1 || sudo dnf install -y postgresql15
psql "$(aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --query SecretString --output text)" \
  -c "SELECT categoria, COUNT(*), ROUND(AVG(preco),2) FROM t_produtos GROUP BY categoria;"
```

**✅ Checkpoint L₂:** você inseriu 20 produtos no RDS **lendo o segredo do Secrets Manager**?

### Passo 4 — Discussão (3 min)

1. O que aconteceria se a `conn_str` viesse hardcoded no `popular_produtos.py` e o arquivo fosse commitado num repo público?
2. Como você protegeria esse segredo se ele fosse usado por um agente rodando numa AWS Lambda? *(dica: a função lê o segredo em runtime com a execution role — e o Secrets Manager pode rotacionar a senha sozinho)*
3. Por que o `boto3` "simplesmente funciona" no CloudShell, sem chave? De onde vem a credencial? E no seu notebook?

---

## Atividade 3 — DynamoDB / MongoDB + busca vetorial (L₃)

### Parte A — DynamoDB (20 min)

**Conferir:** console **DynamoDB** → Tables → `qc-aula02-xxxxxx-reviews` → chave de partição `produto_id` (Number) e de ordenação `review_id` (String). Capacidade **On-demand**.

O [`popular_reviews.py`](scripts/popular_reviews.py) insere 30 reviews com `batch_writer` e faz uma **Query** na partição `produto_id = 5` filtrando `score >= 4`.

```bash
# OPCIONAL: export DYNAMO_TABLE=...
pip install --user boto3
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 popular_reviews.py
```

**Explorar no console:** a tabela → **Explore table items** → **Query** com `produto_id = 5`. Compare com **Scan**: a Query lê uma partição; o Scan lê a tabela inteira (e cobra por isso).

### Parte B — Busca vetorial com pgvector (25 min)

O mesmo RDS da Atividade 2 vira um Vector DB com a extensão **pgvector**. O [`indexar_produtos.py`](scripts/indexar_produtos.py):

1. Cria a extensão `vector`, a tabela `produtos_vetor` e um índice **HNSW**
2. Baixa o CSV do S3
3. Gera os embeddings (MiniLM multilíngue, 384 dimensões) **aqui no CloudShell** e grava cada produto já com o seu vetor
4. Demonstra busca por palavra × busca por significado × filtro + vetor

```bash
# OPCIONAL: export SECRET_ID=...  export BUCKET_NAME=...  (ou DB_HOST + DB_PASSWORD)
pip install --user boto3 "psycopg[binary]" pgvector fastembed
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 indexar_produtos.py
```

Na primeira execução o modelo (~220 MB) é baixado para o `/tmp` (o `$HOME` do CloudShell tem só 1 GB).

> **Por que embedding local e não um serviço?** O Learner Lab não libera o Amazon Bedrock. Em produção, o modelo de embedding seria do Bedrock (Titan/Cohere) — ou o **Bedrock Knowledge Bases** faria chunking, embeddings e índice de uma vez.

**Busca no psql (opcional):**

```bash
psql "$(aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --query SecretString --output text)" \
  -c "SELECT a.nome, b.nome AS parecido, ROUND((1 - (a.embedding <=> b.embedding))::numeric, 2) AS similaridade
      FROM produtos_vetor a JOIN produtos_vetor b ON a.id <> b.id
      WHERE a.id = 1 ORDER BY a.embedding <=> b.embedding LIMIT 3;"
```

### Parte C — MongoDB na EC2 (alternativa ao DynamoDB)

A EC2 `qc-aula02-xxxxxx-mongo` sobe o MongoDB 7.0 e o Mongo Express em Docker (~2 min após o apply).

```bash
# OPCIONAL: export MONGO_IP=...  export MONGO_SECRET_ID=...
pip install --user boto3 pymongo
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 popular_reviews_mongo.py
```

O script lê usuário e senha do **Secrets Manager** — o mesmo padrão do RDS.

**Explorar no Mongo Express:** abra `$(terraform output -raw mongo_express_url)` no navegador (usuário `qcadmin`, senha `QCview2024!`) → `qc-db` → `reviews`.

> **Para discutir:** a porta 27017 só aceita o IP do CloudShell, mas a 8081 está aberta para a internet (com senha). Por que essa diferença? O que mudaria em produção?

**✅ Checkpoint L₃:** reviews no DynamoDB (e/ou no Mongo) e a busca "algo para trabalhar em pé" trouxe a mesa de escritório sem nenhuma palavra em comum?

---

## Wrap-up — Destroy e custo zero (10 min)

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
terraform destroy -auto-approve -var="db_password=$DB_PASSWORD"
```

O destroy apaga bucket (mesmo com objetos — `force_destroy`), RDS (sem snapshot final), segredos (sem janela de recuperação), tabela DynamoDB e a EC2 do Mongo. Leva ~5 min por causa do RDS.

**Conferir:** página do Learner Lab → crédito consumido. **RDS esquecido ligado é o recurso mais caro desta aula.**

---

## Conexão com o projeto Quantum Commerce

```
infrastructure/
  ├── main.tf, variables.tf, outputs.tf
  ├── storage.tf    (S3: catálogo, imagens, logs + lifecycle)
  ├── rds.tf        (t_produtos — transacional; produtos_vetor — pgvector)
  ├── secrets.tf    (Secrets Manager)
  ├── dynamodb.tf   (reviews — NoSQL)
  └── mongo.tf      (reviews — MongoDB na EC2, alternativa)
```

- **Aula 3** — a Lambda lê o catálogo do S3
- **Aula 4** — serviços de IA analisam reviews e imagens do bucket
- **Aula 5** — agentes usam o catálogo e a busca vetorial como ferramentas

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| `ExpiredToken` / `InvalidClientTokenId` | Sessão do Learner Lab acabou | **Start Lab** de novo e abra um CloudShell novo |
| `InvalidParameterValue: The parameter MasterUserPassword...` | Senha com `/ @ "` ou espaço | `export DB_PASSWORD=$(openssl rand -hex 16)` |
| Python: `connection timeout` no RDS ou no Mongo | IP do CloudShell mudou | `terraform apply -var="db_password=$DB_PASSWORD"` de novo |
| `AccessDenied` ao criar recurso | Serviço/tipo fora do que o Learner Lab libera | Confira `bash ../check_regions.sh`; use `us-east-1` |
| `NoSuchKey` no script | O upload da Atividade 1 não aconteceu | Refaça o `aws s3 cp` e confira com `aws s3 ls` |
| `ResourceNotFoundException` no Secrets Manager | `SECRET_ID` vazio ou de outro apply | `export SECRET_ID=$(terraform output -raw secret_id)` |
| `extension "vector" is not available` | Versão do PostgreSQL sem pgvector | O lab usa PostgreSQL 16 (com pgvector). Confira `engine_version` em `rds.tf` |
| `No space left on device` no CloudShell | `$HOME` de 1 GB cheio (providers, pip) | `du -sh ~/.local ~/.terraform.d ~/aie-cloud/*/*/lab/terraform/.terraform`; use o `TF_PLUGIN_CACHE_DIR` e apague `.terraform` de labs antigos |
| MongoDB: `ServerSelectionTimeoutError` | EC2 ainda subindo os containers | Aguarde 2 min e rode de novo. Log: EC2 → Actions → Monitor → Get system log |
| Mongo Express pede senha | Basic auth ligado de propósito | Usuário `qcadmin`, senha `QCview2024!` |
| `BucketAlreadyExists` | Nome global de bucket | O sufixo aleatório evita; rode `terraform apply` de novo |

---

## Tarefa pós-aula

1. Atualizar o diagrama da arquitetura QC (camada de dados detalhada)
2. Responder as 3 perguntas da L₂ (Secrets Manager)
3. Resolver pelo menos o Nível 1 de [exercicios.md](../exercicios.md)

---

## Referências

- [Amazon S3 — Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Amazon RDS for PostgreSQL — extensões (pgvector)](https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-extensions.html)
- [pgvector](https://github.com/pgvector/pgvector)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [Amazon DynamoDB — boas práticas de chave de partição](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html)
- [Credenciais do boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
