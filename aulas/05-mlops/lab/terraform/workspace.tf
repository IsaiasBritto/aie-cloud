# Application Insights — dependência do Workspace
resource "azurerm_application_insights" "ml" {
  name                = "appi-ml-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  application_type    = "web"
  tags                = local.tags
}

# Azure ML Workspace
resource "azurerm_machine_learning_workspace" "ws" {
  name                          = "mlw-qc-${random_string.sufixo.result}"
  resource_group_name           = azurerm_resource_group.rg.name
  location                      = azurerm_resource_group.rg.location
  application_insights_id       = azurerm_application_insights.ml.id
  key_vault_id                  = azurerm_key_vault.ml.id
  storage_account_id            = azurerm_storage_account.ml.id
  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}
