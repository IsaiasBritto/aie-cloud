# Cosmos DB Account — modo Serverless (paga por operação).
# free_tier_enabled fica DESLIGADO por padrão: o desconto do free-tier só vale
# para provisioned throughput (não para serverless), e o Azure permite apenas
# 1 conta free-tier por assinatura — o que trava o lab se já houver outra.
# Em serverless o custo das 4h de aula é de centavos. Ligue via -var se quiser.
resource "azurerm_cosmosdb_account" "qc" {
  name = "cosmos-qc-${random_string.sufixo.result}"

  # Região própria (local.location_cosmos, default = var.location).
  # A conta NÃO precisa ficar na mesma região do Resource Group, então trocar
  # esta região não move Storage, Key Vault nem SQL — nada é recriado.
  # Use quando aparecer:
  #   503 ServiceUnavailable "high demand in this region"
  # que é capacidade esgotada da Azure, não problema da sua assinatura.
  location            = local.location_cosmos
  resource_group_name = azurerm_resource_group.rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  free_tier_enabled   = var.cosmos_free_tier

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = local.location_cosmos
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }

  tags = local.tags
}

# Role data-plane do Cosmos (Built-in Data Contributor, id ...0002).
# OBS.: no Cloud Shell o lab autentica no Cosmos por KEY (o Cloud Shell não
# emite token AAD para a audience do Cosmos). Esta role existe para o cenário
# de PRODUÇÃO — uma Function/Container com Managed Identity usaria AAD direto,
# sem key. Mantida como referência do padrão correto em prod.
resource "azurerm_cosmosdb_sql_role_assignment" "qc_data" {
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.qc.name
  role_definition_id  = "${azurerm_cosmosdb_account.qc.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = data.azurerm_client_config.current.object_id
  scope               = azurerm_cosmosdb_account.qc.id
}

# Database
resource "azurerm_cosmosdb_sql_database" "qc" {
  name                = "qc-db"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.qc.name
}

# Container de reviews — particionado por produto_id
resource "azurerm_cosmosdb_sql_container" "reviews" {
  name                = "reviews"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.qc.name
  database_name       = azurerm_cosmosdb_sql_database.qc.name
  partition_key_paths = ["/produto_id"]
}
