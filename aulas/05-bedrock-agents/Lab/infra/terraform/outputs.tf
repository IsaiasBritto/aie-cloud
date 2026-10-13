output "bucket" {
  description = "Use em ARMAZENAMENTO_BUCKET no .env para rodar local"
  value       = aws_s3_bucket.deteccoes.bucket
}

output "ecr_api" {
  value = aws_ecr_repository.app["api"].repository_url
}

output "ecr_web" {
  value = aws_ecr_repository.app["web"].repository_url
}

output "cluster" {
  value = aws_ecs_cluster.deva3.name
}

output "servico" {
  value = var.servico_ativo ? aws_ecs_service.deva3[0].name : "(servico_ativo = false)"
}

output "log_group" {
  value = aws_cloudwatch_log_group.deva3.name
}
