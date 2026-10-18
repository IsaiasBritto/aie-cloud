# Bucket do CATÁLOGO da QC — criado NESTA aula (a Aula 3 não depende da Aula 2)
resource "aws_s3_bucket" "catalogo" {
  bucket        = "${local.nome}-catalogo"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "catalogo" {
  bucket                  = aws_s3_bucket.catalogo.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Sobe o produtos.csv no apply — sem passo de upload manual
resource "aws_s3_object" "produtos" {
  bucket       = aws_s3_bucket.catalogo.id
  key          = "catalogo/produtos.csv"
  source       = "${path.module}/../data/produtos.csv"
  etag         = filemd5("${path.module}/../data/produtos.csv")
  content_type = "text/csv"
}
