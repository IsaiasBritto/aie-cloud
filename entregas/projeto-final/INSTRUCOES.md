# Projeto Integrado Final — Quantum Commerce

**Vale:** 50% da nota total
**Formato:** Entrega via ZIP no Portal FIAP — **sem apresentação oral**
**Prazo:** 1 semana após a Aula 6
**Rubrica específica:** seção "Rubrica do Projeto Integrado Final" em [rubrica.md](../rubrica.md) (50 pts)

---

## O que é

O **Projeto Integrado Final** é a consolidação de tudo o que o grupo construiu ao longo das 5 aulas anteriores em **um único entregável coerente** que demonstra:

1. **Arquitetura cloud completa** para a Quantum Commerce
2. **Infraestrutura como Código** consolidada e funcional
3. **5 tools** consumíveis por agentes
4. **Análise FinOps** com estimativa de custo + propostas de otimização
5. **Reflexão estratégica** sobre como a arquitetura evoluiria nos próximos 12 meses

> A Aula 6 dedica **1h40 de trabalho assistido** para vocês consolidarem isso com suporte do professor. A semana seguinte é para polir antes da entrega.

---

## Conteúdo obrigatório do ZIP

Nome do arquivo: `projeto-integrado-grupo-NN.zip`

```
projeto-integrado-grupo-NN/
├── README.md                              # ⭐ Documento principal (instruções + visão)
├── distribuicao-do-trabalho.md            # Quem fez o quê nas 6 aulas + projeto final
├── arquitetura/
│   ├── diagrama-final.png                 # Diagrama da arquitetura QC completa
│   └── decisoes-tecnicas.md               # ADR-style: principais decisões + alternativas
├── terraform/                             # ⭐ IaC consolidado
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── storage.tf
│   ├── databases.tf
│   ├── cognitive.tf
│   ├── lambda.tf
│   ├── ml.tf
│   └── README.md                          # Como aplicar e destruir
├── function/                              # ⭐ Lambda consolidada com 5 tools
│   ├── function_app.py                    # handler (Powertools) ou lambda_function.py
│   ├── requirements.txt
│   └── README.md
├── tools-spec.md                          # ⭐ JSON Schema das 5 tools (formato function calling)
├── finops/                                # ⭐ Análise FinOps
│   ├── estimativa-qc.csv                  # Export do AWS Pricing Calculator
│   ├── analise-otimizacao.md              # Top 3 caros + propostas
│   └── pricing-calculator-link.md         # Link compartilhável da estimativa
└── reflexao-estrategica.md                # ⭐ Roadmap 12 meses + lições aprendidas
```

**Tamanho do ZIP:** < 20 MB (limite do Portal FIAP). **Não incluir:**

- `terraform.tfstate*` (segredos vazam — usar `.gitignore`)
- `__pycache__/`, `.venv/`, `node_modules/`
- Áudios ou imagens binárias grandes (>5 MB)
- Modelos `.pkl` treinados (descrever no README como regenerar)

---

## Como gerar o ZIP

A partir do repo privado do grupo:

```bash
cd ~/qc-grupo-NN
git status
git pull origin main

# Criar pasta consolidada se ainda não existe
mkdir -p projeto-integrado-final
# (mover/consolidar arquivos das aulas 1-5 para essa pasta)

# Gerar ZIP só do versionado (respeita .gitignore)
git archive --format=zip --prefix=projeto-integrado-grupo-NN/ \
  -o ~/projeto-integrado-grupo-NN.zip HEAD:projeto-integrado-final

# Verificar tamanho e conteúdo
ls -lh ~/projeto-integrado-grupo-NN.zip
unzip -l ~/projeto-integrado-grupo-NN.zip
```

Upload no Portal FIAP, **um único membro** do grupo (combine antes).

---

## Detalhes de cada peça obrigatória

### 1. README.md (do projeto)

Estrutura sugerida:

```markdown
# Projeto Integrado — Quantum Commerce — Grupo NN

## Visão geral
Em 2-3 parágrafos: o que a QC precisa, qual a proposta da nossa arquitetura, decisões-chave.

## Stack escolhida
Tabela: serviço AWS | propósito | custo mensal | alternativas consideradas

## Como executar
Passos para alguém de fora reproduzir o ambiente:
1. terraform init && terraform apply
2. (popular dados de exemplo)
3. (deploy da Lambda — código via `aws lambda update-function-code`)
4. (testar as 5 tools)

## Estrutura do repositório
Mapa dos arquivos.

## Equipe
Tabela: nome | GitHub | papel no projeto.

## Licença
Padrão MIT ou CC.
```

### 2. arquitetura/diagrama-final.png

