# Storage para dados do lab (áudios e imagens) — independente de aulas anteriores
resource "azurerm_storage_account" "data" {
  name                     = "stdata04${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

resource "azurerm_storage_container" "audios" {
  name                 = "audios"
  storage_account_id = azurerm_storage_account.data.id
}

resource "azurerm_storage_container" "imagens" {
  name                 = "imagens"
  storage_account_id = azurerm_storage_account.data.id
}
