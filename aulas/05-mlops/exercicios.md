# Exercícios — Aula 5

**Tema:** MLOps na Nuvem
**Formato:** **Entrega obrigatória por grupo** — ZIP no Portal FIAP
**Vale:** 10% da nota final ([rubrica completa](../../entregas/rubrica.md))
**Prazo:** 1 dia antes da Aula 6
**Como entregar:** ver [entregas/entrega-05/INSTRUCOES.md](../../entregas/entrega-05/INSTRUCOES.md)

---

## Instruções gerais

Esta é a **5ª e última entrega intermediária**. A Aula 6 é dedicada ao **trabalho em grupo no projeto integrado final** (50% da nota — entrega ZIP, **sem apresentação oral**).

### Importante — perfil dos alunos

Esta disciplina é uma das **primeiras do MBA**, e **NÃO é necessário** conhecimento prévio de Python/ML para fazer os exercícios. N1 e N2 são **conceituais e de operacionalização** (não exigem programação ML). N3 é avançado e opcional. Modelagem em profundidade é tema da disciplina **"AI Foundation and Learning Models"**.

### Estrutura dos 3 níveis (divisão de trabalho dentro do grupo)

- 🟢 **Nível 1 — Básico:** conceitos (ciclo de vida, maturidade MLOps, MLflow params/metrics/artifacts, Registry/rollback, segurança de dados). Tudo perguntas/respostas — **zero código**
- 🟡 **Nível 2 — Intermediário:** raciocínio + integração leve (integrar a 5ª tool na Lambda, plano de drift monitoring para a QC). Código pré-pronto disponível no repo
- 🔴 **Nível 3 — Avançado:** **bônus opcional** — Hyperparameter Tuning (otimização de hiperparâmetros), endpoint produtivo com load test, A/B testing real, MLOps vs LLMOps comparado

**Mínimo obrigatório:** N1 + N2 cobertos. **N3 é bônus** (até +2 pts extras).

### Distribuição entre membros (sugerida)

- Iniciantes: N1 — consolidação dos conceitos
- Intermediários: N2 — integração na Lambda + plano de drift
- Experientes (com background ML): N3 — sweep, endpoint produtivo, A/B

> **Rodízio:** quem fez N1 nas Aulas 1-4 deve assumir N2 ou N3 agora. Esta é a última oportunidade antes da entrega final.

### Template obrigatório

Use o [template em `entregas/template-entrega-grupo.md`](../../entregas/template-entrega-grupo.md) para o `entrega-grupo-aula05.md` dentro do ZIP.

> **Política "no install":** Tudo no AWS CloudShell ou no console do SageMaker AI.

---

## 🟢 Nível 1 — Básico

### Exercício 1.1 — Diagnóstico de Maturidade MLOps

Para cada cenário abaixo, identifique o **nível de maturidade MLOps** (0 = Manual / 1 = Pipeline automation / 2 = CI/CD completo) e justifique:

| Cenário | Nível | Justificativa |
|---------|-------|---------------|
| DS treina modelo no notebook, exporta .pkl, manda pro time de produto via Slack | | |
| Equipe usa SageMaker Pipelines + Model Registry + deploy manual pelo console | | |
| Pull Request muda código → CI roda testes + treino + avaliação → se aprovado, deploy automático no Endpoint Production | | |
| Pipeline roda toda semana com dataset atualizado, retreina + registra nova versão; aprovação humana antes de promover para Production | | |
| Modelo em produção monitora drift; quando passa do limite, dispara retreino automático e cria PR para revisão | | |

**Pergunta complementar:** Onde a Quantum Commerce está hoje (na sua opinião — sem ter visto a QC real)? Onde ela deveria estar em 12 meses?

<details>
<summary>Sugestões de gabarito</summary>

1. **Nível 0** — totalmente manual
2. **Nível 1** — pipeline existe mas deploy é manual
3. **Nível 2** — CI/CD completo
4. **Nível 1 (avançado, quase 2)** — automatizado mas com aprovação humana
5. **Nível 2** — retreino automático com feedback loop

QC hoje (provavelmente): nível 0. Em 12 meses: nível 1 — pipeline reproduzível + Registry + retreino mensal.

</details>

---

### Exercício 1.2 — Para que serve cada tipo de log no MLflow?

Para cada artefato/métrica, marque se você logaria como `param`, `metric` ou `artifact`:

| Item | param | metric | artifact |
|------|-------|--------|----------|
| `learning_rate=0.01` | | | |
| Curva de loss durante 100 epochs | | | |
| Modelo serializado `.pkl` | | | |
| Versão da biblioteca scikit-learn | | | |
| AUC final no test set | | | |
| Confusion matrix em PNG | | | |
| Dataset usado (caminho/hash) | | | |
| `random_seed=42` | | | |
| Precisão por classe (5 classes) | | | |
| Notebook .ipynb original | | | |