Diagrama da arquitetura completa, com todas as camadas:

- **Frontend** (não construído, apenas marcado como integração)
- **API / Lambda** (5 tools, Function URL)
- **Dados:** S3, RDS PostgreSQL + pgvector, DynamoDB (e/ou MongoDB)
- **Cognitivos:** Transcribe, Polly, Comprehend, Rekognition
- **ML:** SageMaker AI (Training Job + Model Registry + endpoint)
- **Identidade & Segredos:** IAM roles + Secrets Manager (transversal)
- **Observabilidade:** CloudWatch Logs / Metrics / Logs Insights (transversal)
- **Setas** mostrando fluxos de dados e chamadas de tools

Ferramentas aceitas: Excalidraw, draw.io, Visio, Lucid, Mermaid, foto de quadro branco (legível).

### 3. arquitetura/decisoes-tecnicas.md

Estilo **Architecture Decision Records (ADR)** — para cada decisão importante:

- **Decisão:** o que foi escolhido
- **Contexto:** por que essa decisão foi necessária
- **Opções consideradas:** quais alternativas
- **Consequências:** trade-offs aceitos

Mínimo de **5 decisões** documentadas (ex.: "por que RDS PostgreSQL com pgvector e não OpenSearch", "por que Lambda e não ECS Fargate no MVP", "por que IAM role em vez de segredo no Secrets Manager", "por que endpoint serverless e não instância 24/7", etc.).

### 4. terraform/ (IaC consolidado)

- **Único projeto Terraform** que provisiona TODA a infra QC com `terraform apply`
- Arquivos separados por domínio (`storage.tf`, `databases.tf`, `cognitive.tf`, `ml.tf`, `lambda.tf`)
- `variables.tf` com tudo parametrizável (region, sufixo, etc.)
- `outputs.tf` expondo endpoints e nomes
- `README.md` explicando ordem de execução e como destruir

**Critério de aceitação:** `terraform validate` e `terraform plan` rodam sem erros (no Learner Lab, usando a `LabRole`).

> Não é exigido que `terraform apply` seja executado pelo professor durante a correção — basta que o `plan` valide.

### 5. function/ (5 tools)

Lambda consolidada com as rotas:

| Rota | Aula | O que faz |
|------|------|-----------|
| `/produtos` | 3 | Lista produtos do S3 filtrados por categoria/nome |
| `/transcrever` | 4 | Transcribe: fala → texto de áudio do S3 |
| `/analisar-reviews` | 4 | Comprehend: sentimento + entidades sobre reviews do MongoDB/DynamoDB |
| `/analisar-imagem` | 4 | Rekognition: rótulos + texto (OCR) |
| `/recomendar` | 5 | Chama o endpoint do SageMaker — top 5 produtos similares |

Todas as rotas devem usar a **role da Lambda** (sem chave de acesso no código); segredo de banco só via **Secrets Manager**. Documentação inline em cada rota (docstring).

### 6. tools-spec.md

Especificação das 5 tools no formato **`toolSpec` da API Converse (Bedrock)** / **OpenAI function calling** / **Anthropic tool use**:

```json
[
  {
    "name": "buscar_produtos_qc",
    "description": "Quando o cliente perguntar sobre catálogo, produtos disponíveis, preços, estoque ou características de produtos. Use com termos da fala do cliente.",
    "url": "https://<id>.lambda-url.us-east-1.on.aws/produtos",
    "method": "GET",
    "input_schema": {
      "type": "object",
      "properties": {
        "categoria": {"type": "string", "description": "categoria do produto, ex: moveis, eletronicos"},
        "nome":      {"type": "string", "description": "trecho do nome do produto"}
      }
    }
  }
]
```

Inclua para **cada tool**:

- `name`, `description` clara que ensine o agente quando usar
- URL completa do endpoint
- Método HTTP
- Schema dos parâmetros
- Pelo menos **2 exemplos** de query/conversa que disparariam essa tool

### 7. finops/estimativa-qc.csv + analise-otimizacao.md

Export do AWS Pricing Calculator (do L₂ da Aula 6) + análise:

- Top 3 itens mais caros
- 3 propostas de otimização com economia estimada
- Comparação com Reserved Instances / Savings Plans de 1 ano
- TCO mensal final (otimizado vs não-otimizado)
- Parágrafo "como apresentar para o CFO"

### 8. reflexao-estrategica.md

**Roadmap de 12 meses** para a arquitetura QC, em 4 períodos:

