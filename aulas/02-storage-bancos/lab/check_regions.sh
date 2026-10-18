#!/usr/bin/env bash
# Pré-voo da Aula 2: confere se a sessão do Learner Lab tem acesso aos serviços
# do lab ANTES do terraform apply (evita descobrir o problema no meio da aula).
# Uso: bash check_regions.sh
REGIAO="${AWS_REGION:-$(aws configure get region)}"
REGIAO="${REGIAO:-us-east-1}"
echo "Região: $REGIAO"

ok()   { echo "  ✓ $1"; }
falha(){ echo "  ✗ $1"; FALHOU=1; }
FALHOU=0

aws sts get-caller-identity --query Arn --output text >/dev/null 2>&1 \
  && ok "Credenciais válidas (Learner Lab ativo)" || falha "Sem credencial — rode Start Lab e abra um CloudShell novo"

aws s3api list-buckets --query "length(Buckets)" --output text >/dev/null 2>&1 \
  && ok "S3" || falha "S3"

V=$(aws rds describe-db-engine-versions --engine postgres --region "$REGIAO" \
      --query "DBEngineVersions[?starts_with(EngineVersion, '16')].EngineVersion | [-1]" --output text 2>/dev/null)
[ -n "$V" ] && [ "$V" != "None" ] && ok "RDS PostgreSQL 16 disponível ($V)" || falha "RDS PostgreSQL 16"

aws rds describe-orderable-db-instance-options --engine postgres --engine-version "${V:-16}" \
  --db-instance-class db.t3.micro --region "$REGIAO" --query "length(OrderableDBInstanceOptions)" \
  --output text 2>/dev/null | grep -qv '^0$' && ok "db.t3.micro oferecida" || falha "db.t3.micro"

aws dynamodb list-tables --region "$REGIAO" --max-items 1 >/dev/null 2>&1 \
  && ok "DynamoDB" || falha "DynamoDB"

aws secretsmanager list-secrets --region "$REGIAO" --max-results 1 >/dev/null 2>&1 \
  && ok "Secrets Manager" || falha "Secrets Manager"

aws ec2 describe-instance-type-offerings --region "$REGIAO" --filters Name=instance-type,Values=t3.small \
  --query "length(InstanceTypeOfferings)" --output text 2>/dev/null | grep -qv '^0$' \
  && ok "EC2 t3.small (MongoDB)" || falha "EC2 t3.small"

echo "IP de saída deste CloudShell (liberado no RDS/Mongo): $(curl -s https://checkip.amazonaws.com)"
[ "$FALHOU" = 0 ] && echo "Tudo pronto para o terraform apply." || { echo "Corrija os itens com ✗ antes de seguir."; exit 1; }
