# Diagramas da solução — Eva no Azure

Modelo **C4**, de fora para dentro. Cada nível responde a uma pergunta
diferente, e cada um tem um público diferente:

| Nível | Pergunta | Para quem |
|---|---|---|
| **1. Contexto** | Quem usa o sistema e com o que ele fala? | qualquer pessoa |
| **2. Contêineres** | De que peças executáveis ele é feito? | quem opera e quem desenvolve |
| **3. Componentes** | O que existe dentro da aplicação? | quem vai mexer no código |
| **4. Código** | Como cada componente é escrito? | (o próprio código; não desenhamos) |

> A regra do C4 que mais economiza discussão: **um diagrama, um nível de
> abstração**. Misturar "usuário" com "função Python" no mesmo desenho é o que
> transforma diagrama em decoração.

---

## Nível 1 — Contexto

Quem interage com a Eva, e com quais sistemas externos ela fala. Nenhuma
tecnologia aparece aqui de propósito: este desenho continua válido se
trocarmos Streamlit por React ou Azure por AWS.

```mermaid
graph TB
    aluno["👤 <b>Aluno / Usuário</b><br/>conversa com a Eva pelo navegador"]
    prof["👤 <b>Instrutor / Operador</b><br/>publica e opera a aplicação"]

    eva["<b>Eva</b><br/><i>[Sistema]</i><br/>Agente conversacional que usa<br/>ferramentas e mantém memória"]

    foundry["<b>Microsoft Foundry</b><br/><i>[Sistema externo]</i><br/>Hospeda o modelo de linguagem"]
    entra["<b>Microsoft Entra ID</b><br/><i>[Sistema externo]</i><br/>Emite os tokens de identidade"]
    monitor["<b>Azure Monitor</b><br/><i>[Sistema externo]</i><br/>Guarda latência, tokens e<br/>custo estimado. É AQUI que<br/>se observa, não na Eva."]

    aluno -->|"pergunta e recebe resposta<br/>HTTPS"| eva
    prof -->|"publica, troca o deployment,<br/>reinicia"| eva
    prof -->|"consulta latência, tokens<br/>e custo estimado"| monitor
    eva -->|"pede uma resposta ao modelo<br/>HTTPS + token"| foundry
    eva -->|"prova quem é<br/>(sem senha, sem chave)"| entra
    eva -->|"envia traços e métricas<br/>OpenTelemetry"| monitor
    entra -.->|"valida o token"| foundry

    classDef sistema fill:#1168bd,stroke:#0b4884,color:#fff
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    classDef pessoa fill:#08427b,stroke:#052e56,color:#fff
    class eva sistema
    class foundry,entra,monitor externo
    class aluno,prof pessoa
```

**Duas relações que valem parar:**

**A seta pontilhada.** A Eva não guarda credencial: ela pede um token ao Entra
e o Foundry valida esse token. É a relação que os alunos costumam não enxergar
— **quem autoriza não é quem atende**.

**O instrutor tem duas setas, e elas vão para lugares diferentes.** Ele
*publica e opera* a Eva, mas **não observa através dela**: a aplicação não tem
painel de custo nem de latência. A barra lateral mostra apenas se a telemetria
está ligada e se os preços foram configurados — nada de histórico, nada de
gráfico.

Quem observa, observa na **plataforma**: Azure Monitor / Application Insights
para o que a aplicação instrumentou, e as métricas do próprio Foundry para o
que o serviço mede sozinho (essas ficaram fora do desenho para não poluir — o
diagrama de observabilidade, mais abaixo, abre as três janelas).

Essa separação não é detalhe de desenho, é decisão de arquitetura: **construir
painel dentro da aplicação é reimplementar, pior, o que a plataforma já faz.**
E é a resposta para a pergunta que sempre aparece: *"por que a Eva não mostra
quanto já gastei?"*

---

## Nível 2 — Contêineres

Cada caixa aqui é algo que **executa ou armazena** separadamente — não é
"classe", nem "container Docker" necessariamente.

