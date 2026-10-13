# Exercícios — Aula 3

**Tema:** Serverless & Containers
**Formato:** **Entrega obrigatória por grupo** — ZIP no Portal FIAP
**Vale:** 10% da nota final ([rubrica completa](../../entregas/rubrica.md))
**Prazo:** 1 dia antes da Aula 4
**Como entregar:** ver [entregas/entrega-03/INSTRUCOES.md](../../entregas/entrega-03/INSTRUCOES.md)

---

## Instruções gerais

Esta é a **3ª entrega de grupo** da disciplina. Os 3 níveis são **divisão de trabalho dentro do grupo**:

- 🟢 **Nível 1 — Básico:** quando usar serverless, IAM Role vs alternativas, cold start, Dockerfile review
- 🟡 **Nível 2 — Intermediário:** segunda tool (cálculo de frete), observabilidade com CloudWatch, Fargate (restart, sizing e segredos)
- 🔴 **Nível 3 — Avançado:** **bônus opcional** — spec de tool para agente, benchmark de carga, CI/CD com GitHub Actions + OIDC

**Mínimo obrigatório:** N1 + N2 cobertos. **N3 é bônus** (até +2 pts extras).

### Distribuição entre membros (sugerida)

- Iniciantes: N1 (consolidação dos conceitos de serverless + IAM)
- Intermediários: N2 (estender a Lambda da aula com nova tool e observabilidade)
- Experientes: N3 (bônus) — design de tool de agente, benchmark, CI/CD

> **Rodízio:** quem fez N1 nas Aulas 1-2 deve assumir N2 ou N3 agora. Vale Critério 4 da rubrica.

### Template obrigatório

Use o [template em `entregas/template-entrega-grupo.md`](../../entregas/template-entrega-grupo.md) para o `entrega-grupo-aula03.md` dentro do ZIP.

> **Política "no install":** tudo no AWS CloudShell, com o Learner Lab iniciado.

---

## 🟢 Nível 1 — Básico: Consolidando os Fundamentos

### Exercício 1.1 — Quando usar serverless?

Para cada cenário da Quantum Commerce, marque **Lambda**, **ECS Fargate**, **App Runner** ou **EKS** e justifique em uma frase:

| Cenário | Escolha | Justificativa |
|---------|---------|---------------|
| API de busca de produtos (1M chamadas/mês, picos na Black Friday) | | |
| Worker que processa pedidos da fila (1000 pedidos/dia, picos noturnos) | | |
| API legada em Java Spring Boot (não pode reescrever, time conhece) | | |
| Pipeline de processamento de imagens de produtos (1 hora por noite) | | |
| Microserviço de pagamentos (regulado, logs detalhados, 100 req/s constante) | | |
| Plataforma com 25 microserviços + service mesh | | |
| Container que extrai dados uma vez por dia e termina | | |

<details>
<summary>Sugestões de gabarito</summary>

- API de busca (1M/mês, picos): **Lambda** — paga por chamada, escala sozinha, o free tier cobre boa parte
- Worker de fila: **Lambda com gatilho SQS** — orientado a evento, escala a zero
- Java Spring Boot legado: **App Runner** (URL HTTPS + auto-scale com pouca operação) ou **ECS Fargate**
- Pipeline batch de 1h/noite: **ECS Fargate (tarefa agendada pelo EventBridge Scheduler)** — paga por segundo, sem limite de 15 min
- Pagamentos com tráfego constante e regulado: **ECS Fargate** ou **EKS** — controle fino, sem cold start
- 25 microserviços + service mesh: **EKS** — o ecossistema de mesh mais maduro
- Container one-shot diário: **ECS Fargate (RunTask agendado)** — exatamente o caso de uso

</details>

---

### Exercício 1.2 — IAM Role vs alternativas

Para cada estratégia de credencial, marque **vulnerabilidade alta**, **média** ou **baixa** e justifique:

| Estratégia | Vulnerabilidade | Por quê |
|------------|-----------------|---------|
| Access key da AWS hardcoded no `lambda_function.py` | | |
| Access key em variável de ambiente da Lambda | | |
| Connection string no Secrets Manager, lida com access key de um usuário IAM | | |
| Connection string no Secrets Manager, lida com a execution role da Lambda | | |
| Sem segredo — a execution role tem permissão direta no recurso (S3) | | |

**Pergunta adicional:** em quais estratégias **um vazamento do código no GitHub continua sendo problema**? Em quais não é? Por quê?

---

### Exercício 1.3 — Cold start na prática

Faça **3 chamadas** à sua Lambda (do L₂), com intervalo de:

- Chamada 1: **agora** (provavelmente fria)
- Chamada 2: **5 segundos depois**
- Chamada 3: **30 minutos depois** (provavelmente fria de novo)

```bash
time curl -s -o /dev/null "${FUNC_URL}produtos"
```

