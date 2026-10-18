# Lab — observar a Eva em produção

A Eva está no ar. Agora a pergunta muda de "funciona?" para **"o que ela está
fazendo, quanto demora e quanto custa?"** — e a resposta mora em três lugares
diferentes, que não concordam entre si. Este lab é sobre os três e sobre a
discordância.

> **Pré-requisitos:**
>
> - A Eva publicada com o `infra/deploy.sh` (`GUIA-DEPLOY-CLI.md`).
> - Alguns minutos de conversa com ela — inclusive perguntas que usam
>   ferramenta ("que dia é hoje?") e perguntas que não usam ("o que é um
>   agente?"). Sem tráfego, toda consulta volta vazia.
> - Preços configurados (`preco_entrada_por_1m`, `preco_saida_por_1m`) se você
>   quiser custo diferente de zero.

---

## As três janelas — e por que nenhuma sozinha basta

| Janela | Onde | Sabe | Não sabe |
|---|---|---|---|
| **1. Métricas do Bedrock** | CloudWatch → *Metrics* → `AWS/Bedrock` | chamadas, tokens, latência e erros **por modelo**, sem instrumentar nada | o que é um turno; nada do provedor openai |
| **2. Log bruto da chamada** | *Model invocation logging* do Bedrock | o prompt e a resposta **completos** | custo; e guarda dado pessoal |
| **3. A telemetria da Eva** | CloudWatch Logs → `/ecs/eva/<sufixo>` | turno, iteração, tokens, custo estimado, erro | o preço real |

> **No Learner Lab** (provedor openai) só a janela 3 existe — e é por isso que
> ela foi escrita. As janelas 1 e 2 ficam para a demonstração do professor,
> numa conta com Bedrock.

---

## Parte 1 — Métricas do Bedrock: o que existe sem instrumentar nada

**Conta comum, com o provedor bedrock.** Console → **CloudWatch** → *Metrics*
→ *All metrics* → **AWS/Bedrock** → *By ModelId*.

| Métrica | O que é | Estatística útil |
|---|---|---|
| `Invocations` | chamadas bem-sucedidas | Sum |
| `InputTokenCount` / `OutputTokenCount` | tokens cobrados | Sum |
| `InvocationLatency` | latência da chamada | p50, p95 |
| `InvocationThrottles` | chamadas barradas por cota | Sum |
| `InvocationClientErrors` / `InvocationServerErrors` | erros 4xx / 5xx | Sum |

### As três armadilhas da Parte 1

1. **A dimensão é o `ModelId` que você chamou.** Se a Eva usa o perfil
   `us.amazon.nova-lite-v1:0`, procure por ele — não pelo ID nu do modelo.
2. **Throttle não aparece como erro na tela da Eva.** O boto3 tenta de novo
   (`mode=adaptive`) e a resposta só demora mais. A métrica é o único lugar
   onde isso aparece.
3. **Granularidade de 1 minuto.** Para uma conversa de teste, use período de
   1 minuto e estatística *Sum* — a média de 5 minutos esconde tudo.

### Exercício

Converse com a Eva por 2 minutos e encontre o pico de `OutputTokenCount`.
Qual pergunta gerou ele?

---

## Parte 2 — Model invocation logging: o log bruto da chamada

Bedrock → **Settings** → **Model invocation logging** → ligue, destino
**CloudWatch Logs**, log group `/bedrock/invocacoes`, com uma role que possa
escrever nele.

A partir daí, **toda chamada** grava o prompt e a resposta completos. É o que
se usa para auditar e depurar ("o que exatamente o modelo recebeu?").

> ⚠️ **Isto é dado do usuário.** O log guarda tudo que foi digitado — inclusive
> dado pessoal. Quem tem leitura no CloudWatch vê. É custo (GB ingerido) **e**
> LGPD. Ligue para a aula, defina retenção curta e **desligue depois**.

Compare uma linha do log bruto com a linha da Eva para o mesmo turno: o que
um tem que o outro não tem?

---

## Parte 3 — A telemetria da Eva: o que só existe porque você instrumentou

### 3.0 — Como chegar na tela

1. Console → **CloudWatch** → **Logs** → **Logs Insights**.
2. Em *Select log group(s)*, escolha `/ecs/eva/<sufixo>` (o output
   `log_group_name` do Terraform).
3. Janela de tempo: **1h** (ou o tempo desde que você conversou).
4. Cole a consulta e **Run query**.

#### 3.0.0 — A primeira consulta: uma chamada por linha

```
fields @timestamp, turno_id, iteracao, modelo, duracao_ms,
       tokens_entrada, tokens_saida, custo_estimado_usd, erro
| filter evento = "eva.chamada_modelo"
| sort @timestamp desc
| limit 50
```

Repare que linhas com o **mesmo `turno_id`** e `iteracao` 1, 2... são a mesma
pergunta dando voltas no laço. É a unidade que nenhuma métrica de plataforma
enxerga.

#### 3.0.1 — O erro que todo mundo comete uma vez

O log group tem **duas coisas misturadas**: a saída do Streamlit ("You can now
view your Streamlit app...") e as linhas JSON da Eva. Esquecer o
`filter evento = "eva.chamada_modelo"` faz as agregações somarem campos
inexistentes — e o `stats` devolve um número que parece certo e não é.

#### 3.0.2 — Se a consulta rodar e vier vazia

| Sintoma | Causa provável |
|---|---|
| Nem as linhas do Streamlit aparecem | log group errado, ou janela de tempo antes do deploy |
| Só aparecem linhas do Streamlit | `EVA_TELEMETRIA` não chegou como `stdout` na task definition |
| Aparecem linhas, `custo_estimado_usd` = 0 | preços em 0 no `terraform.tfvars` |
| Tudo certo, mas atrasado | o driver `awslogs` entrega em segundos; o Insights às vezes leva um minuto |

#### 3.0.3 — Sem console, direto do terminal

```bash
LOGS=$(cd ../infra/terraform && terraform output -raw log_group_name)

# acompanhar ao vivo, só a telemetria
aws logs tail "$LOGS" --follow --filter-pattern '{ $.evento = "eva.chamada_modelo" }'

# custo por turno (a consulta do LAB-FINOPS, já empacotada)
bash ../infra/custo.sh 1
```

### O mapa: do seu código para o campo

| No código (`telemetria.py`) | No Logs Insights |
|---|---|
| `novo_turno()` em `responder*()` | `turno_id` |
| a volta do `for` do laço | `iteracao` |
| `params["modelId"]` | `modelo` |
| `perf_counter()` em volta da chamada **inteira** (inclusive o stream) | `duracao_ms` |
| `usage.inputTokens` / `outputTokens` | `tokens_entrada` / `tokens_saida` |
| `custo_estimado()` com os preços da task definition | `custo_estimado_usd` |
| o tipo da exceção, se houve | `erro` (e `falhou` = 0 ou 1) |

### 3.1 — Volume e latência

```
filter evento = "eva.chamada_modelo"
| stats count(*) as chamadas, avg(duracao_ms) as media_ms,
        pct(duracao_ms, 50) as p50_ms, pct(duracao_ms, 95) as p95_ms
  by bin(5m)
```

Clique em **Visualization** → *Line*. Por que o p95 é tão maior que o p50?
(Dica: compare `streaming = true` com `false`, e chamadas com muitos tokens de
saída.)

### 3.2 — Tokens, por modelo e por tipo

```
filter evento = "eva.chamada_modelo"
| stats sum(tokens_entrada) as entrada, sum(tokens_saida) as saida by modelo
```

Troque o modelo na barra lateral da Eva, converse um pouco e rode de novo.

### 3.3 — Custo estimado acumulado

```
filter evento = "eva.chamada_modelo"
| stats sum(custo_estimado_usd) as custo by bin(15m)
```

### 3.4 — O que quebrou

```
filter evento = "eva.chamada_modelo" and falhou = 1
| stats count(*) as falhas by erro, modelo
```

Provoque um erro de propósito: na barra lateral, troque o model ID por
`modelo-que-nao-existe` e mande uma pergunta. Que valor apareceu em `erro`?

### 3.5 — Iterações por turno (a consulta que justifica o lab)

```
filter evento = "eva.chamada_modelo"
| stats count(*) as iteracoes, sum(custo_estimado_usd) as custo by turno_id
| sort iteracoes desc
| limit 20
```

Nenhuma métrica de plataforma responde isto, porque o Bedrock não sabe que as
três chamadas de um turno são da mesma pergunta. **O turno é um conceito do
seu código** — só o seu código pode medi-lo.

### 3.6 — O histórico crescendo

Faça uma conversa longa (10 perguntas, sem "Nova conversa") e rode:

```
filter evento = "eva.chamada_modelo"
| fields @timestamp, iteracao, tokens_entrada
| sort @timestamp asc
```

Visualize como linha. Os tokens de entrada **sobem monotonicamente**: cada
pergunta reenvia tudo o que veio antes. É o 3.1 do `LAB-FINOPS.md`, desenhado.

---

## Parte 4 — Cruzar as janelas: a discrepância que ensina

Na mesma janela de tempo (conta comum), compare:

| Fonte | Número |
|---|---|
| `AWS/Bedrock` → `OutputTokenCount` (Sum) | tokens que o serviço contou |
| Logs Insights → `sum(tokens_saida)` | tokens que a Eva contou |

Eles vão divergir. Explique cada diferença. As causas mais comuns:

- o `verificar.py` também chamou o modelo (e também gerou log, se a
  telemetria estava ligada);
- uma retentativa do boto3 conta como duas invocações no serviço e uma
  chamada na Eva;
- chamadas feitas local, sem `EVA_TELEMETRIA`, contam só no serviço.

---

## Parte 5 — Custo: token não é dinheiro

`custo_estimado_usd` é **token × preço que você digitou**. Ele não sabe de:

- tier (*Priority* custa mais, *Flex* menos);
- **cache** de prompt (token lido do cache custa uma fração);
- inferência entre regiões com sobrepreço (perfil regional vs. global);
- mudança de tabela de preço.

Por isso a linha leva o nome **estimado**. Escreva isso no seu painel.

---

## Parte 6 — Três alarmes que valem a pena

| Alarme | Sobre | Por quê |
|---|---|---|
| **Tokens de saída por hora** | filtro de métrica em `tokens_saida` (5.2 do `LAB-FINOPS.md`) | agente em laço não dá erro — só gasta |
| **Erros da Eva** | filtro de métrica `{ $.evento = "eva.chamada_modelo" }` com `metricValue=$.falhou` | a tela engole o erro; o log, não |
| **Throttles** (conta com Bedrock) | `AWS/Bedrock` → `InvocationThrottles` | o primeiro sinal de que a cota ficou pequena |

---

## Exercícios

1. **Primeira consulta** (3.0.0): quantas chamadas e quantos turnos você fez?
2. **O p95** (3.1): qual é a latência p95 da Eva? O que explica a cauda?
3. **Iterações** (3.5): qual pergunta deu mais voltas no laço? Por quê?
4. **O histórico** (3.6): em quantas perguntas os tokens de entrada dobraram?
5. **A discrepância** (Parte 4, conta comum): explique cada diferença.
6. **Instrumente as ferramentas.** Emita uma linha
   `{"evento": "eva.ferramenta", "turno_id", "nome", "duracao_ms"}` em
   `executar_ferramenta()` e responda com dado: qual ferramenta é a mais
   lenta, e quantas vezes cada uma é chamada? (Exige passar o `turno_id` até
   lá — repare como isso muda a assinatura de quem chama.)

---

## Limites honestos deste setup

- **Sem rastreamento distribuído.** Não há trace/span: uma linha por chamada
  basta para custo e iterações, mas não mostra o tempo de cada ferramenta (o
  exercício 6 começa a resolver). O passo seguinte é OpenTelemetry com o
  AWS Distro (ADOT) mandando traces para o X-Ray / CloudWatch.
- **Sem amostragem.** Toda chamada vira linha. Em volume real, a saída é
  *sampling* — e é uma decisão de FinOps disfarçada de decisão técnica.
- **Log misturado.** Streamlit e telemetria no mesmo log group. Em produção,
  separe (outro stream, outro log group, ou EMF para métricas).
- **O preço é digitado.** Ver a Parte 5.

---

## Sources

- [Monitor Amazon Bedrock with Amazon CloudWatch](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring.html)
- [Model invocation logging](https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html)
- [CloudWatch Logs Insights query syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [Using the awslogs log driver (ECS)](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_awslogs.html)
- [Filter and pattern syntax for metric filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)
