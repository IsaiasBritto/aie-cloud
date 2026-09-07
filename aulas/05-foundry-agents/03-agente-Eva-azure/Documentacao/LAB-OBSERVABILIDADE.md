# Lab — observar a Eva em produção

Este lab não cria nada. Ele responde perguntas sobre o que **já está rodando**:

- Quantas chamadas a Eva fez, e quanto cada uma demorou?
- Quantos tokens foram consumidos, e quanto isso custou?
- Quantas **iterações** o agente gastou por pergunta?
- O que quebrou, quando, e por quê?

> Pré-requisito: a Eva publicada no Container Apps (pelo portal, pela CLI ou
> pelo Terraform) e usada por alguns minutos. Telemetria sem tráfego é uma tela
> vazia — mande umas quinze perguntas antes de começar, incluindo uma que force
> ferramenta ("que horas são?") e uma que force erro (peça um deployment que
> não existe na barra lateral).

---

## As três janelas — e por que nenhuma sozinha basta

| Janela | O que ela sabe | O que ela **não** sabe |
| --- | --- | --- |
| **ai.azure.com** (Foundry) | o que o *modelo* recebeu e devolveu | que existe um agente, um loop, uma conversa |
| **portal.azure.com → Metrics** | métricas de plataforma: requisições, tokens, latência, 429 | o que a sua aplicação achou disso |
| **Application Insights** (KQL) | o que **você instrumentou**: iterações, custo estimado, ferramentas | o que o serviço contabilizou de fato |

A frase que vale a aula: **o Foundry mede o serviço, o Application Insights
mede a sua aplicação, e os dois discordam.** A Parte 5 é sobre essa diferença —
e é ali que o lab fica interessante.

```
        ┌────────────── você instrumentou ──────────────┐
        │  telemetria.py → OpenTelemetry → App Insights │
        │  spans, iterações, custo estimado, ferramentas│
        └───────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────────┐
        │   a plataforma mede sozinha, sem seu código   │
        │   ai.azure.com  ·  Azure Monitor Metrics      │
        └───────────────────────────────────────────────┘
```

---

## Parte 1 — ai.azure.com: o que existe sem instrumentar nada

