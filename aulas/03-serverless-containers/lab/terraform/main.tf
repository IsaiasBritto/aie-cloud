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
  nome = "qc-aula03-${random_string.sufixo.result}"
  tags = {
    aula         = "3"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    provisionado = "terraform"
  }
}

# No Learner Lab não se cria IAM role: Lambda e ECS usam a LabRole existente
data "aws_iam_role" "lab" {
  name = "LabRole"
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
