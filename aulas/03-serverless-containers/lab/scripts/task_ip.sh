#!/usr/bin/env bash
# Imprime o IP público da tarefa Fargate do serviço produtos-api.
# Uso (de dentro de lab/terraform):  TASK_IP=$(bash ../scripts/task_ip.sh)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../terraform" && pwd)"
CLUSTER=$(cd "$DIR" && terraform output -raw ecs_cluster_name)

for _ in $(seq 1 30); do
  TASK=$(aws ecs list-tasks --cluster "$CLUSTER" --service-name produtos-api \
           --desired-status RUNNING --query 'taskArns[0]' --output text 2>/dev/null || true)
  if [ -n "$TASK" ] && [ "$TASK" != "None" ]; then
    ENI=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK" \
            --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" --output text)
    if [ -n "$ENI" ] && [ "$ENI" != "None" ]; then
      IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI" \
             --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
      if [ -n "$IP" ] && [ "$IP" != "None" ]; then
        echo "$IP"
        exit 0
      fi
    fi
  fi
  echo "Aguardando a tarefa Fargate subir..." >&2
  sleep 10
done
echo "A tarefa não ficou RUNNING em 5 min. Veja: ECS → Clusters → $CLUSTER → Tasks (aba Logs)" >&2
exit 1
