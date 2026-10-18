# Exercícios — Aula 4

**Tema:** Serviços de IA da AWS & APIs
**Formato:** **Entrega obrigatória por grupo** — ZIP no Portal FIAP
**Vale:** 10% da nota final ([rubrica completa](../../entregas/rubrica.md))
**Prazo:** 1 dia antes da Aula 5
**Como entregar:** ver [entregas/entrega-04/INSTRUCOES.md](../../entregas/entrega-04/INSTRUCOES.md)

---

## Instruções gerais

Esta é a **4ª entrega de grupo** da disciplina. Os 3 níveis são **divisão de trabalho dentro do grupo**:

- 🟢 **Nível 1 — Básico:** pronto × custom × LLM, custo mensal, segurança (IAM Role × access key), capacidades do Rekognition
- 🟡 **Nível 2 — Intermediário:** pipeline robusto de reviews (resumo + PII + sentimento por aspecto), casos de uso de voz, Rekognition pronto × Custom Labels
- 🔴 **Nível 3 — Avançado:** **bônus opcional** — embeddings reais no pgvector, Custom Labels, sumarização com LLM no Bedrock

**Mínimo obrigatório:** N1 + N2 cobertos. **N3 é bônus** (até +2 pts extras).

### Distribuição entre membros (sugerida)

- Iniciantes: N1 — consolidação dos tipos de serviço de IA
- Intermediários: N2 — estender o pipeline da Lambda
- Experientes: N3 — embeddings, modelo próprio e LLM

> **Rodízio:** quem fez N1 nas Aulas 1-3 deve assumir N2 ou N3 agora.

### Template obrigatório

Use o [template em `entregas/template-entrega-grupo.md`](../../entregas/template-entrega-grupo.md) para o `entrega-grupo-aula04.md` dentro do ZIP.

> **Política "no install":** tudo no AWS CloudShell, com o Learner Lab iniciado. O Learner Lab **não libera o Amazon Bedrock**: os itens com Bedrock são de arquitetura e estimativa (ou para quem tiver conta própria).

---

## 🟢 Nível 1 — Básico: Consolidando os Fundamentos

### Exercício 1.1 — Pronto × Custom × LLM

Para cada caso da Quantum Commerce, marque a opção mais adequada (**API pronta**, **modelo customizado** ou **LLM**) e justifique em 1-2 frases:

| Caso de uso | Pronta | Custom | LLM | Justificativa |
|-------------|--------|--------|-----|---------------|
| Detectar idioma de uma review | | | | |
| Classificar produtos em 5 categorias da QC (jargão próprio) | | | | |
| Gerar descrição de produto a partir da foto + specs | | | | |
| Transcrever áudio de atendimento em PT-BR | | | | |
| Extrair CPF, e-mail, telefone de chat (LGPD) | | | | |
| Responder pergunta aberta do cliente sobre política de troca | | | | |
| OCR de etiqueta nutricional | | | | |
| Identificar peças industriais da empresa em foto de estoque | | | | |

<details>
<summary>Sugestões de gabarito</summary>

- Detectar idioma: **Pronta** (Comprehend `DetectDominantLanguage`)
- Categorias com jargão próprio QC: **Custom** (Comprehend Custom Classification)
- Descrição de produto: **LLM** (Bedrock) — abertura criativa
- Transcrever PT-BR: **Pronta** (Transcribe) — modelo bem treinado em PT
- Extrair PII: **Pronta** (Comprehend `DetectPiiEntities` — confira o suporte ao português; senão, Macie para dados no S3 ou um LLM com instrução)
- Pergunta aberta sobre política: **LLM** + RAG com os documentos da política
- OCR de etiqueta: **Pronta** (Textract, ou `DetectText` do Rekognition para texto curto)
- Peças industriais: **Custom** (Rekognition Custom Labels) — vocabulário não cabe num modelo genérico

</details>

---

### Exercício 1.2 — Calcule o custo mensal

