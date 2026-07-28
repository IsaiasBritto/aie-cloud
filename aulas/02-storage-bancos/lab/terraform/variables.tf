variable "location" {
  # centralus: região permitida pela política das contas Azure for Students E
  # onde o Azure SQL realmente provisiona (em eastus2 o SQL fica "ProvisioningDisabled"
  # nessas contas, e o AI Search costuma estar sem capacidade).
  # Se a sua conta bloquear centralus, veja as regiões permitidas no guia e rode:
  # terraform apply -var="location=<regiao>"
  description = "Região do Azure onde os recursos serão provisionados"
  type        = string
  default     = "eastus2"
}

variable "location_sql" {
  type        = string
  description = "Região do SQL Server — separada porque nem toda região permite provisionamento"
  default     = "canadacentral"
}

variable "location_search" {
  type        = string
  description = "Região do AI Search — o SKU free tem cota por região"
  default     = "southcentralus"
}

variable "location_aci" {
  type        = string
  description = "Regiao do Container Instance - IPs de saida diferentes tem cota propria no Docker Hub"
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
