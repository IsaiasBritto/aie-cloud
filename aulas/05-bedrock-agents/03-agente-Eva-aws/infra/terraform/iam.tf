# Identidade da Eva.
#
# Learner Lab: não se cria role — usamos a LabRole como task role (credencial
# do código) e execution role (puxar imagem, ler segredo, escrever log).
#
# Conta comum (criar_role = true): uma role mínima. Em produção, separe as
# duas roles: a execution role não precisa de Bedrock, e a task role não
# precisa ler o segredo depois que o ECS já o injetou.

data "aws_iam_role" "existente" {
  count = var.criar_role ? 0 : 1
  name  = var.role_name
}

data "aws_iam_policy_document" "confia_ecs" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eva" {
  count              = var.criar_role ? 1 : 0
  name               = "${local.nome}-task"
  assume_role_policy = data.aws_iam_policy_document.confia_ecs.json
}

resource "aws_iam_role_policy_attachment" "execucao" {
  count      = var.criar_role ? 1 : 0
  role       = aws_iam_role.eva[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "eva" {
  statement {
    sid = "InvocaModelos"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      "arn:aws:bedrock:*::foundation-model/*",
      "arn:aws:bedrock:*:${data.aws_caller_identity.atual.account_id}:inference-profile/*",
    ]
  }

  dynamic "statement" {
    for_each = local.usa_openai ? [1] : []
    content {
      sid       = "LeChaveOpenAI"
      actions   = ["secretsmanager:GetSecretValue"]
      resources = [aws_secretsmanager_secret.openai[0].arn]
    }
  }
}

resource "aws_iam_role_policy" "eva" {
  count  = var.criar_role ? 1 : 0
  name   = "eva-minimo"
  role   = aws_iam_role.eva[0].id
  policy = data.aws_iam_policy_document.eva.json
}