A Quantum Commerce processa por mês:

- **2M de reviews** para sentimento + entidades (média 200 caracteres cada)
- **50.000 horas de atendimento** transcritas
- **500 mil imagens de produto** analisadas (rótulos + texto)

Use o [AWS Pricing Calculator](https://calculator.aws) (us-east-1) e preencha:

| Serviço | Volume | Preço unitário | Total mensal |
|---------|--------|----------------|--------------|
| Comprehend (sentimento) | 2M reviews | ~US$ 0,0001 por unidade de 100 caracteres (mín. 3 unidades por documento) | |
| Comprehend (entidades) | 2M reviews | idem | |
| Transcribe (batch, PT-BR) | 3M minutos | ~US$ 0,024/min nos primeiros 250 mil min, com descontos por faixa | |
| Rekognition (`DetectLabels` + `DetectText`) | 500 mil × 2 chamadas | ~US$ 1,00 por mil imagens por API | |
| **Total** | | | |

**Análise:**

a) Qual serviço pesa mais? Repare no **mínimo de 3 unidades**: uma review de 200 caracteres paga como 300.
b) Se trocar sentimento + entidades por um LLM pequeno no Bedrock (Claude Haiku 5.5: US$ 0,10/1M tokens de entrada e US$ 0,50/1M de saída), com ~60 tokens de entrada e ~20 de saída por review, quanto custaria? E em **batch** (−50%)?
c) Em que cenário vale trocar API pronta por LLM — e em qual o LLM perde mesmo sendo mais barato? (pense em determinismo, latência e auditoria)

---

### Exercício 1.3 — Segurança: como a Lambda autentica nos serviços de IA?

Marque a estratégia recomendada para produção e justifique:

| Estratégia | Recomendado? | Razão |
|-----------|--------------|-------|
| Access key hardcoded no `function_app.py` | | |
| Access key em variável de ambiente da Lambda | | |
| Access key no Secrets Manager, lida pela Lambda | | |
| Execution role da Lambda com permissão direta no Comprehend/Rekognition | | |

**Perguntas extras:**

1. Por que, na AWS, **não existe** "chave do serviço de IA" como em outras nuvens? Onde fica, então, o controle de acesso?
2. O lab deixa a porta 27017 do MongoDB aberta para a internet porque a Lambda está fora da VPC. Como seria em produção? (Lambda numa subnet privada da VPC, Mongo em subnet privada, regra de entrada referenciando o **security group da Lambda**, e VPC endpoints para S3/Secrets Manager)
3. O `semear_reviews.py` tem a senha do Mongo no código. Reescreva-o lendo o segredo `$MONGO_SECRET_ID`.

<details>
<summary>Sugestão</summary>

- Hardcoded → **NÃO** (vaza no repositório)
- Variável de ambiente → **não ideal** (quem lê a configuração da função vê)
- Secrets Manager → **ok para segredos de terceiros** (como a senha do Mongo), mas desnecessário para serviços AWS
- **Execution role** → ✅ **padrão de produção**: credencial temporária, rotacionada pela própria Lambda, auditada no CloudTrail

</details>

---

### Exercício 1.4 — Mapa de capacidades do Rekognition

Para cada cenário da QC, escolha a capacidade (**DetectLabels**, **DetectText**, **DetectFaces/Face Liveness**, **Custom Labels**, **DetectModerationLabels**, ou **outro serviço** — Textract, Bedrock):

| Cenário | Capacidade | Justificativa |
|---------|-----------|---------------|
| Auto-categorizar produto novo enviado pelo vendedor | | |
| Encontrar produtos visualmente parecidos com o da busca | | |
| Contar quantos produtos estão na prateleira de uma loja física | | |
| Extrair o preço da etiqueta de um produto fotografado | | |
| Gerar texto alternativo (alt-text) para acessibilidade | | |
| Saber se a foto tem pessoas (anonimização LGPD) | | |
| Classificar entre os 12 modelos próprios da linha "QC Premium" | | |
| Barrar foto imprópria enviada por vendedor | | |

