# Rubrica de Avaliação

Esta rubrica é única e se aplica a todas as **5 entregas de grupo** das Aulas 1-5. O **projeto integrado final** (entregue via ZIP até **1 semana após a Aula 6**, **sem apresentação oral**) tem rubrica própria ao final deste documento.

---

## Estrutura geral da nota

| Componente | Peso |
|------------|------|
| Entrega de grupo da Aula 1 | 10% |
| Entrega de grupo da Aula 2 | 10% |
| Entrega de grupo da Aula 3 | 10% |
| Entrega de grupo da Aula 4 | 10% |
| Entrega de grupo da Aula 5 | 10% |
| Projeto integrado final (entrega 1 semana após a Aula 6) | 50% |
| **Total** | **100%** |

---

## Regras das entregas intermediárias (Aulas 1-5)

1. **Uma entrega obrigatória por grupo por aula** — ZIP `entrega-grupo-NN-aulaXX.zip` no Portal FIAP (template em [template-entrega-grupo.md](template-entrega-grupo.md)). NÃO se entrega via fork público — grupos trabalham em repos **privados** próprios e geram o ZIP via `git archive`.
2. **Cobertura obrigatória:** Nível 1 (🟢 básico) + Nível 2 (🟡 intermediário). Nível 3 (🔴 avançado) é **bônus opcional**.
3. **Distribuição de trabalho dentro do grupo:** cabeçalho obrigatório identificando qual membro fez qual nível (única evidência da divisão usada na correção — commits ficam no repo privado do grupo).
4. **Prazo:** até 1 dia antes da próxima aula.
5. **Onde entregar:** upload do ZIP no Portal FIAP, na tarefa correspondente da aula. **Apenas 1 membro do grupo** faz o upload (combinar antes para evitar duplicação).
6. **Correção:** o professor baixa o ZIP do Portal e aplica esta rubrica.

---

## Rubrica de avaliação (10 pontos por entrega)

Cada entrega vale **10 pontos**, que correspondem aos 10% da nota final daquela aula.

### Critério 1 — Completude do Nível 1 (3 pontos)

| Pontos | Descrição |
|--------|-----------|
| 3 | Todas as questões do N1 respondidas com correção e justificativa adequada |
| 2 | Maioria das questões respondidas corretamente; alguma justificativa superficial |
| 1 | Apenas parte das questões respondida ou respostas incorretas/sem justificativa |
| 0 | N1 ausente ou substancialmente incompleto |

### Critério 2 — Completude e qualidade do Nível 2 (3 pontos)

| Pontos | Descrição |
|--------|-----------|
| 3 | Bloco do projeto QC bem implementado, decisões justificadas, conecta com a arquitetura global |
| 2 | Implementação correta mas com lacunas de justificativa ou conexão fraca com QC |
| 1 | Implementação parcial ou desconectada do projeto integrado |
| 0 | N2 ausente |

### Critério 3 — Qualidade técnica do código/IaC entregue (2 pontos)

| Pontos | Descrição |
|--------|-----------|
| 2 | Código limpo, commitado no repo privado, Terraform aplicável, sem segredos hardcoded, com README/comentários onde necessário |
| 1 | Código funcional mas com problemas de organização, secrets vazando, ou sem documentação |
| 0 | Código não commitado, não funcional ou ausente |

### Critério 4 — Distribuição do trabalho e colaboração (1 ponto)

| Pontos | Descrição |
|--------|-----------|
| 1 | Cabeçalho preenchido corretamente; rastreio de quem fez o quê; rodízio de papéis entre aulas |
| 0 | Cabeçalho ausente ou trabalho concentrado em uma pessoa repetidamente |

### Critério 5 — Reflexão coletiva e conexão com AI Engineering (1 ponto)

| Pontos | Descrição |
|--------|-----------|
| 1 | Seção de reflexão final discute o aprendizado coletivo + como aquilo se aplica a uma arquitetura agentic |
| 0 | Reflexão ausente ou genérica |

### Bônus — Nível 3 (até 2 pontos extras)

| Pontos | Descrição |
|--------|-----------|
| +2 | N3 entregue, implementado corretamente, com reflexão aprofundada |
| +1 | N3 tentado com implementação parcial ou correta mas sem reflexão |
| 0 | N3 não tentado |

> **Teto da entrega:** 10 pontos. O bônus do N3 pode compensar perdas em outros critérios, mas o máximo continua 10. Casos excepcionais (N3 muito acima do esperado) podem render menção honrosa no projeto final.

---

## Conteúdo obrigatório do ZIP

Estrutura do `entrega-grupo-NN-aulaXX.zip`:

```
qc-grupo-NN-aulaXX/
├── entrega-grupo-aulaXX.md       # ⭐ documento principal (template anexo)
├── README.md                     # Como rodar o que está dentro do ZIP
├── terraform/                    # main.tf, variables.tf, outputs.tf (quando aplicável)
├── scripts/                      # Python e Bash (quando aplicável)
└── diagramas/                    # PNG/SVG da arquitetura (quando aplicável)
```

**NÃO incluir no ZIP:**

