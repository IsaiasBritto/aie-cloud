# Exercícios — Aula 1

**Tema:** Fundamentos de Cloud & Infraestrutura como Código
**Formato:** **Entrega obrigatória por grupo** — ZIP no Portal FIAP
**Vale:** 10% da nota final ([rubrica completa](../../entregas/rubrica.md))
**Prazo:** 1 dia antes da Aula 2
**Como entregar:** ver [entregas/entrega-01/INSTRUCOES.md](../../entregas/entrega-01/INSTRUCOES.md) e [pos-aula-git.md](pos-aula-git.md)

---

## Instruções gerais

Esta é a **primeira entrega de grupo** da disciplina. Ao todo são 5 entregas intermediárias (10% cada) + projeto integrado final entregue como ZIP **1 semana após a Aula 6** (50%, **sem apresentação oral**).

### Como o grupo se organiza

Os 3 níveis de exercícios são **divisão de trabalho dentro do grupo**, não escolha individual livre:

- 🟢 **Nível 1 — Básico:** consolidação dos conceitos da aula (modelos de serviço, 6 Rs, SLA, IAM)
- 🟡 **Nível 2 — Intermediário:** bloco do projeto Quantum Commerce (arquitetura, comparativo de custos, migração)
- 🔴 **Nível 3 — Avançado:** **bônus opcional** — Network Security via Terraform, CloudFormation equivalente, multi-cloud

**Mínimo obrigatório:** N1 + N2 cobertos. **N3 é bônus** (até +2 pts extras na nota da aula).

### Distribuição sugerida (4-5 membros)

- Membros com menos experiência em cloud: assumem N1 (consolidação)
- Membros com experiência intermediária: assumem N2 (projeto QC)
- Membros experientes: assumem N3 (bônus) — se houver perfil avançado no grupo

> Quem fez N1 desta aula deve preferencialmente fazer N2 ou N3 na próxima — **rodízio entre aulas vale ponto** no Critério 4 da rubrica.

### Template obrigatório

Use o [template em `entregas/template-entrega-grupo.md`](../../entregas/template-entrega-grupo.md) — inclui cabeçalho de grupo, distribuição de trabalho, respostas dos níveis e reflexão coletiva.

> **Política "no install":** Todos os exercícios podem ser feitos no AWS CloudShell (com `nano`/`vim`) ou no github.dev. Não instale nada localmente.

---

## 🟢 Nível 1 — Básico: Consolidando os Fundamentos

### Exercício 1.1 — Mapeamento de modelos de serviço

Para cada serviço, identifique se é IaaS, PaaS, SaaS ou FaaS. Justifique em uma frase.

| Serviço | Modelo (IaaS/PaaS/SaaS/FaaS) | Justificativa |
|---------|------------------------------|---------------|
| Gmail | | |
| Amazon EC2 | | |
| AWS Elastic Beanstalk (hospedar uma API) | | |
| AWS Lambda | | |
| Amazon RDS for PostgreSQL | | |
| Salesforce CRM | | |
| Google Kubernetes Engine (GKE) | | |
| Amazon S3 | | |
| Amazon Bedrock | | |

**Gabarito esperado:**

<details>
<summary>Clique para ver o gabarito</summary>

| Serviço | Modelo | Justificativa |
|---------|--------|---------------|
| Gmail | SaaS | Aplicação completa entregue ao usuário; você não gerencia nada da infra |
| Amazon EC2 | IaaS | Você gerencia SO, patches e aplicações; a AWS só fornece hardware virtualizado |
| AWS Elastic Beanstalk | PaaS | A AWS gerencia SO e runtime; você só implanta o código |
| AWS Lambda | FaaS | Você escreve apenas a função; sem servidor fixo, paga por execução |
| Amazon RDS for PostgreSQL | PaaS | A AWS gerencia o motor do banco; você gerencia dados e esquema |
| Salesforce CRM | SaaS | Aplicação completa entregue como serviço |
| GKE | PaaS/IaaS (híbrido) | Você gerencia os pods; GCP gerencia o plano de controle do K8s |
| Amazon S3 | PaaS (a maioria considera) | Storage gerenciado; você gerencia dados e políticas |
| Amazon Bedrock | SaaS / API-as-a-Service | API pronta — você consome via API sem gerenciar modelo ou infra |

</details>

---

### Exercício 1.2 — Os 6 Rs na prática

Leia cada cenário e escolha o R de migração mais adequado (Rehost, Replatform, Refactor, Repurchase, Retire, Retain). Justifique.

