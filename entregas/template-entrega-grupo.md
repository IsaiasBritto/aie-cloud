# Template obrigatório — `entrega-grupo-aulaXX.md`

Use **exatamente este template** dentro do ZIP de cada entrega (substitua os placeholders entre `<>`).

> Copie o bloco abaixo para um novo arquivo `entrega-grupo-aulaXX.md` no repo privado do seu grupo.

---

```markdown
# Entrega Aula <XX> — Grupo <NN>

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** <código da sua turma>
**Data de entrega:** <DD/MM/AAAA>

## Grupo

| # | Nome completo | GitHub | E-mail FIAP |
|---|---------------|--------|-------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

## Distribuição do trabalho

| Membro | Nível assumido | Item específico |
|--------|----------------|-----------------|
| Nome 1 | 🟢 N1 | Exercícios 1.1, 1.2, 1.3 |
| Nome 2 | 🟡 N2 | Exercício 2.1 — Arquitetura QC |
| Nome 3 | 🟡 N2 | Exercício 2.2 — Comparativo |
| Nome 4 | 🔴 N3 (bônus) | Exercício 3.1 — IaC avançado |
| Nome 5 | 🟢 N1 (apoio) | Revisão das respostas N1 |

> Regra: cada membro deve ter pelo menos uma contribuição. O **rodízio entre aulas** (quem fez N1 antes faz N2 depois) é incentivado e vale o ponto do Critério 4 (ver [rubrica.md](rubrica.md)).

---

## 🟢 Nível 1 — Respostas

(Respostas dos exercícios do N1 aqui)

---

## 🟡 Nível 2 — Respostas + Implementação

(Respostas + diagramas + código quando aplicável)

---

## 🔴 Nível 3 — Bônus (se aplicável)

(Respostas + scripts/links)

---

## Reflexão coletiva

3-5 parágrafos respondendo:

1. O que o grupo aprendeu de mais importante nesta aula?
2. Como isso se conecta com a arquitetura cloud de uma plataforma agentic?
3. Que decisão arquitetural vocês fariam diferente se começassem o projeto QC hoje?

---

## Artefatos do ZIP

- Diagrama: `diagramas/arquitetura-qc-aulaXX.png`
- Código IaC: `terraform/`
- Scripts: `scripts/`
- Endpoint ativo (se houver): URL pública sem credenciais — apenas para demonstração durante a janela de correção
```

---

## Lembretes ao gerar o ZIP

- Nome do ZIP: `entrega-grupo-NN-aulaXX.zip` (substitua NN e XX)
- Estrutura interna: pasta única `qc-grupo-NN-aulaXX/` no topo
- Tamanho ideal: < 5 MB
- **NÃO incluir:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`, `.venv/`

Comando recomendado no CloudShell:

```bash
cd ~/qc-grupo-NN
git pull origin main
git archive --format=zip --prefix=qc-grupo-NN-aulaXX/ -o ~/entrega-grupo-NN-aulaXX.zip HEAD:aulaXX
unzip -l ~/entrega-grupo-NN-aulaXX.zip   # conferir o que entrou
```

Upload do ZIP no Portal FIAP (apenas 1 membro do grupo faz).
