# Pasta `agente/` — os artefatos do agente Deva3

Esta pasta reúne o que pertence ao **agente**, não à aplicação.

```
agente/
├── LEIA-ME.md            este arquivo
└── skills/               procedimentos salvos, um por pasta
    ├── provisionar-ambiente-da-aula/SKILL.md
    ├── publicar-nova-versao/SKILL.md
    └── diagnosticar-erro-de-deteccao/SKILL.md
```

## Por que `AGENTS.md` e `MEMORY.md` ficam na raiz, e não aqui

Por **convenção**. Os harnesses (Claude Code, Codex, Cursor, e o campo *Instruções* do
Microsoft Foundry) procuram o `AGENTS.md` na **raiz** do repositório. Movê-lo para cá
faria o agente abrir o projeto sem manual — e sem a regra que manda ler a memória.

Então o arranjo é este:

| Arquivo | Onde fica | Por quê |
|---|---|---|
| `AGENTS.md` | **raiz** | é onde o harness procura |
| `MEMORY.md` | **raiz** | é o que o `AGENTS.md` §0 manda ler primeiro |
| `SKILL.md` | `agente/skills/<nome>/` | uma pasta por procedimento, como manda a spec |

## Como o agente usa cada um

1. **`AGENTS.md`** — lido automaticamente ao abrir o repositório. Diz quem o agente é,
   o que nunca faz sem confirmação, e manda ler a memória antes de qualquer ação.
2. **`MEMORY.md`** — lido no início de toda sessão. Traz o que já foi decidido e as
   armadilhas que já custaram tempo.
3. **`agente/skills/*/SKILL.md`** — carregados sob demanda. O agente lê apenas `name` e
   `description` de todas as skills e abre o corpo só da que for usar.

## A anatomia de uma skill

```markdown
---
name: publicar-nova-versao
description: Publica uma nova versão do Deva3 construindo as imagens no ACR e
             atualizando os dois Container Apps do grupo rg-aula-05.
---

## Quando usar        ← o gatilho
## Pré-requisitos     ← o que precisa existir antes
## Passos             ← numerados, imperativos
## Verificação        ← checklist que o próprio agente roda
## Armadilhas         ← tirado de erro real
```

Regras do frontmatter: `name` em minúsculas, números e hífen, até 64 caracteres, sem
aspas; `description` até 1.024 caracteres, sem aspas.

**A `description` é o campo mais importante do arquivo.** É por ela que o agente decide
se aquela skill é a certa para a tarefa. Descrição vaga = skill que nunca roda.

Fórmula: **verbo + objeto + contexto + o que devolve**.
