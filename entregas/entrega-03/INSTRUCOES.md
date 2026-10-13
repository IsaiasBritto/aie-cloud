# Entrega 03 — Aula 3 (Serverless & Containers)

**Vale:** 10% da nota final
**Prazo:** até 1 dia antes da Aula 4
**Onde:** upload de UM ZIP no Portal FIAP (combine no grupo quem faz)

---

## O que entregar

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1 (quando usar serverless), 1.2 (IAM Role vs alternativas), 1.3 (cold start), 1.4 (Dockerfile review) | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (segunda tool: cálculo de frete), 2.2 (CloudWatch), 2.3 (Fargate: restart/sizing/segredos) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.1 (spec de tool de agente), 3.2 (benchmark), 3.3 (CI/CD GitHub Actions + OIDC) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total** | | **10 pts** |

Conteúdo dos exercícios: [aulas/03-serverless-containers/exercicios.md](../../aulas/03-serverless-containers/exercicios.md).

---

## Estrutura do ZIP

Nome: `entrega-grupo-NN-aula03.zip`.

```
qc-grupo-NN-aula03/
├── entrega-grupo-aula03.md       # ⭐ documento principal (template em ../template-entrega-grupo.md)
├── README.md                     # Como rodar o que foi entregue
├── terraform/                    # main.tf evoluído (Lambda + Function URL + ECR + ECS Fargate + alarmes se N2.2)
├── function/                     # Código Python da Lambda (incluindo segunda tool se N2.1)
├── docker/                       # Dockerfile + app.py FastAPI (se entregue)
├── .github/workflows/            # Workflow CI/CD (se N3.3)
└── diagramas/
    └── arquitetura-qc-aula03.png # Diagrama da QC com a camada de API/compute
```

**NÃO incluir:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`, `.venv/`, imagens Docker locais.

---

## Como gerar e enviar

```bash
cd ~/qc-grupo-NN
git pull origin main
git archive --format=zip --prefix=qc-grupo-NN-aula03/ -o ~/entrega-grupo-NN-aula03.zip HEAD:aula03
unzip -l ~/entrega-grupo-NN-aula03.zip
```

Upload no Portal FIAP, tarefa "Entrega Aula 3".

---

## Critérios de avaliação

[Rubrica única](../rubrica.md). **Foco específico desta entrega:**

- **N1:** dominar a decisão **Lambda / ECS Fargate / App Runner / EKS** por caso de uso e o conceito de **IAM Role** (execution role, task role) como substituto a credenciais.
- **N2:** a tool de **cálculo de frete** entra como segunda tool consumida pelos agentes na próxima aula. **CloudWatch** (logs, métricas, alarmes) + o endurecimento do **Fargate** (restart, right-sizing/custo, segredos via Secrets Manager, uma tarefa) mostram domínio operacional.
- **N3 (bônus):** o exercício **3.1 (spec de tool)** é o mais valorizado — é o contrato entre o agente e a API que vocês construíram. Bem feito, é peça do projeto integrado final.
- **Reflexão:** discutir como a escolha "Lambda vs Container" muda a forma como o agente consome a tool (cold start, latência, falhas) e o que isso implica para a UX da QC.

---

## Rotação esperada

Quem fez N1 nas Aulas 1-2 deve preferencialmente assumir **N2** ou **N3** aqui (Critério 4 — Distribuição). O cabeçalho `Distribuição do trabalho` é a evidência.
