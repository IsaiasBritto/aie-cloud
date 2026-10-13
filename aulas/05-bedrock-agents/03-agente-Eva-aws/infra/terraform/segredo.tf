# Só existe com provedor = openai. É o equivalente ao Key Vault da versão
# Azure: a chave mora aqui, e o ECS a entrega ao container como variável de
# ambiente na partida (bloco `secrets` da task definition). Ela não aparece
# na imagem, no código nem no console do ECS.
#
# Ressalva honesta: como o valor passa pelo Terraform, ele fica no tfstate.
# Para a aula serve; em produção, crie o segredo fora do Terraform
# (aws secretsmanager put-secret-value) e referencie só o ARN.

resource "aws_secretsmanager_secret" "openai" {
  count                   = local.usa_openai ? 1 : 0
  name                    = "${local.nome}/openai-api-key"
  description             = "Chave da OpenAI usada pela Eva (provedor openai)"
  recovery_window_in_days = 0 # destroy apaga na hora (aula)
}

resource "aws_secretsmanager_secret_version" "openai" {
  count         = local.usa_openai ? 1 : 0
  secret_id     = aws_secretsmanager_secret.openai[0].id
  secret_string = var.openai_api_key

  lifecycle {
    precondition {
      condition     = length(var.openai_api_key) > 0
      error_message = "provedor = openai exige a chave: export TF_VAR_openai_api_key=sk-..."
    }
  }
}
