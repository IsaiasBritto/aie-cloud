# Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents

Repositório de labs, exercícios e código de infraestrutura da disciplina **Cloud & Cognitive Environments**, do MBA **AI Engineering & Multi-Agents** da FIAP.

**Professor:** Isaias Britto

**O crédito de elaboração do material é do Prof. Elton Freitas, sendo esse um Fork do material original - https://github.com/elthonf/aie-cloud/**
---

## Sobre a disciplina

A disciplina forma a base de infraestrutura cloud sobre a qual o restante do MBA constrói soluções de Agentic AI. São **6 aulas de 4 horas**, com forte componente prático — todos os labs rodam **sem instalação local** no [Azure Cloud Shell](https://shell.azure.com).

| # | Tema |
|---|------|
| 1 | [Fundamentos & IaC](aulas/01-fundamentos-iac/) |
| 2 | [Storage & Bancos](aulas/02-storage-bancos/) |
| 3 | [Serverless & Containers](aulas/03-serverless-containers/) |
| 4 | [Serviços Cognitivos](aulas/04-servicos-cognitivos/) |
| 5 | [MLOps](aulas/05-mlops/) |
| 6 | [FinOps & Projeto Final](aulas/06-finops-projeto-final/) |

---

## Antes de começar

Leia o [SETUP.md](SETUP.md) — ele cobre os 3 passos obrigatórios antes da Aula 1:

1. Ativar **Azure for Students** com seu e-mail `@fiap.com.br` (gratuito, $100 de crédito, sem cartão de crédito).
2. Abrir o **Azure Cloud Shell** (`shell.azure.com`) — ambiente pronto com `az`, `terraform`, `bicep`, `python3`, `git`.
3. Clonar este repositório dentro do Cloud Shell.

---

## Estrutura do repositório

```
aulas/                    Material de cada aula (lab, exercícios, IaC)
quantum-commerce/         Case integrador — briefing do projeto avaliativo
entregas/                 Rubrica, template e instruções de cada entrega
recursos/                 Cheatsheets, troubleshooting, glossário
```

---

## Avaliação — entregas em grupo

A disciplina é avaliada por **5 entregas intermediárias em grupo** (Aulas 1-5, 10% cada) + **projeto integrado final** (entrega ZIP **1 semana após a Aula 6**, 50%, **sem apresentação oral**). Cada entrega é um **ZIP no Portal FIAP** gerado a partir do repo PRIVADO do grupo no GitHub — não há fork público.

Veja [entregas/](entregas/) para a rubrica, o template obrigatório e as instruções de cada entrega. O fluxo completo (curso Alura → repo privado → ZIP via `git archive` → upload no Portal) está em [aulas/01-fundamentos-iac/pos-aula-git.md](aulas/01-fundamentos-iac/pos-aula-git.md).

O case integrador é a **Quantum Commerce** — veja [quantum-commerce/](quantum-commerce/) para o briefing.

---

## Licença

Conteúdo licenciado sob [CC BY 4.0](LICENSE). Você pode reutilizar, adaptar e redistribuir desde que dê crédito.