```mermaid
graph TB
    aluno["👤 Aluno"]

    subgraph azure["☁️ Azure — um grupo de recursos, todos marcados com as tags de FinOps"]
        app["<b>Container App: eva-app</b><br/><i>[Docker · Python 3.12 · Streamlit]</i><br/>A aplicação. Escala a zero quando<br/>ninguém está usando."]
        acr["<b>Container Registry</b><br/><i>[ACR]</i><br/>Guarda a imagem eva:v1"]
        kv["<b>Key Vault</b><br/><i>[Cofre]</i><br/>Chave do Foundry — só o fallback"]
        appi["<b>Application Insights</b><br/><i>[OpenTelemetry]</i><br/>Spans, latência, tokens, custo"]
        logs["<b>Log Analytics</b><br/><i>[workspace]</i><br/>Onde tudo é consultado com KQL"]
        foundry["<b>Foundry</b><br/><i>[deployment do modelo]</i>"]
    end

    entra["<b>Entra ID</b>"]

    aluno -->|"HTTPS :443<br/>ingress externo"| app
    app -->|"chat/completions<br/>+ Bearer token"| foundry
    app -->|"pede token<br/>DefaultAzureCredential"| entra
    app -->|"exporta spans e métricas<br/>o que VOCÊ instrumentou"| appi
    app -.->|"lê o segredo<br/>só se a identidade falhar"| kv
    acr -->|"a plataforma puxa a imagem<br/>usando a Managed Identity"| app
    appi --> logs
    foundry -.->|"diagnostic settings<br/>opcional, e cobrado"| logs

    classDef app fill:#438dd5,stroke:#2e6295,color:#fff
    classDef dados fill:#438dd5,stroke:#2e6295,color:#fff
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    class app app
    class acr,kv,appi,logs,foundry dados
    class entra externo
```

**As três coisas que valem parar e explicar:**

1. **A seta do Key Vault é pontilhada** porque é caminho de exceção. No fluxo
   normal ela não acontece — e quando acontece, a interface avisa. Fallback
   silencioso é pior que fallback nenhum: a aplicação continua de pé com a
   identidade quebrada e ninguém fica sabendo.
2. **O ACR aponta para o app, não o contrário.** Quem puxa a imagem é a
   plataforma do Container Apps, antes do seu código existir. Por isso a
   identidade precisa da role `AcrPull` *antes* do primeiro deploy da imagem
   privada — e por isso o app nasce com uma imagem pública descartável.
3. **`min-replicas 0`**: sem tráfego, zero contêiner e zero custo de compute.
   O preço é a primeira requisição depois da ociosidade ser lenta (cold start).
4. **A marcação está no título do grupo, não numa caixa.** Tag não é
   componente — é atributo de todos eles. As sete tags (`projeto`, `ambiente`,
   `centro-custo`, `responsavel`, `criado-por`, `criado-em`, `descartavel`) vão
   em cada recurso, porque **tag não é herdada do grupo**. É o que permite
   responder "quanto custou a aula?" no Cost Management.
5. **A seta do Foundry para o Log Analytics é pontilhada** porque é opcional e
   cobrada. O Foundry já emite métricas de plataforma de graça; o que essa seta
   liga é o **log da requisição** — caro em volume, e carregando o que o
   usuário digitou.

---

## Nível 3 — Componentes da aplicação

Agora dentro do `eva-app`. Cada caixa é um módulo ou uma função com
responsabilidade própria.

