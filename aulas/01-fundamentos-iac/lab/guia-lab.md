# Guia de Laboratório — Aula 1

**Tema:** Fundamentos de Cloud & Infraestrutura como Código
**Plataforma:** Microsoft Azure (Azure for Students)
**Ambiente:** **Azure Cloud Shell** — tudo roda no browser, sem instalar nada

---

## Visão geral do lab

Este lab é intercalado com a teoria — você **não fará tudo em sequência ao final da aula**. Cada atividade abaixo corresponde a um momento específico do cronograma.

```
Atividade 1 — Ativar Azure + Cloud Shell           ~20 min  (L₁)
Atividade 2 — Resource Group + IAM via portal      ~15 min  (L₂)
Atividade 3 — Azure Pricing Calculator             ~15 min  (L₃)
Atividade 4 — Criar VM via portal (a "dor")        ~30 min  (L₄)
Atividade 5 — Terraform: recriar a VM via IaC      ~30 min  (L₅)
Atividade 6 — Destroy + verificação custo zero     ~10 min  (L₆)
```

> **Regra de ouro:** Ao final de cada lab, **destrua todos os recursos** (`terraform destroy` ou exclusão do Resource Group). Isso garante custo zero e preserva seu crédito.

---

## Pré-requisitos

- E-mail institucional FIAP (`@fiap.com.br`)
- Navegador moderno (Chrome, Edge ou Firefox atualizado)
- **Nada para instalar** — todo o lab roda no Azure Cloud Shell

> **Pré-aula:** Se ainda não fez, siga o [checklist pré-aula](../pre-aula.md) antes do início.

---

## Atividade 1 — Ativar Azure for Students + Abrir Cloud Shell

**Objetivo:** Obter acesso ao Azure ($100 de crédito, sem cartão) e abrir o Cloud Shell, que será nosso "computador" durante toda a disciplina.

### Passo 1 — Ativar Azure for Students

1. Abra o navegador em **modo anônimo/privado** (evita conflito com contas Microsoft pessoais)
2. Acesse: **https://azure.microsoft.com/free/students**
3. Clique em **"Comece gratuitamente"**
4. Na tela de login, use **`seu.nome@fiap.com.br`** com a senha do portal FIAP
5. Complete o MFA se solicitado
6. Confirme país: **Brasil**
7. Aceite os termos e clique em **"Verificar status acadêmico"**
8. Aguarde 1-2 minutos para ativação

**✅ Checkpoint:** Você acessou `portal.azure.com` e vê **$100,00** de crédito no canto superior direito?

