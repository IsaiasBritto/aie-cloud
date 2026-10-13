# Lab — FinOps na Eva: da régua à tesoura

Este lab é a continuação direta do `LAB-OBSERVABILIDADE.md`. Lá você montou a
**régua**: linhas de telemetria, tokens, iterações, custo estimado. Aqui você
usa a régua para **decidir** — que é o trabalho que a Aula 06 chama de FinOps.

> **Como ele se encaixa na Aula 06.** O bloco de *token economics* da Aula 06
> deixa de ser teoria: há um sistema de IA medido para analisar — a Eva que a
> turma acabou de publicar. O Lab 3 da Aula 06 usa **exatamente** as consultas
> da Parte 2 deste arquivo (sobre uma amostra pronta, para quem não tiver
> tráfego próprio).

> **Pré-requisitos:**
>
> - A Eva publicada e usada por alguns minutos (`GUIA-DEPLOY-CLI.md`).
> - `preco_entrada_por_1m` e `preco_saida_por_1m` preenchidos no
>   `terraform.tfvars` com os preços do **seu** modelo. Enquanto estiverem em
>   `0`, o custo estimado sai zero — é assim de propósito.
> - As tags aplicadas pelo `default_tags` do Terraform (`projeto`, `ambiente`,
>   `responsavel`, `centro-custo`, `aula`). Sem tag não há alocação, e sem
>   alocação não há FinOps.

---

## Por que FinOps em IA não é FinOps de infraestrutura

Em infraestrutura você paga por **capacidade provisionada**: a instância custa
a mesma coisa ociosa ou a 100%. A otimização é encaixar a capacidade na
demanda — right-sizing, Savings Plans, lifecycle.

Num agente, você paga por **uso**, e o uso é decidido pelo **seu código**. Cada
linha que você acrescenta no `agent.md` entra na conta de toda chamada, para
sempre. Cada ferramenta nova gasta uma volta a mais no laço. Cada mensagem de
histórico é reenviada inteira na próxima pergunta.

A frase que vale a aula:

> **Em infraestrutura, o custo é uma consequência da arquitetura.
> Num agente, o custo é uma consequência do prompt.**

---

## As três fontes de número — e qual serve para quê

| Fonte | Granularidade | Atraso | Serve para | No Learner Lab |
| --- | --- | --- | --- | --- |
| **Billing / Cost Explorer** | serviço / dia, por tag | até 24 h | **pagar** e cobrar | ❌ não liberado |
| **Métricas `AWS/Bedrock`** | modelo / minuto, em tokens | minutos | entender **consumo** | ❌ (sem Bedrock) |
| **Logs da Eva** (o seu) | **turno**, em dólar estimado | segundos | **decidir agora** | ✅ |

As três discordam, e a Parte 4 é sobre isso. Guarde desde já a regra:
**para decidir, vale o seu número; para faturar, vale o do provedor.**

---

## Parte 1 — INFORM: onde o dinheiro da Eva está

### 1.1 — Custo pelas tags que você já aplicou

**Conta comum** (no Learner Lab, pule para o 1.2): Billing → **Cost allocation
tags** → ative `projeto`, `responsavel`, `ambiente` e `centro-custo`. Elas só
aparecem no Cost Explorer **depois de ativadas** e só para gastos **a partir
da ativação** — tag ativada hoje não pinta o passado.

Depois, **Cost Explorer** → *Group by* **Tag** e observe o que cada uma
responde:

| Agrupar por | A pergunta que responde |
| --- | --- |
| `projeto` | quanto a Eva custou, separada do resto da conta |
| `responsavel` | quanto **cada pessoa** gastou — é chargeback de verdade |
| `ambiente` | o que é experimento (`aula`) e o que seria produção |
| `centro-custo` | a visão que a diretoria pede |
| **Service** | a decomposição do 1.3 |

### 1.2 — Cobertura de marcação: recurso sem tag é custo sem dono

Funciona no Learner Lab (Resource Groups Tagging API):

