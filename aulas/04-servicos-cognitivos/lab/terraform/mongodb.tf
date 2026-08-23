# ---------------------------------------------------------------------------
# MongoDB + Mongo-Express via Azure Container Instances.
#
# O REGISTRY É CRIADO PELO PRÓPRIO TERRAFORM, de propósito.
#
# Puxar `mongo:7.0` direto do Docker Hub funciona quando uma pessoa testa
# sozinha, e falha quando a turma roda junto:
#
#   409 RegistryErrorResponse: An error response is received from the docker
#   registry 'index.docker.io'. Please retry later.
#
# O limite anônimo do Docker Hub é de 100 pulls por 6 h POR IP, e o ACI sai por
# IPs de saída compartilhados da região — ou seja, a cota é da turma inteira, não
# do aluno. Com um ACR próprio, o pull sai pelo backbone da Azure e o problema
# desaparece.
#
# A versão anterior resolvia isso com um script (`setup-registry-aluno.sh`) que o
# aluno tinha de rodar ANTES do apply, mais um `source` para carregar variáveis.
# Na prática, esquecer qualquer um dos dois reproduzia exatamente o mesmo 409 —
# e a mensagem não dá nenhuma pista de que faltou um passo anterior.
# Trazer isso para dentro do Terraform elimina o pré-requisito: um `apply` só.
#
# Custo: ACR Basic ~US$ 0,17/dia, destruído junto com o lab.
# ---------------------------------------------------------------------------

resource "azurerm_container_registry" "acr" {
  name                = "acrqc04${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"

  # A conta admin do ACR é um par usuário/senha estático com acesso total ao
  # registry. Não é necessária: o ACI autentica por Managed Identity (AcrPull).
  admin_enabled = false

  tags = local.tags
}

# Identidade que o ACI usa para puxar a imagem. User-assigned porque precisa
# existir ANTES do container group, para receber o papel AcrPull.
resource "azurerm_user_assigned_identity" "aci" {
  name                = "id-aci-qc-aula04-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tags                = local.tags
}

resource "azurerm_role_assignment" "aci_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aci.principal_id
}

# Importa as imagens oficiais para o ACR do aluno.
#
# O `az acr import` copia servidor-a-servidor: nada trafega pelo Cloud Shell, e
# o pull da origem é feito pela Azure, não pelo IP compartilhado do ACI.
#
# O prefixo `library/` é OBRIGATÓRIO para imagens oficiais do Docker Hub. Sem
# ele a Azure procura um repositório de usuário chamado "mongo-express", que não
# existe, e o import falha com 401 UNAUTHORIZED.
resource "terraform_data" "importar_imagens" {
  triggers_replace = [azurerm_container_registry.acr.id]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -e
      echo "Importando imagens do MongoDB para ${azurerm_container_registry.acr.name}..."
      az acr import --name "${azurerm_container_registry.acr.name}" \
        --source docker.io/library/mongo:7.0 --image mongo:7.0 --force --output none
      az acr import --name "${azurerm_container_registry.acr.name}" \
        --source docker.io/library/mongo-express:1.0.2 --image mongo-express:1.0.2 --force --output none
      echo "Imagens importadas."
    EOT
  }

  depends_on = [azurerm_container_registry.acr]
}

resource "azurerm_container_group" "mongodb" {
  name                = "aci-qc-aula04-${random_string.sufixo.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  ip_address_type     = "Public"
  dns_name_label      = "qc-mongo-${random_string.sufixo.result}"
  os_type             = "Linux"
  tags                = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aci.id]
  }

  # Pull por Managed Identity: sem usuário, sem senha, nada no state.
  image_registry_credential {
    server                    = azurerm_container_registry.acr.login_server
    user_assigned_identity_id = azurerm_user_assigned_identity.aci.id
  }

  # Container 1: MongoDB 7.0
  container {
    name   = "mongodb"
    image  = "${azurerm_container_registry.acr.login_server}/mongo:7.0"
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
    image  = "${azurerm_container_registry.acr.login_server}/mongo-express:1.0.2"
    cpu    = 0.25
    memory = 0.5

    ports {
      port     = 8081
      protocol = "TCP"
    }

    environment_variables = {
      ME_CONFIG_MONGODB_URL = "mongodb://admin:${local.mongo_admin_pass}@localhost:27017"
      # Basic Auth desativado: Chrome 94+ bloqueia dialogs de Basic Auth em HTTP puro.
      # O MongoDB em si continua protegido por senha — esta interface é só para visualização no lab.
      ME_CONFIG_BASICAUTH            = "false"
      ME_CONFIG_MONGODB_ENABLE_ADMIN = "true"
      ME_CONFIG_SITE_SESSIONSECRET   = "QCsession2024!"
    }
  }

  # A imagem só existe depois do import, e o pull só funciona depois do AcrPull.
  depends_on = [
    terraform_data.importar_imagens,
    azurerm_role_assignment.aci_acr_pull,
  ]
}
