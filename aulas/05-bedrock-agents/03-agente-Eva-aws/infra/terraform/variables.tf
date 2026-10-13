variable "region" {
  description = "Região AWS (no Learner Lab, us-east-1)"
  type        = string
  default     = "us-east-1"
}

variable "provedor" {
  description = "bedrock (task role, sem chave) ou openai (chave no Secrets Manager — use no Learner Lab)"
  type        = string
  default     = "bedrock"

  validation {
    condition     = contains(["bedrock", "openai"], var.provedor)
    error_message = "provedor deve ser bedrock ou openai."
  }
}

variable "bedrock_model_id" {
  description = "Model ID ou perfil de inferência do Bedrock"
  type        = string
  default     = "us.amazon.nova-lite-v1:0"
}

variable "openai_model" {
  description = "Modelo da OpenAI (só com provedor = openai)"
  type        = string
  default     = "gpt-4o-mini"
}

variable "openai_api_key" {
  description = "Chave da OpenAI. Passe por TF_VAR_openai_api_key, nunca em arquivo."
  type        = string
  default     = ""
  sensitive   = true
}

variable "role_name" {
  description = "Role existente usada como task role e execution role (Learner Lab: LabRole)"
  type        = string
  default     = "LabRole"
}

variable "criar_role" {
  description = "true numa conta comum: cria uma role mínima para a Eva (o Learner Lab não permite)"
  type        = bool
  default     = false
}

variable "ecs_enabled" {
  description = "Cria o serviço ECS. Fica false até a imagem existir no ECR."
  type        = bool
  default     = false
}

variable "image_tag" {
  description = "Tag da imagem no ECR"
  type        = string
  default     = "latest"
}

variable "cidr_acesso" {
  description = "Quem pode abrir a Eva na porta 8501"
  type        = string
  default     = "0.0.0.0/0"
}

variable "preco_entrada_por_1m" {
  description = "USD por 1 milhão de tokens de entrada do modelo escolhido (0 = custo zerado no log)"
  type        = string
  default     = "0"
}

variable "preco_saida_por_1m" {
  description = "USD por 1 milhão de tokens de saída do modelo escolhido"
  type        = string
  default     = "0"
}

variable "ambiente" {
  description = "Tag FinOps: ambiente"
  type        = string
  default     = "aula"
}

variable "responsavel" {
  description = "Tag FinOps: quem responde por este ambiente (seu RM ou usuário)"
  type        = string
  default     = "aluno"
}

variable "centro_custo" {
  description = "Tag FinOps: centro de custo"
  type        = string
  default     = "mba-fiap"
}
