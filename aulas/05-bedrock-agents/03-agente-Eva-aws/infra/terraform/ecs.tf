# ECR guarda a imagem; o ECS Fargate roda; o CloudWatch Logs recebe o stdout —
# inclusive as linhas JSON de telemetria (evento = "eva.chamada_modelo").

resource "aws_ecr_repository" "eva" {
  name                 = "${local.nome}-app"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "eva" {
  repository = aws_ecr_repository.eva.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Mantém as 5 imagens mais recentes"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# Retenção explícita: o padrão do CloudWatch é "nunca expira" — custo que
# cresce em silêncio. 7 dias bastam para a aula e para o Lab de FinOps.
resource "aws_cloudwatch_log_group" "eva" {
  name              = "/ecs/eva/${random_string.sufixo.result}"
  retention_in_days = 7
}

resource "aws_ecs_cluster" "eva" {
  name = "${local.nome}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled" # ligado cobra métricas extras; a telemetria da Eva já cobre o essencial
  }
}

resource "aws_security_group" "eva" {
  name        = "${local.nome}-web"
  description = "Porta 8501 do Streamlit da Eva"
  vpc_id      = data.aws_vpc.padrao.id

  ingress {
    description = "Streamlit"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = [var.cidr_acesso]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

locals {
  ambiente_container = [
    { name = "EVA_PROVEDOR", value = var.provedor },
    { name = "AWS_REGION", value = var.region },
    { name = "BEDROCK_MODEL_ID", value = var.bedrock_model_id },
    { name = "OPENAI_MODEL", value = var.openai_model },
    { name = "EVA_TELEMETRIA", value = "stdout" },
    { name = "EVA_PRECO_ENTRADA_POR_1M", value = var.preco_entrada_por_1m },
    { name = "EVA_PRECO_SAIDA_POR_1M", value = var.preco_saida_por_1m },
  ]
}

resource "aws_ecs_task_definition" "eva" {
  family                   = "${local.nome}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"          # 0,5 vCPU — o Streamlit sofre com 0,25
  memory                   = "1024"         # 1 GB
  execution_role_arn       = local.role_arn # puxa imagem, lê o segredo, escreve log
  task_role_arn            = local.role_arn # credencial do código: chama o Bedrock

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([{
    name         = "eva"
    image        = "${aws_ecr_repository.eva.repository_url}:${var.image_tag}"
    essential    = true
    portMappings = [{ containerPort = 8501, protocol = "tcp" }]
    environment  = local.ambiente_container

    # A chave entra por referência ao ARN: o agente do ECS busca o valor na
    # partida. Quem lê a task definition vê o ARN, nunca a chave.
    secrets = local.usa_openai ? [
      { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai[0].arn }
    ] : []

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.eva.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "eva"
      }
    }
  }])

  depends_on = [aws_secretsmanager_secret_version.openai]
}

resource "aws_ecs_service" "eva" {
  count = var.ecs_enabled ? 1 : 0

  name            = "eva"
  cluster         = aws_ecs_cluster.eva.id
  task_definition = aws_ecs_task_definition.eva.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  # Em aula não há tráfego a preservar: troca a tarefa sem subir a nova em
  # paralelo (economiza minutos e uma tarefa duplicada cobrando).
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  network_configuration {
    subnets          = data.aws_subnets.padrao.ids
    security_groups  = [aws_security_group.eva.id]
    assign_public_ip = true # sem load balancer: a tarefa ganha IP público próprio
  }
}
