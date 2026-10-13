terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

resource "random_string" "sufixo" {
  length  = 6
  upper   = false
  special = false
}

locals {
  nome = "qc-aula04-${random_string.sufixo.result}"
  tags = {
    aula         = "4"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    provisionado = "terraform"
  }
  # Credenciais do MongoDB do LAB. Ficam no Secrets Manager para a Lambda;
  # o semear_reviews.py as tem no código DE PROPÓSITO (é o exercício de segurança).
  mongo_admin_pass   = "QCadmin2024!"
  mongo_express_pass = "QCview2024!"
}

# No Learner Lab não se cria IAM role: a Lambda usa a LabRole
data "aws_iam_role" "lab" {
  name = "LabRole"
}

data "aws_vpc" "padrao" {
  default = true
}

# Nada a criar para Transcribe, Polly, Comprehend e Rekognition:
# são APIs da conta, liberadas por IAM (a LabRole já tem acesso).
