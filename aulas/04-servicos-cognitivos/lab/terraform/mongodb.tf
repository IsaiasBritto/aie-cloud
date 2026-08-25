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
# do aluno.
#
# A versão anterior resolvia isso com um script (`setup-registry-aluno.sh`) que o
# aluno tinha de rodar ANTES do apply, mais um `source` para carregar variáveis.
# Na prática, esquecer qualquer um dos dois reproduzia exatamente o mesmo 409 —
# e a mensagem não dá nenhuma pista de que faltou um passo anterior.
# Trazer isso para dentro do Terraform elimina o pré-requisito: um `apply` só.
#
# ATENÇÃO — o ACR sozinho NÃO resolve o limite do Docker Hub.
#
# Este arquivo já afirmou que "com um ACR próprio o pull sai pelo backbone da
# Azure e o problema desaparece". Está errado, e o erro reaparece assim:
#
#   ERROR: (InvalidParameters) ... An error occurred when getting manifest.
#   StatusCode: 429, TOOMANYREQUESTS: You have reached your unauthenticated
#   pull rate limit.
#
# O `az acr import` continua fazendo um pull ANÔNIMO do Docker Hub — só que a
# partir do IP de saída do serviço ACR daquela região, também compartilhado.
# Trocamos um IP compartilhado por outro. A cota some do ACI e aparece no ACR.
#
# A saída real é não depender do Docker Hub no momento do lab: as imagens são
# espelhadas UMA VEZ para o GHCR do professor (workflow
# `.github/workflows/espelhar-imagens-mongo.yml`) e o import puxa de lá.
# Package público do GHCR não tem limite de pull anônimo.
#
# O ACR continua no lab por valor didático — é ele que exercita AcrPull por
# Managed Identity, sem usuário nem senha em lugar nenhum.
#
# Custo: ACR Basic ~US$ 0,17/dia, destruído junto com o lab.
# ---------------------------------------------------------------------------

# Declarada AQUI, e não em variables.tf, de propósito: este arquivo não deve
# depender de nenhum outro para funcionar. Aluno que copia um .tf solto para o
# Cloud Shell não deve receber "Reference to undeclared variable".
variable "registry_espelho" {
  description = <<-EOT
    Registry público de onde as imagens do Mongo são importadas para o ACR.
    Precisa conter `mongo:7.0` e `mongo-express:1.0.2` como packages PÚBLICOS.
    Publique com o workflow `espelhar-imagens-mongo.yml` e ajuste o owner aqui.
  EOT
  type        = string
  default     = "ghcr.io/isaiasbritto"
}

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

# Importa as imagens para o ACR do aluno, em três degraus:
#
#   1. já está no ACR?  -> não faz nada (reaplicar não consome cota de ninguém)
#   2. espelho no GHCR  -> caminho normal, sem limite de pull
#   3. Docker Hub       -> reserva, com 3 tentativas, para quem ainda não
#                          publicou o espelho
#
# O degrau 1 é o que mais importa no dia a dia: sem ele, cada `terraform apply`
# repetido durante a depuração queimava mais 2 pulls da cota compartilhada da
# região — o próprio ciclo de tentativa e erro alimentava o 429.
#
# No degrau 3, o prefixo `library/` é OBRIGATÓRIO para imagens oficiais do
# Docker Hub. Sem ele a Azure procura um repositório de usuário chamado
# "mongo-express", que não existe, e o import falha com 401 UNAUTHORIZED.
resource "terraform_data" "importar_imagens" {
  triggers_replace = [azurerm_container_registry.acr.id]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -euo pipefail

      ACR="${azurerm_container_registry.acr.name}"
      ESPELHO="${var.registry_espelho}"

      importar() {
        origem_espelho="$1"
        origem_hub="$2"
        destino="$3"

        if az acr repository show --name "$ACR" --image "$destino" --output none 2>/dev/null; then
          echo "  $destino ja esta no registry."
          return 0
        fi

        echo "  importando $destino de $origem_espelho ..."
        if az acr import --name "$ACR" --source "$origem_espelho" \
             --image "$destino" --force --output none 2>/dev/null; then
          echo "  ok (espelho)."
          return 0
        fi

        echo "  espelho indisponivel; tentando o Docker Hub ..."
        for tentativa in 1 2 3; do
          if az acr import --name "$ACR" --source "$origem_hub" \
               --image "$destino" --force --output none; then
            echo "  ok (Docker Hub, tentativa $tentativa)."
            return 0
          fi
          # `if` e nao `[ ... ] && ...`: sob `set -e`, um teste que devolve 1
          # no fim do corpo do laco encerraria o script antes da mensagem final.
          if [ "$tentativa" -lt 3 ]; then
            echo "  falhou; aguardando 30 s ..."
            sleep 30
          fi
        done

        {
          echo ""
          echo "Nao foi possivel importar $destino."
          echo ""
          echo "Se o erro cita TOOMANYREQUESTS, o limite anonimo do Docker Hub"
          echo "(100 pulls / 6 h por IP) foi atingido pelo IP de saida compartilhado"
          echo "da regiao. A cota nao e sua: trocar de assinatura nao resolve."
          echo ""
          echo "Saida: o professor roda o workflow 'Espelhar imagens do Mongo no GHCR'"
          echo "e torna os dois packages publicos; depois confirme que"
          echo "var.registry_espelho aponta para esse owner (hoje: $ESPELHO)."
        } >&2
        return 1
      }

      echo "Registry: $ACR"
      importar "$ESPELHO/mongo:7.0" \
               "docker.io/library/mongo:7.0" \
               "mongo:7.0"
      importar "$ESPELHO/mongo-express:1.0.2" \
               "docker.io/library/mongo-express:1.0.2" \
               "mongo-express:1.0.2"
      echo "Imagens prontas."
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
