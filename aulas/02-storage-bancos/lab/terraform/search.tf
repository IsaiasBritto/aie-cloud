# Azure AI Search — SKU Free (3 indexes, 50 MB, 3 réplicas)
# Apenas 1 search service Free permitido por subscription.
resource "azurerm_search_service" "qc" {
  name                = "srch-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "free"
  semantic_search_sku = "free"
  # NÃO definimos semantic_search_sku aqui: o provider azurerm 3.x recusa esse
  # argumento quando sku="free" ("can only be specified when sku is not free"),
  # apesar de o SKU free SUPORTAR o semantic ranker (plano "free", 1000 q/mês).
  # Por isso o semantic é habilitado via `az` após o apply (ver guia, Parte B) —
  # mesmo padrão do data-plane do Cosmos.

  # Habilita autenticação AAD/RBAC no DATA-PLANE (criar índice, indexar, consultar).
  # Sem isso, o serviço aceita só API key e o DefaultAzureCredential dos scripts
  # Python recebe 403 Forbidden — mesmo com as role assignments abaixo.
  # local_auth = true mantém também a API key (modo "Both"), útil no portal.
  local_authentication_enabled = true
  authentication_failure_mode  = "http403"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# Permissão de gerenciar o serviço (criar/deletar índices)
resource "azurerm_role_assignment" "search_admin" {
  scope                = azurerm_search_service.qc.id
  role_definition_name = "Search Service Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Permissão de plano de dados (indexar e consultar documentos)
resource "azurerm_role_assignment" "search_index_data" {
  scope                = azurerm_search_service.qc.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Habilita o semantic ranker (plano free). Feito via azapi porque o provider
# azurerm 3.x recusa semantic_search_sku quando sku="free", apesar de o Azure
# suportar. Sem isso, buscas com query_type="semantic" falham com
# "Semantic search is not enabled for this service".
#resource "azapi_update_resource" "search_semantic" {
#  type        = "Microsoft.Search/searchServices@2023-11-01"
#  resource_id = azurerm_search_service.qc.id
#  body = jsonencode({
#    properties = {
#      semanticSearch = "free"
#    }
#  })
#}
