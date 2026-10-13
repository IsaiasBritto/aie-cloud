output "bucket" {
  description = "Bucket com dados, código e modelos"
  value       = aws_s3_bucket.ml.bucket
}

output "dados_s3_uri" {
  description = "Prefixo do canal de treino (o job monta tudo que está aqui)"
  value       = "s3://${aws_s3_bucket.ml.bucket}/dados/produtos/"
}

output "dados_versao" {
  description = "VersionId do produtos.csv usado — a 'versão do Data Asset'"
  value       = aws_s3_object.produtos.version_id
}

output "model_package_group" {
  description = "Nome do grupo no Model Registry"
  value       = aws_sagemaker_model_package_group.recomendador.model_package_group_name
}

output "role_arn" {
  description = "Role de execução do SageMaker (LabRole)"
  value       = data.aws_iam_role.lab.arn
}

output "sufixo" {
  value = random_string.sufixo.result
}
