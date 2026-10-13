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
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

# Sufixo aleatório: nomes de bucket são globais, e vários alunos rodam o mesmo código
resource "random_string" "sufixo" {
  length  = 6
  upper   = false
  special = false
}

locals {
  nome = "qc-aula02-${random_string.sufixo.result}"
  tags = {
    aula         = "2"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    provisionado = "terraform"
  }
}

# Rede: VPC padrão do Learner Lab
data "aws_vpc" "padrao" {
  default = true
}

# IP público de saída do CloudShell — usado para liberar o RDS e o Mongo só para você.
# Se você abrir um CloudShell novo e o IP mudar, rode terraform apply de novo.
data "http" "meu_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  meu_ip_cidr = "${chomp(data.http.meu_ip.response_body)}/32"
}
