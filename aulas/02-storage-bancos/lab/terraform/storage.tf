# Bucket S3 — base de tudo da QC (equivale ao Storage Account + containers)
resource "aws_s3_bucket" "qc" {
  bucket        = local.nome
  force_destroy = true # o destroy apaga o bucket mesmo com objetos (é lab!)
}

# Nada público: bloqueia ACL e policy públicas
resource "aws_s3_bucket_public_access_block" "qc" {
  bucket                  = aws_s3_bucket.qc.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Criptografia em repouso com chave gerenciada pelo S3
resource "aws_s3_bucket_server_side_encryption_configuration" "qc" {
  bucket = aws_s3_bucket.qc.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Os 3 "containers" viram prefixos. No S3 não existe pasta: o objeto vazio
# terminado em "/" só serve para o prefixo aparecer no console.
resource "aws_s3_object" "prefixos" {
  for_each = toset(["catalogo/", "imagens/", "logs/"])
  bucket   = aws_s3_bucket.qc.id
  key      = each.value
  content  = ""
}

# Lifecycle: logs migram para classes mais baratas e expiram em 1 ano
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.qc.id

  rule {
    id     = "logs-lifecycle"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}
