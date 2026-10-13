# Guia de Laboratório — Aula 1

**Tema:** Fundamentos de Cloud & Infraestrutura como Código
**Plataforma:** Amazon Web Services (AWS Academy Learner Lab)
**Ambiente:** **AWS CloudShell** — tudo roda no browser, sem instalar nada
**Região:** `us-east-1` (N. Virginia) em todos os labs

---

## Visão geral do lab

Este lab é intercalado com a teoria — você **não fará tudo em sequência ao final da aula**. Cada atividade corresponde a um momento do cronograma.

```
Atividade 1 — Iniciar o Learner Lab + CloudShell     ~20 min  (L₁)
Atividade 2 — Tags, Resource Group e IAM             ~15 min  (L₂)
Atividade 3 — AWS Pricing Calculator                 ~15 min  (L₃)
Atividade 4 — Criar a EC2 pelo console (a "dor")     ~30 min  (L₄)
Atividade 5 — Terraform: recriar a EC2 via IaC       ~30 min  (L₅)
Atividade 6 — Destroy + verificação de custo zero    ~10 min  (L₆)
```

> **Regra de ouro:** ao final de cada lab, **destrua todos os recursos** (`terraform destroy` ou *terminate* no console). Na AWS não existe "apagar a pasta": o Resource Group é só uma consulta por tag. Deletar é melhor que parar.

---

## Pré-requisitos

- Convite do **AWS Academy** aceito (chega no e-mail FIAP)
- Navegador moderno (Chrome, Edge ou Firefox atualizado)
- **Nada para instalar** — todo o lab roda no AWS CloudShell

> **Pré-aula:** se ainda não fez, siga o [checklist pré-aula](../pre-aula.md).

---

## Atividade 1 — Iniciar o Learner Lab + abrir o CloudShell

**Objetivo:** ganhar acesso à conta AWS da disciplina e abrir o CloudShell, que será o nosso "computador" durante toda a disciplina.

### Passo 1 — Iniciar o Learner Lab

1. Entre em **https://awsacademy.instructure.com** com o e-mail FIAP
2. Abra o curso **AWS Academy Learner Lab** → **Modules** → **Launch AWS Academy Learner Lab**
3. Clique em **Start Lab** e espere a bolinha ao lado de **AWS** ficar **verde** (1–3 min)
4. Clique em **AWS** — o console abre numa nova aba, já logado
5. Confira no canto superior direito: região **N. Virginia (us-east-1)**

> A sessão dura ~4 h. Quando acaba, as instâncias EC2 **param** (não são apagadas) e voltam no próximo *Start Lab*. O crédito consumido aparece no topo da página do Learner Lab.

**✅ Checkpoint:** você vê o console da AWS em `us-east-1`?

### Passo 2 — Abrir o CloudShell

O CloudShell já vem com:

- `aws` (AWS CLI v2) autenticado com a **LabRole** da sua sessão
- `python3`, `pip`, `git`, `curl`, `jq`, `zip`, `docker`
- 1 GB de armazenamento persistente no `$HOME` (por região)

1. No console, clique no ícone **`>_`** na barra superior (ou busque **CloudShell**)
2. Aguarde o prompt: `[cloudshell-user@ip-... ~]$`

### Passo 3 — Confirmar ambiente e clonar o repositório

```bash
# Quem sou eu? (a ARN mostra a LabRole/voclabs da sua sessão)
aws sts get-caller-identity --output table

# Região padrão (deve ser us-east-1)
aws configure get region

# Ferramentas
aws --version
python3 --version

# Clonar o repositório da disciplina
cd ~
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud
```

> O CloudShell não tem editor gráfico. Use `nano`/`vim` no terminal, ou navegue pelo repositório no GitHub (tecla `.` abre o **github.dev**).

**✅ Checkpoint:** `aws sts get-caller-identity` respondeu e o repositório está em `~/aie-cloud`?

---

## Atividade 2 — Tags, Resource Group e IAM

**Objetivo:** entender como a AWS organiza recursos (conta + região + tags) e como funciona o acesso (IAM).

### O que muda em relação a um "Resource Group" de outras nuvens?

Na AWS o recurso vive na **conta + região**. Não existe pasta obrigatória. Um **Resource Group** é uma **consulta salva por tag**:

- **Organização:** ver tudo de um projeto num lugar só
- **Custo:** a mesma tag, ativada no Billing, separa o gasto por projeto
- **Limpeza:** apagar o grupo **não** apaga os recursos — por isso usamos `terraform destroy`

