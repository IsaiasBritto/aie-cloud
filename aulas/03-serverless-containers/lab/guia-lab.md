# Guia de Laboratório — Aula 3

**Tema:** Serverless & Containers
**Plataforma:** Amazon Web Services (AWS Academy Learner Lab)
**Ambiente:** **AWS CloudShell** — tudo no browser, sem instalar nada
**Região:** `us-east-1`

---

## Visão geral do lab

```
Atividade 1 — Lambda HTTP via Terraform + deploy da v1-mock          ~30 min  (L₁)
Atividade 2 — Lambda lendo o S3 com a execution role (v2-s3)         ~45 min  (L₂)
Atividade 3 — Mesmo código em container: build, ECR e ECS Fargate   ~50 min  (L₃)
Wrap-up    — terraform destroy + verificação de custo                ~10 min
```

> **Regra de ouro:** sempre encerrar com `terraform destroy`.

---

## Pré-requisitos

- ✅ Aula 1 concluída (Learner Lab, CloudShell, Terraform no `$HOME`)

> **Aula independente:** esta aula **não depende da Aula 2**. O Terraform cria o próprio bucket e já sobe o `produtos.csv` no `apply` (de [lab/data/produtos.csv](data/produtos.csv)).

---

## Preparação (5 min)

```bash
# Repositório atualizado
cd ~ && rm -rf aie-cloud
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/03-serverless-containers/lab/terraform

# Terraform no $HOME (só se ainda não instalou)
bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
export PATH="$HOME/bin:$PATH" TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"

# Ferramentas
aws sts get-caller-identity --query Arn --output text
terraform -version
docker --version
```

---

## Atividade 1 — Lambda HTTP via Terraform + deploy (L₁)

### Passo 1 — Fase 1 do Terraform

```bash
terraform init
terraform apply -auto-approve      # ecs_enabled=false (padrão) → o serviço ECS ainda não nasce
terraform output
```

Enquanto o Terraform trabalha, leia os arquivos:

| Arquivo | O que define |
|---------|--------------|
| [main.tf](terraform/main.tf) | Providers, sufixo aleatório, tags padrão, locals, LabRole |
| [variables.tf](terraform/variables.tf) | `region` e `ecs_enabled` (para criar o ECS depois) |
| [outputs.tf](terraform/outputs.tf) | Nomes e endpoints consumidos pelos comandos |
| [storage.tf](terraform/storage.tf) | Bucket S3 (prefixo `catalogo/`) + upload do `produtos.csv` |
| [lambda.tf](terraform/lambda.tf) | Lambda Python 3.12 + Function URL + LabRole como execution role |
| [containers.tf](terraform/containers.tf) | ECR + cluster ECS + tarefa Fargate (count condicional) |

### Passo 2 — Deploy da versão mock (v1)

```bash
# Pegar o nome da função Lambda
FUNC_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw lambda_name)
echo "Lambda: $FUNC_NAME"

# Deploy da v1 (mock): empacota em zip e publica
cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v1-mock
zip -qr /tmp/v1-mock.zip . && aws lambda update-function-code --function-name "$FUNC_NAME" --zip-file fileb:///tmp/v1-mock.zip
aws lambda wait function-updated --function-name "$FUNC_NAME"
```

### Passo 3 — Testar

```bash
FUNC_URL=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_url)

curl -s "${FUNC_URL}health" | python3 -m json.tool
curl -s "${FUNC_URL}produtos" | python3 -m json.tool
curl -s "${FUNC_URL}produtos?categoria=eletronicos" | python3 -m json.tool
```

> ⚠️ **Esperado, não é falha:** a primeira chamada leva ~1 s (cold start). As seguintes são milissegundos.

Abra a Function URL no navegador — e no celular. No console: **Lambda** → a função → aba **Monitor** → **View CloudWatch logs**.

**✅ Checkpoint L₁:** o `curl` retorna JSON com os 5 produtos do mock?

---

## Atividade 2 — Lambda lendo o S3 com a execution role (L₂)

