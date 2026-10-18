# Diagramas da solução — Eva na AWS

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

```mermaid
graph LR
    usuario["<b>Usuário</b><br/><i>[Pessoa]</i><br/>conversa com a Eva<br/>pelo navegador"]
    eva["<b>Eva</b><br/><i>[Sistema]</i><br/>assistente com memória<br/>e ferramentas"]
    modelo["<b>Provedor do modelo</b><br/><i>[Sistema externo]</i><br/>Amazon Bedrock<br/>ou OpenAI (Learner Lab)"]
    operador["<b>Quem opera</b><br/><i>[Pessoa]</i><br/>publica, observa, paga"]

    usuario -->|"pergunta / resposta (HTTP)"| eva
    eva -->|"mensagens + ferramentas"| modelo
    operador -->|"deploy, logs, custo"| eva

    classDef pessoa fill:#08427b,stroke:#052e56,color:#fff
    classDef sistema fill:#1168bd,stroke:#0b4884,color:#fff
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    class usuario,operador pessoa
    class eva sistema
    class modelo externo
```

O nível 1 **não muda** entre Azure e AWS, nem entre Bedrock e OpenAI. É o
teste de que ele está no nível certo: troca de nuvem é detalhe de nível 2.

---

## Nível 2 — Contêineres

```mermaid
graph TB
    usuario["Usuário<br/><i>navegador</i>"]

    subgraph aws["Conta AWS · us-east-1"]
        subgraph ecs["ECS Fargate · VPC padrão"]
            app["<b>eva-app</b><br/><i>[Container: Python + Streamlit]</i><br/>porta 8501 · IP público<br/>task role"]
        end
        ecr["<b>ECR</b><br/><i>[Registry]</i><br/>a imagem"]
        logs["<b>CloudWatch Logs</b><br/><i>[/ecs/eva/...]</i><br/>stdout + telemetria JSON"]
        sm["<b>Secrets Manager</b><br/><i>[só provedor openai]</i><br/>chave da OpenAI"]
        bedrock["<b>Amazon Bedrock</b><br/><i>[bedrock-runtime · Converse]</i>"]
    end
    openai["API da OpenAI<br/><i>[externo]</i>"]

    usuario -->|"HTTP :8501"| app
    ecr -.->|"pull na partida<br/>(execution role)"| app
    sm -.->|"injeta OPENAI_API_KEY<br/>na partida"| app
    app -->|"stdout → driver awslogs"| logs
    app -->|"SigV4 com a task role"| bedrock
    app -.->|"HTTPS + chave<br/>(provedor openai)"| openai

    classDef cont fill:#438dd5,stroke:#2e6295,color:#fff
    classDef aws fill:#ff9900,stroke:#b36b00,color:#000
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    class app cont
    class ecr,logs,sm,bedrock aws
    class openai externo
```

**As setas tracejadas acontecem uma vez, na partida da tarefa.** As cheias,
a cada pergunta. A diferença importa para segurança: a chave da OpenAI cruza a
rede **uma** vez, puxada pelo agente do ECS — o código nunca chama o Secrets
Manager.

**Duas roles, um nome (no Learner Lab).** A task definition tem dois campos:

| Campo | Quem usa | Para quê |
|---|---|---|
| `executionRoleArn` | o **agente do ECS** | puxar a imagem do ECR, ler o segredo, escrever no CloudWatch |
| `taskRoleArn` | o **seu código** | chamar o Bedrock |

No Learner Lab as duas são a `LabRole`, porque não se cria role. Numa conta de
verdade, são duas roles com permissões diferentes — `criar_role = true` no
Terraform mostra o começo disso.

### Equivalência com a versão Azure

