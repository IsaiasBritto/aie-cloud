# Lab — FinOps na Eva: da régua à tesoura

Este lab é a continuação direta do `LAB-OBSERVABILIDADE.md`. Lá você montou a
**régua**: spans, tokens, iterações, custo estimado. Aqui você usa a régua para
**decidir** — que é o trabalho que a Aula 06 chama de FinOps.

> **Como ele se encaixa na Aula 06.** O Bloco 3 do material de FinOps —
> *token economics, modelos idle, cache semântico* — é o único bloco marcado
> como **teoria apenas**, porque não havia um sistema de IA medido para
> analisar. Agora há. Este lab transforma aquele bloco em prática, com a Eva
> que a turma acabou de publicar e o dado da assinatura de cada aluno.

> **Pré-requisitos:**
>
> - A Eva publicada e usada por alguns minutos (`LAB-OBSERVABILIDADE.md`).
> - `EVA_PRECO_ENTRADA_POR_1M` e `EVA_PRECO_SAIDA_POR_1M` preenchidos com os
>   preços do **seu** modelo, na **sua** região. Enquanto estiverem em `0`, o
>   custo estimado sai zero — é assim de propósito.
> - As tags aplicadas pelos guias de deploy (`projeto`, `ambiente`,
>   `centro-custo`, `responsavel`, `criado-por`, `criado-em`, `descartavel`,
>   `aluno`). Sem tag não há alocação, e sem alocação não há FinOps.

---

## Por que FinOps em IA não é FinOps de infraestrutura

Em infraestrutura você paga por **capacidade provisionada**: a VM custa a
mesma coisa ociosa ou a 100%. A otimização é encaixar a capacidade na demanda —
right-sizing, reserva, lifecycle.

Num agente, você paga por **uso**, e o uso é decidido pelo **seu código**. Cada
linha que você acrescenta no `agent.md` entra na conta de toda chamada, para
sempre. Cada ferramenta nova gasta uma volta a mais no laço. Cada mensagem de
histórico é reenviada inteira na próxima pergunta.

A frase que vale a aula:

> **Em infraestrutura, o custo é uma consequência da arquitetura.
> Num agente, o custo é uma consequência do prompt.**

É por isso que "every engineer is FinOps now" fica literal aqui: quem escreve o
system prompt está escrevendo a fatura.

---

## As três fontes de número — e qual serve para quê

| Fonte | Granularidade | Atraso | Serve para |
| --- | --- | --- | --- |
| **Cost Management** | recurso / dia, por tag | horas | **pagar** e cobrar |
| **Metrics do Foundry** | deployment / minuto, em tokens | minutos | entender **consumo** |
| **Application Insights** (o seu) | **turno**, em dólar estimado | 2–5 min | **decidir agora** |

As três discordam, e a Parte 4 é sobre isso. Guarde desde já a regra:
**para decidir, vale o seu número; para faturar, vale o do provedor.**

---

## Parte 1 — INFORM: onde o dinheiro da Eva está

### 1.1 — Custo pelas tags que você já aplicou

**Onde:** portal → **Cost Management + Billing** → **Cost analysis**.

1. **Date range:** desde o início da disciplina.
2. **Granularity:** Daily.
3. **Group by:** **Tag** → `projeto`.

Depois troque o *Group by* e observe o que cada tag responde:

| Agrupar por | A pergunta que responde |
| --- | --- |
| `projeto` | quanto a Eva custou, separada do resto da assinatura |
| `aluno` | quanto **cada pessoa da turma** gastou — é chargeback de verdade |
| `ambiente` | o que é experimento (`aula`) e o que seria produção |
| `centro-custo` | a visão que a diretoria pede |
| **Service name** | a decomposição do 1.3 |

> A tag `aluno` é o exemplo mais concreto de *chargeback* que dá para mostrar
> em sala: mesma assinatura, mesma arquitetura, e ainda assim cada um vê a
> própria conta. É o que separa o nível **Run** do **Crawl** na escala de
> maturidade — e custou uma linha no `deploy.ps1`.

> **Por que este passo é no portal, e não por comando.** A API de Cost
> Management limita de forma agressiva e **a cota é compartilhada**: sem o
> cabeçalho `ClientType`, você divide o balde com todo mundo no mundo que
> também não manda — dá para tomar `429 Too many requests` na primeira
> chamada. Existe o `infra/custo.ps1`, que manda o `ClientType` e tenta de novo
> com espera crescente, mas ele é para **automação**, não para trinta pessoas
> consultando ao vivo. O portal não passa por essa cota.
>
> Fica a lição de arquitetura: **cota compartilhada é uma dependência que não
> aparece no diagrama.** Vale a pergunta para a turma — que outras cotas desta
> solução são compartilhadas? (O TPM do deployment do Foundry e o limite de um
> ambiente do Container Apps por região são duas.)