### Conferir o que já foi provisionado

- **S3** → bucket `qc-aula03-xxxxxx-catalogo` → `catalogo/produtos.csv` (subiu no apply)
- **Lambda** → a função → **Configuration** → **Environment variables**: `BUCKET_NAME` e `CSV_KEY`
- **Configuration** → **Permissions**: a execution role é a **LabRole**

### Passo 1 — Deploy da versão v2-s3

```bash
FUNC_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw lambda_name)

# Deploy da v2 (s3): empacota em zip e publica
cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v2-s3
zip -qr /tmp/v2-s3.zip . && aws lambda update-function-code --function-name "$FUNC_NAME" --zip-file fileb:///tmp/v2-s3.zip
aws lambda wait function-updated --function-name "$FUNC_NAME"
```

### Passo 2 — Testar

```bash
curl -s "${FUNC_URL}health" | python3 -m json.tool        # "source": "s3"
curl -s "${FUNC_URL}produtos?categoria=moveis" | python3 -m json.tool
curl -s "${FUNC_URL}produtos?nome=cadeira" | python3 -m json.tool
# Agora retorna os produtos REAIS do S3
```

> **Plano B:** se vier `AccessDenied` ou `NoSuchKey`, confira a variável `BUCKET_NAME` da função e se o `produtos.csv` está em `catalogo/` (`aws s3 ls s3://$(terraform output -raw bucket_name)/catalogo/`).

### Passo 3 — Reflexão (3 min)

Anote no `entrega-grupo-aula03.md`:

1. Procure "key", "password", "credential", "secret" em todo o código da v2-s3. O que você encontra?
2. Como a Lambda consegue ler o S3 "sem credenciais"? *(a execution role vira credencial temporária em variáveis de ambiente do runtime, renovada pela própria Lambda)*
3. Se um agente em produção precisasse acessar 5 buckets diferentes, qual seria a estratégia? *(uma role por função, com política restrita aos ARNs dos 5 buckets)*

**✅ Checkpoint L₂:** a função retorna os 20 produtos reais do CSV?

---

## Atividade 3 — Container: build no CloudShell, ECR e ECS Fargate (L₃)

### Conferir o código FastAPI

[docker/app.py](docker/app.py) tem a mesma lógica da v2-s3, em FastAPI. O [Dockerfile](docker/Dockerfile) é multi-stage, com base do ECR Public e usuário não-root.

### Passo 1 — Build e push para o ECR

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/docker
ECR_URL=$(cd ../terraform && terraform output -raw ecr_repository_url)
docker build --platform linux/amd64 -t "$ECR_URL:v1" .

# Login no ECR (sem PAT: usa a credencial da LabRole)
aws ecr get-login-password | docker login --username AWS --password-stdin "${ECR_URL%%/*}"

docker push "$ECR_URL:v1"
```

### Passo 2 — Criar a tarefa a partir da imagem no ECR

```bash
# Confere a imagem no ECR
aws ecr describe-images --repository-name produtos-api --output table

# Fase 2 do Terraform: cria o serviço ECS Fargate
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
terraform apply -auto-approve -var="ecs_enabled=true"
```

### Passo 3 — Testar a tarefa

```bash
TASK_IP=$(bash ../scripts/task_ip.sh)
echo "http://$TASK_IP:8080/health"
echo "http://$TASK_IP:8080/produtos?categoria=moveis"
curl -s "http://$TASK_IP:8080/produtos?categoria=moveis" | python3 -m json.tool
```

No console: **ECS** → Clusters → `qc-aula03-xxxxxx-cluster` → Services → `produtos-api` → Tasks → **Logs**.

### Passo 4 — Comparação Lambda × ECS Fargate (5 min)

| Aspecto | Lambda | ECS Fargate |
|---------|--------|-------------|
| URL | `https://<id>.lambda-url.us-east-1.on.aws/produtos` | `http://<ip-da-tarefa>:8080/produtos` |
| TLS | ✅ Embutido | ❌ Precisa de ALB (ou App Runner) |
| Cold start | ~1 s | Não há (sempre ligada) |
| Custo parado | US$ 0 | Paga por segundo enquanto a tarefa existir |
| Auto-scale | ✅ Automático | Configurável (Service Auto Scaling) |
| Duração máxima | 15 min por execução | Sem limite |
| Identidade | Execution role | Task role |