| Trimestre | Foco | Entregáveis |
|-----------|------|-------------|
| Q1 | Estabilizar fundação | (o que foi feito + observabilidade básica) |
| Q2 | Otimização FinOps + segurança | (Reserved Instances, KeyVault avançado) |
| Q3 | Escalar AI capabilities | (Custom Vision, fine-tuning, vector search verdadeira) |
| Q4 | Multi-cloud / preparação para escala global | (CDN, multi-region, DR) |

Inclua também:

- **Lições aprendidas em cada aula** (1-2 linhas por aula)
- **O que faríamos diferente** (autoavaliação honesta)
- **Conexão com agentes:** como essa arquitetura habilita as próximas disciplinas do MBA

### 9. distribuicao-do-trabalho.md

Tabela mostrando quem fez o quê em cada aula e no projeto final:

```markdown
| Aula | Membro 1 | Membro 2 | Membro 3 | Membro 4 | Membro 5 |
|------|----------|----------|----------|----------|----------|
| 1    | N1       | N2       | N2       | N3       | N1       |
| 2    | N2       | N1       | N3       | N1       | N2       |
| 3    | N3       | N1       | N2       | N2       | N1       |
| 4    | N1       | N2       | N1       | N3       | N2       |
| 5    | N2       | N3       | N2       | N1       | N1       |
| Projeto Final | Arquitetura | Terraform | Lambda | FinOps | Reflexão |
```

> O **rodízio entre níveis** ao longo das aulas é parte da avaliação (Critério 4 — Colaboração nas entregas intermediárias). Concentração de trabalho em 1-2 pessoas penaliza.

---

## Como será avaliado

[Rubrica completa](../rubrica.md). Resumo (50 pts):

| Critério | Peso |
|----------|------|
| A — Arquitetura cloud completa | 15 pts |
| B — IaC funcionando | 10 pts |
| C — Análise FinOps | 10 pts |
| D — Conexão explícita com AI/Agentes | 10 pts |
| E — Documentação e clareza do entregável | 5 pts |
| **Total** | **50 pts** (= 50% da nota da disciplina) |

> O professor aplica a rubrica ao ZIP via Claude Code (prompt automático) + revisão humana. Output é nota + comentários, devolvidos via Portal FIAP.

---

## Cronograma sugerido (1 semana após a Aula 6)

| Dia | Tarefa |
|-----|--------|
| Dia 0 (Aula 6) | Aproveitar 1h40 de trabalho assistido para esclarecer dúvidas; gerar estimativa FinOps; identificar gaps |
| Dia 1 | Consolidar Terraform (mais demorado) |
| Dia 2 | Documentar 5 tools (`tools-spec.md` + docstrings) |
| Dia 3 | Diagrama final + `decisoes-tecnicas.md` |
| Dia 4 | `reflexao-estrategica.md` + lições aprendidas |
| Dia 5 | Polir README + `distribuicao-do-trabalho.md` |
| Dia 6 | Revisão coletiva do grupo |
| Dia 7 | Gerar ZIP + upload no Portal FIAP |

> Aproveite ao máximo a Aula 6 para chegar no Dia 0 com o máximo possível adiantado.

---

## Perguntas frequentes

**Q: O Terraform precisa rodar sem erro?**
A: `terraform plan` precisa rodar sem erro. `terraform apply` não é exigido na correção, mas se rodar, é um plus.

**Q: Se eu não fiz o Online Endpoint da Aula 5 (custou), posso entregar sem?**
A: Sim. Documente no README a decisão de não manter o endpoint custosamente. O Terraform pode ter o recurso comentado ou em variável `enable_endpoint = false`.

**Q: Posso usar repositório público para entregar?**
A: NÃO. A entrega é via ZIP no Portal FIAP. Repos públicos foram desencorajados desde a Aula 1 para evitar cópia entre grupos.

**Q: Posso reutilizar trechos de outras disciplinas do MBA?**
A: Sim, desde que seja claramente atribuído e a entrega tenha conteúdo próprio do grupo.

**Q: Como funciona o critério 4 (Distribuição do Trabalho) no projeto final?**
A: O `distribuicao-do-trabalho.md` mostra o histórico de quem fez o quê nas 6 aulas. Rodízio entre N1/N2/N3 ao longo das aulas é valorizado. Concentração de trabalho em 1-2 pessoas penaliza.

**Q: E se o nosso grupo perdeu um membro no meio da disciplina?**
A: Documente no `distribuicao-do-trabalho.md` com data e razão. O professor avalia com bom senso — o objetivo não é punir grupos com saída de membros.

---

## Lembrete final

A entrega é via **Portal FIAP**, não via GitHub público. **Um único membro do grupo faz o upload** (combine antes para evitar duplicação). Após o upload, o professor corrige usando prompt automático + revisão humana, e devolve nota + feedback no próprio Portal.
