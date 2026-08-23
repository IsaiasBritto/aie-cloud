terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      # 4.x e obrigatorio: o lab usa azurerm_function_app_flex_consumption
      # (plano FC1), que nao existe na 3.x. O plano Y1 antigo nao serve porque
      # contas Azure for Students tem cota ZERO de Y1:
      #   401 Unauthorized ... Current Limit (Y1 VMs): 0
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.12"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

resource "random_string" "sufixo" {
  length  = 6
  upper   = false
  special = false
}

locals {
  tags = {
    aula         = "4"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    provisionado = "terraform"
  }
  mongo_admin_pass   = "QCadmin2024!"
  mongo_express_pass = "QCview2024!"

  # Prefixo das imagens do ACI. Vazio quando não há registry configurado — aí o
  # ACI puxa do Docker Hub público, sujeito ao rate limit anônimo de 100 pulls
  # por 6 h por IP (e o ACI sai por IPs compartilhados da região).
  image_prefix = var.registry_server == null ? "" : "${var.registry_server}/"
}

# Resource Group da Aula 4
resource "azurerm_resource_group" "rg" {
  name     = "rg-qc-aula04-${random_string.sufixo.result}"
  location = var.location
  tags     = local.tags
}

# Identidade do usuário autenticado (para RBAC no Key Vault)
data "azurerm_client_config" "current" {}