**Pergunta para o `entrega-grupo-aula03.md`:** para a QC, qual você levaria para produção da API de catálogo? Justifique em 3-5 frases (tráfego, custo, latência aceitável, complexidade operacional).

**✅ Checkpoint L₃:** o mesmo código respondeu `/produtos` como Lambda e como tarefa Fargate?

---

## Wrap-up — Destroy e custo zero (10 min)

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
terraform destroy -auto-approve -var="ecs_enabled=true"
```

Apaga Lambda, bucket, ECR (com as imagens) e o cluster ECS de uma vez. Depois confira o crédito consumido na página do Learner Lab — perto de zero.

> **Parar não é zerar:** tarefa parada, ECR ocioso — ainda há imagem armazenada e logs consumindo. Pausar não basta.

---

## Conexão com o projeto Quantum Commerce

A Function URL que você subiu é o endpoint de catálogo da QC — a **primeira tool** que os agentes vão consumir:

```json
{
  "name": "buscar_produtos",
  "description": "Busca produtos da Quantum Commerce por categoria ou nome",
  "url": "https://<id>.lambda-url.us-east-1.on.aws/produtos",
  "input_schema": {
    "type": "object",
    "properties": {
      "categoria": {"type": "string", "description": "Categoria (ex: moveis, eletronicos)"},
      "nome":      {"type": "string", "description": "Trecho do nome do produto"}
    }
  }
}
```

Duas implementações: a Lambda, que vai para produção, e o container no ECR, como alternativa (Fargate ou App Runner).

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| `curl` na Function URL → `403 Forbidden` | Falta uma das duas permissões da URL pública | `terraform apply` de novo; confira com `aws lambda get-policy --function-name "$FUNC_NAME"` (precisa de `InvokeFunctionUrl` **e** `InvokeFunction`) |
| `ResourceConflictException` no `update-function-code` | Deploy anterior ainda em andamento | `aws lambda wait function-updated --function-name "$FUNC_NAME"` e repita |
| `/produtos` → 500 "falha ao acessar o S3" | `BUCKET_NAME` errado ou CSV fora de `catalogo/` | Ver Plano B da Atividade 2 |
| `Runtime.ImportModuleError` | O zip foi feito fora da pasta (arquivo dentro de subpasta) | Rode o `zip` **de dentro** de `v1-mock/` ou `v2-s3/` |
| `docker push` → `no basic auth credentials` | Login no ECR expirou (vale 12 h) ou não foi feito | Repita o `aws ecr get-login-password ...` |
| Tarefa ECS para com `CannotPullContainerError` | Imagem `:v1` não existe no ECR | Confira `aws ecr describe-images --repository-name produtos-api` |
| Tarefa sobe e cai (`exec format error`) | Imagem buildada para ARM | Rebuild com `--platform linux/amd64` |
| `task_ip.sh` espera e desiste | Tarefa não ficou RUNNING | ECS → cluster → Tasks → **Stopped** → motivo; logs no CloudWatch `/ecs/qc-aula03-.../produtos-api` |
| `curl` na tarefa dá timeout | Security group ou IP antigo | O IP muda a cada tarefa nova: rode `task_ip.sh` de novo |
| `ExpiredToken` | Sessão do Learner Lab acabou | **Start Lab** e CloudShell novo |

---

## Referências

- [AWS Lambda — Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Lambda Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html)
- [Controle de acesso às Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html)
- [Amazon ECR — push de imagem Docker](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html)
- [Amazon ECS no AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [AWS App Runner](https://docs.aws.amazon.com/apprunner/latest/dg/what-is-apprunner.html)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
