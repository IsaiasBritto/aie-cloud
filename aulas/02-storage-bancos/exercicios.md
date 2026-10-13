# Exercícios — Aula 2

**Tema:** Storage & Bancos de Dados na Nuvem
**Formato:** **Entrega obrigatória por grupo** — ZIP no Portal FIAP
**Vale:** 10% da nota final ([rubrica completa](../../entregas/rubrica.md))
**Prazo:** 1 dia antes da Aula 3
**Como entregar:** ver [entregas/entrega-02/INSTRUCOES.md](../../entregas/entrega-02/INSTRUCOES.md)

---

## Instruções gerais

Esta é a **2ª entrega de grupo** da disciplina. Os 3 níveis são **divisão de trabalho dentro do grupo**, não escolha livre:

- 🟢 **Nível 1 — Básico:** consolida storage, classes do S3, relacional vs NoSQL, IAM do Secrets Manager
- 🟡 **Nível 2 — Intermediário:** modelagem de dados QC + plano de migração + particionamento DynamoDB (ou Mongo)
- 🔴 **Nível 3 — Avançado:** **bônus opcional** — busca híbrida (vetor + full-text), OLAP com Athena (proposta), benchmark

**Mínimo obrigatório:** N1 + N2 cobertos. **N3 é bônus** (até +2 pts extras).

### Distribuição entre membros do grupo (sugerida)

- Iniciantes em cloud: N1 (consolidação)
- Intermediários: N2 (bloco QC — matriz de decisão e plano de migração)
- Experientes: N3 (bônus) — busca híbrida é o tópico mais técnico

> **Rodízio:** quem fez N1 na Aula 1 deve preferencialmente fazer N2 ou N3 agora. Vale ponto da rubrica (Critério 4 — Colaboração).

### Template obrigatório

Use o [template em `entregas/template-entrega-grupo.md`](../../entregas/template-entrega-grupo.md) para o `entrega-grupo-aula02.md` dentro do ZIP.

> **Política "no install":** Tudo roda no AWS CloudShell. `pip install --user` é OK no CloudShell.

---

## 🟢 Nível 1 — Básico: Consolidando os Fundamentos

### Exercício 1.1 — Tipos de Storage

Para cada cenário, escolha **Object Storage**, **File Storage** ou **Block Storage** e justifique em uma frase.

| Cenário | Tipo | Justificativa |
|---------|------|---------------|
| Hospedar imagens de produtos do e-commerce QC (5M de SKUs) | | |
| Disco onde roda o sistema operacional de uma VM de banco | | |
| Pasta compartilhada entre 10 VMs de um time de DevOps | | |
| Backup mensal de bancos de dados (retenção 7 anos) | | |
| Storage de modelos `.pkl` do time de ML para serving | | |
| Dump diário de logs de aplicação para análise futura | | |

<details>
<summary>Gabarito sugerido</summary>

- Imagens de produtos: **Object** (volume alto, acesso via HTTP, sem necessidade de sistema de arquivos)
- Disco da VM de banco: **Block** (baixa latência, atrelado a uma VM)
- Pasta compartilhada entre VMs: **File** (montável em múltiplas VMs simultaneamente como `/mnt/dados`)
- Backup com 7 anos: **Object (S3 Glacier Deep Archive)** (custo baixíssimo, acesso raro)
- Modelos `.pkl` para serving: **Object (S3)** (downloads via HTTP, versionamento de objeto)
- Logs para análise: **Object com lifecycle Standard → Standard-IA → Glacier** (analytics serverless com Athena sobre o S3)

</details>

---

### Exercício 1.2 — Tiers de acesso (cálculo)

A Quantum Commerce armazena **2 TB de logs de compras**. Os primeiros 30 dias os logs são consultados para detecção de fraude (S3 Standard). Depois disso, viram dados arquivados de compliance LGPD (S3 Glacier Deep Archive, retenção 5 anos).

a) Quanto custaria 1 mês desses logs **se mantidos 100% em S3 Standard**? (Use ~$0,023/GB/mês em us-east-1)
b) Quanto custaria 1 mês desses logs **com lifecycle: 30 dias Standard + Deep Archive depois**? (Deep Archive ~$0,00099/GB/mês)
c) Economia anual com a lifecycle policy?

<details>
<summary>Gabarito</summary>

