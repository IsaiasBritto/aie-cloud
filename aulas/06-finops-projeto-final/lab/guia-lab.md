# Guia de Laboratório — Aula 6

**Tema:** FinOps + Trabalho no Projeto Integrado
**Plataforma:** AWS Academy Learner Lab (console + CloudShell) + AWS Pricing Calculator

---

## Visão geral do lab

```
Lab 1 — Tag Editor + Trusted Advisor (+ Cost Explorer e Budget na tela do professor)  ~25 min  (L₁)
Lab 2 — AWS Pricing Calculator: TCO da arquitetura QC                                ~30 min  (L₂)
Lab 3 — FinOps na Eva: custo por turno no CloudWatch Logs Insights                   ~35 min  (L₃)
Trabalho assistido em grupo — projeto integrado final                                ~1h40
```

**Sem destroy hoje** — o trabalho é principalmente **analítico**. A única coisa que o
Lab 3 cria é um log group com retenção de 7 dias (centavos, e some sozinho).

> **O que o Learner Lab libera, e o que não.** Tag Editor, Trusted Advisor (checagens
> do plano Basic), CloudWatch e CloudShell: ✅. **Cost Explorer e Budgets: ❌** — o
> professor mostra na conta dele. O "budget" de vocês é o **crédito do Learner Lab**,
> visível na página do lab.

---

## Preparação (3 min — antes do L₁)

1. Learner Lab → **Start Lab** → bolinha **verde** → **AWS** → região **us-east-1**.
2. Abra o **CloudShell** e atualize o repositório:

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git ~/aie-cloud 2>/dev/null || git -C ~/aie-cloud pull
aws sts get-caller-identity --query Arn --output text
```

3. Abra em outra aba: [calculator.aws](https://calculator.aws) (não precisa de login).

---

## Lab 1 — Análise de custo: Tag Editor + Trusted Advisor

**Objetivo:** aplicar o **Inform** e o **Optimize** do FinOps na sua conta do Learner
Lab: onde o crédito foi gasto, o que ainda está vivo, e o que a AWS recomenda.

### Passo 1 — Quanto do crédito já foi (Inform)

1. Página do **Learner Lab** → anote o **crédito consumido** (o indicador de budget).
2. **Na tela do professor** — Billing → **Cost Explorer**: últimos 30 dias, *Daily*,
   *Group by* **Service**. Top 3 da conta dele × o que vocês subiram nas Aulas 1–5.

> Para a maioria, o gasto é pequeno: free tier + `destroy` ao fim de cada aula. Se
> algum item está alto, é um aprendizado real — anote qual e por quê.

### Passo 2 — O que ainda está vivo, por aula (Tag Editor)

Console → **Resource Groups & Tag Editor** → **Tag Editor**:

- Regions: `us-east-1` · Resource types: **All supported resource types**
- Tags: chave **`aula`** (sem valor) → **Search resources**

Vocês colocam essa tag desde a Aula 1 (`default_tags` do Terraform). A lista mostra
**o que sobrou de cada aula**. Repita com `projeto` = `quantum-commerce`, `eva`, `deva3`.

Pelo CloudShell, o mesmo:

```bash
aws resourcegroupstaggingapi get-resources --tag-filters Key=aula \
  --query 'ResourceTagMappingList[].{arn: ResourceARN, aula: Tags[?Key==`aula`]|[0].Value}' \
  --output table