Confirme no CloudWatch: o log da chamada fria tem a linha `REPORT ... Init Duration: ... ms`; a quente, não.

| Chamada | Tempo | Teve `Init Duration`? |
|---------|-------|------------------------|
| 1 (fria) | | |
| 2 (quente) | | |
| 3 (fria de novo) | | |

**Pergunta:** se o agente da QC chamar essa função 1 vez por hora (24 chamadas/dia), quantas serão frias? Como mitigar se a UX exige resposta em < 500 ms? *(pesquise Provisioned Concurrency e SnapStart — e o custo de cada um)*

---

### Exercício 1.4 — Dockerfile review

```dockerfile
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

Liste **5 problemas** (segurança, tamanho, eficiência, boas práticas) e proponha melhorias. Compare com o [Dockerfile do lab](lab/docker/Dockerfile).

<details>
<summary>Sugestões</summary>

1. `python:3.12` (imagem completa ~1 GB) em vez de `python:3.12-slim` (~150 MB)
2. `COPY . .` copia tudo, inclusive `.git` e `__pycache__` → usar `.dockerignore`
3. `pip install` sem `--no-cache-dir` → infla a imagem
4. Sem multi-stage build → ferramentas de build ficam no runtime
5. Roda como root → `USER app` (não-root)
6. `CMD ["python", "app.py"]` para web service → rodar `uvicorn`/`gunicorn` explicitamente
7. Sem `EXPOSE` e sem `HEALTHCHECK`
8. Base do Docker Hub sujeita a limite de pull → espelho no ECR Public (`public.ecr.aws/docker/library/python`)

</details>

---

## 🟡 Nível 2 — Intermediário: Decisões de Design + IaC

### Exercício 2.1 — Segunda tool para o agente: cálculo de frete

- Input: CEP origem, CEP destino, peso (kg)
- Output: valor em R$ + prazo estimado
- Lógica: simples e determinística (R$ por faixa de CEP + R$ por kg)
- 50.000 chamadas/mês esperadas

**Sua tarefa:**

a) Decida: **nova rota na mesma Lambda** (`GET /frete`) ou **nova função** com Function URL própria? Justifique.
b) Implemente a rota `calcular_frete` (continue a `v2-s3/lambda_function.py`, ou crie `v3-frete/`).
c) Atualize o Terraform se criar uma função nova (`aws_lambda_function` + `aws_lambda_function_url` + as duas permissões).
d) Documente como "tool" em JSON Schema (como o catálogo no wrap-up do guia).
e) Reflexão: quando você separaria funções (deploy, permissão, escala, custo) e quando manteria juntas?

---

### Exercício 2.2 — Observabilidade com CloudWatch

A Lambda da Aula 3 já manda logs para o CloudWatch (log group com 7 dias de retenção).

**Sua tarefa:**

a) Faça 20 chamadas variadas (inclua rotas que não existem, para gerar 404) e rode no **CloudWatch Logs Insights**, no log group `/aws/lambda/qc-aula03-...-catalogo`:

```
filter @type = "REPORT"
| stats count() as chamadas, avg(@duration) as media_ms, pct(@duration, 95) as p95_ms,
        max(@maxMemoryUsed / 1000 / 1000) as memoria_mb, sum(strcontains(@message, "Init Duration")) as frias
