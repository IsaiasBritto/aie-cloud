# Eva (local → Bedrock)

A mesma Eva, agora falando com um modelo do **Amazon Bedrock**. A aplicação
continua rodando na **sua máquina**; só o modelo mudou de lugar.

> ⚠️ **O AWS Academy Learner Lab não libera o Bedrock.** Esta pasta roda numa
> conta AWS comum — na aula, é a **demonstração do professor**. O aluno
> acompanha o código e roda a [Eva local](../01-agente-Eva-local/) com a OpenAI.
>
> 📘 **Primeira vez?** Comece pelo [GUIA-BEDROCK.md](GUIA-BEDROCK.md) — conta,
> acesso ao modelo, credencial e política IAM mínima.

---

### Passo 1 — baixar o projeto

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/05-bedrock-agents/02-agente-Eva-local-to-bedrock
```

### Passo 2 — ambiente, dependências e credencial

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
aws configure                      # ou: aws sso login --profile <perfil>
```

**Sempre confira a conexão antes de rodar a Eva:**

```bash
python verificar.py
```

Ele testa credencial (STS), o model ID, uma chamada simples e o tool use — um
de cada vez, dizendo exatamente onde parou. Se o model ID estiver errado, ele
lista os perfis de inferência disponíveis na região.

## Rodar

```bash
python eva.py              # terminal
streamlit run app.py       # interface web
```

---

## O que mudou em relação à Eva original

**1. O cliente — e a autenticação.**

```diff
- cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
+ cliente = boto3.client("bedrock-runtime", region_name="us-east-1")
```

Não existe chave da aplicação. O boto3 assina cada requisição com a sua
credencial AWS, e quem autoriza é a política IAM
(`bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`).

**2. O formato da conversa.** A API **Converse** fala em blocos de conteúdo:

| | OpenAI (Chat Completions) | Bedrock (Converse) |
| --- | --- | --- |
| System prompt | mensagem `role: system` | parâmetro `system=[{"text": ...}]` |
| Declarar tool | `{"type": "function", "function": {...}}` | `{"toolSpec": {"name", "description", "inputSchema": {"json": ...}}}` |
| Modelo pede tool | `message.tool_calls` | bloco `toolUse` + `stopReason == "tool_use"` |
| Resultado da tool | mensagem `role: tool` | bloco `toolResult` numa mensagem `role: user` |
| Tokens | `usage.prompt_tokens` / `completion_tokens` | `usage.inputTokens` / `outputTokens` |

O **loop** faz exatamente a mesma coisa — manda, executa a ferramenta, repete.
As ferramentas, o `agent.md` e o `memory.md` estão inalterados. A tradução do
histórico mora em `_preparar()`, então o `app.py` nem percebe a troca.

**Arquivos novos:** `verificar.py` (diagnóstico) e `GUIA-BEDROCK.md`.

---

## Model ID, perfil de inferência e "acesso ao modelo"

A parte que mais confunde quem vem da OpenAI pública:

| | OpenAI pública | Bedrock |
| --- | --- | --- |
| O que vai em `model` | nome do modelo (`gpt-5.4-mini`) | **model ID** ou **perfil de inferência** (`us.amazon.nova-lite-v1:0`) |
| Modelos disponíveis | todo o catálogo | o catálogo da **região**; alguns pedem formulário de caso de uso (Anthropic) |
| Chamar o ID "nu" de um modelo novo | — | **ValidationException**: use o perfil `us.` ou `global.` |

O perfil de inferência roteia a chamada entre regiões da mesma geografia
(`us.`) ou do mundo (`global.`) — mais vazão, mesmo código. Na interface web,
o campo **Model ID** na barra lateral troca o destino ao vivo, sem reiniciar.

---

## Configuração (`.env`)

| Variável | O que é |
| --- | --- |
| `AWS_PROFILE` | Perfil do `aws configure` (opcional; sem ele, usa o padrão) |
| `AWS_REGION` | Região do Bedrock (`us-east-1`) |
| `BEDROCK_MODEL_ID` | Model ID ou perfil de inferência |
| `EVA_TEMPERATURA` | 0 = objetiva · 1 = criativa |
| `EVA_MAX_ITERACOES` | Teto de voltas do loop |
| `EVA_MAX_TOKENS` | Teto de tokens de saída por chamada |

---

## Problemas comuns

| Erro | Causa provável |
| --- | --- |
| `AccessDeniedException` | Falta `bedrock:InvokeModel` na política; ou é o Learner Lab |
| `ValidationException ... model identifier is invalid` | Model ID errado, ou ID nu onde o modelo exige perfil de inferência |
| `ResourceNotFoundException` | Modelo marcado como *legacy* / descontinuado |
| `ThrottlingException` | Cota de tokens ou requisições por minuto estourada |
| `UnrecognizedClientException` / `ExpiredToken` | Credencial expirada — refaça o login |
| O modelo ignora as ferramentas | O modelo escolhido não suporta tool use na Converse |

`python verificar.py` traduz todos esses.

---

## Próximo passo

Hoje: modelo no Bedrock, aplicação local. Depois
([03-agente-Eva-aws](../03-agente-Eva-aws/)): aplicação também na AWS —
Dockerfile, ECR, **ECS Fargate** com **task role** (a mesma cadeia de
credencial, sem `aws configure`), Secrets Manager e telemetria no
**CloudWatch Logs**.
