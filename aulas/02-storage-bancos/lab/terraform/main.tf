terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      # 4.x e obrigatorio: o codigo usa free_tier_enabled (cosmos) e
      # partition_key_paths (container), que nao existem na 3.x.
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4"
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
      # Permite recriar o Key Vault com o mesmo nome logo apos um destroy,
      # sem esperar os 7 dias de soft delete.
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
    aula         = "2"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    provisionado = "terraform"
  }
  mongo_admin_pass = "QCadmin2024!"
}

# Resource Group da Aula 2
resource "azurerm_resource_group" "rg" {
  name     = "rg-qc-aula02-${random_string.sufixo.result}"
  location = var.location
  tags     = local.tags
}

# Objeto do usuário autenticado (usado para conceder RBAC no Key Vault/Cosmos/Search)
data "azurerm_client_config" "current" {}
