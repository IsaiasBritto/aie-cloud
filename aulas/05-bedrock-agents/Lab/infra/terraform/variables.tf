variable "region" {
  description = "Região AWS (no Learner Lab, us-east-1)"
  type        = string
  default     = "us-east-1"
}

variable "role_name" {
  description = "Role usada pela tarefa (Learner Lab: LabRole)"
  type        = string
  default     = "LabRole"
}

variable "servico_ativo" {
  description = "Cria o serviço ECS. Fica false até as imagens existirem no ECR."
  type        = bool
  default     = false
}

variable "versao" {
  description = "Etiqueta das imagens no ECR. Nunca 'latest'."
  type        = string
  default     = "v1"
}

variable "retencao_dias" {
  description = "LGPD: em quantos dias o S3 apaga sozinho imagens e resultados"
  type        = number
  default     = 7
}

variable "limiar_confianca" {
  description = "Regra de decisão (0 a 1). Quem define é a área de risco."
  type        = string
  default     = "0.60"
}

variable "cidr_acesso" {
  description = "Quem pode abrir a interface (8501) e a API (8000)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "responsavel" {
  description = "Tag FinOps: quem responde por este ambiente (seu RM)"
  type        = string
  default     = "aluno"
}