<details>
<summary>Gabarito</summary>

- `learning_rate=0.01` → **param**
- Curva de loss → **metric** (sequência de valores ao longo das epochs)
- Modelo .pkl → **artifact**
- Versão sklearn → **param** (ou metadado/tag)
- AUC → **metric** (escalar único)
- Confusion matrix PNG → **artifact**
- Dataset → **artifact** (ou param se for caminho/hash)
- random_seed → **param**
- Precisão por classe → **metric** (5 valores)
- Notebook → **artifact**

</details>

---

### Exercício 1.3 — Model Registry: Stages e Rollback

Cenário: você é o ML Engineer da Quantum Commerce. Sua linha do tempo do Registry está assim:

```
recomendador-qc v1  → Approved               (no endpoint há 1 mês)
recomendador-qc v2  → PendingManualApproval  (treinado há 1 semana, em teste)
recomendador-qc v3  → Rejected               (experimento de pesquisa, não validado)
```

**Você quer promover v2 para Production.**

a) Qual o passo a passo seguro (sem causar downtime)?

b) Se o v2 em Production começar a falhar 1 hora depois, como você faz rollback rápido para v1?

c) Após rollback, o que você faz com v2? Archive imediato? Investiga? Por quê?

d) Em **A/B testing**, como você dividiria tráfego entre v1 (estável) e v2 (novo) num único endpoint do SageMaker? (Dica: *production variants* com pesos.)

---

### Exercício 1.4 — Sub-bloco de Segurança: Dados Sensíveis

Para cada situação de risco em ML, escolha a melhor mitigação:

| Situação de risco | Mitigação adequada |
|-------------------|--------------------|
| Modelo de recomendação treinado com CPF, e-mail, telefone dos clientes | |
| Dataset de treino contém dados de cartão de crédito (PCI-DSS) | |
| Pesquisador externo precisa do dataset para benchmark mas a empresa não pode compartilhar dados reais | |
| Modelo é exposto publicamente — risco de inversão (recuperar dados de treino a partir das saídas) | |
| Logs do endpoint capturam payload da request (que pode conter PII do cliente) | |

Opções: **PII Detection antes do treino** (ex.: Amazon Comprehend `DetectPiiEntities`), **Dados sintéticos (SDV)**, **Differential Privacy no treino**, **Política IAM / bucket policy restrita no dataset**, **Sampling de logs com retenção curta**.

---

## 🟡 Nível 2 — Intermediário

### Exercício 2.1 — Documentar o pipeline MLOps da Quantum Commerce

Imagine que você foi contratado pela QC e precisa **documentar** o pipeline MLOps que vocês construíram nesta aula para apresentar ao CIO.

**Sua tarefa (sem código — só documentação):**

a) **Desenhe o pipeline** completo do `recomendador-qc` no Excalidraw/draw.io, mostrando:

- Onde vivem os dados (Blob da Aula 2)
- Como o treino é disparado (manual, schedule, novo dataset)
- Onde o modelo é registrado (Model Registry)
- Como vai para produção (manual ou automático)
- Como é monitorado

b) **Liste os artefatos versionados** em cada etapa:

- O que o tracking captura (MLflow local e métricas do Training Job)?
- O que o Model Registry guarda (veja `registrar_modelo.py`)?
- O que a imagem `sagemaker-scikit-learn` + o `sourcedir.tar.gz` têm dentro?

c) **Responda: por que um pipeline reproduzível** vale mais do que um notebook que treina bem? Imagine os 4 cenários:

- Daniel (data scientist) precisa retreinar com dados de outubro porque novembro está chegando
- Maria (nova ML engineer) acabou de entrar no time e precisa rodar o pipeline
- O modelo em produção começou a falhar — fazer rollback rápido
- A QC quer auditoria de qual modelo recomendou X produto para Y cliente em maio passado

d) **Identifique 3 gaps** entre o nosso lab (provavelmente nível 1 de maturidade MLOps) e o nível 2 (CI/CD completo). O que falta automatizar?

> Este exercício é 100% conceitual e de raciocínio — não exige código novo. É um insumo importante para o projeto integrado.

---

### Exercício 2.2 — Integrar o recomendador na Lambda da QC

A Lambda da Aula 3 precisa de uma 5ª rota `/recomendar`:

