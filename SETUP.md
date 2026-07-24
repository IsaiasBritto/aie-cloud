# Setup — Antes da Aula 1

Este guia leva ~15 minutos. Você **não precisa instalar nada** no seu computador.

---

## 1. Ativar o Azure for Students

A FIAP é uma instituição parceira da Microsoft, então você tem acesso gratuito a **$100 de crédito Azure por ano**, sem cartão de crédito.

1. Acesse [azure.microsoft.com/free/students](https://azure.microsoft.com/free/students).
2. Clique em **Iniciar gratuitamente** (ou *Start free*).
3. Faça login com seu **e-mail institucional FIAP** (`@fiap.com.br`).
4. Confirme os dados e aceite os termos.
5. Verifique seu e-mail e conclua a ativação.

> **Não consegue ativar?** Anote o erro e traga para a Aula 1. Faremos juntos durante a primeira aula.

---

## 2. Abrir o Azure Cloud Shell

O Cloud Shell é seu **ambiente de trabalho durante toda a disciplina**. Já vem com todas as ferramentas configuradas:

- `az` — Azure CLI
- `terraform` — IaC principal
- `bicep` — IaC nativo Azure (comparativo)
- `python3` — labs de MLOps e cognitivos
- `git` — controle de versão
- `code` — editor estilo VS Code no browser

**Como abrir:**

- Direto: [shell.azure.com](https://shell.azure.com)
- Ou pelo portal Azure (`portal.azure.com`), ícone `>_` no canto superior direito.

Na primeira vez, o Cloud Shell vai pedir para criar uma **storage account** para persistir seus arquivos. Aceite — o custo é desprezível (~$0,01/mês) e cabe no crédito de estudante.

Escolha **Bash** quando perguntado (vamos usar Bash em todos os labs).

---

## 3. Clonar este repositório

Dentro do Cloud Shell, rode:

```bash
git clone https://github.com/isaiasbritto/aie-cloud.git
cd aie-cloud
```

Para abrir um arquivo no editor integrado:

```bash
code aulas/01-fundamentos-iac/README.md
```

---

## Pronto!

Se você conseguiu:

- [x] Ativar o Azure for Students
- [x] Abrir o Cloud Shell
- [x] Clonar este repositório

Você está pronto para a **Aula 1**. Nos vemos lá.

---

## Ambientes complementares (usados em aulas específicas)

- **GitHub Codespaces** — a partir da Aula 3, quando precisarmos de Docker. Conta GitHub tem 60h/mês grátis.
- **Google Colab** — Aula 5 (MLOps), para notebooks de treino.
- **Hugging Face Spaces** — Aulas 5 e 6, para deploy de modelos.

Tudo gratuito e via browser — **nada precisa ser instalado localmente**.
