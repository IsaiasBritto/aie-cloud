# Entrega 01 — Aula 1 (Fundamentos & IaC)

**Vale:** 10% da nota final
**Prazo:** até 1 dia antes da Aula 2
**Onde:** upload de UM ZIP no Portal FIAP (combine no grupo quem faz)

---

## O que entregar

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1, 1.2, 1.3, 1.4 respondidos | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — Exercícios 2.1 (com diagrama), 2.2, 2.3 | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — Exercícios 3.1, 3.2, 3.3 (código Terraform/CloudFormation + README) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total** | | **10 pts** |

Conteúdo dos exercícios: [aulas/01-fundamentos-iac/exercicios.md](../../aulas/01-fundamentos-iac/exercicios.md).

---

## Estrutura do ZIP

Nome: `entrega-grupo-NN-aula01.zip` (substitua NN pelo número do grupo).

```
qc-grupo-NN-aula01/
├── entrega-grupo-aula01.md       # ⭐ documento principal (template em ../template-entrega-grupo.md)
├── README.md                     # Como rodar o N3 (se incluído)
├── diagramas/
│   └── arquitetura-qc-aula01.png # Diagrama do Exercício 2.1
└── terraform/                    # Apenas se entregou N3 (Exercício 3.1)
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```

**NÃO incluir:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`.

---

## Como gerar e enviar

1. Use o **template obrigatório** em [../template-entrega-grupo.md](../template-entrega-grupo.md) para o documento principal.
2. Trabalhe no **repo privado do grupo** (configuração em [pos-aula-git.md](../../aulas/01-fundamentos-iac/pos-aula-git.md)).
3. Gere o ZIP no CloudShell:

   ```bash
   cd ~/qc-grupo-NN
   git pull origin main
   git archive --format=zip --prefix=qc-grupo-NN-aula01/ -o ~/entrega-grupo-NN-aula01.zip HEAD:aula01
   unzip -l ~/entrega-grupo-NN-aula01.zip   # conferir
   ```

4. **Um membro** do grupo faz upload do ZIP no **Portal FIAP**, tarefa "Entrega Aula 1".

---

## Critérios de avaliação

Aplica-se a [rubrica única](../rubrica.md) (10 pts: C1 N1 + C2 N2 + C3 qualidade + C4 distribuição + C5 reflexão + bônus N3).

**Foco específico desta entrega:**

- **N1:** dominar IaaS/PaaS/SaaS/FaaS, os 6 Rs, cálculo de SLA, RBAC.
- **N2:** primeiro esboço da arquitetura QC (camadas, provedor, serviços) — base que vai evoluir nas próximas 4 entregas. **Diagrama é parte da entrega.**
- **N3 (bônus):** endurecer o security group via Terraform, traduzir o lab para CloudFormation, ou propor multi-cloud.
- **Reflexão:** conecte o IaC praticado com a necessidade de **reprodutibilidade de agentes** (provisionamento determinístico, segredos versionados, etc.).