```bash
# Tudo que tem a tag projeto=eva
aws resourcegroupstaggingapi get-resources --tag-filters Key=projeto,Values=eva \
  --query 'ResourceTagMappingList[].ResourceARN' --output table
```

Compare com o que o Terraform diz que criou:

```bash
cd ../infra/terraform && terraform state list
```

O que está no state e **não** aparece na primeira lista é recurso sem dono na
fatura. Nem tudo aceita tag — `random_string`, `aws_iam_role_policy`,
`aws_ecr_lifecycle_policy` e `aws_secretsmanager_secret_version` ficam de fora,
e nenhum deles aparece na fatura. Confira a lista antes de sair caçando
fantasma. O mesmo dá para ver pelo console em **Resource Groups & Tag Editor**.

### 1.3 — A decomposição que surpreende: modelo × plataforma

| Peça | Como cobra | O que costuma acontecer num lab |
| --- | --- | --- |
| **Bedrock** (ou OpenAI) | por token | o custo que a turma acha que é "o custo" |
| **ECS Fargate** | vCPU-hora + GB-hora, **ligado ou não** | 0,5 vCPU + 1 GB ≈ US$ 0,025/h ≈ **US$ 18/mês** parado |
| **IPv4 público** | US$ 0,005/h por IP | ≈ US$ 3,60/mês — o custo que ninguém lembra |
| **CloudWatch Logs** | GB ingerido + armazenado | cresce com o tráfego, igual ao modelo |
| **ECR** | GB armazenado | centavos (a lifecycle policy guarda 5 imagens) |
| **Secrets Manager** | por segredo/mês + chamadas | US$ 0,40/mês |

**A pergunta do exercício:** com o tráfego de uma aula, quem ganha — o modelo
ou a tarefa Fargate ligada? Faça a conta com os seus números. (Spoiler de
método, não de resultado: com pouco tráfego, **capacidade parada** costuma
vencer **token**. Com muito tráfego, inverte.)

---

## Parte 2 — A unidade econômica: custo por turno

Aqui está o número que nenhuma ferramenta de plataforma consegue calcular,
porque só o seu código sabe o que é um "turno".

**Onde:** console → **CloudWatch** → **Logs Insights** → log group
`/ecs/eva/<sufixo>` (o output `log_group_name`). Ou pelo terminal:
`bash ../infra/custo.sh`.

### 2.1 — O número

```
filter evento = "eva.chamada_modelo"
| stats sum(custo_estimado_usd) as custo_turno,
        count(*) as iteracoes,
        sum(tokens_entrada) as tokens_in,
        sum(tokens_saida) as tokens_out
  by turno_id
| stats count(*) as turnos,
        avg(custo_turno) as custo_medio,
        pct(custo_turno, 95) as custo_p95,
        max(custo_turno) as custo_max,
        sum(custo_turno) as custo_total,
        avg(iteracoes) as iteracoes_medias
```

**Leia o p95, não a média.** A média é o que você paga num dia normal; o p95 é
o que você paga quando o uso muda. Num agente essa distância é grande, porque
o turno caro não é "um pouco maior" — ele deu quatro voltas no laço reenviando
o histórico inteiro em cada uma.

### 2.2 — Quanto custa uma ferramenta

Num agente a unidade interessante não é o serviço — é a **funcionalidade**:

```
filter evento = "eva.chamada_modelo"
| stats sum(custo_estimado_usd) as custo_turno, count(*) as iteracoes by turno_id
| stats count(*) as turnos, avg(custo_turno) as custo_medio, sum(custo_turno) as custo_total
  by iteracoes
| sort iteracoes asc
```

A linha `iteracoes = 1` é a resposta direta; as de cima usaram ferramenta. A
diferença entre elas é **o preço unitário de dar uma ferramenta ao agente** —
um número que se leva para uma reunião de produto: "essa funcionalidade custa
X por uso — vale?"

### 2.3 — Do custo por turno ao custo mensal

