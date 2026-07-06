# Compute Cluster com SCALE-TO-ZERO (0 nodes idle = custo zero)
resource "azurerm_machine_learning_compute_cluster" "cpu" {
  name                          = "cpu-cluster"
  location                      = azurerm_resource_group.rg.location
  vm_priority                   = "Dedicated"
  vm_size                       = "STANDARD_DS2_V2" # 2 vCPU, 7GB RAM — dentro da quota Azure for Students (6 vCPU max)
  machine_learning_workspace_id = azurerm_machine_learning_workspace.ws.id

  scale_settings {
    min_node_count                       = 0   # ← CRÍTICO: scale to zero
    max_node_count                       = 2
    scale_down_nodes_after_idle_duration = "PT2M" # 2 min idle → desliga
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}
