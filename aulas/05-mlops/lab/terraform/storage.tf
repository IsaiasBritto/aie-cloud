# Storage Account — datastore default do Workspace
resource "azurerm_storage_account" "ml" {
  name                     = "stml${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  is_hns_enabled           = false # ML Workspace requer HNS desabilitado
  tags                     = local.tags
}
