#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo 3 — implantar (ou atualizar) a tarefa no ECS Fargate
#
#   container api  → porta 8000, chama Rekognition e S3 com a LabRole
#   container web  → porta 8501, fala com a API por localhost:8000
#
# Uso:  VERSAO=v1 bash infra/03-implantar-apps.sh
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_ferramentas
mostrar_alvo

azul "terraform apply (servico_ativo=true, versao=${VERSAO})..."
tf apply -input=false -auto-approve -var servico_ativo=true "$@"

CLUSTER=$(saida cluster)
LOGS=$(saida log_group)

# Mesma etiqueta reenviada (v1 de novo) não muda a task definition, e o ECS
# não perceberia a imagem nova. Forçar o deploy resolve os dois casos.
azul "Forçando a troca da tarefa..."
aws ecs update-service --cluster "$CLUSTER" --service deva3 --force-new-deployment \
  --query 'service.deployments[0].status' --output text >/dev/null

azul "Esperando a tarefa nova ficar RUNNING (1 a 3 min)..."
aws ecs wait services-stable --cluster "$CLUSTER" --services deva3 || {
  vermelho "O serviço não estabilizou. Motivo da última tarefa parada:"
  ULTIMA=$(aws ecs list-tasks --cluster "$CLUSTER" --desired-status STOPPED --query 'taskArns[0]' --output text)
  [ "$ULTIMA" != "None" ] && aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$ULTIMA" \
    --query 'tasks[0].{motivo: stoppedReason, containers: containers[].{nome: name, motivo: reason}}'
  echo "Logs: aws logs tail $LOGS --since 10m"
  exit 1
}

TAREFA=$(aws ecs list-tasks --cluster "$CLUSTER" --service-name deva3 --desired-status RUNNING \
           --query 'taskArns[0]' --output text)
ENI=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TAREFA" \
        --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" --output text)
IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI" \
       --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

verde "───────────────────────────────────────────────────────────"
verde " Interface ...... http://${IP}:8501"
verde " API (Swagger) .. http://${IP}:8000/docs"
verde " Saúde .......... http://${IP}:8000/saude"
verde "───────────────────────────────────────────────────────────"
echo "Logs:  aws logs tail $LOGS --follow"
echo "O IP muda a cada implantação (não há load balancer)."
