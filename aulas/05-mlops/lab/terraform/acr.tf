# Container Registry — pré-provisionado para evitar criação lazy no primeiro job
# Sem ACR explícito, o Azure ML cria um durante o "Preparing" do job (~2-3 min extras).
resource "azurerm_container_registry" "ml" {
  name                = "acr${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.tags
}