### Passo 1 — Criar um Resource Group por tag

1. No console, busque **Resource Groups & Tag Editor**
2. **Create resource group** → **Tag based**
3. Resource types: **All supported resource types**
4. Tag key: `aula` · Tag value: `1`
5. Group name: `rg-lab-aula01` → **Create group**

O grupo nasce vazio — os recursos aparecem nele conforme você cria coisas com a tag `aula=1`.

### Passo 2 — Explorar o IAM

1. Busque **IAM** → **Roles** → procure **LabRole**
2. Abra a aba **Permissions** e veja as políticas anexadas
3. **Reflexão (discutir com a turma):**
   - No Learner Lab você **não pode criar** usuários nem roles — usa sempre a LabRole. Por que uma conta de estudante restringe isso?
   - Que política você daria a um agente de IA que só **lê** objetos de um bucket? *(uma política com `s3:GetObject` restrita ao ARN do bucket — e não `AmazonS3FullAccess`)*

**✅ Checkpoint:** você criou `rg-lab-aula01` e viu as políticas da LabRole?

---

## Atividade 3 — AWS Pricing Calculator

**Objetivo:** estimar custos de uma arquitetura antes de provisioná-la.

### Cenário

Uma startup de e-commerce precisa hospedar seu backend:

- 1 VM pequena rodando 24/7
- 50 GB de disco para a aplicação
- 100 GB de armazenamento de objetos para imagens de produtos

### Passos

1. Abra **https://calculator.aws** em outra aba → **Create estimate** (não precisa de login)
2. Região: **US East (N. Virginia)**
3. Adicione **Amazon EC2**:
   - Sistema operacional: Linux
   - Instância: **t3.micro** (2 vCPU, 1 GiB)
   - Uso: 100% (730 h/mês) · Pricing: **On-Demand**
   - EBS: **gp3**, 50 GB
4. Adicione **Amazon S3**:
   - S3 Standard: 100 GB
   - 10.000 requisições GET por mês
5. Role até o final e observe o **total mensal**
6. **Export** → **CSV** (ou **Share** para gerar um link)

> **Reflexão:** e se a startup virar uma Quantum Commerce com 5M de SKUs e 12 países? Como o custo escala? A Aula 6 (FinOps) responde.

**✅ Checkpoint:** você tem uma estimativa exportada com EC2 + EBS + S3?

---

## Atividade 4 — Criar a EC2 pelo console (a "dor" do clicódromo)

**Objetivo:** provisionar uma VM pelo console e sentir quantos cliques são necessários — isso justifica IaC na próxima atividade.

### Passos

1. Busque **EC2** → **Launch instance**

| Campo | Valor |
|-------|-------|
| Name and tags | Name: `vm-lab-aula01` · **Add additional tags**: `aula` = `1`, `disciplina` = `cloud-cognitive` |
| AMI | **Ubuntu Server 24.04 LTS** (x86_64) |
| Instance type | **t3.micro** |
| Key pair | **vockey** (já existe no Learner Lab) |
| Network settings | VPC padrão · Auto-assign public IP: **Enable** |
| Firewall (security group) | Create: liberar **SSH (22)**, **HTTP (80)** e **HTTPS (443)** |
| Storage | 8 GiB **gp3** |

2. **Launch instance** e espere o estado **Running** (~1 min)

### Conectar

**Opção A — EC2 Instance Connect (no browser):** selecione a instância → **Connect** → aba **EC2 Instance Connect** → usuário `ubuntu` → **Connect**.

**Opção B — SSH a partir do CloudShell:**

1. Na página do Learner Lab: **AWS Details** → **Download PEM** (arquivo `labsuser.pem`)
2. No CloudShell: **Actions → Upload file** → envie o `labsuser.pem`

```bash
chmod 400 ~/labsuser.pem
ssh -i ~/labsuser.pem ubuntu@<IP_PUBLICO>
```

### Explorar e publicar uma página

```bash
uname -a
df -h

# Uma página web em 5 segundos (porta 80, liberada no security group)
echo "<h1>Quantum Commerce · Aula 1</h1>" > index.html
sudo python3 -m http.server 80
```

Abra `http://<IP_PUBLICO>` no navegador. `Ctrl+C` para parar e `exit` para sair da VM.

