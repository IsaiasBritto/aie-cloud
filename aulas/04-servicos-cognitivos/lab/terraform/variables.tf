variable "region" {
  description = "Região da AWS (o Learner Lab libera us-east-1 e us-west-2)"
  type        = string
  default     = "us-east-1"
}

variable "mongo_instance_type" {
  description = "Tipo da EC2 do MongoDB"
  type        = string
  default     = "t3.small"
}