```

> **Detalhe da AWS:** numa conta comum, a tag só aparece no **Cost Explorer** depois
> de ativada em *Billing → Cost allocation tags*, e só dali para a frente. Tag ativada
> hoje não pinta o gasto de ontem.

### Passo 3 — Trusted Advisor (Optimize)

Console → busque **Trusted Advisor** → categoria **Cost optimization**.

No suporte **Basic** (o do Learner Lab), as checagens de custo aparecem **bloqueadas**
(exigem Business); as de **segurança** e **limites de serviço** ficam liberadas. As
recomendações de custo mais comuns, quando liberadas:

- EC2 com baixa utilização (right-sizing)
- Reserved Instances e Savings Plans aplicáveis
- Volumes EBS e Elastic IPs sem uso
- RDS ocioso e load balancer sem tráfego

Anote, para a seção `finops/analise-otimizacao.md` do projeto final, o que apareceu
(ou ficou bloqueado) na sua conta.

> Checagem bloqueada? Tudo bem — o aprendizado é saber **onde** consultar.

### Passo 4 — Budget (demo do professor)

Billing → **Budgets** → *Create budget* → *Cost budget*:

- Name: `budget-aula06` · Amount: **US$ 5** · Period: Monthly
- Alertas: **50%, 80% e 100% (real)** + **100% (previsto)** → e-mail
- Bônus: **ação** em 100% — aplicar uma política IAM que nega criar recursos

> O budget avisa **depois** e com **horas de atraso**. Ele não é freio — é alarme.

### Passo 5 — Discussão (5 min)

- Alguém do grupo já gastou boa parte do crédito do Learner Lab? Em quê?
- O que vocês fariam diferente se começassem a disciplina de novo?
- Como isso se aplica à arquitetura de uma empresa em escala?

**✅ Checkpoint L₁:** top 3 identificado + recursos vivos por aula + o que o Trusted
Advisor mostrou (ou bloqueou).

---

## Lab 2 — AWS Pricing Calculator: TCO da QC

**Objetivo:** estimar o **custo mensal** da arquitetura completa da Quantum Commerce
em **escala real** (não free tier). Este resultado entra no projeto integrado final
(seção `finops/`). **Vale como entrega final de FinOps** — pode ser feito em grupo,
na aula ou depois.

### Cenário da QC

Você é arquiteto cloud apresentando à diretoria da QC. Estime o TCO mensal com:

| Componente | Volume mensal esperado |
|------------|------------------------|
| **Amazon S3** | 10 TB (5 TB Standard + 3 TB Standard-IA + 2 TB Glacier Deep Archive) — imagens + logs |
| **Amazon RDS** | PostgreSQL db.r6g.xlarge (4 vCPU) **Multi-AZ** + 100 GB gp3 |
| **Amazon DynamoDB** | Provisionado: 2.000 RCU + 500 WCU + 50 GB |
| **OpenSearch** | Amazon OpenSearch Service: 3 nós r6g.large.search (3 AZs) + 1 TB gp3 |
| **AWS Lambda** | 5M req/mês · 512 MB · 300 ms + **Provisioned Concurrency 2** (sempre quente) |
| **Serviços de IA** | Comprehend: 1M análises de sentimento + Transcribe: 5.000 h + Rekognition: 500 mil imagens |
| **Amazon SageMaker AI** | Notebook ml.t3.medium ocasional + 1 endpoint de inferência ml.m5.xlarge (**24/7**) |
| **Amazon CloudWatch** | 5 GB de logs/mês |
| **Data transfer out** | 500 GB/mês saindo para CDN externa |

### Passo 1 — Adicionar cada serviço

1. Em [calculator.aws](https://calculator.aws) → **Create estimate** → adicione os
   **9 itens** acima, um por um.
2. Região **US East (N. Virginia)** para tudo (padrão da disciplina).
3. Preencha os volumes da tabela. Dê a cada item um **nome** e um **grupo**
   (ex.: grupo "Dados", "IA", "Compute") — a exportação sai organizada.

### Passo 2 — Calcular o total

1. **View summary** → total mensal em USD (e o "first 12 months")
2. Converta para BRL (cotação do dia)
3. Anote os **3 itens mais caros**

### Passo 3 — Otimização hipotética

Para cada item do top 3, proponha uma otimização:

| Item caro | Otimização proposta | Economia estimada |
|-----------|---------------------|-------------------|
| | | |
| | | |
| | | |

Exemplos comuns:

- **Comprehend:** trocar por um modelo pequeno no Bedrock em **lote** (batch, −50%),
  se a tarefa for mais que sentimento
- **Endpoint SageMaker 24/7:** **Serverless Inference** ou **Batch Transform** (paga
  só quando roda) — vocês fizeram isso na Aula 5
- **Egress:** **CloudFront** na frente do S3 — a transferência S3 → CloudFront não é cobrada
- **Lambda com Provisioned Concurrency:** voltar ao sob demanda se o cold start for
  aceitável (o custo fixo vai a zero)
- **S3:** *Intelligent-Tiering* ou lifecycle mais agressivo (a Aula 2 já tinha)

### Passo 4 — Exportar

1. **Export** → **CSV** (ou PDF)
2. Salvar como `finops/estimativa-qc.csv` no repositório privado do grupo
3. **Share** → copiar o link público
4. Guardar o link em `finops/pricing-calculator-link.md`

### Passo 5 — Comparar com Reserved Instances e Savings Plans

Para os itens **24/7** (RDS, OpenSearch, Lambda com Provisioned Concurrency se mantida,
endpoint SageMaker):

1. Reabra a estimativa → **Edit** em cada item 24/7
2. Troque o modelo de preço para **Reserved** (RDS, OpenSearch) ou **Savings Plans**
   (Compute SP cobre Lambda; *SageMaker Savings Plans* cobre o endpoint), 1 ou 3 anos
3. Compare a economia

**Reflexão (escrever em `finops/analise-otimizacao.md`):**

a) Qual o TCO mensal estimado em USD da arquitetura QC sem otimização?
b) Qual o TCO otimizado (com suas 3 propostas aplicadas)?
c) Qual a economia % com compromisso de 1 ano (RI ou Savings Plans)?
d) **Como você apresentaria esses números ao CFO da QC** (em 1 parágrafo)?

**✅ Checkpoint L₂:** estimativa exportada (`.csv`) + análise de 3 otimizações + cenário com compromisso.

---

## Lab 3 — FinOps na Eva: custo por turno

**Objetivo:** aplicar **Inform** e **Optimize** num log real de agente. Descobrir onde
o dinheiro está, calcular o **custo por turno** e propor três otimizações **com número**.

A régua já está pronta: a Eva do professor (Aula 5, `03-agente-Eva-aws`) mediu
tokens, iterações e latência de cada chamada ao modelo. O arquivo
[`finops/eva-amostra.jsonl`](finops/eva-amostra.jsonl) tem ~200 chamadas (~125 turnos),
no mesmo formato que a `telemetria.py` escreve no CloudWatch.

### Passo 1 — Carregar o log

Os preços **não** vêm no arquivo: você informa os do modelo (Amazon Nova Lite,
us-east-1, na página de preços do Bedrock). Sem preço, o custo sai zero — de propósito.

```bash
cd ~/aie-cloud/aulas/06-finops-projeto-final/lab
export EVA_PRECO_ENTRADA_POR_1M=0.06     # confira na página de preços
export EVA_PRECO_SAIDA_POR_1M=0.24
bash finops/carregar-amostra.sh
```

O script cria o log group **`/eva/turnos`** (retenção 7 dias, tag `projeto=eva`) e
envia o log com os horários deslocados para as últimas ~27 horas.

> Publicou a sua própria Eva na Aula 5? Use o log group dela (`/ecs/eva/<sufixo>`)
> nas consultas abaixo — o formato é o mesmo.

### Passo 2 — Onde o dinheiro está

- **Tela do professor:** Cost Explorer por tag `projeto`, depois `responsavel`, depois *Service*.
- **Na sua conta:** Tag Editor → *All supported resource types* → busque recursos
  **sem** a tag `projeto` (*Tag key* `projeto`, valor *(not tagged)*). Lista vazia é o
  esperado: qualquer recurso ali é **custo sem dono**.

Pergunta: no top 3 do professor, quem ganhou — o **modelo** ou a **observabilidade**
(CloudWatch)? E a **tarefa Fargate ligada**?

### Passo 3 — Custo por turno

CloudWatch → **Logs** → **Logs Insights** → log group **`/eva/turnos`** → janela
**últimas 48 h**:

```
filter evento = "eva.chamada_modelo"
| stats sum(custo_estimado_usd) as custo_turno, count(*) as iteracoes by turno_id
| stats count(*) as turnos, avg(custo_turno) as custo_medio,
        pct(custo_turno, 95) as custo_p95, avg(iteracoes) as iteracoes_medias
