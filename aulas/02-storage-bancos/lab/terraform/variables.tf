variable "region" {
  description = "Região da AWS (o Learner Lab libera us-east-1 e us-west-2)"
  type        = string
  default     = "us-east-1"
}

variable "db_password" {
  description = "Senha do usuário master do RDS. Gere com: openssl rand -hex 16 (o RDS não aceita / @ \" e espaço)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 8 && can(regex("^[^/@\" ]+$", var.db_password))
    error_message = "A senha precisa ter 8+ caracteres e não pode conter / @ \" ou espaço."
  }
}

variable "mongo_password" {
  description = "Senha do admin do MongoDB (lab). Fica no Secrets Manager; o Terraform só a injeta na EC2"
  type        = string
  sensitive   = true
  default     = "QCadmin2024!"
}

variable "mongo_instance_type" {
  description = "Tipo da EC2 do MongoDB (MongoDB 7 pede ~1 GB livre de RAM)"
  type        = string
  default     = "t3.small"
}

variable "mongo_ui_cidr" {
  description = "Origem liberada para o Mongo Express (porta 8081). Para restringir ao seu navegador: \"<seu-ip>/32\""
  type        = string
  default     = "0.0.0.0/0"
}

variable "mongo_ui_password" {
  description = "Senha do Mongo Express (usuário qcadmin)"
  type        = string
  sensitive   = true
  default     = "QCview2024!"
}
