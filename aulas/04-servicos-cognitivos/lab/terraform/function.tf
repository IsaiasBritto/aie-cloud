# Storage obrigatório para o runtime da Function App
resource "azurerm_storage_account" "func_sa" {
  name                     = "stfunc04${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

# O Flex Consumption guarda o pacote de deploy num container de blob, e não no
# File Share que o plano Y1 usava. Por isso este container existe.
resource "azurerm_storage_container" "deployments" {
  name               = "deployments"
  storage_account_id = azurerm_storage_account.func_sa.id
}

# Plano FC1 — Flex Consumption.
#
# ATENÇÃO: NÃO volte para "Y1". Contas Azure for Students têm cota ZERO do
# plano Y1 (Linux Consumption clássico), e o apply falha com:
#
#   401 Unauthorized: Operation cannot be completed without additional quota.
#   Current Limit (Y1 VMs): 0
#
# O 401 aqui engana — não é problema de autenticação, é cota. E o Y1 está sendo
# aposentado em set/2028 de qualquer forma. FC1 é o sucessor: pay-per-execution,
# cold start menor e escala melhor. É o mesmo plano usado na Aula 3.
resource "azurerm_service_plan" "plan" {
  name                = "asp-qc-aula04-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.tags
}

resource "azurerm_function_app_flex_consumption" "fn" {
  name                = "func-qc-aula04-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  # Autenticação do pacote de deploy por connection string, de propósito: usar
  # Managed Identity aqui criaria um problema de ovo-e-galinha, já que a
  # identidade só existe depois que a Function é criada.
  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.func_sa.primary_blob_endpoint}${azurerm_storage_container.deployments.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.func_sa.primary_access_key

  # No Flex Consumption o runtime é declarado aqui, e não por
  # FUNCTIONS_WORKER_RUNTIME em app_settings como no Y1.
  runtime_name           = "python"
  runtime_version        = "3.12"
  instance_memory_in_mb  = 2048
  maximum_instance_count = 40

  site_config {}

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "AI_ENDPOINT"          = azurerm_cognitive_account.ai.endpoint
    "AI_REGION"            = var.location
    # AI_KEY via referência de Key Vault — a MI da Function resolve em runtime,
    # sem a chave aparecer no código nem no state da app.
    # A referência só resolve DEPOIS que a role fn_kv_user propaga (1-2 min).
    "AI_KEY"               = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.ai_key.id})"
    "DATA_STORAGE_ACCOUNT" = azurerm_storage_account.data.name
    "MONGODB_URI"          = "mongodb://admin:${local.mongo_admin_pass}@${azurerm_container_group.mongodb.ip_address}:27017/?authSource=admin"
  }

  tags = local.tags
}

# MI da Function: lê segredos do Key Vault (necessário para resolver a KV reference do AI_KEY)
resource "azurerm_role_assignment" "fn_kv_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_function_app_flex_consumption.fn.identity[0].principal_id
}

# MI da Function: chama Language e Vision via Managed Identity (sem chave)
resource "azurerm_role_assignment" "fn_ai_user" {
  scope                = azurerm_cognitive_account.ai.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_function_app_flex_consumption.fn.identity[0].principal_id
}

# MI da Function: lê e escreve no Blob de dados (upload de áudio/imagem para testes)
resource "azurerm_role_assignment" "fn_blob_contributor" {
  scope                = azurerm_storage_account.data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_function_app_flex_consumption.fn.identity[0].principal_id
}