- a) 2.048 GB × $0,023 = **$47,10/mês** (~$565/ano)
- b) Considerando steady state, ~92% do volume em Deep Archive:
  - Standard: 2048 × 30/365 × $0,023 = $3,87/mês (média anual)
  - Deep Archive: 2048 × 335/365 × $0,00099 = $1,86/mês (média anual)
  - Total: ~**$5,73/mês**
- c) Economia anual: ($47,10 - $5,73) × 12 = **~$496/ano**

> Atenção ao que o cálculo não mostra: Deep Archive cobra para **ler** (recuperação em até 12 h) e tem permanência mínima de 180 dias.

> Para a QC com volumes reais (centenas de TB), essa decisão impacta facilmente seis dígitos por ano.

</details>

---

### Exercício 1.3 — Relacional vs NoSQL

Para cada caso de uso da Quantum Commerce, marque qual tipo de banco é mais adequado e justifique:

| Caso de uso | Relacional (RDS PostgreSQL) | NoSQL (DynamoDB) | Vector DB (pgvector) | Justificativa |
|-------------|-----------------------------|------------------|----------------------|---------------|
| Carrinho de compras ativo do usuário | | | | |
| Catálogo de produtos com SKU, preço, estoque | | | | |
| Reviews dos clientes (texto livre + score) | | | | |
| "Encontre produtos similares a este" (recomendação) | | | | |
| Histórico de pedidos para faturamento | | | | |
| Sessão do usuário (chave-valor, expira em 30min) | | | | |
| Logs de comportamento de navegação | | | | |

<details>
<summary>Sugestões</summary>

- Carrinho ativo: **NoSQL doc** (esquema variável, leitura rápida, expira)
- Catálogo: **Relacional** (esquema fixo, joins com categorias, integridade de estoque)
- Reviews: **NoSQL doc** (texto livre, sem schema rígido)
- Recomendação: **Vector DB** (similaridade semântica)
- Histórico de pedidos: **Relacional** (ACID, faturamento exige garantias)
- Sessão (key-value): **DynamoDB com TTL** (ou ElastiCache/Redis, se a latência for crítica)
- Logs de navegação: **NoSQL** ou S3 + Athena — depende do uso analítico

</details>

---

### Exercício 1.4 — Secrets Manager e IAM

Você acabou de provisionar o Secrets Manager da Aula 2. Para cada perfil, descreva a permissão IAM mínima (ações + recurso) e justifique:

| Perfil | Ações IAM no Secrets Manager | Justificativa |
|--------|------------------------------|---------------|
| Você (dev e ops do lab) | | |
| Lambda que consulta `t_produtos` precisa ler a connection string | | |
| Engenheiro de segurança que audita os segredos sem ver os valores | | |
| Pipeline de CI/CD que cria e rotaciona segredos | | |
| Time de FinOps que precisa ver o custo dos segredos sem ver os valores | | |