```

É a consulta do 2.1 do
[`LAB-FINOPS.md`](../../05-bedrock-agents/03-agente-Eva-aws/Documentacao/LAB-FINOPS.md).
Registre **média, p95 e iterações médias**. As outras consultas (preço de uma
ferramenta, entrada × saída, teto de iterações, falhas) estão em
[`finops/consultas-logs-insights.txt`](finops/consultas-logs-insights.txt).

> **Leia o p95, não a média.** A média é o dia normal; o p95 é o que você paga quando
> o uso muda — o turno que deu quatro voltas no laço reenviando o histórico inteiro.

### Passo 4 — Projete o custo mensal

```
custo médio por turno × turnos por usuário por dia × usuários × 30
```

Faça **duas vezes**: com a média e com o p95. A distância entre os dois é o seu
**risco de custo**.

### Passo 5 — Precifique o system prompt

1. Tokens do `agent.md` ≈ caracteres ÷ 4
   (`wc -c ~/aie-cloud/aulas/05-bedrock-agents/03-agente-Eva-aws/agent.md`)
2. × iterações médias por turno × turnos por mês × preço de entrada por token

Resultado: **quanto custa por mês cada parágrafo** que alguém escreveu no prompt.

### Passo 6 — Os dois controles do Operate

1. **Budget** filtrado pela tag `projeto = eva`, em 50 / 80 / 100% (demo do professor).
2. **Filtro de métrica + alarme** — funciona no Learner Lab:

```bash
aws logs put-metric-filter --log-group-name /eva/turnos \
  --filter-name eva-tokens-saida \
  --filter-pattern '{ $.evento = "eva.chamada_modelo" }' \
  --metric-transformations \
    metricName=TokensSaida,metricNamespace=Eva,metricValue='$.tokens_saida',defaultValue=0