### 1.2 — Cobertura de marcação: recurso sem tag é custo sem dono

```powershell
az resource list -g rg-eva-<seu-sufixo> --query "[?tags.projeto==null].name" -o tsv
```

Saída vazia é o resultado esperado. Qualquer nome que apareça é um recurso que
**existe na fatura e não existe em nenhum relatório** — o modo mais comum de
uma conta de nuvem crescer sem responsável.

> Nem tudo aceita tag: `role assignment`, `random_string`, `time_sleep` e
> `time_static` ficam de fora. Nenhum deles aparece na fatura, então a ausência
> não custa nada. Vale conferir a lista antes de sair caçando fantasma.

### 1.3 — A decomposição que surpreende: modelo × plataforma

Ainda no *Cost analysis*, filtre pela tag `projeto = eva-agente` e agrupe por
**Service name**. Você vai ver, em alguma ordem:

| Recurso | O que costuma acontecer num lab |
| --- | --- |
| **Azure OpenAI / AI Services** | o custo do que a turma acha que é "o custo" |
| **Log Analytics** | cobrado por **GB ingerido** — cresce com o tráfego, igual ao modelo |
| **Container Apps** | com `min-replicas 0`, quase nada parado |
| **Container Registry** | fixo e pequeno (Basic) |
| **Key Vault** | centavos, por operação |

**A pergunta do exercício:** na sua assinatura, qual desses é o maior?

Não vou dizer o resultado — depende do seu tráfego, e a graça é medir. Mas
guarde a implicação: **observabilidade tem custo, e ele cresce junto com o
uso.** Em produção, com telemetria de toda chamada e sem amostragem, o
Application Insights pode disputar a liderança com o modelo. Ligar telemetria é
uma decisão de FinOps tanto quanto escolher o modelo.

---

## Parte 2 — A unidade econômica: custo por turno

Aqui está o número que nenhuma das ferramentas de plataforma consegue calcular,
porque só o seu código sabe o que é um "turno".

### 2.1 — O número

**Onde:** portal → `eva-appi` → **Monitoring → Logs** (veja o 4.0 do
`LAB-OBSERVABILIDADE.md` se ainda não sabe chegar nessa tela).

```kusto
dependencies
| where timestamp > ago(7d) and name == "eva.chamada_modelo"
| extend custo   = todouble(customDimensions["eva.custo_estimado_usd"]),
         entrada = toint(customDimensions["eva.tokens.entrada"]),
         saida   = toint(customDimensions["eva.tokens.saida"])
| summarize custo_turno = sum(custo),
            iteracoes   = count(),
            tokens_in   = sum(entrada),
            tokens_out  = sum(saida)
        by operation_Id
| summarize turnos           = count(),
            custo_medio      = avg(custo_turno),
            custo_p95        = percentile(custo_turno, 95),
            custo_max        = max(custo_turno),
            custo_total      = sum(custo_turno),
            iteracoes_medias = avg(iteracoes)
```

**Leia o p95, não a média.** A média é o que você paga num dia normal; o p95 é
o que você paga quando o uso muda. Num agente essa distância é grande, porque
o turno caro não é "um pouco maior" — ele deu quatro voltas no laço reenviando
o histórico inteiro em cada uma.

### 2.2 — Quanto custa uma ferramenta

O deck pede o "top 3 maiores gastadores" por serviço. Num agente a unidade
interessante não é o serviço — é a **funcionalidade**:

```kusto
dependencies
| where timestamp > ago(7d) and name == "eva.chamada_modelo"
| extend custo = todouble(customDimensions["eva.custo_estimado_usd"])
| summarize custo_turno = sum(custo), iteracoes = count() by operation_Id
| extend classe = iif(iteracoes > 1, "com ferramenta", "resposta direta")
| summarize turnos      = count(),
            custo_medio = avg(custo_turno),
            custo_total = sum(custo_turno)
        by classe
```

A diferença entre as duas linhas é **o preço unitário de dar uma ferramenta ao
agente**. É um número que se leva para uma reunião de produto: "essa
funcionalidade custa X por uso — vale?"

### 2.3 — Do custo por turno ao custo mensal