**Cenário A:** Empresa de logística tem sistema de rastreamento de frotas em servidor físico próprio. Código de 2008, sem documentação, só uma pessoa sabe mexer. Quer migrar rápido para ganhar elasticidade.

**Cenário B:** Banco regional usa ERP local de RH. Análise mostra: menos de 5 usuários ativos por mês, dados raramente consultados.

**Cenário C:** Fintech tem API de pagamentos monolítica. Decide aproveitar a migração para refatorar em microserviços com K8s e event-driven.

**Cenário D:** Varejo usa CRM desenvolvido internamente há 15 anos. SaaS de mercado atenderia 90% das necessidades por menor custo.

**Cenário E:** Instituição financeira tem mainframe com dados de clientes que precisa ficar on-premise por exigência do Banco Central.

---

### Exercício 1.3 — Calculando o impacto do SLA

Sistema de e-commerce com SLA de 99,9%.

a) Quantas horas de downtime por ano?
b) Se processa R$ 50.000/hora em vendas, qual o impacto financeiro máximo por ano?
c) Para reduzir o impacto para menos de R$ 50.000/ano, qual SLA mínimo seria necessário?

> **Fórmulas úteis:**
> Downtime anual (horas) = 8.760 × (1 - SLA/100)
> Downtime mensal (min) = 43.800 × (1 - SLA/100)

---

### Exercício 1.4 — IAM na prática

Você é o responsável de segurança da Quantum Commerce. Para cada perfil abaixo, escolha a política gerenciada da AWS (ou descreva a política customizada) mais adequada e justifique:

| Perfil | Política IAM mais adequada | Justificativa |
|--------|--------------------------|---------------|
| Agente de IA que LÊ produtos do S3 para responder ao cliente | | |
| Engenheiro de dados que CARREGA novos catálogos no S3 | | |
| Time de FinOps que precisa VER custos sem alterar recursos | | |
| Auditor externo que precisa LER configurações de toda a conta | | |
| Sistema de CI/CD que provisiona infraestrutura via Terraform | | |

**Referência:** [AWS managed policies for job functions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html)

<details>
<summary>Sugestões de gabarito (existem múltiplas respostas válidas)</summary>

- Agente que lê produtos: política customizada com `s3:GetObject` (e `s3:ListBucket`) restrita ao ARN do bucket/prefixo — não `AmazonS3ReadOnlyAccess`, que lê todos os buckets
- Engenheiro de dados que carrega: `s3:PutObject` restrito ao prefixo `catalogo/`
- FinOps: **AWSBillingReadOnlyAccess** (ou acesso de leitura ao Cost Explorer)
- Auditor externo: **SecurityAudit** ou **ViewOnlyAccess**, via role assumida (sem usuário IAM permanente)
- CI/CD provisionando IaC: role dedicada assumida via **OIDC** (GitHub Actions), com permissões só dos serviços do projeto — nunca `AdministratorAccess`

**Princípio:** O menor privilégio possível para a tarefa. Nunca dar `AdministratorAccess` (ou `*:*`) quando uma política restrita ao recurso basta.

</details>

---

## 🟡 Nível 2 — Intermediário: Análise e Estratégia

### Exercício 2.1 — Arquitetura de alto nível: Quantum Commerce

**Contexto:** A Quantum Commerce é um gigante do e-commerce com 12 países, 5M de SKUs, e quer transformar a experiência de compra com IA conversacional.

**Sua tarefa (em grupo):** Proponha uma arquitetura de alto nível em cloud para a QC. Identifique:

1. **Camadas da arquitetura** — quantas e o que cada uma faz (ex: frontend, API, dados, AI/ML, observabilidade)
2. **Provedor principal** — qual escolheria (Azure, AWS, GCP) e por quê
3. **Serviços por categoria** — preencha a tabela:

| Categoria | Serviço AWS | Alternativa Azure | Alternativa GCP |
|-----------|--------------|-----------------|-----------------|
| Compute (backend) | | | |
| Storage (catálogo, imagens) | | | |
| Banco relacional | | | |
| Banco NoSQL | | | |
| Vector Database | | | |
| Serviços de IA cognitivos | | | |
| CDN | | | |
| Mensageria/Filas | | | |
| Observabilidade (logs/métricas) | | | |

4. **Diagrama** — feito no Excalidraw (excalidraw.com), draw.io (diagrams.net) ou à mão fotografado. **Tudo sem instalação.**

