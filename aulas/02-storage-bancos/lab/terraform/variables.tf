# ---------------------------------------------------------------------------
# Regiao por servico.
#
# Contas Azure for Students tem uma policy "Allowed resource deployment regions"
# que limita as regioes permitidas. Descubra as suas com:
#
#   az policy assignment list \
#     --scope "/subscriptions/$(az account show --query id -o tsv)" \
#     --disable-scope-strict-match \
#     --query "[].{nome:displayName, params:parameters}" -o json
#
# Dentro das regioes permitidas, cada servico ainda pode falhar por um motivo
# proprio - por isso a regiao e separada por servico e nao unica.
# ---------------------------------------------------------------------------

variable "location" {
  description = "Região padrão dos recursos (RG, Storage, Key Vault, Cosmos)"
  type        = string
  default     = "eastus2"
}

variable "location_sql" {
  description = "Região do SQL Server. Em eastus2 as contas Students recebem ProvisioningDisabled."
  type        = string
  default     = "canadacentral"
}

variable "location_search" {
  description = "Região do AI Search. O SKU free tem cota por região e eastus2 costuma estar esgotada."
  type        = string
  default     = "southcentralus"
}

variable "location_aci" {
  description = "Região do Container Instance. Cada região tem IPs de saída próprios, logo cota própria no Docker Hub."
  type        = string
  default     = "southcentralus"
}

variable "cosmos_free_tier" {
  # Mantido desligado: free-tier não beneficia conta serverless e o Azure só
  # permite 1 conta free-tier por assinatura (trava o lab se já houver outra).
  description = "Habilita o Free Tier do Cosmos DB (só 1 por assinatura; sem efeito em serverless)"
  type        = bool
  default     = false
}

variable "sql_admin_password" {
  description = "Senha do admin do Azure SQL Server. Gere uma forte com: openssl rand -base64 24"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Registry das imagens do ACI.
#
# Sem estas variaveis o lab puxa do Docker Hub publico, o que funciona em uso
# individual mas estoura o rate limit anonimo (100 pulls/6h por IP compartilhado
# da regiao) quando a turma inteira roda junto.
#
# Para usar um ACR da disciplina:
#   export TF_VAR_registry_server="meuacr.azurecr.io"
#   export TF_VAR_registry_user="$(az acr credential show -n meuacr --query username -o tsv)"
#   export TF_VAR_registry_password="$(az acr credential show -n meuacr --query 'passwords[0].value' -o tsv)"
# ---------------------------------------------------------------------------

variable "registry_server" {
  description = "Ex: meuacr.azurecr.io. Null = Docker Hub público."
  type        = string
  default     = null
}

variable "registry_user" {
  description = "Usuário do registry. Null = pull anônimo."
  type        = string
  sensitive   = true
  default     = null
}

variable "registry_password" {
  description = "Senha ou token do registry."
  type        = string
  sensitive   = true
  default     = null
}
