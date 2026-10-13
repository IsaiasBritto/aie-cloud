#!/usr/bin/env bash
# Confere em quais regiões o tipo de instância do lab está disponível.
# No AWS Academy Learner Lab só us-east-1 e us-west-2 são liberadas.
# Uso: bash check_region.sh [tipo]   (padrão: t3.micro)
TIPO="${1:-t3.micro}"
REGIOES="us-east-1 us-west-2"

echo "Verificando ${TIPO} nas regiões do Learner Lab..."
for r in $REGIOES; do
  zonas=$(aws ec2 describe-instance-type-offerings \
    --region "$r" --location-type availability-zone \
    --filters "Name=instance-type,Values=${TIPO}" \
    --query "InstanceTypeOfferings[].Location" --output text 2>/dev/null)
  if [ -n "$zonas" ]; then
    echo "✓ ${TIPO} disponível em ${r}: ${zonas}"
  else
    echo "✗ ${TIPO} indisponível (ou sem permissão) em ${r}"
  fi
done