**Referência:** [Ações, recursos e condições do Secrets Manager](https://docs.aws.amazon.com/service-authorization/latest/reference/list_awssecretsmanager.html)

<details>
<summary>Sugestões</summary>

- Você: `secretsmanager:*` restrito ao prefixo `arn:aws:secretsmanager:*:*:secret:qc-aula02-*` (nunca `Resource: "*"` em produção)
- Lambda lendo o segredo: só `secretsmanager:GetSecretValue` no ARN daquele segredo, na **execution role** da função
- Auditor: `secretsmanager:ListSecrets` e `DescribeSecret` — **sem** `GetSecretValue`
- CI/CD: `CreateSecret`, `PutSecretValue`, `RotateSecret` no prefixo do projeto, via role assumida por OIDC
- FinOps: nada no Secrets Manager — acesso de leitura ao Cost Explorer (`ce:Get*`), filtrando pela tag `projeto`

</details>

---

## 🟡 Nível 2 — Intermediário: Decisões Arquiteturais

### Exercício 2.1 — Modelagem de dados da QC (em grupo)

A Quantum Commerce tem os seguintes domínios:

- **Produtos** (catálogo: 5M SKUs)
- **Clientes** (~50M de clientes ativos, perfil + endereço + preferências)
- **Pedidos** (~10M/mês, alta criticidade transacional)
- **Carrinhos ativos** (~500k a qualquer momento, expiram em 24h)
- **Reviews** (~30M de textos livres, alimentam análise de sentimento)
- **Busca de produtos** (consultas dos agentes + frontend)
- **Sessões de usuário** (~1M ativas)
- **Histórico de navegação** (clickstream — bilhões de eventos)
- **Modelos de ML** (recomendação, classificação, predição de churn)

**Sua tarefa:** Preencha a matriz de decisão abaixo:

| Domínio | Serviço AWS escolhido | Tipo/Configuração | Justificativa em 1-2 frases |
|---------|-----------------------|-------------------|------------------------------|
| Produtos | | | |
| Clientes | | | |
| Pedidos | | | |
| Carrinhos | | | |
| Reviews | | | |
| Busca de produtos | | | |
| Sessões | | | |
| Histórico navegação | | | |
| Modelos ML | | | |

**Bonus:** Desenhe o diagrama da camada de dados completa da QC no Excalidraw / draw.io e cole no `respostas-aula02.md`.

> Este exercício é peça-chave do projeto final. Tente fazer em grupo discutindo cada decisão.

---

### Exercício 2.2 — Plano de migração de dados

A Quantum Commerce hoje tem:

- Banco Oracle on-premise com 8 TB (produtos + pedidos + clientes)
- 50 TB de imagens em servidor NAS local
- ~200 TB de logs históricos em fitas magnéticas (compliance fiscal)

**Sua tarefa:** Proponha um plano de migração de 12 meses considerando:

a) **Quais dos 6 Rs** (Aula 1) você usaria para cada repositório atual?
b) **Quais serviços AWS** ficariam com cada um, considerando custo + criticidade?
c) **Como migrar** sem downtime? (Pesquise sobre AWS DMS, AWS DataSync e a família Snowball)
d) **Estimativa de custo de transferência** para os 50 TB de imagens (entrar na AWS é grátis — e sair depois?)
e) **Como manter compliance LGPD** — onde os dados de brasileiros podem ficar?

Use as calculadoras dos 3 provedores se quiser comparar custos.

---

### Exercício 2.3 — Particionamento no DynamoDB (ou no MongoDB)

No lab da Aula 2, a tabela `reviews` tem chave de partição `produto_id` e chave de ordenação `review_id`. Responda:

a) Por que **NÃO** seria boa chave de partição:
   - `review_id` sozinho? (3 razões — pense nas consultas que o agente faz)
   - `score` (1-5)? (2 razões)
   - `data_da_review` (timestamp)? (2 razões)

b) Por que `produto_id` **funciona razoavelmente bem**, mas pode ter um problema. Qual? (Pesquise "hot partition")

c) Se a QC quisesse otimizar para "todas as reviews de um cliente específico", como seria? (Pesquise **Global Secondary Index** no DynamoDB — ou índice composto no MongoDB)

d) Estime: um produto com 50.000 reviews de ~400 bytes. Quanto ocupa a partição? Compare com o limite de **400 KB por item** e com o limite de **10 GB por valor de chave de partição** (que vale quando a tabela tem Local Secondary Index).

e) **Se o grupo fez o Lab 3C (MongoDB):** como a chave de shard do MongoDB se compara à chave de partição do DynamoDB?

---

## 🔴 Nível 3 — Avançado: Busca híbrida, OLAP e benchmark

### Exercício 3.1 — Busca híbrida: vetor + full-text no mesmo PostgreSQL

O lab fez busca **só por significado** (pgvector). Busca só por vetor erra em código de produto, marca e número ("Dell Inspiron 15"); busca só por palavra erra em sinônimo ("algo para trabalhar em pé"). A busca **híbrida** combina as duas.

**Tudo no CloudShell, no mesmo RDS do lab.**

1. Adicione à tabela `produtos_vetor` uma coluna de full-text em português:

```sql
ALTER TABLE produtos_vetor
  ADD COLUMN tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('portuguese', nome || ' ' || coalesce(descricao,''))) STORED;
CREATE INDEX produtos_tsv ON produtos_vetor USING gin (tsv);
```

2. Escreva `buscar_hibrido.py` que, para uma consulta, roda as duas buscas e funde os rankings com **Reciprocal Rank Fusion** (RRF: `score = Σ 1/(60 + posição)`):

