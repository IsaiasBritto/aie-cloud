# Key Vault para guardar a chave do AI Services
# (uso didático — em produção, prefira Managed Identity direto no recurso)
resource "azurerm_key_vault" "kv" {
  name                       = "kv-aula04-${random_string.sufixo.result}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = local.tags
}

# Concede ao usuário autenticado permissão de gerenciar segredos
resource "azurerm_role_assignment" "kv_admin" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Espera a role propagar antes de criar o segredo
resource "time_sleep" "wait_rbac" {
  depends_on      = [azurerm_role_assignment.kv_admin]
  create_duration = "30s"
}

# Chave primária do AI Services como segredo no Vault
resource "azurerm_key_vault_secret" "ai_key" {
  name         = "ai-services-key"
  value        = azurerm_cognitive_account.ai.primary_access_key
  key_vault_id = azurerm_key_vault.kv.id
  depends_on   = [time_sleep.wait_rbac]
}
