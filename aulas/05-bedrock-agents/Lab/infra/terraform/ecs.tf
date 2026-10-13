# Uma tarefa, dois containers: a API (8000) e a interface (8501).
# No modo de rede awsvpc os containers da mesma tarefa compartilham a placa de
# rede — a interface fala com a API por localhost:8000, sem service discovery.

resource "aws_ecr_repository" "app" {
  for_each             = toset(["api", "web"])
  name                 = "${local.nome}-${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  for_each   = aws_ecr_repository.app
  repository = each.value.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Mantém as 5 imagens mais recentes"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 5 }
      action       = { type = "expire" }
    }]
  })
}

resource "aws_cloudwatch_log_group" "deva3" {
  name              = "/ecs/${local.nome}"
  retention_in_days = 7
}

resource "aws_ecs_cluster" "deva3" {
  name = "${local.nome}-cluster"
}

resource "aws_security_group" "deva3" {
  name        = "${local.nome}-web"
  description = "Interface (8501) e API (8000) do Deva3"
  vpc_id      = data.aws_vpc.padrao.id

  ingress {
    description = "Interface Streamlit"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = [var.cidr_acesso]
  }

  ingress {
    description = "API FastAPI (/docs)"
    from_port   = 8000
    to_port     = 8000
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
  log = {
    logDriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.deva3.name
      awslogs-region        = var.region
      awslogs-stream-prefix = "deva3"
    }
  }
}

resource "aws_ecs_task_definition" "deva3" {
  family                   = "${local.nome}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = data.aws_iam_role.lab.arn
  task_role_arn            = data.aws_iam_role.lab.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name         = "api"
      image        = "${aws_ecr_repository.app["api"].repository_url}:${var.versao}"
      essential    = true
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      # Nenhuma chave: Rekognition e S3 usam a task role.
      environment = [
        { name = "AMBIENTE", value = "aws-ecs" },
        { name = "AWS_REGION", value = var.region },
        { name = "ARMAZENAMENTO_BUCKET", value = aws_s3_bucket.deteccoes.bucket },
        { name = "ARMAZENAMENTO_PREFIXO", value = "deteccoes" },
        { name = "PERSISTIR_IMAGENS", value = "true" },
        { name = "LIMIAR_CONFIANCA", value = var.limiar_confianca },
      ]
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request;urllib.request.urlopen('http://localhost:8000/saude',timeout=4)\""]
        interval    = 15
        timeout     = 5
        retries     = 3
        startPeriod = 20
      }
      logConfiguration = local.log
    },
    {
      name         = "web"
      image        = "${aws_ecr_repository.app["web"].repository_url}:${var.versao}"
      essential    = true
      portMappings = [{ containerPort = 8501, protocol = "tcp" }]
      environment = [
        { name = "API_URL", value = "http://localhost:8000" },
      ]
      # A interface só sobe depois que a API responde /saude.
      dependsOn        = [{ containerName = "api", condition = "HEALTHY" }]
      logConfiguration = local.log
    },
  ])
}

resource "aws_ecs_service" "deva3" {
  count = var.servico_ativo ? 1 : 0

  name            = "deva3"
  cluster         = aws_ecs_cluster.deva3.id
  task_definition = aws_ecs_task_definition.deva3.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  network_configuration {
    subnets          = data.aws_subnets.padrao.ids
    security_groups  = [aws_security_group.deva3.id]
    assign_public_ip = true
  }
}
