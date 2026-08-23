# MongoDB + Mongo-Express via Azure Container Instances
# Vantagem sobre VM: sem problema de capacidade de SKU, inicialização em ~2 min,
# mais alinhado ao padrão serverless/container da disciplina
resource "azurerm_container_group" "mongodb" {
  name                = "aci-qc-aula04-${random_string.sufixo.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  ip_address_type     = "Public"
  dns_name_label      = "qc-mongo-${random_string.sufixo.result}"
  os_type             = "Linux"
  tags                = local.tags

  # Credenciais do registry, só quando há um configurado.
  # O bloco "dynamic" some inteiro quando registry_user é null — aí o ACI puxa
  # do Docker Hub público, que é o comportamento antigo.
  dynamic "image_registry_credential" {
    for_each = var.registry_user == null ? [] : [1]
    content {
      server   = coalesce(var.registry_server, "index.docker.io")
      username = var.registry_user
      password = var.registry_password
    }
  }

  # Container 1: MongoDB 7.0
  container {
    name   = "mongodb"
    image  = "${local.image_prefix}mongo:7.0"
    cpu    = 0.5
    memory = 1.0

    ports {
      port     = 27017
      protocol = "TCP"
    }

    environment_variables = {
      MONGO_INITDB_ROOT_USERNAME = "admin"
      MONGO_INITDB_ROOT_PASSWORD = local.mongo_admin_pass
      MONGO_INITDB_DATABASE      = "qc-db"
    }
  }

  # Container 2: Mongo-Express (Web UI)
  # Os containers do mesmo group compartilham rede (localhost)
  container {
    name   = "mongo-express"
    image  = "${local.image_prefix}mongo-express:1.0.2"
    cpu    = 0.25
    memory = 0.5

    ports {
      port     = 8081
      protocol = "TCP"
    }

    environment_variables = {
      ME_CONFIG_MONGODB_URL          = "mongodb://admin:${local.mongo_admin_pass}@localhost:27017"
      # Basic Auth desativado: Chrome 94+ bloqueia dialogs de Basic Auth em HTTP puro.
      # O MongoDB em si continua protegido por senha — esta interface é só para visualização no lab.
      ME_CONFIG_BASICAUTH            = "false"
      ME_CONFIG_MONGODB_ENABLE_ADMIN = "true"
      ME_CONFIG_SITE_SESSIONSECRET   = "QCsession2024!"
    }
  }
}