a) **Implemente a rota no `lambda_function.py`:**
   - Recebe `produto_id` (ou `cliente_id` se o grupo modelou com base em reviews)
   - Chama o endpoint com `boto3.client("sagemaker-runtime").invoke_endpoint(...)`
   - Retorna top 5 produtos similares com nome, preço, categoria

b) **Use a role da Lambda** para autenticar no endpoint (sem chave nenhuma)
   - Mostre a política IAM mínima: `sagemaker:InvokeEndpoint` no ARN do **seu** endpoint
     (no Learner Lab a LabRole já permite; documente o que seria em produção)
   - Documente como fica o código — repare que não há token nem segredo

c) **Trate falhas graciosamente:** se o endpoint estiver indisponível (apagado / cold start / erro), retornar uma resposta de fallback baseada em **categoria** (top 5 produtos da mesma categoria do `produto_id` fornecido)

d) **Documente a tool no formato JSON Schema** (estilo OpenAI function calling), explicando ao agente quando usar `/recomendar` vs `/produtos`

---

### Exercício 2.3 — Drift Monitoring: plano para a QC

Cenário: o recomendador da QC está em produção há 3 meses. Você é o MLOps Engineer.

**Sua tarefa:** Proponha um plano de drift monitoring com:

a) **Métricas a monitorar:**
   - Quais features dos produtos podem driftar? (preço médio, categoria distribution, novos produtos...)
   - Quais métricas de output? (CTR das recomendações, conversão para compra, score de satisfação)

b) **Como detectar drift:**
   - Estatísticos: KS test, PSI (Population Stability Index)
   - ML-based: usar o **SageMaker Model Monitor** (data quality e model quality), com *data capture* no endpoint

c) **Alertas:**
   - Threshold: quando alertar?
   - Para quem? (Slack, e-mail, PagerDuty?)

d) **Resposta automática vs manual:**
   - Em qual caso retreina automaticamente?
   - Em qual caso pausa o modelo e exige revisão humana?
   - Como executar rollback se o retreino piorar?

**Bonus:** desenhe o pipeline completo no Excalidraw/draw.io.

---

## 🔴 Nível 3 — Avançado

> **Nota:** N3 envolve programação Python e conceitos de ML. Se o grupo não tem perfil avançado, entregar apenas N1 + N2 já garante 10 pts (mínimo obrigatório).

### Exercício 3.0 — Hyperparameter Tuning: otimização de hiperparâmetros

Estenda o L₃ para rodar um **Hyperparameter Tuning Job** do SageMaker (o "sweep"):

a) **Parametrize** o `train.py` para aceitar também `--metrica` (`cosine` | `euclidean`)

b) Escreva `scripts/otimizar.py` chamando `create_hyper_parameter_tuning_job`:

```python
sm.create_hyper_parameter_tuning_job(
    HyperParameterTuningJobName=f"rec-qc-tune-{sufixo}",
    HyperParameterTuningJobConfig={
        "Strategy": "Bayesian",
        "HyperParameterTuningJobObjective": {
            "Type": "Maximize", "MetricName": "precision_at_k_proxy"},
        "ResourceLimits": {"MaxNumberOfTrainingJobs": 8, "MaxParallelTrainingJobs": 2},
        "ParameterRanges": {
            "IntegerParameterRanges": [{"Name": "n_neighbors", "MinValue": "3", "MaxValue": "10"}],
            "CategoricalParameterRanges": [{"Name": "metrica", "Values": ['"cosine"', '"euclidean"']}],
        },
    },
    TrainingJobDefinition={...},  # o mesmo do submeter_job.py, sem n_neighbors/metrica fixos
)
```

c) **Submeta** e identifique o melhor job (`describe_hyper_parameter_tuning_job` → `BestTrainingJob`)

d) **Registre** o melhor modelo no Registry como `PendingManualApproval`

**Entrega:**

- `aulas/05-mlops/lab/scripts/otimizar.py` no repo do grupo
- Print da aba *Training jobs* do tuning job
- Reflexão: por que esses ranges? Em que outros parâmetros faria a busca numa situação real?

> ⚠️ 8 jobs × ~3 min de ml.m5.large ≈ centavos — mas confira a cota de jobs simultâneos do Learner Lab antes.

---

### Exercício 3.1 — Endpoint produtivo (com custo controlado)

A) Publique o recomendador em endpoint de **instância** (`--tipo instancia`, ml.m5.large) e configure **auto scaling** (Application Auto Scaling): mín 1, máx 3, métrica `SageMakerVariantInvocationsPerInstance`

B) Ligue o **data capture** do endpoint (10% das requisições, para um prefixo do bucket) — e discuta o que isso implica em LGPD

C) Faça **load test** a partir do CloudShell (ex.: um laço Python com `invoke_endpoint` em 5 threads, 100 requisições)

