#!/usr/bin/env bash
# deploy.sh — publica a Eva no ECS Fargate, do zero, em três movimentos:
#
#   1. terraform apply (ecs_enabled=false)  -> ECR, log group, cluster, segredo
#   2. docker build + push                   -> a imagem vai para o ECR
#   3. terraform apply (ecs_enabled=true)   -> o serviço nasce apontando para a imagem
#
# Por que dois applies: o serviço ECS precisa de uma imagem que ainda não
# existe no primeiro apply. É o mesmo ovo-e-galinha da Aula 3.
#
# Uso (no CloudShell, de dentro desta pasta):
#   cp terraform/terraform.tfvars.example terraform/terraform.tfvars   # e edite
#   export TF_VAR_openai_api_key=sk-...      # só se provedor = "openai"
#   bash deploy.sh
#
# Argumentos extras vão direto para os dois `terraform apply`:
#   bash deploy.sh -var provedor=bedrock -var criar_role=true
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF="$AQUI/terraform"
PROJETO="$AQUI/.."          # contexto do docker build: a pasta da Eva
TAG="v$(date +%Y%m%d-%H%M%S)" # tag nova a cada deploy: força a troca da tarefa

passo() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
falha() { printf '\n\033[1;31mERRO: %s\033[0m\n' "$*" >&2; exit 1; }

command -v terraform >/dev/null || falha "terraform não encontrado. Rode o install_terraform.sh da Aula 1."
command -v docker >/dev/null    || falha "docker não encontrado. Use o CloudShell (já vem com Docker)."
aws sts get-caller-identity >/dev/null 2>&1 || falha "sem credencial AWS. O Learner Lab está ligado (bolinha verde)?"

passo "0/4 Quem sou eu"
aws sts get-caller-identity --query '{conta: Account, arn: Arn}' --output table

passo "1/4 Infra base (ECR, logs, cluster, segredo)"
cd "$TF"
terraform init -input=false -upgrade >/dev/null
terraform apply -input=false -auto-approve -var ecs_enabled=false "$@"

REPO=$(terraform output -raw ecr_repository_url)
REGISTRO="${REPO%%/*}"
REGIAO=$(echo "$REGISTRO" | cut -d. -f4)

passo "2/4 Build e push da imagem ($TAG)"
# O login no ECR usa a SUA credencial (no Learner Lab, a da sessão): nenhuma
# senha de registry fica guardada em lugar nenhum.
aws ecr get-login-password --region "$REGIAO" | docker login --username AWS --password-stdin "$REGISTRO"
docker build -t "$REPO:$TAG" "$PROJETO"
docker push "$REPO:$TAG"

passo "3/4 Serviço ECS apontando para a imagem nova"
terraform apply -input=false -auto-approve -var ecs_enabled=true -var image_tag="$TAG" "$@"

CLUSTER=$(terraform output -raw ecs_cluster_name)
LOGS=$(terraform output -raw log_group_name)

passo "4/4 Esperando a tarefa ficar RUNNING (1 a 3 min)"
IP=""
for _ in $(seq 1 36); do
  TASK=$(aws ecs list-tasks --cluster "$CLUSTER" --service-name eva --desired-status RUNNING \
           --query 'taskArns[0]' --output text 2>/dev/null || true)
  if [ -n "$TASK" ] && [ "$TASK" != "None" ]; then
    ESTADO=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK" --query 'tasks[0].lastStatus' --output text)
    ENI=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK" \
            --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" --output text)
    if [ "$ESTADO" = "RUNNING" ] && [ -n "$ENI" ] && [ "$ENI" != "None" ]; then
      IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI" \
             --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
      [ -n "$IP" ] && [ "$IP" != "None" ] && break
    fi
    echo "  tarefa em $ESTADO..."
  else
    echo "  aguardando o ECS criar a tarefa..."
  fi
  sleep 5
done

[ -n "$IP" ] && [ "$IP" != "None" ] || falha "a tarefa não subiu em 3 min. Veja os logs: aws logs tail $LOGS --since 10m"

cat <<FIM

Eva no ar:   http://$IP:8501
Logs:        aws logs tail $LOGS --follow
Telemetria:  bash $AQUI/custo.sh
Desligar:    cd $TF && terraform destroy -auto-approve $*

O IP muda a cada deploy (não há load balancer). Rode o deploy de novo para
publicar uma versão nova do código.
FIM