```
custo_medio_por_turno  ×  turnos por usuário por dia  ×  usuários  ×  30
                       +  custo fixo da plataforma (Fargate + IP + logs)
```

Faça também o cenário do p95: **se todo turno fosse como o p95, quanto seria?**
A distância entre os dois cenários é o seu risco de custo — e é ela que
justifica o alarme da Parte 5.

---

## Parte 3 — OPTIMIZE: as cinco alavancas de um agente

### 3.1 — O histórico é o custo

Num turno de **5 iterações** com um histórico de **3.000 tokens**, você não
paga 3.000 de entrada: paga cerca de **15.000**, porque o histórico inteiro
volta a cada iteração — junto com o `agent.md`, o `memory.md` e a descrição de
todas as ferramentas.

```
filter evento = "eva.chamada_modelo"
| stats sum(tokens_entrada) as entrada, sum(tokens_saida) as saida
```

Divida `entrada` por `saida`. Ver `20` é comum. Como entrada e saída têm
preços diferentes (no Nova Lite, 4×; no Claude, 5×), essa proporção decide
**onde** otimizar: encurtar prompt ou encurtar resposta.

### 3.2 — O prompt de sistema tem preço mensal

1. Conte os tokens do seu `agent.md` (aproximação: caracteres ÷ 4).
2. Multiplique pela média de iterações por turno (o `iteracoes_medias` do 2.1).
3. Multiplique pelos turnos por mês da conta do 2.3.
4. Multiplique pelo preço de entrada por milhão.

O resultado é **quanto custa por mês cada parágrafo do seu system prompt**.
Não é argumento para escrever prompt ruim — é argumento para escrever prompt
**enxuto**, que costuma ser melhor pelos dois motivos ao mesmo tempo.

### 3.3 — Teto de iterações é controle de custo, não só de segurança

`EVA_MAX_ITERACOES` (padrão `5`) é também o **teto de gasto por turno**.
Dimensione com dado, não com chute:

```
filter evento = "eva.chamada_modelo"
| stats count(*) as iteracoes by turno_id
| stats pct(iteracoes, 50) as p50, pct(iteracoes, 95) as p95,
        pct(iteracoes, 99) as p99, max(iteracoes) as maximo
```

Se `maximo` for `5`, alguém foi cortado no meio de uma resposta. Se o `p99`
for `2`, o seu teto de `5` protege contra um cenário que não acontece — e você
pode baixá-lo sem custo de qualidade.

### 3.4 — Capacidade parada: a alavanca que o Fargate não puxa sozinho

Na versão Azure, `min-replicas 0` desligava o contêiner sem uso. **O ECS não
faz isso**: a tarefa Fargate cobra enquanto existe, com ou sem pergunta. As
opções, da mais simples à mais elaborada:

```bash
# Desligar ao fim da aula (religar: --desired-count 1)
aws ecs update-service --cluster <ecs_cluster_name> --service eva --desired-count 0
```

- **Agendar** o desligamento (EventBridge Scheduler chamando `UpdateService`).
- **Trocar de serviço**: Lambda ou App Runner escalam a zero — com cold start
  e outras restrições (o Streamlit precisa de WebSocket).
- **Fargate Spot**: até ~70% mais barato, interrompível. Serve para lab.

**Essa decisão é de FinOps, não de infraestrutura.** O preço do zero é o
cold start; em aula ele é obviamente bom, em produção com usuário esperando
talvez não.

### 3.5 — As estratégias de desconto, traduzidas para IA

| Estratégia (infra) | Equivalente no Bedrock | O que muda |
| --- | --- | --- |
| On-Demand | **On-demand**, por token (tier Standard) | o que a Eva usa. Sem compromisso |
| Reserved / Savings Plans | **Provisioned Throughput** | capacidade dedicada por hora, com ou sem uso. Compromisso de 1 ou 6 meses |
| Spot | **Batch inference** (~50% off) e tier **Flex** | assíncrono ou com latência variável. Serve para lote, não para chat |
| Prioridade | tier **Priority** (mais caro) | latência mais estável quando a região está carregada |
| Right-sizing | escolher o modelo e encurtar o prompt | a alavanca de sempre, e a mais barata |
| — | **Prompt caching** | sem paralelo em infra: token lido do cache custa uma fração |

