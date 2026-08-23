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

# Permissão de PLANO DE DADOS para você mesmo.
#
# Por que isto é necessário mesmo sendo Owner da assinatura:
# ser Owner é plano de CONTROLE — permite criar, configurar e apagar a conta de
# storage. Ler ou escrever um blob é plano de DADOS, e exige um papel próprio.
# São dois sistemas de autorização diferentes sobre o mesmo recurso.
#
# Sem esta atribuição, o upload do CSV falha com:
#   "You do not have the required permissions needed to perform this operation"
# e o script de indexação falha com AuthorizationPermissionMismatch — ambos
# apontando para permissão, sem dizer que a permissão que falta é de outro plano.
#
# A alternativa seria `--auth-mode key`, que usa a chave da conta. Funciona, mas
# joga fora a lição: chave de storage é all-or-nothing e não identifica QUEM
# acessou. O lab inteiro é sobre não fazer isso.
resource "azurerm_role_assignment" "storage_blob_data" {
  scope                = azurerm_storage_account.qc.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
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