```sql
-- ranking por palavra
SELECT id, ts_rank(tsv, plainto_tsquery('portuguese', %s)) AS r
FROM produtos_vetor WHERE tsv @@ plainto_tsquery('portuguese', %s)
ORDER BY r DESC LIMIT 10;

-- ranking por significado
SELECT id FROM produtos_vetor ORDER BY embedding <=> %s LIMIT 10;
```

3. Rode as 3 consultas abaixo nos 3 modos (palavra, vetor, híbrido) e registre o top 3 de cada:
   - `"Dell Inspiron"`
   - `"algo para trabalhar em pé"`
   - `"presente para quem gosta de correr"`

**Reflexão (no `entrega-grupo-aula02.md`):**

1. Em qual consulta cada modo falhou? Por quê?
2. Que modelo de embedding você usaria em produção? (Dica: Amazon Titan Text Embeddings V2 ou Cohere Embed Multilingual, no Bedrock)
3. Como manter os embeddings atualizados quando produtos novos chegam? (pipeline incremental — evento do S3 → Lambda)
4. Quando valeria trocar o pgvector por **Amazon OpenSearch Service** ou por **Bedrock Knowledge Bases**?

---

### Exercício 3.2 — OLAP com Athena: proposta (sem executar)

> O Learner Lab não libera o Athena — este exercício é de **arquitetura**, não de execução.

A QC quer analisar 3 anos de logs de compras (dezenas de TB) sem carregar tudo num data warehouse.

1. **Desenhe** o fluxo: logs no S3 (`logs/`) → catálogo no **AWS Glue Data Catalog** → SQL no **Amazon Athena** → painel no **Amazon QuickSight**.
2. **Escreva** a DDL e a consulta que você rodaria (formato e particionamento são a parte importante):

```sql
CREATE EXTERNAL TABLE logs_compras (
  pedido_id string, produto_id int, valor decimal(10,2), ts timestamp
)
PARTITIONED BY (ano int, mes int)
STORED AS PARQUET
LOCATION 's3://<bucket>/logs/compras/';

SELECT mes, COUNT(*) AS pedidos, SUM(valor) AS receita
FROM logs_compras WHERE ano = 2026
GROUP BY mes ORDER BY mes;
```

3. **Calcule:** o Athena cobra por TB lido (~US$ 5/TB). Quanto custa a consulta acima sobre 30 TB de CSV sem partição? E sobre o mesmo dado em Parquet particionado por ano/mês, sabendo que o Parquet costuma comprimir ~5× e a consulta só lê 1 ano de 3?
4. **Compare** com o Amazon Redshift Serverless: quando o warehouse passa a valer a pena?

---

### Exercício 3.3 — Benchmark: RDS × DynamoDB × pgvector

Para a pergunta do agente "**cadeira ergonômica para dor lombar**", você tem 3 opções na QC:

a) **RDS PostgreSQL** com `ILIKE '%cadeira%'` e filtros de categoria/preço
b) **DynamoDB** — sem busca por texto nativa: o que seria preciso? (Scan com filtro? índice externo?)
c) **pgvector** com busca por significado (ou a híbrida do 3.1)

**Tarefa:**

1. Implemente (a) e (c); para (b), implemente o Scan com `contains()` e explique por que não escala
2. Meça a latência média de 10 consultas em cada (`time.perf_counter()`)
3. Compare a **qualidade** (quem traz o produto certo?)
4. Projete o **custo** de 1M consultas/mês em cada (use o AWS Pricing Calculator)
5. **Recomende** qual usar para o agente de busca da QC

Entrega: tabela comparativa + recomendação justificada.

---

## Critérios de entrega

A entrega é **um ZIP por grupo** (`entrega-grupo-NN-aula02.zip`) no Portal FIAP. Estrutura completa, prazo e dicas de geração do ZIP em [entregas/entrega-02/INSTRUCOES.md](../../entregas/entrega-02/INSTRUCOES.md).

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1, 1.2, 1.3, 1.4 respondidos | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (matriz + diagrama), 2.2 (migração), 2.3 (particionamento DynamoDB ou Mongo) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.1 (busca híbrida: vetor + full-text), 3.2 (OLAP: proposta com Athena), 3.3 (benchmark) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total da entrega** | | **10 pts** (10% da nota final) |

**Prazo:** 1 dia antes da Aula 3.
**Onde:** upload do ZIP no Portal FIAP. Apenas 1 membro do grupo faz o upload.
