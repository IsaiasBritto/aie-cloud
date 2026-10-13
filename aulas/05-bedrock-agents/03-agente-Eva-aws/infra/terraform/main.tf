# Eva na AWS: ECR + ECS Fargate + CloudWatch Logs (+ Secrets Manager se o
# provedor for openai). Mesmo papel do Container Apps + ACR + Key Vault + App
# Insights da versão Azure — cada peça com o seu equivalente.

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

  # FinOps: toda peça nasce marcada. Diferente do Azure, aqui a tag vai em
  # CADA recurso automaticamente — o default_tags faz a "herança" por nós.
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
  nome = "eva-${random_string.sufixo.result}"
  tags = {
    aula         = "5"
    disciplina   = "cloud-cognitive"
    projeto      = "eva"
    ambiente     = var.ambiente
    responsavel  = var.responsavel
    centro-custo = var.centro_custo
    provisionado = "terraform"
  }

  usa_openai = var.provedor == "openai"
  role_arn   = var.criar_role ? aws_iam_role.eva[0].arn : data.aws_iam_role.existente[0].arn
}

data "aws_caller_identity" "atual" {}

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
