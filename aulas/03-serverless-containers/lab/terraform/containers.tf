# ECR guarda a imagem do container FastAPI; o ECS Fargate roda a imagem.
# O serviço só nasce com ecs_enabled = true (a imagem precisa existir antes).

resource "aws_ecr_repository" "produtos_api" {
  name                 = "produtos-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # destroy apaga o repositório mesmo com imagens

  image_scanning_configuration {
    scan_on_push = true
  }
}

# FinOps: guarda só as 5 imagens mais recentes
resource "aws_ecr_lifecycle_policy" "produtos_api" {
  repository = aws_ecr_repository.produtos_api.name
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

resource "aws_ecs_cluster" "qc" {
  name = "${local.nome}-cluster"
}

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.nome}/produtos-api"
  retention_in_days = 7
}

resource "aws_security_group" "api" {
  name        = "${local.nome}-api"
  description = "Porta 8080 da API de produtos"
  vpc_id      = data.aws_vpc.padrao.id

  ingress {
    description = "API FastAPI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "produtos_api" {
  family                   = "${local.nome}-produtos-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256" # 0,25 vCPU
  memory                   = "512" # 0,5 GB
  execution_role_arn       = data.aws_iam_role.lab.arn # puxa a imagem e escreve logs
  task_role_arn            = data.aws_iam_role.lab.arn # credencial do código (lê o S3)

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([{
    name         = "produtos-api"
    image        = "${aws_ecr_repository.produtos_api.repository_url}:${var.image_tag}"
    essential    = true
    portMappings = [{ containerPort = 8080, protocol = "tcp" }]
    environment = [
      { name = "BUCKET_NAME", value = aws_s3_bucket.catalogo.bucket },
      { name = "CSV_KEY", value = aws_s3_object.produtos.key },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.ecs.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "api"
      }
    }
  }])
}

resource "aws_ecs_service" "produtos_api" {
  count = var.ecs_enabled ? 1 : 0

  name            = "produtos-api"
  cluster         = aws_ecs_cluster.qc.id
  task_definition = aws_ecs_task_definition.produtos_api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.padrao.ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true # sem load balancer: a tarefa ganha IP público próprio
  }
}
