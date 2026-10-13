# Bucket de dados do lab (áudios e imagens) — independente das aulas anteriores
resource "aws_s3_bucket" "data" {
  bucket        = "${local.nome}-dados"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "prefixos" {
  for_each = toset(["audios/", "imagens/"])
  bucket   = aws_s3_bucket.data.id
  key      = each.value
  content  = ""
}