D) Reporte:

- p50, p95, p99 de latência (métrica `ModelLatency` no CloudWatch)
- Throughput máximo
- Custo total do experimento (instâncias × tempo ativo)
- Comparação com o **serverless** da Atividade 4 (cold start × custo parado zero)

E) **Reflexão:** quando vale endpoint dedicado vs serverless vs Lambda com o modelo embutido (o `.joblib` tem poucos KB)?

---

### Exercício 3.2 — A/B testing real

A) Crie um **EndpointConfig com duas production variants** no mesmo endpoint: `blue` com a v1 e `green` com a v2 (do L₃ Parte D)

B) Configure os **pesos**:

- blue (v1): 0.8
- green (v2): 0.2

C) Envie 100 requisições e veja, no CloudWatch, `Invocations` por variante

D) Analise (mesmo que sintético):

- Qual variante foi mais rápida?
- Qual gerou recomendações mais variadas?

E) **Promova ou faça rollback** com `update_endpoint_weights_and_capacities`:

- v2 melhor: 50/50 → 0/100, e aprove a v2 no Registry
- v2 pior: 100/0, e rejeite a v2 no Registry

Documente cada passo com o comando usado.

---

### Exercício 3.3 — MLOps vs LLMOps: aplicar à Quantum Commerce

A QC quer trocar o recomendador clássico por um **agente conversacional** que usa LLM + vector search da Aula 2 (pgvector) + tools (a Lambda).

**Sua tarefa:** Compare os 2 cenários lado a lado:

| Aspecto | MLOps (recomendador atual) | LLMOps (agente conversacional) |
|---------|----------------------------|--------------------------------|
| Artefato versionado | | |
| Pipeline de "treino" | | |
| Avaliação offline | | |
| Avaliação online | | |
| Deploy | | |
| Monitoramento | | |
| Drift detection | | |
| Tempo entre "experimento" e produção | | |
| Custo de operação mensal (ordem de grandeza) | | |

**Reflexão (1 página):**

- Quais ferramentas da Aula 5 (Tracking, Registry, Endpoints) **continuam relevantes** em LLMOps (ex.: Amazon Bedrock)?
- Quais **mudam** ou ganham componentes novos (prompt registry, eval framework, RAG quality, etc.)?
- Como você posicionaria os 2 sistemas na arquitetura QC? (substituir? coexistir? hibridizar?)

---

## Critérios de entrega

A entrega é **um ZIP por grupo** (`entrega-grupo-NN-aula05.zip`) no Portal FIAP. Estrutura completa, prazo e dicas de geração do ZIP em [entregas/entrega-05/INSTRUCOES.md](../../entregas/entrega-05/INSTRUCOES.md).

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1, 1.2, 1.3, 1.4 | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (documentação pipeline MLOps), 2.2 (5ª tool na Lambda), 2.3 (plano de drift) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.0 (tuning), 3.1 (endpoint + load test), 3.2 (A/B testing), 3.3 (MLOps vs LLMOps) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total da entrega** | | **10 pts** (10% da nota final) |

**Prazo:** 1 dia antes da Aula 6.
**Onde:** upload do ZIP no Portal FIAP.

> **⚠️ Atenção custo:** se você manteve um endpoint de **instância** do N3 ativo entre a aula e a entrega, **apague agora** (`python3 scripts/limpar.py --registro`). ~US$ 2,76/dia por instância. Reforço da rubrica: Critério 3 desconta se o endpoint estiver ativo na hora da correção.

---

## Lembrete: Aula 6 = FinOps + projeto integrado

A Aula 6 tem 2 partes:

1. **FinOps** (parte inicial) — princípios, ferramentas e calculadoras de custo aplicados à arquitetura da QC
2. **Tempo guiado para trabalho em grupo no projeto integrado final** (vale 50% da nota total — entrega ZIP, **sem apresentação oral**)

Comece a consolidar agora:

1. **Diagrama final** da arquitetura QC com **todas as camadas** (Aulas 1-5): IaC, dados, API serverless, cognitivos, ML
2. **Terraform consolidado** que provisiona tudo (S3 + RDS/pgvector + DynamoDB + Lambda + Secrets Manager + bucket/Registry do SageMaker)
3. **Estimativa de custos** mensal — vocês completam na Aula 6 com FinOps + calculadora
4. **5 tools do agente** documentadas (`/produtos`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`, `/recomendar`)
5. **Documento final** no formato ZIP para o Portal FIAP

Rubrica do projeto integrado final em [entregas/projeto-final/INSTRUCOES.md](../../entregas/projeto-final/INSTRUCOES.md).
