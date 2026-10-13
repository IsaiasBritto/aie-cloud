# Deva3 na AWS: S3 + ECR (2 repositórios) + ECS Fargate (1 tarefa, 2 containers)
# + CloudWatch Logs. O Rekognition não se provisiona: é API pronta, cobrada
# por imagem — a tarefa só precisa de permissão para chamá-lo (LabRole).

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
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      aula         = "5"
      disciplina   = "cloud-cognitive"
      projeto      = "deva3"
      responsavel  = var.responsavel
      dado-pessoal = "biometrico" # LGPD: marca o que guarda dado sensível
      provisionado = "terraform"
    }
  }
}

resource "random_string" "sufixo" {
  length  = 6
  upper   = false
  special = false
}

locals {
  nome = "deva3-${random_string.sufixo.result}"
}

# Learner Lab: não se cria role. A LabRole é task role (Rekognition, S3) e
# execution role (puxar imagem, escrever log).
data "aws_iam_role" "lab" {
  name = var.role_name
}

data "aws_vpc" "padrao" {
  default = true
}

data "aws_subnets" "padrao" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.padrao.id]
  }
  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}