```
custo_medio_por_turno  ×  turnos por usuário por dia  ×  usuários  ×  30
```

Três números, um deles medido e dois estimados por você. É a conta que a
diretoria pede, e é honesta desde que você diga qual parte é medida.

Faça também o cenário do p95: **se todo turno fosse como o p95, quanto seria?**
A distância entre os dois cenários é o seu risco de custo — e é ela que
justifica o alerta da Parte 5.

---

## Parte 3 — OPTIMIZE: as cinco alavancas de um agente

### 3.1 — O histórico é o custo

Esta é a alavanca que a maioria das pessoas não enxerga. Num turno de **5
iterações** com um histórico de **3.000 tokens**, você não paga 3.000 de
entrada: paga cerca de **15.000**, porque o histórico inteiro volta a cada
iteração — junto com o `agent.md`, o `memory.md` e a descrição de todas as
ferramentas.

O gráfico que prova isso é o 4.6 do lab de observabilidade: numa conversa
longa, a linha de tokens de entrada **sobe monotonicamente**. Vale projetar.

Confirme a desproporção na sua própria conversa:

```kusto
dependencies
| where timestamp > ago(7d) and name == "eva.chamada_modelo"
| extend entrada = toint(customDimensions["eva.tokens.entrada"]),
         saida   = toint(customDimensions["eva.tokens.saida"])
| summarize entrada = sum(entrada), saida = sum(saida)
| extend proporcao = round(todouble(entrada) / todouble(saida), 1)
```

Ver `20` nessa coluna é comum. Como entrada e saída têm preços diferentes, essa
proporção é o que decide **onde** otimizar: encurtar prompt ou encurtar
resposta. Otimizar o lado errado é trabalho jogado fora.

### 3.2 — O prompt de sistema tem preço mensal

Um exercício de três minutos que muda a forma como a turma escreve prompt:

1. Conte os tokens do seu `agent.md` (aproximação boa o suficiente:
   caracteres ÷ 4).
2. Multiplique pela média de iterações por turno (o `iteracoes_medias` do 2.1).
3. Multiplique pelos turnos por mês da conta do 2.3.
4. Multiplique pelo preço de entrada por milhão.

O resultado é **quanto custa por mês cada parágrafo do seu system prompt**.
Não é argumento para escrever prompt ruim — é argumento para escrever prompt
**enxuto**, que costuma ser melhor pelos dois motivos ao mesmo tempo.

### 3.3 — Teto de iterações é controle de custo, não só de segurança

`EVA_MAX_ITERACOES` (padrão `5`) é normalmente apresentado como proteção contra
laço infinito. Ele é também o **teto de gasto por turno**: sem ele, um turno
sozinho pode custar o dia inteiro.

Dimensione com dado, não com chute:

```kusto
dependencies
| where timestamp > ago(30d) and name == "eva.chamada_modelo"
| summarize iteracoes = count() by operation_Id
| summarize p50 = percentile(iteracoes, 50),
            p95 = percentile(iteracoes, 95),
            p99 = percentile(iteracoes, 99),
            no_limite = countif(iteracoes >= 5)
```

Se `no_limite` for maior que zero, alguém foi cortado no meio de uma resposta.
Se o `p99` for `2`, o seu teto de `5` está protegendo contra um cenário que não
acontece — e você pode baixá-lo sem custo de qualidade.

### 3.4 — Scale-to-zero: a única alavanca que o deck já ensinava

O material da Aula 06 usa o exemplo do *ML Endpoint 24/7 → scale-to-zero, queda
de 95%*. Na Eva isso já está aplicado: `min-replicas 0` no Container App. O
contêiner some quando ninguém usa e sobe na primeira requisição.

O preço disso é o **cold start** — a primeira pergunta depois de um período
parado demora mais. É o trade-off clássico, e num ambiente de aula ele é
obviamente bom. Em produção com usuário esperando, `min-replicas 1` pode valer
o custo. **Essa decisão é de FinOps, não de infraestrutura.**

Confira quanto isso está de fato economizando: no *Cost analysis*, filtre por
`Service name = Azure Container Apps` e olhe a curva diária.

### 3.5 — As estratégias de desconto, traduzidas para IA

O deck traz a tabela clássica de compute (Pay-as-you-go / Reserved / Spot /
Savings Plan / Right-sizing). Ela tem equivalente no mundo de modelos — e uma
linha que não existe em infraestrutura:

