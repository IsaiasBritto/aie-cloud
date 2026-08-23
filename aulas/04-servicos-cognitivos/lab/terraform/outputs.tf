output "resource_group_name" {
  description = "Nome do Resource Group da Aula 4"
  value       = azurerm_resource_group.rg.name
}

# AI Services
output "ai_endpoint" {
  description = "Endpoint do Azure AI Services (Speech, Language, Vision)"
  value       = azurerm_cognitive_account.ai.endpoint
}

output "ai_name" {
  description = "Nome do recurso AI Services"
  value       = azurerm_cognitive_account.ai.name
}

# Key Vault
output "key_vault_name" {
  description = "Nome do Key Vault (com a chave do AI Services como segredo)"
  value       = azurerm_key_vault.kv.name
}

# Storage de dados (áudios e imagens)
output "data_storage_account_name" {
  description = "Nome do Storage Account de dados (containers: audios, imagens)"
  value       = azurerm_storage_account.data.name
}

# MongoDB ACI
output "mongodb_public_ip" {
  description = "IP público do Azure Container Instance com MongoDB"
  value       = azurerm_container_group.mongodb.ip_address
}

output "mongodb_fqdn" {
  description = "FQDN do ACI (alternativa ao IP)"
  value       = azurerm_container_group.mongodb.fqdn
}

output "mongo_express_url" {
  description = "URL do Mongo Express (interface web do MongoDB)"
  value       = "http://${azurerm_container_group.mongodb.ip_address}:8081"
}

output "mongodb_connection_string" {
  description = "Connection string do MongoDB (usar na Function ou em scripts)"
  value       = "mongodb://admin:${local.mongo_admin_pass}@${azurerm_container_group.mongodb.ip_address}:27017/?authSource=admin"
  sensitive   = true
}

# Function
output "function_app_name" {
  description = "Nome da Function App"
  value       = azurerm_function_app_flex_consumption.fn.name
}

output "function_app_hostname" {
  description = "URL HTTPS da Function App"
  value       = "https://${azurerm_function_app_flex_consumption.fn.default_hostname}"
}
