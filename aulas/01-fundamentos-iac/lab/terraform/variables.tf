variable "region" {
  description = "Região da AWS (o Learner Lab libera us-east-1 e us-west-2)"
  type        = string
  default     = "us-east-1"
}

variable "stack_name" {
  description = "Valor da tag 'stack', usada pelo Resource Group para achar os recursos"
  type        = string
  default     = "iac-aula01"
}

variable "vm_name" {
  description = "Nome da instância EC2 (tag Name)"
  type        = string
  default     = "vm-lab-aula01"
}

variable "instance_type" {
  description = "Tipo da instância (o Learner Lab aceita de nano a large)"
  type        = string
  default     = "t3.micro"
}

variable "ssh_cidr" {
  description = "Origem liberada para SSH. 0.0.0.0/0 é didático — o exercício 3.1 restringe ao seu IP"
  type        = string
  default     = "0.0.0.0/0"
}

variable "ssh_public_key_path" {
  description = "Chave pública SSH usada no key pair (no CloudShell: ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}