> **Entrega:** O grupo commita o esboço (`respostas-aula01.md` + imagem do diagrama) no fork até 1 dia antes da Aula 2. O professor dá feedback escrito durante a semana. O diagrama evolui a cada aula até a entrega final na Aula 6.

---

### Exercício 2.2 — Comparativo de custos: 3 provedores

Você precisa recomendar infraestrutura para um projeto de AI Engineering. Use as calculadoras para comparar:

- 2 VMs com 2 vCPUs e 8 GB RAM (Linux, 24/7)
- 500 GB de object storage
- 1 banco gerenciado com 2 vCPUs / 8 GB RAM / 100 GB
- 10 milhões de requisições/mês para função serverless

| Item | AWS | Azure | GCP | Notas |
|------|-------|-----|-----|-------|
| 2 × VM (2vCPU/8GB) | | | | Tipo: |
| 500 GB storage | | | | Tipo: |
| Banco gerenciado | | | | Tipo: |
| 10M req serverless | | | | Tipo: |
| **Total mensal** | | | | |
| **Total anual** | | | | |

**Análise:**

a) Qual provedor ficou mais barato? A diferença é significativa?
b) Aplicando Reserved Instances de 1 ano no mais caro, o resultado muda?
c) Além de preço, que outros fatores você consideraria para um projeto de IA?

**Calculadoras:**

- AWS: https://calculator.aws
- Azure: https://azure.microsoft.com/pricing/calculator
- GCP: https://cloud.google.com/products/calculator

---

### Exercício 2.3 — Estratégia de migração para sua empresa

Pense no seu contexto profissional atual (ou empresa que conhece bem).

a) Descreva um sistema/workload (sem dados confidenciais — pode ser genérico)
b) Qual dos 6 Rs você aplicaria? Justifique custo, risco, ganho, prazo
c) Que serviço AWS usaria? Estimativa mensal?
d) Maior obstáculo técnico ou organizacional? Como endereçaria?

---

## 🔴 Nível 3 — Avançado: IaC e Automação

### Exercício 3.1 — Terraform: endurecer a segurança de rede da VM

**Tudo no CloudShell — sem instalação.**

O `main.tf` do lab (Atividade 5) já provisiona a EC2 com um security group, mas a regra de **SSH vem liberada para qualquer origem (`0.0.0.0/0`)** — uma má prática. **Modifique** o código do lab para deixá-lo mais seguro:

1. **Restrinja o SSH (porta 22)** para aceitar conexões **apenas do seu IP público** (`curl -s https://checkip.amazonaws.com` no CloudShell para obter o IP de saída). Use a variável `ssh_cidr` (ou uma nova `meu_ip`) em vez de hardcode.
2. **Crie um segundo security group** `sg-app` que só aceita a porta 8080 **vindo do security group da VM** (referência entre security groups, não CIDR) — pensando em isolar a futura camada de aplicação da QC.
3. **Adicione um output** que exponha apenas o IP público da VM (já existe `public_ip_address` — confirme que aparece após o `apply`).
4. Rode `terraform plan` e identifique no diff **exatamente** qual regra do security group mudou (não deve recriar a VM).

**Critérios:**

- `terraform plan` + `apply` rodam sem erro e **não recriam** a VM (apenas atualizam o security group)
- `terraform destroy` ao final remove tudo
- Código commitado no repositório privado do grupo

**Dica:** Documentação dos recursos:

- `aws_security_group` (bloco `ingress` → `cidr_blocks`) ou `aws_vpc_security_group_ingress_rule`
- `referenced_security_group_id` para a regra entre security groups
- variável `variable "meu_ip"` + `"${var.meu_ip}/32"`

> No CloudShell o IP de saída muda entre sessões. Se o SSH parar de funcionar, rode de novo com o IP atual — é exatamente por isso que em produção se usa **SSM Session Manager** em vez de porta 22 aberta.

---

### Exercício 3.2 — CloudFormation equivalente

Pegue o `main.tf` do lab (EC2 + security group) e **traduza para CloudFormation** — ou parta do exemplo em [`lab/cloudformation/ec2-lab.yaml`](lab/cloudformation/ec2-lab.yaml) e evolua.

**Tudo no CloudShell — a AWS CLI já tem tudo o que é preciso.**

1. Crie `template.yaml` em `~/aula01-cfn/`
2. Implemente os mesmos recursos do lab (security group + EC2 Ubuntu 24.04 + tags), incluindo o endurecimento do exercício 3.1 como **parâmetro** (`SshCidr`)
3. Faça deploy:

