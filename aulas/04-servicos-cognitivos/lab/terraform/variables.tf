variable "location" {
  description = "Região do Azure onde os recursos serão provisionados"
  type        = string
  default     = "eastus2"
  # Padrão da disciplina: eastus2.
  # Vision 4.0 Caption não disponível em eastus2 — lab usa Tags + OCR + Objects.
  # Para Caption completo: eastus, westus2, westeurope (verificar política da conta).
  # Azure for Students bloqueia eastus e brazilsouth para a maioria dos recursos.
}

# ---------------------------------------------------------------------------
# Registry das imagens do MongoDB (mesmo padrão da Aula 2).
#
# Sem estas variáveis o ACI puxa do Docker Hub público, o que funciona em uso
# individual mas falha quando a turma roda junto:
#
#   409 RegistryErrorResponse: An error response is received from the docker
#   registry 'index.docker.io'. Please retry later.
#
# O limite anônimo é de 100 pulls por 6 h POR IP, e o ACI sai por IPs de saída
# compartilhados da região — então a cota é da turma inteira, não sua.
#
# Reaproveite o ACR criado na Aula 2 (ele fica em rg-qc-registry, fora do RG do
# lab, e sobrevive ao destroy):
#
#   source ~/.qc-registry.env
#
# Se o arquivo não existir mais:
#   bash ~/aie-cloud/aulas/02-storage-bancos/lab/terraform/setup-registry-aluno.sh
# ---------------------------------------------------------------------------

variable "registry_server" {
  description = "Ex: meuacr.azurecr.io. Null = Docker Hub público."
  type        = string
  default     = null
}

variable "registry_user" {
  description = "Usuário do registry. Null = pull anônimo."
  type        = string
  sensitive   = true
  default     = null
}

variable "registry_password" {
  description = "Senha ou token do registry."
  type        = string
  sensitive   = true
  default     = null
}

variable "location" {
  description = "Região do Azure onde os recursos serão provisionados"
  type        = string
  default     = "eastus2"
  # Padrão da disciplina: eastus2.
  # Vision 4.0 Caption não disponível em eastus2 — lab usa Tags + OCR + Objects.
  # Para Caption completo: eastus, westus2, westeurope (verificar política da conta).
  # Azure for Students bloqueia eastus e brazilsouth para a maioria dos recursos.
}
