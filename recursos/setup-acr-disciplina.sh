#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Setup do ACR da disciplina — rodar UMA VEZ, pelo professor, antes da Aula 2.
#
# NAO faz parte do Terraform do lab. Motivos:
#   - o ACR precisa sobreviver ao "terraform destroy" de cada aluno
#   - nao queremos 30 registries criados, um por aluno
#
# Por que existe:
#   O ACI puxa imagem do Docker Hub por IPs de saida compartilhados da regiao.
#   O limite anonimo (100 pulls/6h por IP) estoura quando a turma roda junto, e
#   o create falha com "409 RegistryErrorResponse". Com o ACR, o pull sai do
#   backbone da Azure e o problema desaparece.
#
# Custo: ACR Basic ~ US$ 0,17/dia. Mantenha ligado durante a disciplina.
#
# Uso:
#   chmod +x setup-acr-disciplina.sh
#   ./setup-acr-disciplina.sh
# ---------------------------------------------------------------------------
set -euo pipefail

RG="${RG:-rg-fiap-shared}"
LOCAL="${LOCAL:-southcentralus}"
ACR="${ACR:-acrfiapaie}"      # nome global unico; ajuste se ja existir

echo "==> Resource Group compartilhado: $RG"
az group create -n "$RG" -l "$LOCAL" -o none

echo "==> Registry: $ACR"
if az acr show -n "$ACR" -g "$RG" -o none 2>/dev/null; then
  echo "    ja existe, pulando a criacao"
else
  az acr create -g "$RG" -n "$ACR" --sku Basic -l "$LOCAL" -o none
fi

# O "library/" e obrigatorio para imagens oficiais do Docker Hub.
# Sem ele o import falha com 401 UNAUTHORIZED, porque a Azure procura um
# repositorio de usuario chamado "mongo-express", que nao existe.
echo "==> Importando imagens (passa pelo backbone da Azure, sem rate limit)"
az acr import -n "$ACR" --source docker.io/library/mongo:7.0 \
  --image mongo:7.0 --force -o none
az acr import -n "$ACR" --source docker.io/library/mongo-express:1.0.2 \
  --image mongo-express:1.0.2 --force -o none

echo "==> Habilitando admin user (autenticacao simples para o ACI do lab)"
az acr update -n "$ACR" --admin-enabled true -o none

echo
echo "==> Conteudo do registry:"
az acr repository list -n "$ACR" -o table

echo
echo "======================================================================"
echo "Distribua estas tres linhas para a turma (colar antes do apply):"
echo "======================================================================"
echo "export TF_VAR_registry_server=\"$(az acr show -n "$ACR" --query loginServer -o tsv)\""
echo "export TF_VAR_registry_user=\"$(az acr credential show -n "$ACR" --query username -o tsv)\""
echo "export TF_VAR_registry_password=\"$(az acr credential show -n "$ACR" --query 'passwords[0].value' -o tsv)\""
echo "======================================================================"
echo
echo "OBS.: admin user distribui a mesma credencial para todos. Em producao o"
echo "certo seria uma Managed Identity com a role AcrPull por consumidor."