```bash
cd ~/aula01-cfn
aws cloudformation validate-template --template-body file://template.yaml

aws cloudformation deploy \
  --stack-name aula01-grupo \
  --template-file template.yaml \
  --parameter-overrides SshCidr="$(curl -s https://checkip.amazonaws.com)/32"

aws cloudformation describe-stacks --stack-name aula01-grupo --query "Stacks[0].Outputs"
```

4. Compare os artefatos e responda no README do grupo:
   - Quantas linhas tem cada arquivo (`main.tf` × `template.yaml`)?
   - Onde fica o **estado** em cada um? O que acontece se alguém apagar a EC2 pelo console (*drift*)? Teste `aws cloudformation detect-stack-drift`.
   - Em que cenário você escolheria CloudFormation sobre Terraform?

5. **Não esqueça:** `aws cloudformation delete-stack --stack-name aula01-grupo` ao final.

---

### Exercício 3.3 — Desafio de arquitetura: multi-cloud para a Quantum Commerce

**Contexto:** O CTO da QC quer evitar lock-in e pediu análise multi-cloud.

a) **Desenhe uma arquitetura multi-cloud** com pelo menos 2 provedores. Justifique por que cada workload em cada nuvem.

b) **Identifique 4 desafios principais**: latência entre nuvens, identidade unificada, custos de egress, observabilidade.

c) **Compare 2 ferramentas IaC multi-cloud:**
   - **Terraform** (HashiCorp) — https://www.terraform.io
   - **Pulumi** — https://www.pulumi.com

   Para cada: linguagem, pricing, suporte aos 3 grandes, quando escolher.

d) **Estime custo de egress:** 10 TB/mês entre AWS (us-east-1) e Azure (Brazil South). Consulte tabelas de preço e calcule.

> **Dica avançada:** Pesquise **AWS Outposts** e **Azure Arc** — como se encaixariam na QC?

---

## Critérios de entrega

A entrega é **um ZIP por grupo** (`entrega-grupo-NN-aula01.zip`) no Portal FIAP. Estrutura completa, prazo e dicas de geração do ZIP em [entregas/entrega-01/INSTRUCOES.md](../../entregas/entrega-01/INSTRUCOES.md).

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1, 1.2, 1.3, 1.4 respondidos | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — Exercícios 2.1 (com diagrama), 2.2, 2.3 | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — Exercícios 3.1, 3.2, 3.3 (código Terraform/CloudFormation + README) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total da entrega** | | **10 pts** (10% da nota final) |

**Prazo:** 1 dia antes da Aula 2.
**Onde:** upload do ZIP no Portal FIAP. Apenas 1 membro do grupo faz o upload.

> **Atraso:** -1 pt por dia. **Sem entrega:** zero. **Free riders:** quem não contribuir em 2+ aulas consecutivas perde participação no projeto (ver [rubrica](../../entregas/rubrica.md)).

---

## Gabarito parcial — Nível 1

### 1.2 — Os 6 Rs

<details>
<summary>Clique para ver as respostas</summary>

**Cenário A (sistema de 2008 sem doc):** **Rehost (Lift & Shift)** — migração rápida sem alterar código. Risco do único mantenedor + urgência justificam o caminho de menor esforço.

**Cenário B (ERP com 5 usuários/mês):** **Retire** — o custo de migrar provavelmente excede o valor gerado. Arquivar dados em storage frio e aposentar.

**Cenário C (API de pagamentos monolítica):** **Refactor** — decisão de reescrever em microserviços foi explícita. Alto esforço, maior ganho.

**Cenário D (CRM interno de 15 anos):** **Repurchase** — SaaS de mercado cobre 90% por menor custo. Decisão de negócio.

**Cenário E (mainframe por regulação BACEN):** **Retain** — compliance dita. Não é falha de estratégia.

</details>

### 1.3 — SLA e impacto

<details>
<summary>Clique para ver as respostas</summary>

**a)** 8.760 × (1 - 0,999) = **8,76 horas/ano** (~525 min)

**b)** 8,76 × R$ 50.000 = **R$ 438.000/ano**

**c)** Máx downtime = 50.000 ÷ 50.000 = 1h/ano → 1 ÷ 8.760 = 0,0114% → SLA mínimo **99,9886%** → na prática **SLA 99,99%** (52 min/ano)

</details>