---

## 🟡 Nível 2 — Intermediário: Pipeline e Decisões

### Exercício 2.1 — Pipeline robusto de reviews QC

O L₃ fez sentimento + entidades. Estenda a rota `/analisar-reviews` (ou crie `/analisar-reviews-v2`) com:

a) **PII:** antes da análise, redija CPF, e-mail e telefone. Teste `comprehend.detect_pii_entities` e confira se o português é suportado; se não for, implemente com regex para CPF/telefone/e-mail e explique a limitação.

b) **Sentimento por aspecto:** use `comprehend.detect_targeted_sentiment` para identificar **aspectos** ("entrega" → negativo, "qualidade" → positivo). Confira os idiomas suportados — se o português não estiver, use `TranslateText` do Amazon Translate antes (e discuta o custo e o risco de traduzir).

c) **Resumo:** para reviews com mais de 300 caracteres, um resumo de 1 frase — com quê? (Comprehend não resume: compare `DetectKeyPhrases` com um LLM no Bedrock)

d) **Persistência estruturada** no MongoDB:

```json
{
  "id": "r001",
  "produto": "Notebook Pro X",
  "texto": "Adorei o produto, mas a entrega demorou demais",
  "texto_redigido": "...",
  "sentimento": "MIXED",
  "sentimento_score": {"positive": 0.6, "negative": 0.3, "neutral": 0.05, "mixed": 0.05},
  "aspectos": [
    {"texto": "produto", "sentimento": "POSITIVE"},
    {"texto": "entrega", "sentimento": "NEGATIVE"}
  ],
  "entidades": [],
  "frases_chave": [],
  "processado_em": "2026-10-20T14:30:00Z"
}
```

**Entrega:** código atualizado + 3 reviews processadas no `entrega-grupo-aula04.md`.

---

### Exercício 2.2 — Casos de uso de voz na QC (Transcribe + Polly)

Proponha **3 casos de uso** concretos de fala → texto ou texto → fala para a QC. Para cada um:

a) Qual o problema de negócio?
b) Transcribe ou Polly? Tempo real (streaming) ou batch?
c) Arquitetura (que componentes da QC envolve? Amazon Connect? Lex?)
d) Volume mensal + custo estimado
e) Riscos (qualidade em PT-BR, latência, LGPD — gravação é dado pessoal)
f) Métricas de sucesso

Inspiração: URA com Amazon Lex + Connect · transcrição pós-atendimento com **Transcribe Call Analytics** · leitura automática de descrições (acessibilidade) · busca por voz no app · áudio de anúncio gerado pelo Polly.

---

### Exercício 2.3 — Rekognition pronto × Custom Labels

A QC decide entre o Rekognition pronto e um modelo próprio para classificar imagens de produtos.

**Dados:** 5M de SKUs em 150 categorias da QC (ex.: "sofá-3-lugares-modular"); 90% das fotos em fundo branco; ~30-50 imagens rotuladas por categoria; 50 mil classificações/mês.

a) Calcule o custo mensal:
   - **Pronto + LLM** para mapear os rótulos genéricos → categoria QC: Rekognition US$ 0,001 × 50 mil + LLM no Bedrock
   - **Custom Labels:** horas de treino (~US$ 1/h) + **horas de inferência com o modelo ligado** (~US$ 4/h por unidade) — atenção: Custom Labels cobra pelo tempo em que o modelo fica **rodando**, não por imagem
b) Compare a **qualidade esperada** no vocabulário específico.
c) Compare a **manutenção** quando a QC adiciona 20 categorias por trimestre.
d) **Recomende** — e, se fizer sentido, proponha um híbrido (Custom Labels nos top 20, pronto + LLM no resto; ou inferência em lote em janelas fixas).

---

## 🔴 Nível 3 — Avançado: Embeddings, modelo próprio e LLM

### Exercício 3.1 — Embeddings reais no pgvector