| Azure | AWS | Observação |
|---|---|---|
| Azure Container Apps | **ECS Fargate** | sem load balancer: IP público por tarefa |
| Container Registry (ACR) | **ECR** | login com a credencial da sessão |
| Managed Identity | **task role** | credencial temporária entregue pelo ECS |
| Key Vault | **Secrets Manager** | só existe no caminho com chave |
| Application Insights | **CloudWatch Logs + Logs Insights** | JSON no stdout, sem SDK |
| Microsoft Foundry | **Amazon Bedrock** | ou OpenAI, onde o Bedrock não está liberado |
| tags + Azure Policy | **`default_tags`** do provider | tag em todo recurso, sem herança manual |

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
            cliente["<b>get_cliente()</b><br/>bedrock-runtime (task role)<br/>ou _ClienteOpenAI (chave)"]
            loop["<b>responder() / responder_stream()</b><br/>o loop do agente"]
            chamar["<b>chamar_modelo() / _parametros()</b><br/>ponto único de saída:<br/>traduz o histórico · mede"]
            tools["<b>FERRAMENTAS + EXECUTORES</b><br/>o que a Eva sabe fazer"]
        end

        telem["<b>telemetria.py</b><br/>uma linha JSON por chamada:<br/>turno, tokens, custo"]
    end

    md[("agent.md<br/>memory.md")]
    bedrock["Bedrock"]
    logs["CloudWatch Logs"]

    appui -->|"responder(mensagens)"| loop
    ctx --> loop
    md --> ctx
    loop -->|"pede a resposta"| chamar
    loop -->|"executa o que o modelo pediu"| tools
    tools -->|"toolResult vira mensagem"| loop
    cliente --> chamar
    chamar -->|"Converse"| bedrock
    chamar --> telem
    telem -->|"stdout"| logs

    classDef comp fill:#85bbf0,stroke:#5d82a8,color:#000
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    class appui,ctx,cliente,loop,chamar,tools,telem comp
    class bedrock,logs externo
```

**Por que `chamar_modelo()` é o componente mais importante do desenho:** é o
**ponto único de saída**. Traduzir o histórico para a Converse e medir a
chamada foram escritos **uma vez** e valem para os dois caminhos. Se essa
lógica estivesse duplicada, toda correção precisaria ser feita em dois
lugares — e mais cedo ou mais tarde só um deles seria corrigido.

**E por que `get_cliente()` devolve algo com a mesma cara nos dois
provedores.** O `_ClienteOpenAI` expõe `converse()` e `converse_stream()`
como se fosse o `bedrock-runtime`. O laço não sabe com quem fala. Trocar de
provedor muda uma borda, não o agente.

### O mesmo nível, por outra lente: o harness

```mermaid
graph LR
    harness["<b>O HARNESS faz o resto</b> — eva.py<br/><br/>decide chamar de novo · sabe parar<br/>executa as ferramentas · declara o schema<br/>guarda a conversa · monta o prompt<br/>autentica · traduz o formato · mede<br/><br/><i>95% do código, 0% de IA</i>"]
    modelo["<b>O MODELO faz uma coisa</b><br/><br/>recebe uma lista de mensagens<br/>devolve texto<br/><b>ou um bloco toolUse</b><br/><br/><i>e nada mais</i>"]

    harness -->|"mensagens + toolSpec"| modelo
    modelo -->|"texto, ou 'quero chamar X'"| harness

    classDef comp fill:#85bbf0,stroke:#5d82a8,color:#000
    classDef externo fill:#999,stroke:#6b6b6b,color:#fff
    class harness comp
    class modelo externo
```

O [ANATOMIA-DO-HARNESS.md](ANATOMIA-DO-HARNESS.md) abre a caixa azul: o
diagrama do laço passo a passo, as dez responsabilidades com número de linha, e
a lista honesta do que este harness ainda **não** faz.

---

## Observabilidade — as três janelas

Nenhum dos diagramas acima mostra **quem consegue ver o quê**:

```mermaid
graph LR
    subgraph j1["1 · Métricas do Bedrock"]
        m1["CloudWatch → AWS/Bedrock<br/>Invocations · InputTokenCount<br/>OutputTokenCount · InvocationLatency"]
    end
    subgraph j2["2 · Logs da tarefa"]
        m2["CloudWatch Logs<br/>stdout do Streamlit<br/>+ eva.chamada_modelo (JSON)"]
    end
    subgraph j3["3 · Fatura"]
        m3["Billing / Cost Explorer<br/><i>não liberado no Learner Lab</i><br/>chega com até 24 h de atraso"]
    end

    q1["Quantas chamadas e<br/>quantos tokens a conta fez?"] --> j1
    q2["Quanto custou cada TURNO<br/>e quantas voltas ele deu?"] --> j2
    q3["Quanto a AWS vai cobrar?"] --> j3
