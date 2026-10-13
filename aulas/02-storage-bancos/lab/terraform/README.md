# Terraform — Aula 2 (camada de dados da QC)

Provisiona, num único `apply`, a camada de dados da Quantum Commerce na AWS:

| Arquivo | Recurso |
|---------|---------|
| [main.tf](main.tf) | Providers (aws, random, http), sufixo aleatório, `default_tags`, VPC padrão e IP do CloudShell |
| [variables.tf](variables.tf) | `region`, `db_password` (obrigatória), senhas do MongoDB |
| [storage.tf](storage.tf) | Bucket S3 privado e criptografado + prefixos `catalogo/`, `imagens/`, `logs/` + lifecycle dos logs |
| [rds.tf](rds.tf) | RDS PostgreSQL 16 `db.t3.micro` (pgvector disponível) + security group só para o seu IP |
| [secrets.tf](secrets.tf) | Secrets Manager: connection string do PostgreSQL e credenciais do MongoDB |
| [dynamodb.tf](dynamodb.tf) | Tabela on-demand `reviews` (partição `produto_id`, ordenação `review_id`) |
| [mongo.tf](mongo.tf) + [mongo-user-data.sh.tftpl](mongo-user-data.sh.tftpl) | EC2 Amazon Linux 2023 com Docker: MongoDB 7.0 + Mongo Express 1.0.2 (imagens do ECR Public) |
| [outputs.tf](outputs.tf) | `bucket_name`, `secret_id`, `mongo_secret_id`, `dynamodb_table`, `db_endpoint`, `mongodb_public_ip`, `mongo_express_url` |

## Como usar (AWS CloudShell, Learner Lab iniciado)

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
export PATH="$HOME/bin:$PATH" TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"

export DB_PASSWORD=$(openssl rand -hex 16)   # RDS não aceita / @ " e espaço
terraform init
terraform apply -auto-approve -var="db_password=$DB_PASSWORD"

# ...labs...

terraform destroy -auto-approve -var="db_password=$DB_PASSWORD"
```

## Decisões de projeto

- **Acesso só do seu IP:** `data "http"` descobre o IP de saída do CloudShell e libera só ele no RDS (5432) e no MongoDB (27017). Se abrir um CloudShell novo e o IP mudar, rode `apply` de novo.
- **Sem segredo no código:** os scripts leem a connection string do Secrets Manager com a credencial da LabRole. `recovery_window_in_days = 0` deixa recriar o mesmo nome logo depois de um destroy.
- **Custo de lab:** RDS sem backup automático nem snapshot final, DynamoDB on-demand, bucket com `force_destroy`. O RDS é o item mais caro — não esqueça o destroy.
- **Learner Lab:** nada de IAM role nova; nada de região fora de `us-east-1`/`us-west-2`.
- **Imagens do Mongo:** `public.ecr.aws/docker/library/*` é o espelho oficial das imagens do Docker Hub, sem limite de pull anônimo.
