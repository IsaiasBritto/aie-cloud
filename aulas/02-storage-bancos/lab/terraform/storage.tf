# Storage Account — base de tudo da QC
resource "azurerm_storage_account" "qc" {
  name                     = "stqc${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

# Container para o catálogo (acessado por agentes/funções)
resource "azurerm_storage_container" "catalogo" {
  name                  = "catalogo"
  storage_account_id    = azurerm_storage_account.qc.id
  container_access_type = "private"
}

# Container para imagens dos produtos
resource "azurerm_storage_container" "imagens" {
  name                  = "imagens"
  storage_account_id    = azurerm_storage_account.qc.id
  container_access_type = "private"
}

# Container para logs (com lifecycle Hot → Cool → Archive)
resource "azurerm_storage_container" "logs" {
  name                  = "logs"
  storage_account_id    = azurerm_storage_account.qc.id
  container_access_type = "private"
}

# Lifecycle policy: logs migram automaticamente para tiers mais baratos
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.qc.id

  rule {
    name    = "logs-lifecycle"
    enabled = true
    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["logs/"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30
        tier_to_archive_after_days_since_modification_greater_than = 90
        delete_after_days_since_modification_greater_than          = 365
      }
    }
  }
}