```mermaid
graph TB
    subgraph container["Container eva-app"]
        appui["<b>app.py</b><br/><i>[Streamlit]</i><br/>Só interface: chat, barra lateral,<br/>rastro das ferramentas"]

        subgraph nucleo["eva.py — o núcleo"]
            ctx["<b>carregar_contexto()</b><br/>agent.md + memory.md<br/>→ prompt de sistema"]
            cliente["<b>get_cliente()</b><br/>identidade primeiro,<br/>chave como fallback.<br/><i>Mesmo cliente OpenAI nos dois modos</i>"]
            loop["<b>responder() / responder_stream()</b><br/>o loop do agente"]
            chamar["<b>chamar_modelo()</b><br/>ponto único de saída:<br/>renova token · adapta params · mede"]
            tools["<b>FERRAMENTAS + EXECUTORES</b><br/>o que a Eva sabe fazer"]
        end

        telem["<b>telemetria.py</b><br/><i>[OpenTelemetry]</i><br/>spans, latência, tokens, custo"]
    end

    md[("agent.md<br/>memory.md")]
    foundry["Foundry"]
    appi["App Insights"]
    entra["Entra ID"]

    appui -->|"responder(mensagens)"| loop
    ctx --> loop
    md --> ctx
    loop -->|"pede a resposta"| chamar
    loop -->|"executa o que o modelo pediu"| tools
    tools -->|"resultado vira mensagem"| loop
    cliente --> chamar
    cliente -->|"token"| entra
    chamar -->|"HTTPS"| foundry
    chamar --> telem
    telem --> appi

    classDef comp fill:#85bbf0,stroke:#5d82a8,color:#000
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    class appui,ctx,cliente,loop,chamar,tools,telem comp
    class foundry,appi,entra externo
```

**Por que `chamar_modelo()` é o componente mais importante do desenho:** é o
**ponto único de saída**. Três responsabilidades transversais moram ali —
renovar o token do Entra, adaptar parâmetros que o modelo recusa
(`max_tokens` → `max_completion_tokens`) e medir a chamada. Como
`responder()` e `responder_stream()` passam pelo mesmo lugar, cada uma dessas
três coisas foi escrita **uma vez** e vale para os dois caminhos.

Se essa lógica estivesse duplicada nas duas funções, toda correção precisaria
ser feita em dois lugares — e mais cedo ou mais tarde só um deles seria
corrigido. Vale como pergunta para a turma: *o que mais deveria passar por
esse funil?* (Retry, rate limit, cache, log de auditoria.)

**E por que `get_cliente()` devolve o mesmo tipo de cliente nos dois modos.**
Chave e identidade mudam só a credencial — a classe é a mesma (`OpenAI`) e a
rota é a mesma (`/openai/v1/`). Trocar para `AzureOpenAI` no modo identidade
parece natural e **quebra**: aquele cliente foi feito para a rota clássica e
reescreve o caminho da URL, inserindo `/deployments/<modelo>/`. O resultado é
`404 Resource not found`, um erro que aponta para o lugar errado.

A simetria é deliberada: se mudar a autenticação mudasse também a rota, você
nunca saberia qual das duas quebrou.

### O mesmo nível, por outra lente: o harness

O desenho acima mostra as peças **lado a lado**. Vale um segundo olhar sobre o
mesmo nível, agora perguntando *quem é responsável pelo quê* — porque a divisão
não é a que a maioria das pessoas imagina:

```mermaid
graph LR
    harness["<b>O HARNESS faz o resto</b> — eva.py<br/><br/>decide chamar de novo · sabe parar<br/>executa as ferramentas · declara o schema<br/>guarda a conversa · monta o prompt<br/>autentica · adapta parâmetros · mede<br/><br/><i>95% do código, 0% de IA</i>"]
    modelo["<b>O MODELO faz uma coisa</b><br/><br/>recebe uma lista de mensagens<br/>devolve texto<br/><b>ou uma intenção</b><br/><br/><i>e nada mais</i>"]

    harness -->|"mensagens + schema das ferramentas"| modelo
    modelo -->|"texto, ou 'quero chamar X'"| harness

    classDef comp fill:#85bbf0,stroke:#5d82a8,color:#000
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    class harness comp
    class modelo externo
```

**Harness** é o nome desse código em volta — o que fica entre o modelo e o
mundo. Todo o Nível 3 acima é harness, exceto a seta que sai para o Foundry.