| Estratégia (infra) | Equivalente em IA | O que muda |
| --- | --- | --- |
| Pay-as-you-go | **Standard**, pago por token | o que a Eva usa. Sem compromisso, sem SLA de latência |
| Reserved Instances | **PTU** (Provisioned Throughput Units) **+ Azure Reservations** | capacidade dedicada, preço fixo por PTU/hora. Reservas de 1 mês ou 1 ano com desconto |
| Spot (barato, interrompível) | **Batch** | processamento assíncrono a tarifa reduzida. Serve para lote, não para chat |
| Right-sizing | escolher o modelo e encurtar o prompt | a alavanca de sempre, e a mais barata de aplicar |
| — | **Prompt caching** | não tem paralelo em infra: token vindo do cache não consome capacidade |

Dois detalhes que valem em sala:

- **Reserva não garante capacidade.** A própria documentação manda criar o
  deployment primeiro, confirmar que há capacidade, e só depois comprar a
  reserva para travar o preço. Comprar antes é assinar um compromisso sobre
  algo que talvez não exista na sua região.
- **PTU é caro se ocioso.** Ele inverte o modelo: você passa a pagar por
  capacidade, esteja usando ou não. Só compensa acima de um volume — e achar
  esse ponto de equilíbrio é, literalmente, o trabalho do FinOps Engineer.

Para a Eva em sala, **Standard é o certo**. A tabela existe para a turma saber
o que perguntar quando o volume crescer.

---

## Parte 4 — A conta que não fecha (e por que isso é o exercício)

Compare, na mesma janela:

| Fonte | O número |
| --- | --- |
| Cost Management, tag `projeto` | custo real, em dólar |
| Metrics do Foundry, `TokenTransaction` | tokens contabilizados pelo serviço |
| App Insights, `eva.custo_estimado_usd` | a sua estimativa |

**Os três vão divergir.** As causas estão detalhadas na Parte 5 do
`LAB-OBSERVABILIDADE.md` — retry do SDK, streaming sem `include_usage`,
telemetria desligada por um período. Some a essas duas específicas de FinOps:

- **O Cost Management atrasa horas.** Gastar e olhar em seguida não funciona.
- **A granularidade é o recurso, não o deployment.** Dois modelos no mesmo
  recurso do Foundry aparecem numa linha só. Para separar custo por modelo, ou
  separa o recurso, ou usa a métrica de tokens.

A conclusão que a turma leva: **todo painel de custo de IA é uma estimativa, e
quase nenhum escreve isso na tela.** O seu vai escrever.

---

## Parte 5 — OPERATE: três controles, do mais simples ao mais importante

### 5.1 — Budget alert (o do deck, apontado para a Eva)

Portal → **Cost Management** → **Budgets** → **+ Add**.

- **Scope:** o seu grupo `rg-eva-<seu-sufixo>` (não a assinatura inteira — a
  graça é isolar a Eva).
- **Name:** `budget-eva`
- **Amount:** o que sobrou do seu crédito, ou `$5`
- **Alert conditions:** 50%, 80%, 100%
- **Recipients:** o seu e-mail

Isso é o nível **Crawl**. Necessário, e insuficiente sozinho: o budget avisa
depois de gastar.

### 5.2 — Alerta de tokens por hora (o que o budget não pega)

**Um agente em laço não derruba nada — ele só gasta.** Não há erro, não há
lentidão, não há alerta de disponibilidade. Você descobre no fechamento do mês.

Portal → recurso do Foundry → **Monitoring → Alerts** → **+ Create** →
métrica `TokenTransaction`, agregação *Total*, janela de 1 hora, limite acima
do seu pico normal (use o 2.1 para saber qual é).

Este é o cinto de segurança que o `EVA_MAX_ITERACOES` não dá: ele protege **um
turno por vez**, e este protege **o dia**.

### 5.3 — O controle mais eficaz de todos: apagar

Em ambiente de aula, a maior economia não é otimizar — é **desprovisionar**. As
tags `descartavel=sim` e `criado-em` existem exatamente para isso.

No portal → **Resource Graph Explorer**:

```kusto
Resources
| where tags['descartavel'] == 'sim'
| where todatetime(tags['criado-em']) < ago(7d)
| project name, type, resourceGroup, tags['aluno'], tags['criado-em']
```

Tudo que aparecer aí é candidato a sumir:

```powershell
az group delete --name rg-eva-<seu-sufixo> --yes --no-wait
```

