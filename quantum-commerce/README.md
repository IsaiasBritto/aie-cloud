# Projeto Integrado — Case Quantum Commerce

A **Quantum Commerce** é o case integrador da disciplina **Cloud & Cognitive Environments**, parte do MBA AI Engineering & Multi-Agents da FIAP.

A contribuição da disciplina para o case é:

> **Selecionar os principais componentes de cloud da Quantum Commerce, apresentar as camadas e como elas se comunicam para suportar os agentes conversacionais (considerando bases vetoriais e APIs serverless). Gerar estimativa de custo via calculadora de cloud e apresentar em visão executiva.**

O briefing detalhado do case (negócio, personas, requisitos) será disponibilizado pela coordenação no início do módulo.

---

## Como o projeto evolui ao longo da disciplina

Cada aula contribui com um bloco do projeto integrado. Esses blocos são entregues como **ZIPs no Portal FIAP** (uma entrega por grupo por aula). Detalhes da política de entrega, rubrica e template em [entregas/](../entregas/).

| Aula | Contribuição para o projeto |
|------|------------------------------|
| 1 | Definir a arquitetura cloud de alto nível (diagrama) e provisionar a base na AWS (rede padrão, EC2, tags) |
| 2 | Provisionar storage e bancos (catálogo, transações, clientes) |
| 3 | Implantar microserviços/funções do backend (Lambda com Function URL, container no ECS Fargate) |
| 4 | Integrar capacidades cognitivas (busca por imagem, sentimento de reviews, voz) |
| 5 | Construir pipeline de MLOps para o modelo de recomendação |
| 6 | Análise FinOps + trabalho assistido no projeto integrado final (entrega ZIP 1 semana depois, 50% da nota — **sem apresentação oral**) |

---

## Estrutura desta pasta

- `arquitetura/` — Diagrama-alvo da arquitetura cloud (será disponibilizado)

---

## Avaliação

A nota da disciplina vem **inteiramente** deste projeto integrado em grupo, distribuída assim:

| Componente | Peso |
|------------|------|
| 5 entregas intermediárias (Aulas 1-5, 10% cada) | 50% |
| Projeto integrado final (entrega 1 semana após a Aula 6) | 50% |
| **Total** | **100%** |

Não há prova individual. Rubrica completa em [entregas/rubrica.md](../entregas/rubrica.md).

---

## Como o grupo se organiza

- Os grupos são formados **no início da Aula 1**.
- Cada grupo cria **um repositório privado** no GitHub para trabalhar (não fork do `aie-cloud`).
- Cada entrega vira um ZIP gerado via `git archive` desse repo privado.
- Os 3 níveis de exercícios (🟢/🟡/🔴) são **divisão de trabalho** dentro do grupo, com rodízio entre aulas (vale ponto da rubrica).

Tutorial completo em [pos-aula-git.md da Aula 1](../aulas/01-fundamentos-iac/pos-aula-git.md).
