# Aula 6 — FinOps & Projeto Integrado Final

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Explicar o que é **FinOps** e os três pilares: **Inform, Optimize, Operate**.
- Usar **Tag Editor, Trusted Advisor e Cost Explorer** para identificar desperdícios (no Learner Lab, Cost Explorer e Budgets são demonstração do professor).
- Aplicar técnicas de otimização: Reserved Instances, Savings Plans, Spot, auto scaling, right-sizing, lifecycle policies.
- Aplicar FinOps especificamente a workloads de AI (tokens, embeddings, GPU, modelos idle).
- Estimar o custo mensal (TCO) da arquitetura cloud da QC no **AWS Pricing Calculator**.
- Calcular o **custo por turno** de um agente a partir da telemetria no **CloudWatch Logs Insights**.
- **Consolidar o projeto integrado final** com suporte do professor.

---

## Formato da aula

A Aula 6 tem **2 partes**:

1. **FinOps (~1h50)** — T→L intercalados sobre os 3 pilares, Tag Editor + Trusted Advisor, técnicas de otimização e FinOps aplicado a AI (Lab 3: custo por turno da Eva).
2. **Trabalho assistido em grupo (~1h40)** — tempo guiado para consolidar o **Projeto Integrado Final**, com o professor circulando para tirar dúvidas e atender grupos com pendências.

**Não há apresentação oral.** O projeto integrado final é entregue como ZIP no Portal FIAP **1 semana após esta aula**.

---

## Projeto Integrado Final (50% da nota)

A entrega final consolida tudo o que foi construído nas Aulas 1-5 em **um único ZIP coerente**:

- Arquitetura cloud completa da QC (diagrama + ADRs)
- Terraform consolidado que provisiona TODA a infra
- Lambda com as 5 tools (`/produtos`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`, `/recomendar`)
- Tools-spec em JSON Schema (function calling)
- Análise FinOps (estimativa + propostas de otimização)
- Reflexão estratégica (roadmap 12 meses + lições aprendidas)

**Detalhes completos do entregável + cronograma + perguntas frequentes:** [entregas/projeto-final/INSTRUCOES.md](../../entregas/projeto-final/INSTRUCOES.md).

**Rubrica (50 pts):** [entregas/rubrica.md](../../entregas/rubrica.md) — seção "Rubrica do Projeto Integrado Final".

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — Lab 1 (Tag Editor + Trusted Advisor), Lab 2 (AWS Pricing Calculator), Lab 3 (custo por turno da Eva) + checklist do trabalho em grupo |
| [lab/finops/](lab/finops/) | `carregar-amostra.sh` + `eva-amostra.jsonl` (log da Eva) + `consultas-logs-insights.txt` — Lab 3 |

> **Não há `exercicios.md` separado.** A "entrega" desta aula é o **projeto integrado final** ([entregas/projeto-final/](../../entregas/projeto-final/)), entregue como ZIP **1 semana após a Aula 6**. O lab desta aula alimenta diretamente a seção `finops/` do ZIP final.

---

## Pré-requisitos

- Aulas 1 a 5 concluídas
- Projeto da Quantum Commerce em andamento (5 entregas intermediárias submetidas)
- Cada grupo já tem **arquitetura QC parcialmente definida** das entregas anteriores
- Repositório privado do grupo atualizado com material das Aulas 1-5