E para a plataforma: **Compute Savings Plans cobrem Fargate**. A Eva tem as
duas faturas — modelo e capacidade — e cada uma tem o seu desconto.

---

## Parte 4 — A conta que não fecha (e por que isso é o exercício)

Compare, na mesma janela (conta comum):

| Fonte | O número |
| --- | --- |
| Cost Explorer, tag `projeto = eva` | custo real, em dólar |
| CloudWatch → `AWS/Bedrock` → `InputTokenCount` / `OutputTokenCount` | tokens contabilizados pelo serviço |
| Logs Insights, `sum(custo_estimado_usd)` | a sua estimativa |

**Os três vão divergir.** Causas típicas:

- **Retentativa do boto3** (`mode=adaptive`): a chamada que tomou throttling e
  repetiu é cobrada uma vez, mas medida como uma chamada só.
- **Telemetria desligada** num período (rodou local sem `EVA_TELEMETRIA`).
- **O `verificar.py`** também gasta token — e também aparece nos logs.
- **A tag não pega token.** O consumo do Bedrock on-demand não carrega as tags
  dos seus recursos; para alocar custo de modelo por projeto, use um
  **application inference profile** com tags (exercício 7).
- **O Cost Explorer atrasa.** Gastar e olhar em seguida não funciona.

A conclusão que a turma leva: **todo painel de custo de IA é uma estimativa, e
quase nenhum escreve isso na tela.** O seu vai escrever.

---

## Parte 5 — OPERATE: três controles, do mais simples ao mais importante

### 5.1 — Budget (conta comum)

Billing → **Budgets** → *Create budget* → *Cost budget*, filtro **Tag
`projeto = eva`**, alertas em 50%, 80% e 100%. É o nível **Crawl**: necessário
e insuficiente sozinho — o budget avisa **depois** de gastar, com horas de
atraso. No Learner Lab o Budgets não é liberado; o controle de lá é o saldo
do próprio lab.

### 5.2 — Alarme de tokens por hora (o que o budget não pega)

**Um agente em laço não derruba nada — ele só gasta.** Não há erro, não há
lentidão. Funciona no Learner Lab, a partir dos logs da Eva:

```bash
LOGS=$(cd ../infra/terraform && terraform output -raw log_group_name)

# 1. Filtro de métrica: transforma o campo tokens_saida em métrica
aws logs put-metric-filter --log-group-name "$LOGS" \
  --filter-name eva-tokens-saida \
  --filter-pattern '{ $.evento = "eva.chamada_modelo" }' \
  --metric-transformations \
    metricName=TokensSaida,metricNamespace=Eva,metricValue='$.tokens_saida',defaultValue=0

# 2. Alarme: mais de 50 mil tokens de saída em 1 hora
aws cloudwatch put-metric-alarm --alarm-name eva-tokens-saida-hora \
  --namespace Eva --metric-name TokensSaida --statistic Sum \
  --period 3600 --evaluation-periods 1 --threshold 50000 \
  --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching
```

Ajuste o limite ao seu pico normal (use o 2.1). Em conta comum, acrescente
`--alarm-actions <ARN de um tópico SNS>` para receber e-mail. Este é o cinto
de segurança que o `EVA_MAX_ITERACOES` não dá: ele protege **um turno por
vez**, e o alarme protege **o dia**.

> Na conta comum, com Bedrock, dá para alarmar direto na métrica nativa
> `AWS/Bedrock` → `OutputTokenCount` — sem filtro de métrica. O filtro sobre o
> log vale para os dois provedores, e é o que funciona no Learner Lab.

### 5.3 — O controle mais eficaz de todos: apagar

