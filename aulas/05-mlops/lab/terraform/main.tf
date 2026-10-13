# Aula 5 — MLOps no Amazon SageMaker AI (AWS Academy Learner Lab)
#
# Compare com a versão Azure: lá era preciso um Workspace + Storage + Key Vault +
# App Insights + ACR + Compute Cluster antes do primeiro treino. No SageMaker não
# existe "workspace" a provisionar: o serviço já está na região. O que o
# Terraform cria é só o que é NOSSO:
#
#   - um bucket S3 (dados versionados, código do treino, artefatos dos modelos)
#   - o dataset produtos.csv dentro dele, com versionamento ligado
#   - um Model Package Group — o "Model Registry" do recomendador
#
# O compute do treino (ml.m5.large) e o do endpoint nascem e morrem por chamada
# de API: são o equivalente ao cluster com scale-to-zero, sem cluster nenhum.

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
      projeto      = "quantum-commerce"
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
  nome = "qc-aula05-${random_string.sufixo.result}"
}

# No Learner Lab não se cria role: o SageMaker executa treino e endpoint com a LabRole.
data "aws_iam_role" "lab" {
  name = "LabRole"
}

resource "aws_s3_bucket" "ml" {
  bucket        = "${local.nome}-ml"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "ml" {
  bucket                  = aws_s3_bucket.ml.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versionamento = o "Data Asset versionado" da versão Azure. Cada upload do
# produtos.csv vira uma versão nova, com ID — e o job registra qual usou.
resource "aws_s3_bucket_versioning" "ml" {
  bucket = aws_s3_bucket.ml.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "produtos" {
  bucket = aws_s3_bucket.ml.id
  key    = "dados/produtos/produtos.csv"
  source = "${path.module}/../../../02-storage-bancos/lab/data/produtos.csv"
  etag   = filemd5("${path.module}/../../../02-storage-bancos/lab/data/produtos.csv")

  depends_on = [aws_s3_bucket_versioning.ml]
}

# O Model Registry: um grupo por modelo, uma versão por registro.
resource "aws_sagemaker_model_package_group" "recomendador" {
  model_package_group_name        = "recomendador-qc-${random_string.sufixo.result}"
  model_package_group_description = "Recomendador content-based da Quantum Commerce (Aula 5)"
}
