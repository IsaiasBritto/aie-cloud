# Entrega 04 — Aula 4 (Serviços Cognitivos & APIs)

**Vale:** 10% da nota final
**Prazo:** até 1 dia antes da Aula 5
**Onde:** upload de UM ZIP no Portal FIAP (combine no grupo quem faz)

---

## O que entregar

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1 (pronto/custom/LLM), 1.2 (custo mensal), 1.3 (segurança MI vs API key), 1.4 (Vision capabilities) | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (pipeline robusto: summary + PII + opinion mining), 2.2 (casos de Speech na QC), 2.3 (Vision pronto vs Custom Vision) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.1 (embeddings reais no pgvector), 3.2 (Rekognition Custom Labels), 3.3 (sumarização com LLM no Bedrock) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total** | | **10 pts** |

Conteúdo dos exercícios: [aulas/04-servicos-cognitivos/exercicios.md](../../aulas/04-servicos-cognitivos/exercicios.md).

---

## Estrutura do ZIP

Nome: `entrega-grupo-NN-aula04.zip`.

```
qc-grupo-NN-aula04/
├── entrega-grupo-aula04.md       # ⭐ documento principal (template em ../template-entrega-grupo.md)
├── README.md                     # Como rodar o pipeline (deploy + curl de cada rota)
├── terraform/                    # main.tf evoluído (Lambda + S3 + Secrets Manager + Mongo, e o que o N3 exigir)
├── function/                     # function_app.py (Lambda + Powertools) com rotas adicionais (sumarização se N2.1/N3.3)
├── scripts/                      # Python: re-indexação com embeddings (se N3.1)
└── diagramas/
    └── arquitetura-qc-aula04.png # QC atualizada com a camada cognitiva (Speech/Language/Vision)
```

Anexar também no `entrega-grupo-aula04.md`:

- 3 exemplos de reviews processadas com schema completo (se N2.1 entregue)
- JSON de saída de uma análise de imagem (Vision)
- Print do dashboard do Custom Vision se N3.2

**NÃO incluir:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`, áudio/imagem binários (>5 MB), chaves de API.

---

## Como gerar e enviar

```bash
cd ~/qc-grupo-NN
git pull origin main
git archive --format=zip --prefix=qc-grupo-NN-aula04/ -o ~/entrega-grupo-NN-aula04.zip HEAD:aula04
unzip -l ~/entrega-grupo-NN-aula04.zip
```

Upload no Portal FIAP, tarefa "Entrega Aula 4".

---

## Critérios de avaliação

[Rubrica única](../rubrica.md). **Foco específico desta entrega:**

- **N1:** dominar a tríade **pronta/custom/LLM** e explicar como a Lambda autentica nos serviços de IA **pela role** (execution role), sem chave no código.
- **N2:** o **pipeline robusto de reviews** (com PII redaction + summarization + opinion mining) é o que torna o sentimento útil para o agente da QC tomar decisões reais. **Vision pronto vs Custom** é decisão de produto a ser justificada.
- **N3 (bônus):** o **3.1 (embeddings reais)** é o **fechamento do RAG** começado na Aula 2 — gera vetores reais e re-indexa a tabela `produtos_vetor` do pgvector (Aula 2). É a base do agente conversacional da QC. **Muito valorizado.**
- **Reflexão:** discutir como a **chain pronta + custom + LLM** muda a arquitetura ao longo do ciclo de vida do produto (MVP → escala) e o impacto de custo.

---

## Rotação esperada

Quem fez N1 nas Aulas 1-3 deve preferencialmente assumir **N2** ou **N3** aqui (Critério 4 — Distribuição). O cabeçalho `Distribuição do trabalho` é a evidência.