aws cloudwatch put-metric-alarm --alarm-name eva-tokens-saida-hora \
  --namespace Eva --metric-name TokensSaida --statistic Sum \
  --period 3600 --evaluation-periods 1 --threshold 20000 \
  --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching
```

O filtro só conta eventos **novos**. Rode o `carregar-amostra.sh` de novo e, em alguns
minutos, veja a métrica `Eva / TokensSaida` em CloudWatch → *Metrics* e o estado do
alarme em *Alarms*.

> **Um agente em laço não derruba nada — ele só gasta.** Não há erro, não há
> lentidão. O alarme por hora é o cinto de segurança que o `EVA_MAX_ITERACOES` não
> dá: o teto protege **um turno**; o alarme protege **o dia**.

### O entregável

```
finops-eva/
├── analise-custo-eva.md          # top 3 + modelo × observabilidade × capacidade
├── custo-por-turno.md            # média, p95, projeção mensal (2 cenários), memória de cálculo
├── otimizacoes-propostas.md      # 3 alavancas + quanto cada uma economiza
└── consultas-logs-insights.txt   # as consultas que você de fato usou, com o resultado
```

A pergunta que fecha a disciplina: **como você apresentaria esses números ao CFO —
em um parágrafo, sem jargão?**

### Limpeza (opcional)

```bash
aws cloudwatch delete-alarms --alarm-names eva-tokens-saida-hora
aws logs delete-log-group --log-group-name /eva/turnos
```

(Sem isso, o log group se esvazia sozinho em 7 dias.)

---

## Trabalho assistido em grupo (1h40)

**Esta é a parte mais valiosa da Aula 6.** O professor está disponível em tempo real.

### Checklist do projeto integrado final

#### Documentação

- [ ] `README.md` com visão geral da arquitetura, links de cada componente, instruções de execução
- [ ] `arquitetura/diagrama-final.png` exportado do Excalidraw/draw.io
- [ ] `arquitetura/decisoes-tecnicas.md` com ADRs (mínimo 5 decisões)
- [ ] `reflexao-estrategica.md` com roadmap de 12 meses para evolução da arquitetura QC
- [ ] `distribuicao-do-trabalho.md` com rastreio de quem fez o quê em cada aula + no projeto final

#### Infraestrutura

- [ ] `terraform/main.tf` consolidado provisionando a infra QC (S3, RDS + pgvector, DynamoDB, Secrets Manager, Lambda + Function URL, ECR/ECS, bucket e Registry do SageMaker)
- [ ] `terraform/variables.tf` + `terraform/outputs.tf`
- [ ] `terraform validate` e `terraform plan` sem erros (validado durante a aula)

#### Lambda e tools

- [ ] `function/lambda_function.py` (ou `function_app.py` com Powertools) com as 5 tools: `/produtos`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`, `/recomendar`
- [ ] `function/requirements.txt` atualizado
- [ ] `tools-spec.md` com JSON Schema das 5 tools (formato `toolSpec` da Converse ou function calling)