Isso reposiciona uma pergunta comum na sala: *"qual framework de agente
usar?"*. O `create_agent()` do LangChain, usado no projeto MeuAgenteLC, é
exatamente esta caixa azul — escrita por outra pessoa. Escrever ela primeiro,
como fizemos aqui e no `agentebase`, é o que permite avaliar depois **o que o
framework esconde e o que cobra em troca**.

O [ANATOMIA-DO-HARNESS.md](ANATOMIA-DO-HARNESS.md) abre a caixa azul: o
diagrama do laço passo a passo, as dez responsabilidades com número de linha, e
a lista honesta do que este harness ainda **não** faz.

---

## Observabilidade — as três janelas

Nenhum dos diagramas acima mostra **quem consegue ver o quê**. E essa é a
pergunta que aparece quando algo dá errado em produção.

```mermaid
graph LR
    app["<b>eva-app</b>"]
    foundry["<b>Foundry</b><br/>deployment"]

    subgraph plataforma["Mede sozinha — sem uma linha do seu código"]
        aifoundry["<b>ai.azure.com</b><br/>requisições, tokens,<br/>latência, cota"]
        metrics["<b>Azure Monitor Metrics</b><br/>AzureOpenAIRequests<br/>ProcessedPromptTokens<br/>AzureOpenAITimeToResponse"]
    end

    subgraph instrumentada["Só existe porque você instrumentou"]
        appi["<b>Application Insights</b><br/>span eva.chamada_modelo<br/>iterações por turno<br/>custo estimado"]
    end

    custo["<b>Cost Management</b><br/>o custo REAL,<br/>agrupado por tag"]

    app -->|"OpenTelemetry"| appi
    app -->|"chat/completions"| foundry
    foundry --> aifoundry
    foundry --> metrics
    foundry -.->|"horas de defasagem"| custo
    app -.->|"horas de defasagem"| custo

    classDef comp fill:#438dd5,stroke:#2e6295,color:#fff
    classDef obs fill:#85bbf0,stroke:#5d82a8,color:#000
    classDef dinheiro fill:#6b9e78,stroke:#4a6f54,color:#fff
    class app,foundry comp
    class aifoundry,metrics,appi obs
    class custo dinheiro
```

**A divisão que importa:** o lado esquerdo mede **o serviço** e existe de
graça, sem você fazer nada. O lado direito mede **a sua aplicação** e só existe
porque o `telemetria.py` está lá.

Três perguntas, três janelas diferentes — e é por isso que nenhuma sozinha
basta:

| Pergunta | Onde |
| --- | --- |
| "Tomei 429?" | só nas métricas de plataforma — o SDK tenta de novo e sua app nem sabe |
| "Quantas iterações por turno?" | só no Application Insights — a plataforma não sabe que existe um agente |
| "Quanto vou pagar?" | só no Cost Management — e com horas de atraso |

Os dois números de token **não vão bater**: o Foundry conta o que processou
(incluindo retry), a Eva conta o que o SDK devolveu. Para cobrança vale o do
provedor; o seu é estimativa para decidir em tempo real.

O [LAB-OBSERVABILIDADE.md](LAB-OBSERVABILIDADE.md) percorre as três com KQL.

---

## Provisionamento — três caminhos, os mesmos recursos

```mermaid
graph TB
    portal["<b>Portal</b><br/>clicar<br/><i>ensina o quê</i>"]
    cli["<b>Azure CLI</b><br/>deploy.ps1<br/><i>ensina a ordem</i>"]
    tf["<b>Terraform</b><br/>main.tf<br/><i>ensina o estado</i>"]

    recursos["<b>Os mesmos 6 recursos</b><br/>ACR · Key Vault · Log Analytics<br/>App Insights · Environment · Container App"]

    sys["identidade<br/><b>system-assigned</b>"]
    user["identidade<br/><b>user-assigned</b>"]

    portal --> sys
    cli --> sys
    tf --> user
    sys --> recursos
    user --> recursos

    classDef caminho fill:#438dd5,stroke:#2e6295,color:#fff
    classDef ident fill:#c8a04a,stroke:#8a6d2f,color:#fff
    classDef alvo fill:#85bbf0,stroke:#5d82a8,color:#000
    class portal,cli,tf caminho
    class sys,user ident
    class recursos alvo
```