```

| Janela | Sabe | Não sabe |
|---|---|---|
| **Métricas do Bedrock** | volume, tokens e latência por modelo, sem instrumentar nada | o que é um turno; quem perguntou; nada do provedor openai |
| **Logs da Eva** | turno, iteração, tokens, custo estimado, erro | o preço real (usa a tabela que você configurou) |
| **Fatura** | o valor cobrado | o porquê |

Nenhuma sozinha basta — o [LAB-OBSERVABILIDADE.md](LAB-OBSERVABILIDADE.md)
cruza as três.

---

## Provisionamento — um caminho, três movimentos

```mermaid
graph LR
    a["<b>terraform apply</b><br/>ecs_enabled=false<br/><i>ECR, logs, cluster,<br/>segredo, SG</i>"] --> b["<b>docker build + push</b><br/><i>imagem v2026...</i>"]
    b --> c["<b>terraform apply</b><br/>ecs_enabled=true<br/>image_tag=v2026...<br/><i>serviço ECS</i>"]
    c --> d["<b>aws ecs / ec2</b><br/><i>descobre o IP<br/>público da tarefa</i>"]
```

O `infra/deploy.sh` faz os quatro. Por que não um apply só: o serviço ECS
precisa de uma imagem que ainda não existe no primeiro apply — o mesmo
ovo-e-galinha da Aula 3.

---

## Sequência — uma pergunta, do clique à resposta

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant A as app.py
    participant E as eva.py (laço)
    participant B as Bedrock (Converse)
    participant T as telemetria.py
    participant L as CloudWatch Logs

    U->>A: "que dia é hoje?"
    A->>E: responder_stream(mensagens)
    E->>E: turno_id = novo_turno()
    E->>B: converse_stream(system, messages, toolConfig)
    B-->>E: bloco toolUse que_horas_sao · stopReason=tool_use
    E->>T: medir_chamada(iteracao=1)
    T->>L: {"evento":"eva.chamada_modelo","iteracao":1,...}
    E->>E: executar_ferramenta("que_horas_sao")
    E->>B: converse_stream(... + toolResult)
    B-->>E: texto em pedaços · stopReason=end_turn
    E->>T: medir_chamada(iteracao=2)
    T->>L: {"evento":"eva.chamada_modelo","iteracao":2,...}
    E-->>A: ("texto", ...)
    A-->>U: "Hoje é segunda-feira, 12/10."
```

Uma pergunta, **duas** chamadas ao modelo, **duas** linhas de log com o mesmo
`turno_id`. É por isso que o custo que importa é por turno, não por chamada.

---

## O que os diagramas deixam de fora, de propósito

- **Rede** — não há load balancer, HTTPS nem subnet privada. A tarefa tem IP
  público e a porta 8501 aberta para `cidr_acesso`. Em produção: ALB com
  certificado do ACM, tarefa em subnet privada, VPC endpoint para o Bedrock.
- **Estado** — não há banco. O histórico vive na memória do processo, e a
  `memory.md` está *dentro da imagem*: o que a Eva "aprender" some quando a
  tarefa é trocada. É a limitação mais importante desta arquitetura.
- **Escala** — uma tarefa. Com duas, dois usuários veriam memórias diferentes.
- **CI/CD** — o deploy é um script rodado à mão. Não há pipeline, homologação
  nem rollback automático.
- **Autenticação do usuário** — qualquer um com o IP conversa com a Eva (e
  gasta o seu dinheiro). Restrinja `cidr_acesso` ao seu IP fora da aula.

Bom exercício de arquitetura: **qual caixa você acrescentaria primeiro?**
(Uma resposta defensável: um armazenamento externo para o estado — DynamoDB
para a conversa, S3 para o `memory.md` — e reparar que isso muda o nível 2,
não o nível 1.)
