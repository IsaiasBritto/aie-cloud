output "ecr_repository_url" {
  value = aws_ecr_repository.eva.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.eva.name
}

output "ecs_service_name" {
  value = var.ecs_enabled ? aws_ecs_service.eva[0].name : "(ecs_enabled = false)"
}

output "log_group_name" {
  description = "Onde caem os logs e a telemetria da Eva"
  value       = aws_cloudwatch_log_group.eva.name
}

output "task_role_arn" {
  value = local.role_arn
}

output "provedor" {
  value = var.provedor
}

output "segredo_openai" {
  value = local.usa_openai ? aws_secretsmanager_secret.openai[0].name : "(não usado: provedor bedrock)"
}