Volte ao Resource Group `rg-lab-aula01`: a instância apareceu lá por causa da tag `aula=1`.

**✅ Checkpoint:** você criou a EC2, conectou e viu a página no navegador?

### NÃO TERMINE A INSTÂNCIA AGORA — vamos compará-la com a versão IaC primeiro.

> **Conte os cliques:** quantos foram necessários? Imagine fazer isso em 50 ambientes. Essa é a dor que o IaC resolve.

---

## Atividade 5 — Terraform: recriar a MESMA EC2 via IaC

**Objetivo:** reprovisionar via Terraform a **mesma VM** da Atividade 4 (Ubuntu 24.04, `t3.micro`, security group com 22/80/443), agora em código versionável.

### Passo 1 — Instalar o Terraform e criar a chave SSH

O CloudShell não traz o Terraform. O script abaixo instala no seu `$HOME` (que persiste entre sessões):

```bash
bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
export PATH="$HOME/bin:$PATH"
terraform -version

# Conferir conta e região (deve ser us-east-1)
aws sts get-caller-identity && aws configure get region

# Cria ~/.ssh/id_rsa e id_rsa.pub se ainda não existirem (não sobrescreve nada)
test -f ~/.ssh/id_rsa.pub || ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

### Passo 2 — Ir para o código Terraform pronto

```bash
cd ~/aie-cloud/aulas/01-fundamentos-iac/lab/terraform
ls
# main.tf  variables.tf  outputs.tf  README.md
```

| Arquivo | O que define |
|---------|--------------|
| [main.tf](terraform/main.tf) | Provider + tags padrão + security group + key pair + EC2 (VPC padrão) + Resource Group por tag |
| [variables.tf](terraform/variables.tf) | Região, tags, tipo da instância e caminho da chave SSH |
| [outputs.tf](terraform/outputs.tf) | IP público, nome da VM e o comando SSH pronto |

### Passo 3 — Executar o Terraform

```bash
# Baixa o provider aws
terraform init

# Mostra o que será criado (sem aplicar) — repare nos ~4 recursos
terraform plan

# Aplica de fato — digite 'yes' (~1-2 min)
terraform apply

# Conectar na VM usando o output
terraform output -raw ssh_command   # copie e cole o comando exibido
```

No console:

- **Resource Groups** → `rg-iac-aula01`: a EC2, o security group e o key pair da versão IaC
- Compare com `rg-lab-aula01` (console): mesma VM, mas a versão IaC é **reproduzível** e nasceu de ~150 linhas versionáveis, não de 30 cliques

### Passo 4 — Demonstração de idempotência

Adicione uma tag no bloco `locals` do `main.tf` (`nano main.tf`):

```hcl
locals {
  tags = {
    aula         = "1"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    provisionado = "terraform"
    stack        = var.stack_name
    ambiente     = "lab"      # NOVA TAG
  }
}
```

```bash
terraform plan
# Observe: ele só atualiza as tags (update in-place) — não recria a VM
terraform apply
```

> **Conceito-chave:** o Terraform mantém estado (`terraform.tfstate`) e só faz o necessário para chegar ao estado desejado. Isso é **idempotência**.

### Passo 5 — Comparar com CloudFormation (leitura)

A mesma VM em CloudFormation, o IaC nativo da AWS, está em [`cloudformation/ec2-lab.yaml`](cloudformation/ec2-lab.yaml):

```bash
cd ~/aie-cloud/aulas/01-fundamentos-iac/lab/cloudformation
cat ec2-lab.yaml
aws cloudformation validate-template --template-body file://ec2-lab.yaml
```

- CloudFormation (YAML/JSON) é nativo da AWS; o estado é a **stack**, guardada pela própria AWS
- Terraform usa HCL, funciona multi-cloud e o estado é um arquivo seu
- Os dois são declarativos e idempotentes

**✅ Checkpoint:** você recriou a VM via Terraform, conectou pelo `ssh_command` e viu a idempotência no segundo `apply`?

---

## Atividade 6 — Destroy + verificação de custo zero

### Passo 1 — Destruir o ambiente Terraform

```bash
cd ~/aie-cloud/aulas/01-fundamentos-iac/lab/terraform
terraform destroy
# Digite 'yes'
```

### Passo 2 — Terminar a EC2 criada pelo console

**Console:** EC2 → selecione `vm-lab-aula01` → **Instance state → Terminate instance**.

**Ou pela CLI:**

```bash
ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=vm-lab-aula01" "Name=instance-state-name,Values=running,stopped" \
  --query "Reservations[].Instances[].InstanceId" --output text)
