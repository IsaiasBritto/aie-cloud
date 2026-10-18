# Credenciais do MongoDB para a Lambda — lidas em runtime, nunca no código da função
resource "aws_secretsmanager_secret" "mongo" {
  name                    = "${local.nome}/mongo"
  description             = "Conexão do MongoDB da Aula 4 (usada pela Lambda)"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "mongo" {
  secret_id = aws_secretsmanager_secret.mongo.id
  secret_string = jsonencode({
    uri      = "mongodb://admin:${urlencode(local.mongo_admin_pass)}@${aws_instance.mongo.public_ip}:27017/?authSource=admin"
    username = "admin"
    password = local.mongo_admin_pass
    host     = aws_instance.mongo.public_ip
  })
}
