output "resource_group_name" {
  description = "Nome do Resource Group da Aula 5"
  value       = azurerm_resource_group.rg.name
}

output "subscription_id" {
  description = "ID da subscription (usado pelo MLClient)"
  value       = data.azurerm_client_config.current.subscription_id
}

output "workspace_name" {
  description = "Nome do Azure ML Workspace"
  value       = azurerm_machine_learning_workspace.ws.name
}

output "storage_account_name" {
  description = "Nome do Storage Account do datastore default (workspaceblobstore)"
  value       = azurerm_storage_account.ml.name
}

output "compute_cluster_name" {
  description = "Nome do Compute Cluster (sempre 'cpu-cluster')"
  value       = azurerm_machine_learning_compute_cluster.cpu.name
}

output "container_registry_name" {
  description = "Nome do Container Registry (imagens de environment dos jobs)"
  value       = azurerm_container_registry.ml.name
}
