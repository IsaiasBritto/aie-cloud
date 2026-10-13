# Container — Aula 3

Versão **FastAPI** da API de catálogo da QC, com a mesma lógica da Lambda `v2-s3`, empacotada num **container Docker** para rodar no **Amazon ECS (Fargate)**.

| Arquivo | O que é |
|---------|---------|
| [app.py](app.py) | API FastAPI com `/health` e `/produtos` |
| [requirements.txt](requirements.txt) | FastAPI + Uvicorn + boto3 |
| [Dockerfile](Dockerfile) | Multi-stage build, base do ECR Public, usuário não-root |

## Passo A — Build no CloudShell e push para o ECR

O AWS CloudShell já tem Docker. O login no ECR usa a credencial da sua sessão (LabRole) — sem token pessoal.

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/docker
ECR_URL=$(cd ../terraform && terraform output -raw ecr_repository_url)

# Build (CloudShell é x86_64; o --platform deixa explícito o que o Fargate vai rodar)
docker build --platform linux/amd64 -t "$ECR_URL:v1" .

# Login no ECR (sem PAT: usa a credencial da LabRole)
aws ecr get-login-password | docker login --username AWS --password-stdin "${ECR_URL%%/*}"

docker push "$ECR_URL:v1"

# Confere a imagem no ECR (o scan de vulnerabilidades roda no push)
aws ecr describe-images --repository-name produtos-api --output table
```

> **CloudShell sem espaço?** O `$HOME` tem 1 GB, mas as imagens Docker ficam fora dele. Se o build falhar por espaço, rode `docker system prune -af`.

## Passo B — Subir a tarefa no ECS Fargate

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
terraform apply -auto-approve -var="ecs_enabled=true"

TASK_IP=$(bash ../scripts/task_ip.sh)
curl "http://$TASK_IP:8080/health"
curl "http://$TASK_IP:8080/produtos?categoria=moveis"
```

> Sem load balancer, a tarefa ganha um IP público próprio, que muda a cada reinício. Em produção: **Application Load Balancer** na frente do serviço — ou **App Runner**, que entrega URL HTTPS e auto-scale a partir da mesma imagem do ECR.

## Comparação com a Lambda (mesma lógica, runtime diferente)

| Aspecto | Lambda v2-s3 | ECS Fargate (este container) |
|---------|--------------|------------------------------|
| URL | `https://<id>.lambda-url.us-east-1.on.aws/produtos` | `http://<ip-da-tarefa>:8080/produtos` |
| TLS | ✅ Embutido | ❌ Precisa de ALB ou App Runner |
| Cold start | ~1 s | Não há (sempre ligada) |
| Custo parado | US$ 0 | Paga por segundo enquanto a tarefa existir |
| Auto-scale | ✅ Automático | Configurável (Service Auto Scaling) |
| Linguagem/dependências | Runtimes suportados | Qualquer coisa que rode em Linux |
| Identidade | Execution role (LabRole) | Task role (LabRole) |