> Repare no que essa consulta só é possível porque a tag `criado-em` foi
> aplicada na **criação**, por código. Tag colocada depois, na mão, não
> responde "há quanto tempo isso está aqui". É o argumento prático para tag em
> IaC — e ele é de FinOps, não de organização.

---

## Parte 6 — Maturidade: onde a Eva está hoje

Usando a escala Crawl / Walk / Run da Aula 06:

| Nível | O que exige | A Eva tem? |
| --- | --- | --- |
| **Crawl** | tags + budget alert | ✅ tags aplicadas por código nos três caminhos de deploy; budget na 5.1 |
| **Walk** | dashboards + otimização aplicada | ✅ o `LAB-OBSERVABILIDADE.md` inteiro; `min-replicas 0`; teto de iterações |
| **Run** | chargeback + KPI + retro mensal | ⚠️ **metade.** A tag `aluno` já permite chargeback e o custo por turno já é um KPI. Falta o **ritual**: alguém olhar todo mês e decidir algo |

O que falta não é ferramenta — é cadência. É exatamente o ponto do deck de que
a maioria das empresas **para no Inform**: elas têm o painel, e ninguém abre.

---

## Exercícios

1. **Ache o maior gastador da Eva.** Cost analysis, tag `projeto`, agrupado por
   *Service name*. Foi o modelo? Foi o Log Analytics? Explique **por quê**.
2. **Calcule o custo por turno** (2.1) e o custo mensal projetado (2.3) para
   100 usuários fazendo 10 turnos por dia. Apresente média **e** p95.
3. **Precifique o seu system prompt** (3.2). Quanto custa por mês cada
   parágrafo do `agent.md`?
4. **Dimensione o `EVA_MAX_ITERACOES` com dado** (3.3). Qual valor cobre 95%
   dos turnos reais? Compare com o padrão `5` e justifique mudar ou manter.
5. **Meça o preço de uma ferramenta** (2.2). Quanto custa, por uso, dar essa
   capacidade ao agente?
6. **Provoque a divergência** (Parte 4). Compare as três fontes na mesma
   janela e explique cada diferença encontrada.
7. **O difícil — o ponto de equilíbrio do PTU.** A partir de quantos turnos por
   dia a capacidade provisionada ficaria mais barata que o pago por token? Use
   a página de preços do Azure OpenAI e o seu custo por turno medido.

### O entregável

Seguindo o padrão da disciplina:

```
finops-eva/
├── analise-custo-eva.md          # top 3 gastadores + por que cada um
├── custo-por-turno.md            # média, p95, projeção mensal, memória de cálculo
├── otimizacoes-propostas.md      # 3 alavancas escolhidas + o quanto cada uma economiza
└── consultas.kql                 # as consultas que você de fato usou
```

Em `otimizacoes-propostas.md`, a pergunta que fecha a disciplina:
**como você apresentaria esses números ao CFO — em um parágrafo, sem jargão?**

---

## Limites honestos deste lab

- **O custo estimado é estimativa.** Preço fixo em variável de ambiente não
  sabe de desconto, de reserva, nem de mudança de tabela. Serve para decidir,
  não para faturar.
- **Sem amostragem, a telemetria não escala.** Toda chamada vira log. Em volume
  real, a saída é *sampling* — que troca precisão por conta menor, e é uma
  decisão de FinOps disfarçada de decisão técnica.
- **`operation_Id` é a requisição HTTP, não a conversa.** Serve para o custo do
  turno; para o custo de uma conversa inteira seria preciso um identificador
  próprio, propagado como atributo — e aí entra a discussão de privacidade.
- **Sem `user_Id`, não há "quem gastou mais" dentro da aplicação.** A tag
  `aluno` resolve isso na camada de infraestrutura, não na de uso.
- **Preço de modelo muda.** Qualquer número deste lab tem prazo de validade;
  a página de preços do Azure OpenAI é a fonte, não este arquivo.

---

## Sources

- [FinOps Framework — FinOps Foundation](https://www.finops.org/framework/)
- [Provisioned throughput (PTU) — Microsoft Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/provisioned-throughput)
- [Azure OpenAI Service — Pricing](https://azure.microsoft.com/en-us/pricing/details/azure-openai/)
- [Monitoring data reference for Azure OpenAI](https://learn.microsoft.com/en-us/azure/foundry/openai/monitor-openai-reference)
- [Cost Management — analisar custo por tag](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/group-filter)
- [Azure Resource Graph Explorer](https://learn.microsoft.com/en-us/azure/governance/resource-graph/first-query-portal)