> **Problema comum:** "Esta conta já está associada a uma assinatura" → veja [Troubleshooting](#troubleshooting--problemas-comuns) ao final.

### Passo 2 — Abrir o Cloud Shell

O Cloud Shell é seu ambiente de trabalho desta disciplina. Ele já vem com:

- `az` (Azure CLI) autenticado na sua assinatura
- `terraform`, `bicep`
- `python3`, `git`, `curl`, `jq`
- Editor `code` (estilo VS Code) integrado
- 5 GB de storage persistente (você não perde arquivos entre sessões)

1. No portal Azure, clique no ícone **`>_`** no topo (ou acesse https://shell.azure.com)
2. Na primeira vez, ele pergunta o tipo de shell — escolha **Bash**
3. Aceite criar um Storage Account para persistência (free tier — sem custo)
4. Aguarde abrir o prompt: `usuario@Azure:~$`

### Passo 3 — Confirmar ambiente e clonar o repositório

Execute no Cloud Shell:

```bash
# Confirmar autenticação
az account show --query "{nome:name, id:id, usuario:user.name}"

# Confirmar ferramentas instaladas
terraform -version
bicep --version
python3 --version

# Clonar o repositório da disciplina
cd ~
git clone https://github.com/isaiasbritto/aie-cloud.git
cd aie-cloud

# Abrir o editor estilo VS Code com o repo aberto
code .
```

Quando `code .` for executado, um editor aparece na parte superior do Cloud Shell.

**✅ Checkpoint:** Você consegue ver o editor aberto com os arquivos do repositório?

---

## Atividade 2 — Resource Group + IAM via Portal

**Objetivo:** Criar o Resource Group que será o "container" do lab e entender o conceito de RBAC na prática.

### O que é um Resource Group?

Um Resource Group é um contêiner lógico no Azure — pense numa "pasta de projeto". Tudo que você criar para um fim específico fica dentro dele. Benefícios:

- **Organização:** todos os recursos de um lab num só lugar
- **Custo:** ver gasto agregado
- **Limpeza:** deletar o grupo → deleta tudo dentro de uma vez

### Passo 1 — Criar o Resource Group

1. No portal, busque **"Resource groups"** na barra superior
2. Clique em **"+ Criar"**

| Campo | Valor |
|-------|-------|
| Assinatura | Azure for Students |
| Nome | `rg-lab-aula01` |
| Região | **East US 2** (`eastus2`) |

3. Antes de clicar em "Revisar + criar", vá para a aba **"Tags"** e adicione:
   - Tag: `aula` = `1`
   - Tag: `disciplina` = `cloud-cognitive`
4. Clique em **"Revisar + criar"** → **"Criar"**

### Passo 2 — Explorar IAM (Identity and Access Management)

1. Após criação, clique em **"Ir para o recurso"**
2. No menu lateral, clique em **"Controle de acesso (IAM)"**
3. Aba **"Atribuições de função"** → procure seu nome — você deve aparecer como **Owner** (padrão na conta de estudante)
4. **Reflexão (discutir com a turma):**
   - Por que NÃO seria boa prática que o agente de IA da sua aplicação tenha role Owner no Resource Group de produção?
   - Que role você daria a um agente que só lê dados do Storage? *(Storage Blob Data Reader)*

**✅ Checkpoint:** Você criou `rg-lab-aula01` com tags e visualizou seu papel em IAM?

---

## Atividade 3 — Azure Pricing Calculator

**Objetivo:** Estimar custos de uma arquitetura antes de provisioná-la.

### Cenário

Uma startup de e-commerce precisa hospedar seu backend:

- 1 VM pequena rodando 24/7
- 50 GB de disco para a aplicação
- 100 GB de Blob Storage para imagens de produtos

### Passos

1. Abra **https://azure.microsoft.com/pricing/calculator** em outra aba
2. Em **"Compute"**, clique em **"Virtual Machines"** → **"Adicionar ao cálculo"**
   - Região: East US 2
   - SO: Linux
   - Tipo: **B1s** (1 vCPU, 1 GB RAM)
   - Horas/mês: 730 (24h × ~30,4 dias)
3. Em **"Storage"** → **"Managed Disks"** → adicione:
   - Tipo: Standard SSD
   - Tamanho: 64 GB
4. Em **"Storage"** → **"Storage Accounts"** → adicione:
   - Tipo: Block Blob Storage
   - Redundância: LRS
   - Capacidade: 100 GB
   - Operações de leitura: 10.000/mês
5. Role até o final, observe o **total mensal**
6. Clique em **"Exportar"** → **Excel**

> **Reflexão:** E se a startup virar uma Quantum Commerce com 5M de SKUs e 12 países? Como o custo escala? Aula 6 (FinOps) responde isso.

**✅ Checkpoint:** Você tem uma estimativa exportada com VM + Disco + Blob?

---

## Atividade 4 — Criar VM via Portal (a "dor" do clicódromo)

**Objetivo:** Provisionar uma VM pelo portal e sentir quantos cliques são necessários — vai justificar IaC na atividade seguinte.

> **Importante:** Use o Resource Group `rg-lab-aula01` criado na Atividade 2.

### Passos

1. Na barra de busca do portal, busque **"Virtual Machines"** → **"+ Criar"** → **"Máquina virtual do Azure"**

2. Aba **"Básico"**:

| Campo | Valor (Opção 1) | Valor (Opção 2) |
|-------|-------|-------|
| Assinatura | Azure for Students | Azure for Students |
| Grupo de recursos | `rg-lab-aula01` | `rg-lab-aula01` |
| Nome | `vm-lab-aula01` | `vm-lab-aula01` |
| Região | **East US 2** (`eastus2`) | **East US 2** (`eastus2`) |
| Opções de disponibilidade | Nenhuma redundância | Nenhuma redundância |
| Imagem | **Ubuntu Pro Server 26.04 LTS - ARM Gen2** | Ubuntu Server 24.04 LTS – Gen2 X64 |
| Tamanho | **Standard_D2ps_v6** (2 vCPU, 8 GiB RAM) | Standard D2s v3 (2 vcpus, 8 GiB memória)
| Autenticação | Chave pública SSH | Chave pública SSH |
| Usuário | `azureuser` | `azureuser` |
| Chave SSH | **Gerar novo par** (nome: `vm-lab-aula01-key`) | **Gerar novo par** (nome: `vm-lab-aula01-key`) |

> ⚠️ **Atenção ao custo:** `Standard_D2s_v3` + disco Premium SSD **não é free-tier** (consome ~$0,10/h do seu crédito). Esta é a configuração de referência do lab — por isso a **regra de ouro** vale dobrado: destrua tudo (Atividade 6) assim que terminar.

3. Aba **"Discos"**: tipo de disco do SO = **Premium SSD (LRS)**
4. Aba **"Rede"**: deixar o Azure criar a VNet (`vm-lab-aula01-vnet`, `10.0.0.0/24`) e o IP público (`vm-lab-aula01-ip`, Standard estático). No NSG, confirme as portas de entrada **SSH (22)**, **HTTP (80)** e **HTTPS (443)**
5. Aba **"Gerenciamento"**: **desmarque** Application Insights e monitoramento avançado (custo)
6. **"Revisar + criar"** → observe o custo estimado → **"Criar"**
7. Janela aparece para baixar a chave SSH — clique em **"Baixar chave privada e criar recurso"**.

> **Atenção (no install):** Em vez de baixar a chave e configurar SSH no seu computador, vamos usar a chave SSH que o **Cloud Shell** já tem (gerada automaticamente). Para isso, no momento da criação da VM, você poderia ter escolhido "Usar chave existente" → cole o conteúdo de `~/.ssh/id_rsa.pub` do Cloud Shell. Como já criamos com chave nova, **vamos demonstrar conexão pelo próprio portal**.

8. Após a implantação (~2-3 min), na visão geral da VM, clique em **"Conectar"** → **"SSH via navegador"** (Azure Bastion não está disponível no free tier, então use o link **"Cloud Shell"**).

   Alternativa simples: copie a chave gerada como texto (link "Visualizar chave privada"), cole num arquivo `~/key.pem` no Cloud Shell:

   ```bash
   cd ~
   nano key.pem    # cole o conteúdo, Ctrl+O para salvar, Ctrl+X para sair
   chmod 400 key.pem
   ssh -i key.pem azureuser@<IP_PUBLICO_DA_VM>
   ```

9. Quando conectado, explore:

   ```bash
   uname -a
   df -h
   # Sair:
   exit
   ```

**✅ Checkpoint:** Você criou a VM, conseguiu se conectar e voltar para o Cloud Shell?

### NÃO DELETE A VM AGORA — vamos compará-la com a versão IaC primeiro.

> **Conte os cliques:** Quantos cliques foram necessários para criar essa VM? Imagine fazer isso em 50 ambientes diferentes. Essa é a dor que o IaC resolve.

> **Dica — o portal já fala IaC:** na tela **"Revisar + criar"** existe o link **"Baixar um modelo para automação"**. Ele gera exatamente o par `template.json` + `parameters.json` que está em [`../template/`](../template/) deste lab — o ARM template desta mesma VM. Na próxima atividade vamos reescrever esse template em Terraform.

---

## Atividade 5 — Terraform: recriar a MESMA VM via IaC

**Objetivo:** Reprovisionar via Terraform a **mesma VM** que você criou no portal na Atividade 4 (Ubuntu 24.04, `Standard_D2s_v3`, com VNet + NSG + IP público). Esse código é o equivalente em Terraform do template ARM que está em [`../template/`](../template/) — aquele que o portal gera no link "Baixar um modelo para automação".

### Passo 1 — Garantir a chave SSH no Cloud Shell

A VM autentica **somente por chave SSH**. Garanta que o Cloud Shell já tem um par de chaves:

```bash
# Cria ~/.ssh/id_rsa e id_rsa.pub se ainda não existirem (não sobrescreve nada)
test -f ~/.ssh/id_rsa.pub || ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

### Passo 2 — Ir para o código Terraform pronto

O código já está no repositório que você clonou na Atividade 1. Vá até a pasta:

```bash
cd ~/aie-cloud/aulas/01-fundamentos-iac/lab/terraform
ls
# Você verá: main.tf  variables.tf  outputs.tf  README.md
```

Abra os arquivos no editor para ler o que cada um faz:

```bash
code .
```

### Passo 3 — Entender os 3 arquivos

| Arquivo | O que define |
|---------|--------------|
| [main.tf](terraform/main.tf) | Provider, Resource Group, VNet + Subnet, NSG (SSH/HTTP/HTTPS), IP público, NIC e a VM Linux |
| [variables.tf](terraform/variables.tf) | Região (`eastus2`), nome do RG, tamanho da VM, usuário e caminho da chave SSH |
| [outputs.tf](terraform/outputs.tf) | IP público, nome da VM e o comando SSH pronto |

> Leia o [README](terraform/README.md) da pasta `terraform/` — ele traz uma tabela de **paridade** mostrando que cada recurso bate com o template ARM do portal.

### Passo 4 — Executar o Terraform

No terminal do Cloud Shell, ainda em `~/aie-cloud/aulas/01-fundamentos-iac/lab/terraform`:

```bash
# Inicializa providers e baixa plugins
terraform init

# Mostra o que será criado (sem aplicar) — repare nos ~7 recursos
terraform plan

# Aplica de fato — digite 'yes' quando perguntar (~2-3 min, sobe a VM)
terraform apply
```

Após `apply` concluir, conecte na VM usando o output gerado:

```bash
# Mostra o comando ssh já com o IP público preenchido
terraform output -raw ssh_command
# Copie e cole o comando exibido (ex.: ssh azureuser@20.x.x.x)
```

Verifique no portal:

- Acesse "Resource groups" → você vê o **`rg-iac-aula01`** recém-criado
- Dentro dele: a VM `vm-lab-aula01` + VNet + NSG + IP — **idêntica** à que você criou na Atividade 4
- Compare com `rg-lab-aula01` (criado manualmente): mesma VM, mas a versão IaC é **reproduzível** e nasceu de ~150 linhas versionáveis, não de 30 cliques

### Passo 5 — Demonstração de idempotência

Adicione uma tag nova editando o bloco `locals` no topo do `main.tf`:

```hcl
locals {
  tags = {
    aula         = "1"
    disciplina   = "cloud-cognitive"
    provisionado = "terraform"
    ambiente     = "lab"      # NOVA TAG
  }
}
```

Rode novamente:

```bash
terraform plan
# Observe: ele detecta apenas a tag adicional nos recursos (não recria a VM)
terraform apply
```

> **Conceito-chave:** O Terraform mantém estado (`terraform.tfstate`) e só faz o que é necessário para chegar ao estado desejado. Isso é **idempotência**.

### Passo 6 — Comparar com Bicep (apenas observação, sem rodar)

Como exercício de leitura, veja como a **mesma VM** ficaria em Bicep, decompilando o template ARM que está no lab:

```bash
# Decompilar o template ARM do portal (já versionado no repo) para Bicep
cd ~/aie-cloud/aulas/01-fundamentos-iac/template
bicep decompile template.json --outfile ~/vm-lab-aula01.bicep

# Abrir o arquivo Bicep gerado
code ~/vm-lab-aula01.bicep
```

Compare lado a lado: o `template.json` (ARM, verboso), o `main.tf` (Terraform/HCL) e o Bicep gerado. Note:

- ARM (JSON) é o formato nativo do Azure, porém verboso
- Terraform usa HCL e funciona multi-cloud
- Bicep tem sintaxe enxuta, específica para Azure, e compila para ARM
- Todos são declarativos e idempotentes

**✅ Checkpoint:** Você recriou a VM via Terraform, conectou nela pelo output `ssh_command` e observou idempotência ao rodar `apply` duas vezes?

---

## Atividade 6 — Destroy + Verificação de Custo Zero

**Objetivo:** Garantir que NENHUM recurso continua gerando custo e refletir sobre IaC vs portal.

### Passo 1 — Destruir o ambiente Terraform

```bash
cd ~/aie-cloud/aulas/01-fundamentos-iac/lab/terraform
terraform destroy
# Digite 'yes' quando perguntar
```

Aguarde ~2 minutos. Todos os recursos da versão IaC (RG `rg-iac-aula01` + VM + disco + VNet + NSG + IP) são removidos. **Esse passo é crítico:** a `Standard_D2s_v3` gera custo enquanto existir.

### Passo 2 — Deletar o Resource Group criado manualmente

A VM `vm-lab-aula01` ainda está no `rg-lab-aula01`. Para eliminá-la (e a VM + disco + IP que ela criou):

**Opção A — Via portal:**

1. Buscar "Resource groups"
2. Clicar em `rg-lab-aula01`
3. **"Excluir grupo de recursos"** → digitar o nome → Excluir

**Opção B — Via CLI no Cloud Shell:**

```bash
az group delete --name rg-lab-aula01 --yes --no-wait
```

> **Por que deletar o grupo inteiro?** Apenas parar a VM não elimina o custo do disco e do IP público. Deletar o grupo garante custo zero.

### Passo 3 — Verificar custo zero

1. No portal, busque **"Cost Management"** → **"Análise de custo"**
2. Filtre por período: hoje
3. O total deve ser próximo de $0,10 (negligenciável)

### Passo 4 — Reflexão final (5 min)

Discuta com seu grupo (será necessário para a Aula 2):

1. Qual versão (portal vs Terraform) você levaria para produção e por quê?
2. O que aconteceria se você perdesse o arquivo `terraform.tfstate`?
3. Como você versionaria esse código para que seu time inteiro use? *(gancho para Git — tarefa pós-aula)*
4. Como o IaC se conecta a um agente de IA reproduzível?

---

## Conceitos-chave praticados hoje

| Conceito | Onde você aplicou |
|----------|-------------------|
| Cloud Shell como ambiente único | Em todas as atividades |
| IaaS (VM) | Atividade 4 |
| Resource Group | Atividades 2 e 5 |
| RBAC e princípio do menor privilégio | Atividade 2 (discussão IAM) |
| Pricing Calculator | Atividade 3 |
| IaC com Terraform | Atividade 5 |
| Bicep (comparativo) | Atividade 5 — Passo 5 |
| Idempotência | Atividade 5 — Passo 4 |
| Destroy / custo zero | Atividade 6 |

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| E-mail `@fiap.com.br` recusado | Conta Microsoft pré-existente | `account.microsoft.com` → desconectar conta antiga → tentar de novo |
| Portal Azure em inglês | Configuração padrão | ⚙️ no topo → **Idioma e região** → Português (Brasil) |
| Cloud Shell pede Storage Account | Primeira vez no Cloud Shell | Aceitar criação automática (free) |
| `Standard_D2s_v3` não disponível / quota | Quota da família Dsv3 esgotada na região | Pedir aumento de quota no portal, ou ajustar `vm_size`/`location` em `variables.tf` |
| `terraform init` falha com erro de provider | Sem internet ou plugin antigo | `rm -rf .terraform && terraform init` |
| `terraform apply` erro `file: no such file` na chave SSH | Cloud Shell sem par de chaves | Rode o Passo 1 da Atividade 5: `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""` |
| Não consigo ver VM no `rg-lab-aula01` após criar | Criada em outro grupo por engano | Buscar a VM por nome — está em algum lugar; mover ou recriar |
| "Permission denied" no SSH | Permissões do `.pem` muito abertas | `chmod 400 ~/key.pem` |
| Custo apareceu maior que $1 | VM esquecida ligada | Deletar o RG inteiro imediatamente |

---

## Conexão com o projeto Quantum Commerce

O Resource Group e o `main.tf` que você criou hoje são o **embrião da infraestrutura QC**. Nas próximas aulas, esse mesmo padrão evolui:

```
infrastructure/
  ├── main.tf                  # (Aula 1) RG + VNet + NSG + IP + VM Linux
  ├── network.tf               # (Aula 2) VNet + subnets adicionais
  ├── storage.tf               # (Aula 2) Blob + Azure SQL + Cosmos
  ├── functions.tf             # (Aula 3) Azure Function App
  ├── cognitive.tf             # (Aula 4) Azure AI Services
  ├── ml.tf                    # (Aula 5) Azure ML Workspace
  └── outputs.tf               # Endpoints e nomes consumidos por outras disciplinas
```

**Tarefa do grupo (entrega na Aula 2):**

- Esboço de arquitetura QC (diagrama no Excalidraw, draw.io ou foto de papel)
- Identificar: camadas, provedor escolhido, categorias de serviço

---

## Tarefa pós-aula obrigatória — Git sem instalar

Antes da Aula 2, complete o tutorial:

👉 **[pos-aula-git.md](../pos-aula-git.md)** — ~20 min, sem instalação local. Criar conta GitHub, fork do repo da disciplina, edição via `github.dev`.

---

## Referências

- [Azure for Students](https://azure.microsoft.com/free/students)
- [Azure Cloud Shell](https://shell.azure.com)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Terraform vs Bicep — comparativo oficial Microsoft](https://learn.microsoft.com/azure/developer/terraform/comparing-terraform-and-bicep)
- [Azure RBAC Built-in Roles](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles)
- [Azure VM Sizes](https://learn.microsoft.com/azure/virtual-machines/sizes)
