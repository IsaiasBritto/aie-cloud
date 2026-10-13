# Terraform — Aula 3

Provisiona a **camada de compute** da Quantum Commerce na AWS:

| Arquivo | O que define |
|---------|--------------|
| [main.tf](main.tf) | Providers, sufixo aleatório, tags padrão, LabRole, VPC e subnets padrão |
| [variables.tf](variables.tf) | `region`, `ecs_enabled` (para criar o ECS depois) e `image_tag` |
| [outputs.tf](outputs.tf) | `lambda_name`, `function_url`, `ecr_repository_url`, `bucket_name`, cluster/serviço ECS |
| [storage.tf](storage.tf) | Bucket S3 (prefixo `catalogo/`) + upload do `produtos.csv` |
| [lambda.tf](lambda.tf) | Lambda Python 3.12 + Function URL + LabRole como execution role + log group com retenção |
| [containers.tf](containers.tf) | ECR (com lifecycle) + cluster ECS + task definition + serviço Fargate (condicional) |

> **Independente da Aula 2:** esta aula cria o próprio bucket e sobe o CSV no apply.

## Como usar (AWS CloudShell, Learner Lab iniciado)

### Fase 1 — Tudo, menos o serviço ECS (~2 min)

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
export PATH="$HOME/bin:$PATH" TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
terraform init
terraform apply -auto-approve
terraform output
```

### Fase 2 — Depois do `docker push` da imagem (ver [docker/README.md](../docker/README.md))

```bash
terraform apply -auto-approve -var="ecs_enabled=true"
TASK_IP=$(bash ../scripts/task_ip.sh)
curl "http://$TASK_IP:8080/health"
```

### Encerramento

```bash
terraform destroy -auto-approve
```

Apaga Lambda, bucket, ECR (com as imagens) e o cluster ECS de uma vez.

## Decisões de projeto

- **LabRole em tudo:** o Learner Lab não deixa criar IAM roles. Em produção, cada componente teria a sua role, com só as permissões que usa.
- **Function URL sem API Gateway:** o caminho mais curto para HTTPS. Desde out/2025, uma URL pública exige duas permissões na política da função (`InvokeFunctionUrl` e `InvokeFunction` com a condição `InvokedViaFunctionUrl`); a segunda é criada via CLI no `terraform_data`.
- **`ignore_changes` no código da Lambda:** o Terraform publica a v1 só na criação; o deploy seguinte é do aluno (`update-function-code`), e um novo `apply` não desfaz.
- **Logs com retenção de 7 dias:** log group sem retenção guarda para sempre — e cobra.