**Onde:** [ai.azure.com](https://ai.azure.com) → seu projeto → **Deployments** →
o deployment (`eva-aula`) → aba de métricas/monitoramento.

O portal do Foundry mostra, por deployment e sem uma linha de código sua:
requisições, tokens de entrada e de saída, latência, e a utilização contra a
cota (TPM/RPM).

### O exercício da Parte 1

Mande cinco perguntas na Eva e olhe a contagem de **requisições**. Depois
mande **uma** pergunta que force ferramenta ("que horas são?").

Pergunta para a turma: **a contagem subiu quanto?**

Subiu **dois**. Uma pergunta com ferramenta são duas chamadas ao modelo — a que
pede a ferramenta e a que lê o resultado. É o loop do agente aparecendo na
fatura.

E aqui está o limite desta janela: para o Foundry, foram duas requisições
independentes. Ele não sabe que pertencem ao mesmo turno, nem que existe um
agente. **Quem sabe disso é só o seu código** — e é por isso que a Parte 4
existe.

---

## Parte 2 — portal.azure.com → Metrics: as métricas de plataforma

**Onde:** [portal.azure.com](https://portal.azure.com) → seu recurso do Foundry
→ **Monitoring → Metrics**.

As mesmas informações da Parte 1, mas consultáveis, combináveis, com filtro,
divisão por dimensão e — o que importa — **alertáveis**.

### As métricas que interessam

| Métrica | Para quê |
| --- | --- |
| `AzureOpenAIRequests` | volume. Divida por `StatusCode` e o 429 aparece sozinho |
| `ProcessedPromptTokens` | tokens de entrada |
| `GeneratedTokens` | tokens de saída |
| `TokenTransaction` | total processado (entrada + saída) |
| `AzureOpenAITimeToResponse` | latência até a resposta |
| `AzureOpenAINormalizedTTFTInMS` | tempo até o **primeiro** byte — é o que o usuário sente no streaming |
| `AzureOpenAINormalizedTBTInMS` | tempo **entre** tokens — a "velocidade de digitação" |
| `AzureOpenAITokenPerSecond` | vazão |
| `AzureOpenAIAvailabilityRate` | disponibilidade |

Dimensões úteis para dividir (**Apply splitting**): `ModelDeploymentName`,
`StatusCode`, `StreamType`, `ModelName`, `ModelVersion`.

> **Não use a métrica `Latency`** que aparece em "Cognitive Services — HTTP
> Requests". A própria documentação da Microsoft desaconselha para Azure
> OpenAI: ela mede coisa diferente. Use `AzureOpenAITimeToResponse`.

### As três armadilhas da Parte 2

**1. Latência sem token ao lado é ruído.** Uma resposta de 2.000 tokens demora
mais que uma de 20 — e isso não é problema. Sempre olhe latência e tokens no
mesmo gráfico antes de concluir que "está lento".

**2. Streaming muda o que "latência" significa.** Com streaming, o usuário
começa a ler quando o primeiro token chega. `AzureOpenAITimeToResponse` pode
estar alto e a experiência ser ótima — quem responde por isso é o
`...NormalizedTTFTInMS`.

**3. O 429 só existe aqui.** Estourar a cota (TPM) devolve HTTP 429, o SDK
tenta de novo por baixo, e a sua aplicação **nem fica sabendo**. No App
Insights não há erro nenhum; aqui, `AzureOpenAIRequests` dividido por
`StatusCode` mostra a barra vermelha.

### Exercício

Baixe a cota (TPM) do seu deployment para o mínimo, mande cinco perguntas
seguidas e observe o 429 aparecer. Depois volte a cota.

Pergunta: **por que o usuário não viu erro nenhum?**

---

## Parte 3 — Diagnostic settings: o log bruto da chamada

Métrica é número agregado. Para ver **a requisição**, é preciso ligar os logs de
diagnóstico.

**Onde:** recurso do Foundry → **Monitoring → Diagnostic settings** → **+ Add**
→ destino: o mesmo workspace do Log Analytics (`eva-logs`).

| Categoria | O que traz | Custa para exportar? |
| --- | --- | --- |
| `Audit` | operações de gestão | não |
| `RequestResponse` | metadados da requisição | não |
| `AzureOpenAIRequestUsage` | consumo de token por requisição | **sim** |
| `Trace` | rastreamento interno | não |
| `ManagedNetworkEvent` | eventos de rede gerenciada | **sim** |

Tudo cai na tabela `AzureDiagnostics`:

```kusto
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
| where Category == "AzureOpenAIRequestUsage"
| summarize tokens = sum(todouble(properties_tokens_s)) by ModelDeploymentName_s, bin(TimeGenerated, 1h)
| render timechart
```

> **Duas advertências antes de ligar isto em produção.** Log é cobrado por
> ingestão e por retenção — em volume, custa mais que o modelo. E log de
> requisição de um agente carrega **o que o usuário digitou**: se houver dado
> pessoal na conversa, você acabou de criar um problema de LGPD num lugar onde
> ninguém procura. Ligue com prazo e propósito, não "por via das dúvidas".

---

## Parte 4 — Application Insights: o que só existe porque você instrumentou

### 4.0 — Como chegar na tela (leia antes de colar qualquer consulta)

Todas as consultas desta parte rodam num lugar só: o blade **Logs** do
Application Insights. O caminho:

1. Abra **[portal.azure.com](https://portal.azure.com)**.
2. Na **busca do topo**, digite o nome do seu Application Insights: `eva-appi`.
   Ele aparece com o ícone roxo de *Application Insights* — clique nele.
   - Não lembra o nome ou o grupo? Liste pelo CLI — vale para os três caminhos
     de publicação (portal, CLI e Terraform):

     ```powershell
     az resource list --resource-type Microsoft.Insights/components `
       --query "[].{nome:name, grupo:resourceGroup}" -o table
     ```

   - Com a turma inteira rodando, **cada aluno tem o seu**. Confirme o grupo
     antes de concluir que a telemetria não funcionou.
3. No menu lateral esquerdo, seção **Monitoring**, clique em **Logs**.
   É *Logs* — não *Metrics*, não *Transaction search*, e **não** o workspace do
   Log Analytics (o passo 4.0.1 explica a diferença).
4. Na primeira vez abre um modal **Queries** com consultas de exemplo. Feche no
   **X**. Ele volta toda vez até você desmarcar *Always show Queries on startup*.
5. Se houver um seletor **Simple mode / KQL mode** no topo do editor, escolha
   **KQL mode** — no modo simples não dá para colar consulta.
6. Cole a consulta e clique em **Run** (ou **Shift + Enter**).

> **Sobre o seletor de tempo.** As consultas abaixo trazem o filtro dentro do
> texto (`ago(24h)`). Quando isso acontece, o seletor do portal passa a mostrar
> **"Set in query"** e para de valer — é o comportamento correto. Para mudar a
> janela, mude o `ago(...)`, não o seletor.

#### 4.0.0 — A primeira consulta: um turno por linha

Esta é a consulta para colar no passo 6. Ela é o "olá mundo" do lab — se ela
devolve linhas, a telemetria está chegando e todo o resto desta Parte 4
funciona:

```kusto
dependencies
| where timestamp > ago(24h) and name == "eva.chamada_modelo"
| extend entrada = toint(customDimensions["eva.tokens.entrada"]),
         saida   = toint(customDimensions["eva.tokens.saida"]),
         erro    = tostring(customDimensions["eva.erro"])
| summarize iteracoes = count(),
            inicio     = min(timestamp),
            duracao_ms = sum(duration),
            tokens_in  = sum(entrada),
            tokens_out = sum(saida),
            erros      = countif(isnotempty(erro))
        by operation_Id
| order by inicio desc
```

Cada linha é **um turno do usuário**, não uma chamada ao modelo. Quem faz esse
agrupamento é o `operation_Id`, que o OpenTelemetry propaga por toda a
requisição HTTP — as N chamadas do laço do agente carregam o mesmo valor.

Como ler a saída:

| Coluna | O que dizer para a turma |
| --- | --- |
| `iteracoes` | `1` = resposta direta. `2` ou mais = o agente chamou ferramenta e voltou para ler o resultado. É o laço aparecendo em forma de dado |
| `duracao_ms` | soma das chamadas do turno — o que o usuário esperou de modelo, sem contar o resto |
| `tokens_in` vs `tokens_out` | a entrada cresce com o histórico; a saída, não. A desproporção é o assunto do 4.2 |
| `erros` | `0` esperado. Diferente de zero, vá para o 4.4 |

> **A mesma consulta, no workspace do Log Analytics** (se você preferir
> trabalhar no `eva-logs` em vez do `eva-appi`) — os nomes mudam, a lógica não:
>
> ```kusto
> AppDependencies
> | where TimeGenerated > ago(24h) and Name == "eva.chamada_modelo"
> | extend entrada = toint(Properties["eva.tokens.entrada"]),
>          saida   = toint(Properties["eva.tokens.saida"]),
>          erro    = tostring(Properties["eva.erro"])
> | summarize iteracoes = count(),
>             inicio     = min(TimeGenerated),
>             duracao_ms = sum(DurationMs),
>             tokens_in  = sum(entrada),
>             tokens_out = sum(saida),
>             erros      = countif(isnotempty(erro))
>         by OperationId
> | order by inicio desc
> ```

O 4.5 faz a mesma pergunta de outro jeito: aqui você vê **turno a turno**, lá
você vê a **estatística da turma inteira de turnos**. Comece por aqui, porque
uma linha só já é suficiente para explicar o laço.

#### 4.0.1 — O erro que todo mundo comete uma vez

```
'where' operator: Failed to resolve table or column expression named 'AppDependencies'
```

Essa mensagem quer dizer: **você está na tela A com a consulta da tela B.**

Os dados são os mesmos — o Application Insights é *workspace-based*, então tudo
mora fisicamente no `eva-logs`. O que muda é a **gramática**, e ela é decidida
pelo recurso que você abriu:

| Você abriu… | Tabelas | Colunas |
| --- | --- | --- |
| **`eva-appi`** (Application Insights) | `dependencies`, `traces`, `exceptions`, `customMetrics` | `timestamp`, `duration`, `customDimensions`, `operation_Id` |
| **`eva-logs`** (Log Analytics workspace) | `AppDependencies`, `AppTraces`, `AppExceptions`, `AppMetrics` | `TimeGenerated`, `DurationMs`, `Properties`, `OperationId` |

**As consultas deste lab usam a forma do Application Insights** (coluna da
esquerda). Se preferir trabalhar no workspace, traduza pelos dois nomes.

Um jeito rápido de descobrir em que escopo você está, sem ler o breadcrumb:

```kusto
search * | take 1 | project $table
```

O nome que voltar diz qual gramática usar.

> **A mesma mensagem, outra causa.** `AppDependencies` só passa a existir no
> workspace **depois** que ele recebeu o primeiro dado do Application Insights.
> Então, se você for direto ao `eva-logs` antes da primeira conversa com a Eva,
> vai tomar exatamente este erro — só que aí por falta de dado, não por escopo
> errado. Erro idêntico, diagnóstico diferente: é um bom momento para ensinar
> que mensagem de erro não é diagnóstico.

#### 4.0.2 — Se a consulta rodar e vier vazia

Nesta ordem — é quase sempre uma das quatro:

1. **Ninguém conversou com a Eva.** Abra a URL e mande algumas perguntas,
   incluindo uma que force ferramenta (para ver `iteracoes > 1`).
2. **Espere de 2 a 5 minutos.** A ingestão não é instantânea, e a consulta certa
   numa janela vazia devolve zero linhas sem reclamar de nada.
3. **A telemetria está desligada.** Veja o indicador na barra lateral da Eva.
   Sem `APPLICATIONINSIGHTS_CONNECTION_STRING`, o `telemetria.py` vira no-op de
   propósito — a aplicação roda igual e não emite nada.
4. **Application Insights errado** (veja o passo 2 acima).

O teste que separa *"não tem dado"* de *"minha consulta está errada"*:

```kusto
dependencies | take 10
```

Se isso volta e a consulta completa não, o problema é o filtro. Se nem isso
volta, é ingestão.

#### 4.0.3 — Sem portal, direto do terminal

A mesma consulta, pelo Azure CLI. Útil para projetar em aula sem navegar menu, e
para quem publicou pelo portal ou pela CLI (não depende de Terraform nenhum).

**Uma vez, para ter o comando:**

```powershell
az extension add --name application-insights --upgrade
```

**Descobrir qual é o seu Application Insights e em que grupo ele está:**

```powershell
az resource list --resource-type Microsoft.Insights/components `
  --query "[].{nome:name, grupo:resourceGroup, regiao:location}" -o table
```

Com a turma inteira na mesma assinatura vão aparecer vários. O seu é o que está
no **seu** grupo (`rg-eva-<seu-sufixo>`).

**Guardar nas variáveis e rodar:**

```powershell
$APPI = "eva-appi"
$RG   = az resource list --name $APPI `
          --resource-type Microsoft.Insights/components `
          --query "[0].resourceGroup" -o tsv

$CONSULTA = @'
dependencies
| where name == "eva.chamada_modelo"
| extend entrada = toint(customDimensions["eva.tokens.entrada"]),
         saida   = toint(customDimensions["eva.tokens.saida"]),
         erro    = tostring(customDimensions["eva.erro"])
| summarize iteracoes = count(),
            inicio     = min(timestamp),
            duracao_ms = sum(duration),
            tokens_in  = sum(entrada),
            tokens_out = sum(saida),
            erros      = countif(isnotempty(erro))
        by operation_Id
| order by inicio desc
'@

az monitor app-insights query -a $APPI -g $RG --offset 24h -o table `
  --analytics-query $CONSULTA
```

Três detalhes que fazem a diferença entre funcionar e não funcionar:

1. **`--offset 24h` não é opcional.** O padrão do comando é **1 hora**, e essa
   janela é aplicada *além* do que a consulta pede. Um `ago(24h)` no texto com
   `--offset` no padrão devolve **1 hora** de dado, sem aviso nenhum — por isso
   o `ago(24h)` saiu do texto aqui e virou o `--offset`. Uma janela só, num
   lugar só.
2. **O here-string `@' ... '@` guarda a consulta sem escapar aspas.** Com aspas
   simples ele não expande `$`, então o KQL vai literal. O `'@` de fechamento
   precisa começar na **coluna 1** — indentado, o PowerShell não fecha e você
   ganha um erro de sintaxe que não fala nada de KQL.
3. **É a gramática do Application Insights** (`dependencies`, `timestamp`,
   `customDimensions`), igual ao portal — o `-a` (`--apps`) decide o escopo, exatamente
   como o recurso que você abre no portal decide.

Para conferir rápido se está chegando dado, sem montar consulta:

```powershell
az monitor app-insights query -a $APPI -g $RG --offset 24h -o table `
  --analytics-query "dependencies | summarize chamadas=count() by name"
```

### O mapa: do seu código para a tabela

O `telemetria.py` emite OpenTelemetry. O exportador do Azure Monitor traduz:

| O que o código faz | Onde aparece |
| --- | --- |
| `tracer.start_as_current_span("eva.chamada_modelo")` (span interno) | `dependencies` |
| atributos do span (`eva.deployment`, `eva.tokens.entrada`…) | coluna `customDimensions` |
| `span.record_exception(exc)` | `exceptions` |
| histogramas e contadores (`eva.chamada.duracao`, `eva.tokens`…) | `customMetrics` |
| `service.name = "eva-agente"` | coluna `cloud_RoleName` |

> Lembrete do 4.0.1: as consultas abaixo usam os nomes do **Application
> Insights**. No workspace do Log Analytics as mesmas linhas atendem por
> `AppDependencies`, `AppMetrics`, `AppTraces` e `AppExceptions`.

### 4.1 — Volume e latência

```kusto
dependencies
| where name == "eva.chamada_modelo"
| summarize
    chamadas = count(),
    p50 = percentile(duration, 50),
    p95 = percentile(duration, 95),
    max = max(duration)
  by bin(timestamp, 15m)
| render timechart
```

> **Por que os percentis saem daqui e não das métricas.** Em `customMetrics` o
> histograma chega **pré-agregado** (soma, contagem, mínimo, máximo) — não dá
> para calcular p95 a partir disso. Em `dependencies`, cada linha é **uma
> chamada**, então o percentil é real. Métrica é barata e agregada; log é caro
> e detalhado. Escolher errado é pagar caro por um número que você não pode
> calcular.

### 4.2 — Tokens, por deployment e por tipo

```kusto
dependencies
| where name == "eva.chamada_modelo"
| extend
    deployment = tostring(customDimensions["eva.deployment"]),
    entrada    = toint(customDimensions["eva.tokens.entrada"]),
    saida      = toint(customDimensions["eva.tokens.saida"])
| summarize entrada = sum(entrada), saida = sum(saida) by deployment, bin(timestamp, 1h)
| render columnchart
```

**A pergunta que este gráfico responde e o Foundry não:** a proporção
entrada/saída. Num agente ela é violentamente desequilibrada — o histórico
inteiro, mais o `agent.md`, mais o `memory.md`, mais os resultados de
ferramenta vão na **entrada** a cada iteração. É comum ver 20 para 1.

Como a entrada costuma ser mais barata que a saída, essa proporção é o que
decide se vale a pena otimizar prompt ou resposta.

### 4.3 — Custo estimado acumulado

```kusto
dependencies
| where name == "eva.chamada_modelo"
| extend custo = todouble(customDimensions["eva.custo_estimado_usd"])
| summarize total_usd = sum(custo) by bin(timestamp, 1d)
| render columnchart
```

Se der zero, não é bug: o `telemetria.py` nasce com preço `0` de propósito.
Preencha `EVA_PRECO_ENTRADA_POR_1M` e `EVA_PRECO_SAIDA_POR_1M` com os valores
do seu modelo. **Número inventado em painel de custo é pior que painel
nenhum** — e essa decisão está comentada no código.

### 4.4 — O que quebrou

```kusto
dependencies
| where name == "eva.chamada_modelo"
| where isnotempty(customDimensions["eva.erro"])
| extend erro = tostring(customDimensions["eva.erro"])
| summarize vezes = count() by erro, bin(timestamp, 1h)
| order by vezes desc
```

E o detalhe, com a exceção inteira:

```kusto
exceptions
| where cloud_RoleName == "eva-agente"
| project timestamp, type, outerMessage, operation_Id
| order by timestamp desc
| take 20
```

### 4.5 — Iterações por turno (a consulta que justifica o lab)

Esta é a pergunta que **nenhuma** métrica de plataforma responde. O
`operation_Id` amarra as chamadas do mesmo turno:

```kusto
dependencies
| where name == "eva.chamada_modelo"
| summarize iteracoes = count(), duracao_total = sum(duration) by operation_Id
| summarize
    turnos = count(),
    media_iteracoes = avg(iteracoes),
    turnos_com_ferramenta = countif(iteracoes > 1),
    turnos_no_limite = countif(iteracoes >= 5)
```

Três números que valem a aula inteira:

- **média de iterações** — quanto o loop realmente gira no seu domínio. É o
  número que dimensiona o `EVA_MAX_ITERACOES`, em vez do chute.
- **turnos com ferramenta** — com que frequência o agente usa o que você deu.
  Se for perto de zero, a `description` está vaga.
- **turnos no limite** — se for maior que zero, alguém foi cortado no meio.
  Ou o teto está baixo, ou há uma ferramenta em laço.

### 4.6 — O histórico crescendo

```kusto
dependencies
| where name == "eva.chamada_modelo"
| extend entrada = toint(customDimensions["eva.tokens.entrada"])
| project timestamp, operation_Id, entrada
| order by timestamp asc
| render timechart
```

Numa conversa longa, a linha **sobe monotonicamente** — cada turno reenvia
tudo que veio antes. É a demonstração visual de por que memória por arquivo
tem teto e por que RAG existe. Vale projetar em aula: o gráfico convence mais
que a explicação.

---

## Parte 5 — Cruzar as três janelas: a discrepância que ensina

Compare, na mesma janela de tempo:

| Fonte | Número |
| --- | --- |
| Foundry / Metrics | `TokenTransaction` (soma) |
| Application Insights | soma de `eva.tokens.entrada` + `eva.tokens.saida` |

**Eles não vão bater.** Isso não é defeito — é o exercício.

| Motivo da diferença | Para que lado |
| --- | --- |
| Retry automático do SDK (429, 5xx) | Foundry conta mais |
| Chamada que falhou depois de processar | Foundry conta mais |
| Chamada em streaming sem `include_usage` | a Eva conta menos |
| Telemetria desligada por um período | a Eva conta menos |
| Erro antes de chegar ao serviço | a Eva conta mais |

A conclusão que a turma precisa levar: **para cobrança, vale o número do
provedor.** O seu é estimativa — útil para decidir, não para faturar. Todo
painel de custo de IA que você vir por aí tem essa mesma ressalva, e quase
nenhum a escreve.

> Detalhe do nosso código, que explica uma das linhas: em streaming o
> `chamar_modelo()` **não** mede — o retorno é um gerador que só será
> consumido depois, então tempo e tokens não existem ainda. Quem instrumenta é
> o `responder_stream()`, e ele depende de `stream_options={"include_usage":
> True}`. Sem esse parâmetro, o provedor não manda o `usage` no fim do stream
> e a contagem sai zerada — sem erro nenhum.

---

## Parte 6 — Custo: token não é dinheiro

Três números diferentes, três propósitos:

| Número | Onde | Serve para |
| --- | --- | --- |
| Tokens | Foundry / Metrics | entender **consumo** |
| Custo estimado | App Insights (seu) | decidir **em tempo real** |
| Custo real | Cost Management | **pagar** e cobrar |

**Onde ver o real:** portal → **Cost Management + Billing** → **Cost analysis**
→ *Group by* → **Tag** → `projeto` (a marcação que os guias de deploy aplicam).

Três coisas que surpreendem:

1. **Há defasagem.** O custo não aparece em tempo real — leva horas até
   consolidar. Não adianta gastar e olhar em seguida.
2. **A granularidade é o recurso, não o deployment.** Dois deployments no mesmo
   recurso do Foundry aparecem numa linha só. Se precisa separar custo por
   modelo, ou separa o recurso, ou usa a métrica de tokens.
3. **O container também custa** — e com `min-replicas 0` ele custa quase nada
   parado. Ver isso lado a lado com o custo do modelo costuma reordenar as
   prioridades de otimização de quem estava mexendo no lugar errado.

---

## Parte 7 — Três alertas que valem a pena

Métrica que ninguém olha não serve para nada. Alerta é o que transforma painel
em operação.

| Alerta | Onde | Condição sugerida |
| --- | --- | --- |
| **Erro** | App Insights | taxa de falha em `dependencies` acima de 5% em 15 min |
| **Latência** | Foundry / Metrics | p95 de `AzureOpenAITimeToResponse` acima do seu limite |
| **Custo** | Foundry / Metrics | `TokenTransaction` acima de N por hora |

O terceiro é o mais importante e o mais esquecido: **um agente em laço não
derruba nada — ele só gasta.** Sem alerta de volume, você descobre no
fechamento do mês. Um teto de tokens por hora é o cinto de segurança que o
`EVA_MAX_ITERACOES` não consegue dar sozinho, porque ele protege um turno de
cada vez, não o dia inteiro.

---

## Exercícios

1. **Meça o custo de uma ferramenta.** Rode dez perguntas sem ferramenta e dez
   com. Compare tokens e iterações. Quanto uma ferramenta custa por uso?
2. **Ache a conversa mais cara.** Ordene por soma de tokens agrupada por
   `operation_Id`. Abra e explique **por que** ela foi cara.
3. **Dimensione o `EVA_MAX_ITERACOES` com dado.** Use o 4.5: qual valor cobre
   95% dos turnos reais? Compare com o padrão `5`.
4. **Provoque a discrepância.** Derrube a cota, gere 429, e meça de quanto
   ficou a diferença entre o Foundry e o App Insights.
5. **Construa um workbook.** Junte volume, latência p95, tokens e custo numa
   página só. É o entregável que um time de plataforma pede de verdade.
6. **O difícil:** instrumente as **ferramentas**. Hoje `medir_chamada` envolve
   só a chamada ao modelo. Acrescente um span em `executar_ferramenta` e
   responda: qual ferramenta é a mais lenta, e quantas vezes cada uma é
   chamada?

---

## Limites honestos deste setup

- **Sem amostragem.** Toda chamada vira telemetria. Em volume real isso custa;
  a saída é *sampling*, que troca precisão por conta menor.
- **Sem correlação com o usuário.** Não há `user_Id`: não dá para responder
  "quem gastou mais". Acrescentar é fácil e traz uma discussão de privacidade
  junto.
- **`operation_Id` agrupa por requisição HTTP, não por conversa.** Serve para
  contar iterações de um turno; para acompanhar uma conversa inteira seria
  preciso um identificador próprio, propagado como atributo.
- **Custo estimado é estimativa.** Preço fixo no `.env` não sabe de desconto,
  de reserva, nem de mudança de tabela.
- **Retenção padrão.** O workspace nasce com 30 dias. Análise de tendência
  mensal precisa de mais — e mais retenção custa mais.

---

## Sources

- [Monitoring data reference for Azure OpenAI — Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/openai/monitor-openai-reference)
- [Supported metrics — Microsoft.CognitiveServices/accounts](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/supported-metrics/microsoft-cognitiveservices-accounts-metrics)
- [Add, modify, and filter OpenTelemetry — Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-add-modify)
- [Azure Monitor Logs reference — AppDependencies](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/appdependencies)
- [Azure Monitor Logs reference — AppMetrics](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/appmetrics)