- `terraform.tfstate*` (tem segredos)
- `.env`, `*.pem`, `credentials.json`
- `__pycache__/`, `.venv/`, `node_modules/`
- Imagens binárias gigantes (>5 MB)

Tamanho ideal: < 5 MB. Limite do Portal FIAP: ~20 MB.

> **Gerar o ZIP no CloudShell** (a partir do repo privado do grupo):
>
> ```bash
> cd ~/qc-grupo-NN
> git archive --format=zip --prefix=qc-grupo-NN-aula01/ -o ~/entrega-grupo-NN-aula01.zip HEAD:aula01
> ```

Template obrigatório do `entrega-grupo-aulaXX.md`: ver [template-entrega-grupo.md](template-entrega-grupo.md).

---

## Rubrica do Projeto Integrado Final (50 pontos)

O projeto integrado final consolida tudo o que foi construído ao longo das 6 aulas. **Não há apresentação oral** — o grupo entrega um ZIP via Portal FIAP **1 semana após a Aula 6**.

**Conteúdo obrigatório do ZIP `projeto-integrado-grupo-NN.zip`:**

- `README.md` — visão geral da arquitetura QC, decisões-chave, instruções de execução
- `arquitetura/diagrama-final.png` — diagrama da arquitetura QC com todas as camadas (Aulas 1-5)
- `arquitetura/decisoes-tecnicas.md` — ADRs (mínimo 5 decisões)
- `terraform/` — IaC consolidado que provisiona toda a infra (S3 + RDS/pgvector + DynamoDB + Secrets Manager + Lambda + ECR/ECS + bucket e Registry do SageMaker)
- `function/` — Lambda da QC com as 5 tools (`/produtos`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`, `/recomendar`)
- `tools-spec.md` — spec das 5 tools em JSON Schema para consumo por agentes
- `finops/` — estimativa de custo mensal + propostas de otimização (export do Pricing Calculator + análise)
- `reflexao-estrategica.md` — roadmap de 12 meses + lições aprendidas
- `distribuicao-do-trabalho.md` — quem fez o quê em cada aula e no projeto final

> Detalhes completos do entregável em [projeto-final/INSTRUCOES.md](projeto-final/INSTRUCOES.md).

### Critério A — Arquitetura cloud completa (15 pontos)

| Pontos | Descrição |
|--------|-----------|
| 13-15 | Arquitetura coerente, todas as camadas justificadas, escolhas de serviço bem fundamentadas, conexões claras |
| 9-12 | Arquitetura coerente com algumas lacunas de justificativa |
| 5-8 | Arquitetura incompleta ou com escolhas pouco justificadas |
| 0-4 | Arquitetura superficial ou desconectada do case QC |

### Critério B — IaC funcionando (10 pontos)

| Pontos | Descrição |
|--------|-----------|
| 9-10 | Terraform aplicável (`terraform plan` roda sem erro), infra reproduzível, sem segredos hardcoded |
| 6-8 | `terraform plan` roda com pequenos ajustes; alguma fragilidade |
| 3-5 | TF parcial; `plan` falha sem intervenção do corretor |
| 0-2 | Sem TF ou TF inutilizável |

### Critério C — Análise de custos (FinOps) (10 pontos)

| Pontos | Descrição |
|--------|-----------|
| 9-10 | Estimativa executiva detalhada, comparativos, propostas de otimização concretas |
| 6-8 | Estimativa correta, otimizações superficiais |
| 3-5 | Estimativa parcial ou irrealista |
| 0-2 | Sem análise de custo |

### Critério D — Conexão explícita com AI/Agentes (10 pontos)

| Pontos | Descrição |
|--------|-----------|
| 9-10 | Cada componente da arquitetura é justificado pela necessidade dos agentes (RAG, tools, identidade, governança) |
| 6-8 | Conexão presente mas em alguns pontos genérica |
| 3-5 | Conexão fraca, AI parece adicionada por cima |
| 0-2 | Não há conexão com o contexto agentic |

### Critério E — Documentação e clareza do entregável (5 pontos)

| Pontos | Descrição |
|--------|-----------|
| 5 | README claro, instruções reproduzíveis (`terraform apply` rodaria), diagrama legível, reflexão estratégica bem estruturada, evidência de colaboração entre membros (commits + cabeçalho de distribuição) |
| 3-4 | Documentação presente com lacunas (ex: README sem instruções de execução; diagrama presente mas sem legenda) |
| 1-2 | Documentação fragmentada — leitor externo precisaria de muito esforço para entender o projeto |
| 0 | Sem documentação coerente; ZIP é coleção desorganizada de arquivos |

---

## Observações finais

1. **Atrasos:** entregas após o prazo perdem 1 ponto por dia (até zerar)
2. **Plágio entre grupos:** zera a entrega de todos os grupos envolvidos
3. **Free riders:** se um membro não contribuir em **2 ou mais aulas consecutivas** sem justificativa, perde a participação no projeto e é avaliado individualmente em recuperação
4. **Recuperação:** seguir regulamento da FIAP
5. **Casos excepcionais:** licenças médicas, viagens corporativas etc. — comunicar previamente ao professor
