# MongoDB + Mongo-Express via Azure Container Instances
# Alternativa ao Cosmos DB para regiões onde ele não está disponível (Azure for Students).
# Mesma abordagem da Aula 4: sem problema de capacidade de SKU, inicialização em ~2 min.
#
# ATENCAO - de onde vem a imagem:
# Por padrao o ACI puxa do Docker Hub publico, por IPs de saida compartilhados da
# regiao. O limite anonimo (100 pulls/6h por IP) estoura com facilidade e o create
# falha com "409 RegistryErrorResponse". Trocar de regiao ajuda so as vezes.
#
# Para apontar para um registry proprio (ACR), defina:
#   TF_VAR_registry_server    = "meuacr.azurecr.io"
#   TF_VAR_registry_user      = "<usuario>"
#   TF_VAR_registry_password  = "<senha>"
# Sem essas variaveis o lab continua funcionando com o Docker Hub publico.
#
# Popular o ACR uma vez (o import passa pelo backbone da Azure, sem rate limit):
#   az acr import -n <acr> --source docker.io/library/mongo:7.0 --image mongo:7.0
#   az acr import -n <acr> --source docker.io/library/mongo-express:1.0.2 --image mongo-express:1.0.2
resource "azurerm_container_group" "mongodb" {
  name                = "aci-qc-aula02-${random_string.sufixo.result}"
  location            = local.location_aci
  resource_group_name = azurerm_resource_group.rg.name
  ip_address_type     = "Public"
  dns_name_label      = "qc-mongo-${random_string.sufixo.result}"
  os_type             = "Linux"
  tags                = local.tags

  # Credencial do registry. So e gerada se registry_user estiver definido,
  # entao o lab continua funcionando para quem nao configurou nada.
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
  # Os containers do mesmo group compartilham rede (localhost).
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
      ME_CONFIG_MONGODB_URL = "mongodb://admin:${local.mongo_admin_pass}@localhost:27017"
      # Basic Auth desativado: Chrome 94+ bloqueia dialogs de Basic Auth em HTTP puro.
      # O MongoDB em si continua protegido por senha — esta interface é só para o lab.
      ME_CONFIG_BASICAUTH            = "false"
      ME_CONFIG_MONGODB_ENABLE_ADMIN = "true"
      ME_CONFIG_SITE_SESSIONSECRET   = "QCsession2024!"
    }
  }
}