Em ambiente de aula, a maior economia não é otimizar — é **desprovisionar**:

```bash
cd ../infra/terraform && terraform destroy -auto-approve
```

E para achar o que sobrou de alguém (ou de você, semana passada):

```bash
aws resourcegroupstaggingapi get-resources --tag-filters Key=ambiente,Values=aula \
  --query 'ResourceTagMappingList[].ResourceARN' --output text
```

> Repare que essa busca só funciona porque a tag foi aplicada na **criação**,
> por código (`default_tags`). Tag colocada depois, na mão, sempre esquece
> alguém. É o argumento prático para tag em IaC — e ele é de FinOps.

---

## Parte 6 — Maturidade: onde a Eva está hoje

| Nível | O que exige | A Eva tem? |
| --- | --- | --- |
| **Crawl** | tags + budget | ✅ tags por `default_tags` em todo recurso; budget na 5.1 (conta comum) |
| **Walk** | dashboards + otimização aplicada | ✅ Logs Insights, alarme de tokens, teto de iterações, retenção de 7 dias |
| **Run** | chargeback + KPI + retro mensal | ⚠️ **metade.** `responsavel` permite chargeback e o custo por turno já é KPI. Falta o **ritual**: alguém olhar todo mês e decidir algo |

O que falta não é ferramenta — é cadência.

---

## Exercícios

1. **Ache o maior gastador da Eva** (1.3). Com o tráfego da aula, foi o modelo
   ou a capacidade parada? Mostre a conta.
2. **Calcule o custo por turno** (2.1) e o custo mensal projetado (2.3) para
   100 usuários fazendo 10 turnos por dia. Apresente média **e** p95.
3. **Precifique o seu system prompt** (3.2). Quanto custa por mês cada
   parágrafo do `agent.md`?
4. **Dimensione o `EVA_MAX_ITERACOES` com dado** (3.3).
5. **Meça o preço de uma ferramenta** (2.2).
6. **Crie o alarme da 5.2** e faça-o disparar de propósito (baixe o limite
   para 100 e converse com a Eva). Quanto tempo levou para o estado mudar?
7. **O difícil — custo de modelo com dono.** Numa conta comum, crie um
   *application inference profile* com a tag `projeto=eva`, aponte o
   `bedrock_model_id` para o ARN dele e mostre o custo do modelo aparecendo
   por tag no Cost Explorer.

### O entregável

```
finops-eva/
├── analise-custo-eva.md          # top 3 gastadores + por que cada um
├── custo-por-turno.md            # média, p95, projeção mensal, memória de cálculo
├── otimizacoes-propostas.md      # 3 alavancas escolhidas + o quanto cada uma economiza
└── consultas-logs-insights.txt   # as consultas que você de fato usou
```

Em `otimizacoes-propostas.md`, a pergunta que fecha a disciplina:
**como você apresentaria esses números ao CFO — em um parágrafo, sem jargão?**

---

## Limites honestos deste lab

- **O custo estimado é estimativa.** Preço fixo em variável de ambiente não
  sabe de desconto, de tier, de cache, nem de mudança de tabela.
- **Sem amostragem, a telemetria não escala.** Toda chamada vira linha de log,
  e o CloudWatch cobra por GB ingerido.
- **`turno_id` não é a conversa.** Para o custo de uma conversa inteira seria
  preciso um identificador de sessão — e aí entra a discussão de privacidade.
- **Sem usuário identificado, não há "quem gastou mais" dentro da
  aplicação.** A tag `responsavel` resolve na camada de infraestrutura.
- **Preço de modelo muda.** A página de preços do Bedrock é a fonte, não este
  arquivo.

---

## Sources

- [FinOps Framework — FinOps Foundation](https://www.finops.org/framework/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
- [Monitoring Amazon Bedrock with CloudWatch](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring.html)
- [CloudWatch Logs Insights query syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [Creating metric filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringPolicyExamples.html)
- [AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [Application inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
