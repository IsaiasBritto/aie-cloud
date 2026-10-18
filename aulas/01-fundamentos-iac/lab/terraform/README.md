# Terraform — Aula 1, Atividade 5

Código pronto da Atividade 5. **Recria, via IaC, a mesma EC2 que você criou no console na Atividade 4.**

Provisiona: security group (SSH/HTTP/HTTPS) + key pair (sua chave do CloudShell) + EC2 Ubuntu 24.04 `t3.micro` na VPC padrão + um Resource Group que encontra tudo pela tag `stack`.

> 💰 **Custo:** `t3.micro` + 8 GB gp3 custam centavos por hora no Learner Lab. Mesmo assim, **sempre rode `terraform destroy` ao final** (regra de ouro).

## Pré-requisitos (AWS CloudShell, Learner Lab iniciado)

```bash
# Terraform no $HOME (só na 1ª vez)
bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
export PATH="$HOME/bin:$PATH"

# Chave SSH (não sobrescreve se já existir)
test -f ~/.ssh/id_rsa.pub || ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

## Como usar

```bash
cd ~/aie-cloud/aulas/01-fundamentos-iac/lab/terraform
terraform init
terraform plan
terraform apply                      # digite 'yes'
terraform output -raw ssh_command    # copie e cole o comando exibido

# Ao final (regra de ouro)
terraform destroy
```

## Arquivos

| Arquivo | O que contém |
|---------|--------------|
| [main.tf](main.tf) | Provider + `default_tags` + security group + key pair + EC2 + Resource Group por tag |
| [variables.tf](variables.tf) | Região, tag `stack`, nome, tipo da instância, origem do SSH e caminho da chave |
| [outputs.tf](outputs.tf) | ID, IP público, comando SSH e nome do Resource Group |

## Paridade com a Atividade 4 (console)

| Item | Console | Terraform |
|------|---------|-----------|
| AMI | Ubuntu Server 24.04 LTS x86_64 | `data "aws_ami"` (Canonical, a mais recente) |
| Tipo | `t3.micro` | `var.instance_type` |
| Disco | 8 GiB gp3 | igual, criptografado |
| Rede | VPC padrão, IP público | igual |
| Security group | SSH 22 / HTTP 80 / HTTPS 443 | igual (`var.ssh_cidr` para o SSH) |
| Chave | `vockey` (labsuser.pem) | `~/.ssh/id_rsa.pub` do CloudShell |
| Agrupamento | Resource Group `rg-lab-aula01` (tag `aula=1`) | Resource Group `rg-iac-aula01` (tag `stack`) |

## Observações

- **Tags em tudo:** `default_tags` no provider aplica `aula`, `disciplina`, `projeto`, `provisionado` e `stack` em todos os recursos — é o que permite o FinOps da Aula 6.
- **Idempotência:** rode `terraform apply` duas vezes — na segunda, nada muda.
- **Estado:** o `terraform.tfstate` fica no `$HOME` do CloudShell. Em projetos reais ele vai para um backend remoto (S3 + DynamoDB para lock, ou Terraform Cloud).
- **Resource Group ≠ pasta:** apagar `rg-iac-aula01` não apaga a EC2. Quem apaga é o `terraform destroy`.
- **Learner Lab:** não cria IAM users/roles; para EC2 que precise acessar outros serviços, use o instance profile `LabInstanceProfile`.

## Conexão com o Quantum Commerce

```
aula01/  EC2 + security group + tags
aula02/  + S3 + RDS PostgreSQL (pgvector) + DynamoDB + Secrets Manager
aula03/  + AWS Lambda + ECR + ECS Fargate
aula04/  + Comprehend, Rekognition, Transcribe, Polly
aula05/  + agentes (Bedrock/AgentCore) e MLOps (SageMaker AI)
aula06/  + análise FinOps de tudo
```
