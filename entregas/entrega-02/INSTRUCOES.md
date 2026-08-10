# Entrega 02 — Aula 2 (Storage & Bancos de Dados)

**Vale:** 10% da nota final
**Prazo:** até 1 dia antes da Aula 3
**Onde:** upload de UM ZIP no Portal FIAP (combine no grupo quem faz)

---

## O que entregar

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1, 1.2, 1.3, 1.4 (storage, tiers, relacional vs NoSQL, RBAC do Key Vault) | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — Exercícios 2.1 (matriz de dados QC + diagrama), 2.2 (plano de migração), 2.3 (particionamento Cosmos) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — Exercícios 3.1 (vector search verdadeira) |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total** | | **10 pts** |

Conteúdo dos exercícios: [aulas/02-storage-bancos/exercicios.md](../../aulas/02-storage-bancos/exercicios.md).

---

## Estrutura do ZIP

Nome: `entrega-grupo-NN-aula02.zip`.

```
qc-grupo-NN-aula02/
├── entrega-grupo-aula02.md       # ⭐ documento principal (template em ../template-entrega-grupo.md)
├── README.md                     # Como rodar o que foi entregue
├── diagramas/
│   └── arquitetura-qc-aula02.png # Diagrama da camada de dados QC (do Ex 2.1)
├── terraform/                    # main.tf evoluído + storage/sql/keyvault/cosmos/search (se N2 ou N3)
└── scripts/                      # Python: vector search se N3
```

**NÃO incluir:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`.

---

## Como gerar e enviar

Mesmo fluxo da entrega 01:

```bash
cd ~/qc-grupo-NN
git pull origin main
git archive --format=zip --prefix=qc-grupo-NN-aula02/ -o ~/entrega-grupo-NN-aula02.zip HEAD:aula02
unzip -l ~/entrega-grupo-NN-aula02.zip
```

Upload no Portal FIAP, tarefa "Entrega Aula 2".

---

## Critérios de avaliação

[Rubrica única](../rubrica.md). **Foco específico desta entrega:**

- **N1:** justificar a escolha entre Object/File/Block e entre relacional/NoSQL/vector com base no caso de uso. RBAC do Key Vault no nível de menor privilégio.
- **N2:** a **matriz de decisão de dados** da QC (9 domínios) com serviço + SKU + justificativa, e o **diagrama atualizado** incluindo a camada de dados. Esta é a peça central do projeto integrado nesta aula.
- **N3 (bônus):** o exercício de **vector search verdadeira** (com embeddings) é o mais valorizado — é base do RAG dos agentes.
- **Reflexão:** discutir por que segregar segredos no Key Vault muda o modelo de segurança em uma plataforma agentic.

---

## Rotação esperada

Quem fez N1 na entrega 01 deve preferencialmente assumir **N2** ou **N3** aqui (Critério 4 — Distribuição). O cabeçalho `Distribuição do trabalho` é a evidência.