```

b) Em **Lambda → Monitor**, tire **um print** das métricas Invocations, Duration e Errors.
c) Estenda o Terraform com um `aws_cloudwatch_metric_alarm` sobre a métrica `Errors` da função (≥ 1 em 5 min).
d) Responda: qual o p95 de latência? A memória configurada (256 MB) está sobrando? Quanto custaria baixar para 128 MB — e o que acontece com a latência? *(na Lambda, CPU é proporcional à memória)*
e) Para um sistema multiagente em produção, qual a estratégia de logs/métricas/traces? Pesquise **OpenTelemetry** e **AWS X-Ray**.

---

### Exercício 2.3 — Fargate: restart, sizing e segredos

O lab subiu uma tarefa Fargate **básica**. Evolua o `containers.tf`:

a) **Serviço × tarefa avulsa** — o lab usa um **serviço** (o ECS recria a tarefa se ela cair). Crie uma variante para um **job batch** da QC (recalcular recomendações à noite e terminar): `aws_scheduler_schedule` disparando `RunTask`. Quando usar serviço e quando usar tarefa agendada?

b) **Right-sizing + custo** — o lab usa 0,25 vCPU / 0,5 GB. Suba uma variante com 1 vCPU / 2 GB. No [AWS Pricing Calculator](https://calculator.aws), estime o custo/mês de **1 tarefa 24/7** em cada tamanho e compare com a Lambda equivalente para 1M chamadas/mês.

c) **Segredo na task definition** — injete um valor do Secrets Manager com o bloco `secrets` do container (`valueFrom` = ARN do segredo) em vez de `environment`. Mostre a diferença com `aws ecs describe-task-definition`: o valor aparece?

d) **Escala** — o serviço do lab tem `desired_count = 1` e nenhum auto scaling. O que acontece num pico de Black Friday? Escreva o `aws_appautoscaling_target` + `aws_appautoscaling_policy` (target tracking em CPU 60%) e explique por que, sem load balancer, escalar não basta.

e) **Reflexão:** para a QC, quais workloads você levaria para **Fargate** e quais para **Lambda**? Considere custo parado, HTTPS, escala e simplicidade operacional.

---

## 🔴 Nível 3 — Avançado: Tool de Agente + Benchmark + CI/CD

### Exercício 3.1 — A Lambda como tool de um agente (conceitual + código)

a) Escreva a **descrição completa** da tool no formato de tool use (Anthropic) / function calling:

```json
{
  "name": "buscar_produtos_qc",
  "description": "...",
  "input_schema": {
    "type": "object",
    "properties": {
      "categoria": {"type": "string", "description": "..."},
      "nome": {"type": "string", "description": "..."}
    }
  }
}
```

A descrição **deve ensinar o agente quando usar a tool**. Inclua exemplos.

b) Escreva 3 conversas usuário-agente em que o agente chama a tool:
   - "Tem cadeira boa para home office?"
   - "Quanto custa o Galaxy S24?"
   - "Preciso de algo para café"

   Para cada: pergunta → chamada à tool (parâmetros) → resposta do agente.

c) Identifique 2 casos em que o agente **NÃO deve chamar a tool** mesmo o usuário falando de produto. Justifique.

d) Como manter a descrição da tool sincronizada com o endpoint? (versionamento, contract testing, OpenAPI)

---

### Exercício 3.2 — Benchmark de carga

No CloudShell, instale o Apache Bench e dispare carga na sua Lambda:

```bash
sudo dnf install -y httpd-tools
ab -n 1000 -c 50 "${FUNC_URL}produtos?categoria=moveis"
```

**Reporte:** latência média, p50, p95, p99, throughput (req/s), taxa de erro e custo (Lambda x86: US$ 0,20 por 1M requisições + US$ 0,0000166667 por GB-s).

Repita contra a tarefa Fargate (`http://$TASK_IP:8080/produtos?categoria=moveis`) e compare:

| Métrica | Lambda | ECS Fargate |
|---------|--------|-------------|
| Latência média | | |
| p95 | | |
| Throughput | | |
| Erros | | |
| Custo aprox. por 1M req | | |

a) Qual aguentou melhor? Por quê? (olhe a métrica `ConcurrentExecutions` da Lambda)
b) Em qual cenário cada um venceria?
c) Como você arquitetaria a API da QC para a Black Friday (10× tráfego)?

---

### Exercício 3.3 — Pipeline CI/CD para a Lambda

Crie `.github/workflows/deploy-lambda.yml` no repositório privado do grupo que:

a) Roda em cada push para `main` que altere `aula03/function/**`
b) Faz lint (`ruff`)
c) Roda testes (`pytest` — pelo menos 1 teste do handler, com o evento da Function URL simulado)
d) Faz `aws lambda update-function-code` automaticamente

**Pontos extras:**

- Autentique com **OIDC** (`aws-actions/configure-aws-credentials` + role com trust no `token.actions.githubusercontent.com`), sem access key guardada em secret
- Publique uma **versão** e mova um **alias** `prod` só depois do teste (`aws lambda publish-version` + `update-alias`)

> **Limitação do Learner Lab:** ele não deixa criar o provedor OIDC nem a role. Escreva o Terraform/IAM que seria necessário e explique o fluxo; para testar, use as credenciais temporárias de **AWS Details** do Learner Lab como secrets do repositório (expiram em ~4 h — e é exatamente por isso que OIDC é o certo).

---

## Critérios de entrega

A entrega é **um ZIP por grupo** (`entrega-grupo-NN-aula03.zip`) no Portal FIAP. Estrutura completa em [entregas/entrega-03/INSTRUCOES.md](../../entregas/entrega-03/INSTRUCOES.md).

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1 (quando usar serverless), 1.2 (IAM Role vs alternativas), 1.3 (cold start), 1.4 (Dockerfile review) | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (segunda tool: cálculo de frete), 2.2 (CloudWatch), 2.3 (Fargate: restart/sizing/secrets) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.1 (spec de tool de agente), 3.2 (benchmark), 3.3 (CI/CD GitHub Actions + OIDC) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total da entrega** | | **10 pts** (10% da nota final) |

**Prazo:** 1 dia antes da Aula 4.
**Onde:** upload do ZIP no Portal FIAP. Apenas 1 membro do grupo faz o upload.