**Por que o Terraform usa identidade diferente** — e não é preferência:

O `azurerm` não aceita identidade *system-assigned* no bloco `registry` do
Container App. E há uma dependência circular: com system-assigned, o
`principal_id` só existe **depois** que o app é criado, mas o app precisa da
role `AcrPull` para conseguir puxar a imagem e nascer.

No portal e na CLI isso se resolve em duas fases manuais — criar o app com uma
imagem pública, dar a identidade, trocar a imagem. **Em IaC declarativa esse
"depois" não existe.** A identidade autônoma quebra o ciclo: nasce primeiro,
recebe as roles, e o app já nasce podendo.

É o exemplo mais concreto do curso de uma coisa que ninguém escolhe por
preferência — a ferramenta impõe.

---

## Sequência — uma pergunta, do clique à resposta

Não faz parte do C4, mas é o complemento que responde "e o que acontece
**quando**":

```mermaid
sequenceDiagram
    autonumber
    participant U as Aluno
    participant A as app.py
    participant E as eva.py
    participant I as Entra ID
    participant F as Foundry
    participant T as App Insights

    U->>A: "que horas são?"
    A->>E: responder(mensagens)
    E->>E: carregar_contexto() — agent.md + memory.md
    E->>I: token — cache interno, só vai à rede perto de expirar
    I-->>E: Bearer token
    E->>F: chat/completions + ferramentas
    F-->>E: "quero chamar que_horas_sao"
    Note over E: o modelo NÃO executa nada —<br/>quem executa é o Python
    E->>E: executar_ferramenta("que_horas_sao")
    E->>F: mesma conversa + resultado da ferramenta
    F-->>E: "São 14h32 de sexta-feira."
    E->>T: span: latência, tokens, custo
    E-->>A: resposta + rastro das ferramentas
    A-->>U: mostra na tela
```

O passo 6→7 é o coração do agente e o que mais confunde: **o modelo devolve
uma intenção, não uma execução.** Ele diz "quero chamar `que_horas_sao`" e
para. Quem roda a função é o seu Python, na sua máquina, com as suas
permissões. É isso que torna o `MAX_ITERACOES` necessário — o ciclo 6→9 pode
se repetir.

---

## O que os diagramas deixam de fora, de propósito

Um diagrama honesto tem uma lista assim:

- **Rede** — não há VNet, private endpoint nem firewall. O Foundry está
  acessível pela internet pública, protegido só por identidade. Em produção
  de verdade isso mudaria, e mudaria o nível 2.
- **Estado** — não há banco. O histórico da conversa vive na memória do
  processo, e a `memory.md` está *dentro da imagem*: com `min-replicas 0`, o
  que a Eva "aprender" some quando o contêiner morre. É a limitação mais
  importante desta arquitetura, e a que justifica o próximo passo.
- **Escala** — uma réplica não conversa com a outra. Com duas réplicas, dois
  usuários podem ver memórias diferentes.
- **CI/CD** — o deploy é um script rodado à mão. Não há pipeline, não há
  ambiente de homologação, não há rollback automático.
- **Amostragem de telemetria** — toda chamada vira span. Em volume real isso
  custa; a saída é *sampling*, que troca precisão por conta menor.

O que **deixou** de faltar desde a primeira versão destes diagramas: a
marcação de FinOps (agora em todos os recursos, nos três caminhos de
provisionamento) e a análise da telemetria (o
[LAB-OBSERVABILIDADE.md](LAB-OBSERVABILIDADE.md)).

Bom exercício de arquitetura: **qual caixa você acrescentaria primeiro?**
(Uma resposta defensável: um armazenamento externo para o estado — e reparar
que isso muda o nível 2, não o nível 1. O contexto continua o mesmo.)