A Aula 2 gerou embeddings com MiniLM no CloudShell. Agora, use os **resultados de IA desta aula** para enriquecer a busca:

a) Para cada review analisada no MongoDB, gere um embedding do texto (mesmo modelo da Aula 2, com `fastembed`) e grave numa tabela `reviews_vetor` no RDS da Aula 2 (ou num RDS novo) com o sentimento do Comprehend como coluna.
b) Implemente a consulta: "reviews **negativas** que falam de **entrega atrasada**" = filtro `sentimento = 'NEGATIVE'` + `ORDER BY embedding <=> :consulta`.
c) Compare com a mesma busca só por palavra (`ILIKE '%entrega%'`).
d) **Produção:** troque o MiniLM pelo **Amazon Titan Text Embeddings V2** (1024 dimensões) no Bedrock. Estime o custo de vetorizar 30M de reviews (~80 tokens cada) a ~US$ 0,02 por 1M tokens.

---

### Exercício 3.2 — Custom Labels para a linha "QC Premium"

a) No console do **Rekognition → Custom Labels**, crie um projeto com 3 rótulos fictícios (`qc-sofa-premium`, `qc-poltrona-premium`, `qc-mesa-premium`).
b) Envie 15-20 imagens por rótulo para um bucket S3 (use imagens livres, ex.: Unsplash) e crie o dataset.
c) **Treine** o modelo e avalie precision, recall e F1 no conjunto de teste.
d) **Inicie** o modelo, teste com `detect_custom_labels` e **pare** o modelo logo em seguida (ele cobra por hora ligado).
e) Documente: prints das métricas, o ARN do modelo e o custo estimado de 50 mil predições/mês (compare "ligado 24/7" × "ligado 1 h/dia processando em lote").

> Se o Learner Lab recusar o treino, entregue o desenho do pipeline (S3 → dataset → treino → avaliação → start/stop agendado) e a estimativa de custo.

---

### Exercício 3.3 — Sumarizar reviews por produto com LLM (Bedrock)

Desenhe (e, se tiver conta própria, implemente) a rota `/sumarizar-reviews-produto`:

a) Recebe `produto` como query param
b) Lê **todas as reviews** desse produto no MongoDB (já com sentimento)
c) Chama um modelo do Bedrock (ex.: Claude Haiku 5.5 via `bedrock-runtime` `converse`) com prompt estruturado:

```
Você é um analista de e-commerce. Analise as reviews abaixo do produto {produto} e retorne em JSON:
{
  "resumo_geral": "1-2 frases",
  "pontos_positivos": [...],
  "pontos_negativos": [...],
  "recomendacoes_de_acao": [...]
}

Reviews:
{lista de reviews com sentimento}
```

d) Retorna o JSON estruturado
e) Compare com a versão **só com Comprehend** do L₃: quando o LLM ganha? Quando a API pronta basta?
f) **Custo:** estime para 5M produtos × 50 reviews (use tokens de entrada/saída e o desconto de batch).

---

## Critérios de entrega

A entrega é **um ZIP por grupo** (`entrega-grupo-NN-aula04.zip`) no Portal FIAP. Estrutura em [entregas/entrega-04/INSTRUCOES.md](../../entregas/entrega-04/INSTRUCOES.md).

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1 (pronto/custom/LLM), 1.2 (custo mensal), 1.3 (segurança IAM Role vs access key), 1.4 (capacidades do Rekognition) | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (pipeline robusto: PII + aspectos + resumo), 2.2 (casos de voz na QC), 2.3 (Rekognition pronto vs Custom Labels) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.1 (embeddings reais no pgvector), 3.2 (Custom Labels), 3.3 (sumarização LLM com Bedrock) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total da entrega** | | **10 pts** (10% da nota final) |

**Prazo:** 1 dia antes da Aula 5.
**Onde:** upload do ZIP no Portal FIAP. Apenas 1 membro do grupo faz o upload.
