# Outputs consumidos pelo guia, pelos scripts e pelo app (exportar-outputs.sh)

output "data_bucket_name" {
  description = "Bucket de dados (prefixos audios/ e imagens/)"
  value       = aws_s3_bucket.data.bucket
}

output "lambda_name" {
  description = "Nome da Lambda (aws lambda update-function-code)"
  value       = aws_lambda_function.cognitivo.function_name
}

output "function_url" {
  description = "URL HTTPS da Lambda (termina com /)"
  value       = aws_lambda_function_url.cognitivo.function_url
}

output "mongodb_public_ip" {
  description = "IP público da EC2 com MongoDB"
  value       = aws_instance.mongo.public_ip
}

output "mongo_express_url" {
  description = "Mongo Express (usuário qcadmin, senha QCview2024!) — ~2 min após o apply"
  value       = "http://${aws_instance.mongo.public_ip}:8081"
}

output "mongo_secret_id" {
  description = "Segredo com a URI do MongoDB (lido pela Lambda)"
  value       = aws_secretsmanager_secret.mongo.name
}
