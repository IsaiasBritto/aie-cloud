# Azure AI Search — SKU Free (3 índices, 50 MB, 1 réplica, 1 partição).
# Apenas 1 search service Free permitido por subscription.
resource "azurerm_search_service" "qc" {
  name                = "srch-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = local.location_search
  sku                 = "free"

  # NAO declare semantic_search_sku aqui. O provider azurerm (3.x e 4.x) recusa
  # o argumento quando sku = "free":
  #   Error: `semantic_search_sku` can only be specified when `sku` is not set to "free"
  # O tier free SUPORTA o semantic ranker (plano "free", 1000 queries/mes), mas
  # ele so e habilitavel fora do Terraform, depois do apply:
  #
  #   az search service update \
  #     --name $(terraform output -raw search_service_name) \
  #     --resource-group $(terraform output -raw resource_group_name) \
  #     --semantic-search free
  #
  # Tentar forcar via azapi_update_resource NAO funciona: a Azure aceita a
  # chamada e reverte semanticSearch para "disabled", entao o plan nunca
  # converge. Mesmo padrao do data-plane do Cosmos (ver guia, Parte B).

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

# ---------------------------------------------------------------------------
# Habilita o semantic ranker via CLI, porque o provider nao permite declarar.
#
# terraform_data e nativo desde o Terraform 1.4 - nao exige o provider "null".
# triggers_replace faz o comando rodar de novo se o search service for
# recriado (id novo), e ficar quieto nos applies seguintes.
#
# ATENCAO - isto e um escape hatch, nao IaC de verdade:
#   - roda na maquina que executa o terraform, nao na Azure
#   - exige "az" instalado e autenticado (ok no Cloud Shell)
#   - o Terraform nao sabe o estado real: se alguem desabilitar o semantic
#     pelo portal, nenhum plan vai acusar a diferenca
# Use provisioner so quando nao houver alternativa declarativa - que e
# exatamente o caso aqui.
# ---------------------------------------------------------------------------
resource "terraform_data" "search_semantic" {
  triggers_replace = [azurerm_search_service.qc.id]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -e
      echo "Habilitando semantic ranker (plano free) em ${azurerm_search_service.qc.name}..."
      az search service update \
        --name "${azurerm_search_service.qc.name}" \
        --resource-group "${azurerm_resource_group.rg.name}" \
        --semantic-search free \
        --output none
      echo "Semantic ranker habilitado."
    EOT
  }
}
