# Outputs consumidos pelo guia e pelos scripts Python (export VAR=$(terraform output -raw ...))

output "bucket_name" {
  description = "Bucket S3 da QC (prefixos catalogo/, imagens/, logs/)"
  value       = aws_s3_bucket.qc.bucket
}

output "secret_id" {
  description = "Segredo com a connection string do PostgreSQL"
  value       = aws_secretsmanager_secret.postgres.name
}

output "mongo_secret_id" {
  description = "Segredo com as credenciais do MongoDB"
  value       = aws_secretsmanager_secret.mongo.name
}

output "dynamodb_table" {
  description = "Tabela DynamoDB de reviews (chave produto_id + review_id)"
  value       = aws_dynamodb_table.reviews.name
}

output "db_endpoint" {
  description = "Host do RDS PostgreSQL"
  value       = aws_db_instance.qc.address
}

output "db_name" {
  description = "Banco de dados do RDS"
  value       = aws_db_instance.qc.db_name
}

output "mongodb_public_ip" {
  description = "IP público da EC2 com MongoDB"
  value       = aws_instance.mongo.public_ip
}

output "mongo_express_url" {
  description = "Interface web do MongoDB (usuário qcadmin; leva ~2 min após o apply)"
  value       = "http://${aws_instance.mongo.public_ip}:8081"
}

output "meu_ip" {
  description = "IP do CloudShell liberado no RDS e no Mongo"
  value       = local.meu_ip_cidr
}
