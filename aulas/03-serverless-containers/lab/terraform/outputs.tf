output "bucket_name" {
  description = "Bucket do catálogo (já com catalogo/produtos.csv)"
  value       = aws_s3_bucket.catalogo.bucket
}

output "lambda_name" {
  description = "Nome da função Lambda (usar no aws lambda update-function-code)"
  value       = aws_lambda_function.catalogo.function_name
}

output "function_url" {
  description = "URL HTTPS da função (termina com /)"
  value       = aws_lambda_function_url.catalogo.function_url
}

output "ecr_repository_url" {
  description = "Repositório ECR (destino do docker push)"
  value       = aws_ecr_repository.produtos_api.repository_url
}

output "ecs_cluster_name" {
  description = "Cluster ECS"
  value       = aws_ecs_cluster.qc.name
}

output "ecs_service_name" {
  description = "Serviço ECS quando habilitado"
  value       = var.ecs_enabled ? aws_ecs_service.produtos_api[0].name : "ECS desabilitado — depois do docker push, rode: terraform apply -var=\"ecs_enabled=true\""
}
