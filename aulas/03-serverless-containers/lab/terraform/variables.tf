variable "region" {
  description = "Região da AWS (o Learner Lab libera us-east-1 e us-west-2)"
  type        = string
  default     = "us-east-1"
}

variable "ecs_enabled" {
  description = "Quando true, cria o serviço ECS Fargate. Deixe false no primeiro apply: a imagem precisa estar no ECR antes"
  type        = bool
  default     = false
}

variable "image_tag" {
  description = "Tag da imagem no ECR usada pela tarefa Fargate"
  type        = string
  default     = "v1"
}
