# Terraform — Aula 1, Atividade 5

Código pronto da Atividade 5 do laboratório. **Recria, via IaC, a mesma VM que você criou no portal na Atividade 4** — o equivalente Terraform do template ARM exportado em [`template.json`](template.json).

Provisiona: Resource Group + Virtual Network + Subnet + Network Security Group (SSH/HTTP/HTTPS) + IP público + NIC + VM Linux (Ubuntu 26.04 LTS ARM64, zona 1, Trusted Launch, Spot).

> ⚠️ **Custo:** este lab usa `Standard_D2ps_v6` (série Arm Cobalt) + disco `Premium_LRS` (30 GB) em `eastus2`, zona `1` — **idêntico ao template do portal**. A VM roda como **Spot instance** (`priority = Spot`, `max_bid_price = -1`, `eviction_policy = Deallocate`), o que reduz custo mas permite que a VM seja desalocada a qualquer momento por preço/capacidade. Ainda assim, está **fora do free-tier** e gera custo enquanto provisionada. **Sempre rode `terraform destroy` ao final** (regra de ouro — custo zero).

## Pré-requisito — chave SSH no Cloud Shell

A VM usa autenticação somente por chave SSH. Garanta que o Cloud Shell tem um par de chaves:

```bash
# Cria ~/.ssh/id_rsa e id_rsa.pub se ainda não existirem (não sobrescreve)
test -f ~/.ssh/id_rsa.pub || ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

## Como usar (no Azure Cloud Shell)

```bash
# Clonar o repositório (apenas na primeira vez)
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/01-fundamentos-iac/lab/terraform

# Inicializar providers
terraform init

# Ver o que será criado
terraform plan

# Aplicar (digite 'yes' quando perguntar)
terraform apply

# Conectar na VM usando o output ssh_command
terraform output -raw ssh_command   # copie e cole o comando exibido

# Destruir TUDO ao final (regra de ouro — custo zero)
terraform destroy
```

## Arquivos

| Arquivo | O que contém |
|---------|--------------|
| [main.tf](main.tf) | Provider + rede (VNet, Subnet, NSG, IP, NIC) + VM Linux |
| [variables.tf](variables.tf) | Região, RG, tamanho da VM, zona, usuário e caminho da chave SSH |
| [outputs.tf](outputs.tf) | IP público, nome da VM e comando SSH pronto |

## Paridade com o template ARM (`template.json`)

| Recurso | Template ARM (portal) | Terraform |
|---------|-----------------------|-----------|
| Imagem | Ubuntu 26.04 LTS ARM64 (`canonical/ubuntu-26_04-lts/pro-server-arm64`) | igual |
| Tamanho | `Standard_D2ps_v6` (série Arm Cobalt) | igual (`var.vm_size`) |
| Disco | `Premium_LRS`, 30 GB, controller `SCSI` | igual |
| Zona | `1` | igual (`var.zone`) |
| Região | `eastus2` | igual (`var.location`) |
| Segurança | Trusted Launch (Secure Boot + vTPM) | igual (`secure_boot_enabled` / `vtpm_enabled`) |
| Prioridade | Spot, `evictionPolicy = Deallocate`, `maxPrice = -1` | igual (`priority` / `eviction_policy` / `max_bid_price`) |
| Rede | VNet 10.0.0.0/16 + subnet `default` 10.0.0.0/24 | igual |
| NSG | SSH 22 / HTTPS 443 / HTTP 80 (associado à NIC) | igual |
| IP público | Static, SKU Standard | igual |
| Autenticação | chave SSH (sem senha) | igual (`admin_ssh_key`) |
| Resource Group | `rg-lab-aula01` (manual) | `rg-iac-aula01` (separado, p/ comparar portal × IaC) |

## Observações

- **Idempotência:** rode `terraform apply` duas vezes — na segunda, o Terraform detecta que nada mudou e não recria nada.
- **Estado:** o arquivo `terraform.tfstate` é gerado localmente. Em projetos reais, ele vai para um remote backend (Azure Storage, S3, Terraform Cloud).
- **NSG na NIC:** o template do portal associa o NSG à interface de rede (não à subnet); o Terraform mantém a mesma topologia via `azurerm_network_interface_security_group_association`.
- **Imagem ARM64:** `Standard_D2ps_v6` é uma VM baseada em processador Arm (Cobalt), por isso a imagem também precisa ser ARM64 (`pro-server-arm64`) — imagens x64 não bootam nessa família de VM.
- **Spot eviction:** com `priority = "Spot"` a VM pode ser desalocada pela Azure a qualquer momento por preço/capacidade; se isso acontecer, `terraform apply` religa a VM, mas o estado (disco, IP) é preservado.

## Conexão com o Quantum Commerce

Esta VM + rede é o **embrião da infraestrutura QC**. Nas próximas aulas, ela evolui:

```
aula01/  RG + VNet + Subnet + NSG + IP + VM (Ubuntu)
aula02/  + Storage Containers + Azure SQL + Cosmos DB + AI Search
aula03/  + Azure Functions + Container Instances
aula04/  + Azure AI Services (Speech, Vision, Language)
aula05/  + Azure ML Workspace + MLflow
aula06/  + análise FinOps de tudo
```
