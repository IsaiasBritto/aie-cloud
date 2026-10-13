# Entregas — Cloud & Cognitive Environments

A disciplina é avaliada por **5 entregas intermediárias em grupo** (Aulas 1-5) + **projeto integrado final** (entrega ZIP **1 semana após a Aula 6**, **sem apresentação oral**).

| Componente | Peso |
|------------|------|
| Entregas das Aulas 1-5 (10% cada) | 50% |
| Projeto integrado final (entrega 1 semana após a Aula 6) | 50% |
| **Total** | **100%** |

---

## Fluxo de cada entrega intermediária

```
┌─────────────────────────────────────────────────────────────┐
│  github.com/IsaiasBritto/aie-cloud   (PÚBLICO — só leitura)      │
│  Material oficial: planos, labs, exercícios                  │
│  → git clone (não fork)                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  Repo PRIVADO do seu grupo (GitHub)  │
        │  4-5 membros como collaborators       │
        │  Aqui vocês trabalham juntos          │
        └──────────────────────────────────────┘
                            │
                            │ git archive (gera ZIP)
                            ▼
        ┌──────────────────────────────────────┐
        │  Portal FIAP                         │
        │  Upload de UM ZIP por entrega        │
        └──────────────────────────────────────┘
```

> **Por que não fazer fork público?** Com ~10 grupos × 2 turmas, fork público permitiria cópia entre grupos. O Portal FIAP isola as entregas.

Como configurar o repo privado, gerar o ZIP e fazer upload está em [aulas/01-fundamentos-iac/pos-aula-git.md](../aulas/01-fundamentos-iac/pos-aula-git.md).

---

## Estrutura desta pasta

| Caminho | Conteúdo |
|---------|----------|
| [rubrica.md](rubrica.md) | Rubrica única aplicada às 5 entregas intermediárias + rubrica do projeto integrado final |
| [template-entrega-grupo.md](template-entrega-grupo.md) | Template obrigatório do documento principal dentro de cada ZIP |
| [entrega-01/](entrega-01/) | Instruções específicas da entrega da Aula 1 |
| [entrega-02/](entrega-02/) | Instruções específicas da entrega da Aula 2 |
| [entrega-03/](entrega-03/) | Instruções específicas da entrega da Aula 3 |
| [entrega-04/](entrega-04/) | Instruções específicas da entrega da Aula 4 |
| [entrega-05/](entrega-05/) | Instruções específicas da entrega da Aula 5 |
| [projeto-final/](projeto-final/) | Instruções do projeto integrado final (50% da nota) — entrega ZIP, sem apresentação oral |

---

## Regras-resumo (detalhes na rubrica)

- **Cobertura obrigatória:** 🟢 Nível 1 + 🟡 Nível 2 dos exercícios da aula. 🔴 Nível 3 é bônus opcional (+2 pts extras).
- **Cabeçalho obrigatório:** seção "Distribuição do trabalho" identificando quem fez qual nível — única evidência da divisão usada na correção.
- **Prazo:** 1 dia antes da próxima aula. Atraso = -1 pt/dia.
- **Apenas 1 membro do grupo faz o upload** no Portal (combine antes para evitar duplicação).
- **Não incluir no ZIP:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`. Tamanho ideal < 5 MB.

---

## Para o aluno individual: como contribuir

1. Conclua o **curso Alura "Git e GitHub: compartilhando e colaborando em projetos"** (gratuito, pré-requisito).
2. Configure-se como collaborator no repo privado do seu grupo (ver [pos-aula-git.md](../aulas/01-fundamentos-iac/pos-aula-git.md)).
3. Em cada aula, pegue um **nível** dos exercícios — combine no grupo e faça **rodízio** entre aulas (vale ponto do Critério 4 da rubrica).
4. Antes do prazo, ajude a montar o `entrega-grupo-aulaXX.md` usando o [template](template-entrega-grupo.md).