aws ec2 terminate-instances --instance-ids $ID
```

Apague também o security group criado pelo console (EC2 → Security Groups) depois que a instância terminar, e o Resource Group `rg-lab-aula01` (que, lembre, não apaga nada sozinho).

> **Por que terminar e não parar?** Instância parada não cobra CPU, mas o volume EBS e o IP elástico (se houver) continuam cobrando. Terminar garante custo zero.

### Passo 3 — Verificar custo

Na página do Learner Lab, confira o crédito consumido. A conta do dia deve ser de centavos.

### Passo 4 — Reflexão final (5 min)

1. Qual versão (console × Terraform) você levaria para produção e por quê?
2. O que aconteceria se você perdesse o arquivo `terraform.tfstate`?
3. Como versionar esse código para o time inteiro usar? *(gancho para Git — tarefa pós-aula)*
4. Como o IaC se conecta a um agente de IA reproduzível?

---

## Conceitos-chave praticados hoje

| Conceito | Onde você aplicou |
|----------|-------------------|
| CloudShell como ambiente único | Todas as atividades |
| IaaS (EC2) | Atividade 4 |
| Tags e Resource Group (consulta) | Atividades 2 e 5 |
| IAM e menor privilégio | Atividade 2 |
| Pricing Calculator | Atividade 3 |
| IaC com Terraform | Atividade 5 |
| CloudFormation (comparativo) | Atividade 5 — Passo 5 |
| Idempotência | Atividade 5 — Passo 4 |
| Destroy / custo zero | Atividade 6 |

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| Botão **AWS** cinza/vermelho no Learner Lab | Sessão não iniciada | **Start Lab** e aguarde a bolinha verde |
| `ExpiredToken` no CloudShell | A sessão do Learner Lab acabou | Reinicie o lab e abra um CloudShell novo |
| `terraform: command not found` | PATH não atualizado | `export PATH="$HOME/bin:$PATH"` |
| `terraform apply` erro `no such file` na chave SSH | CloudShell sem par de chaves | `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""` |
| `UnauthorizedOperation` ao criar recurso | Tipo de instância ou serviço fora do Learner Lab | Use `t3.micro` e `us-east-1` |
| `InvalidKeyPair.Duplicate` | Key pair de um apply anterior | `terraform destroy` e de novo `apply`, ou apague o key pair no console |
| "Permission denied (publickey)" no SSH | Chave errada ou permissões abertas | `chmod 400 ~/labsuser.pem`; use `-i ~/.ssh/id_rsa` para a VM do Terraform |
| Página não abre na porta 80 | Security group sem HTTP ou servidor parado | Libere a porta 80 e rode o `http.server` com `sudo` |

---

## Conexão com o projeto Quantum Commerce

O `main.tf` de hoje é o **embrião da infraestrutura QC**. Nas próximas aulas o padrão evolui:

```
infrastructure/
  ├── main.tf        # (Aula 1) provider + tags + EC2 + security group
  ├── storage.tf     # (Aula 2) S3 + RDS PostgreSQL + DynamoDB
  ├── lambda.tf      # (Aula 3) AWS Lambda + ECR + ECS Fargate
  ├── ai.tf          # (Aula 4) Comprehend, Rekognition, Transcribe, Polly
  ├── agents.tf      # (Aula 5) Bedrock / AgentCore
  └── outputs.tf     # Endpoints e nomes consumidos por outras disciplinas
```

**Tarefa do grupo (entrega na Aula 2):** esboço da arquitetura QC (Excalidraw, draw.io ou foto de papel), com camadas, provedor escolhido e categorias de serviço.

---

## Tarefa pós-aula obrigatória — Git sem instalar

👉 **[pos-aula-git.md](../pos-aula-git.md)** — ~20 min, sem instalação local.

---

## Referências

- [AWS Academy Learner Lab — guia do aluno](https://awsacademy.instructure.com)
- [AWS CloudShell](https://docs.aws.amazon.com/cloudshell/latest/userguide/welcome.html)
- [AWS Pricing Calculator](https://calculator.aws)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)
- [AWS Resource Groups](https://docs.aws.amazon.com/ARG/latest/userguide/resource-groups.html)
- [Tipos de instância EC2](https://aws.amazon.com/ec2/instance-types/)