#### FinOps

- [ ] `finops/estimativa-qc.csv` exportado do AWS Pricing Calculator (Lab 2)
- [ ] `finops/analise-otimizacao.md` com top 3 itens caros + propostas + comparação com Reserved / Savings Plans
- [ ] `finops/pricing-calculator-link.md` com o link compartilhável da estimativa
- [ ] `finops-eva/` do Lab 3 (opcional no projeto, recomendado)

> Detalhes completos: [entregas/projeto-final/INSTRUCOES.md](../../../entregas/projeto-final/INSTRUCOES.md).

### Conversas comuns que você terá com o professor

- "Nosso Terraform não consolida porque cada aula virou pasta separada — como mesclar?"
- "Como documentar as 5 tools sem virar um documento de 100 páginas?"
- "Em FinOps, qual a maior otimização possível na arquitetura QC?"
- "Faltou X da Aula Y, dá tempo de fazer agora?"

### Tópicos que podem precisar de mini-revisão (sob demanda)

- Terraform com módulos (consolidação de várias aulas em um projeto)
- Roles e `default_tags` (o padrão que se repete em todas as aulas)
- Preço do Bedrock (por token) × Comprehend (por unidade de texto)
- Endpoint SageMaker serverless × instância × Batch Transform

---

## Encerramento da Aula 6

- **Prazo final:** 1 semana após esta aula
- Entrega: **Portal FIAP**, tarefa "Projeto Integrado Final"
- ZIP **< 20 MB** (sem `terraform.tfstate`, sem `.terraform/`, sem áudios, sem imagens grandes)
- Rubrica: [entregas/rubrica.md](../../../entregas/rubrica.md)
- Instruções: [entregas/projeto-final/INSTRUCOES.md](../../../entregas/projeto-final/INSTRUCOES.md)

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Tag Editor não acha nada | Região errada (use `us-east-1`) ou tudo já foi destruído — ótimo sinal |
| Trusted Advisor com checagens de custo bloqueadas | Esperado no suporte Basic. Registre isso na análise |
| Pricing Calculator sem um tipo de instância em N. Virginia | Use o mais próximo e registre a troca na análise |
| Estimativa muito alta (> US$ 10k/mês) | Revise volumes — Transcribe (5.000 h) e OpenSearch costumam disparar |
| Estimativa muito baixa (< US$ 500/mês) | Revise volumes — provavelmente ficou free tier em algum item |
| `carregar-amostra.sh`: "Sem credencial AWS" | Learner Lab desligado — Start Lab e reabra o CloudShell |
| Logs Insights volta vazio | Janela de tempo curta: use **48 h**; confira o log group `/eva/turnos` |
| `custo_estimado_usd` zerado | Os `EVA_PRECO_*` não estavam exportados. Exporte e rode o carregador de novo (stream novo) |
| Métrica `Eva/TokensSaida` não aparece | O filtro só conta eventos posteriores a ele: rode o carregador de novo |

---

## Referências

- [AWS Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
- [Cost allocation tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
- [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [AWS Trusted Advisor](https://docs.aws.amazon.com/awssupport/latest/user/trusted-advisor.html)
- [AWS Pricing Calculator](https://calculator.aws)
- [Savings Plans](https://docs.aws.amazon.com/savingsplans/latest/userguide/what-is-savings-plans.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [FinOps Foundation Framework](https://www.finops.org/framework/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
