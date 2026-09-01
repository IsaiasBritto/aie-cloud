# Substituição da seção "Antes de tudo" — `docs/02-manual-script.md`

Troque a seção atual por tudo o que vem abaixo da linha.

---

## Antes de tudo

> **Em qual shell você está?** Este manual assume **bash** — Git Bash, WSL, macOS
> ou o Azure Cloud Shell. Se você está no PowerShell, o `\` de continuação de linha
> e o `$(date ...)` não existem lá: ou abra o Git Bash, ou use o Cloud Shell.
> É um minuto de decisão que economiza vinte de depuração.

### 0 · Clonar o repositório

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/05-foundry-agents/Lab2
```

`git clone` só aceita a URL do **repositório**. A URL que aparece na barra do navegador
(`.../tree/main/aulas/...`) é caminho de navegação do site, e o git responde
`repository not found`.

A pasta do laboratório é `Lab2`. O nome `deva-continuo` que aparece na árvore do
README é o nome do projeto, não o da pasta.

### 1 · Entrar e escolher a assinatura

```bash
az login
az account show --query "{assinatura:name, id:id}" -o table
az account set --subscription "<sua assinatura>"
```

Confira que a assinatura listada é a que você quer gastar. Quem tem mais de uma
descobre isso tarde.

### 2 · O orçamento — que não é opcional num módulo em que o agente acorda sozinho

```bash
bash infra/00-orcamento.sh
```

Cria um orçamento de **US$ 10 por mês, válido por 3 meses**, com alertas em 50%, 80%
e 100% enviados para o e-mail da sua própria conta do `az login`. Não cria nenhum
recurso que gere custo, e pode ser rodado de novo à vontade: é um `PUT`, sobrescreve
em vez de duplicar.

Para mudar o teto, o prazo ou o destinatário:

```bash
VALOR=25 MESES=6 EMAIL=voce@exemplo.com bash infra/00-orcamento.sh
```

**Se o script falhar**, não insista no terminal. Crie pelo portal — leva um minuto:
*Gerenciamento de Custos → Orçamentos → Adicionar*, valor US$ 10, redefinição mensal,
alertas em 50%, 80% e 100%. O que não pode é seguir para o Módulo 1 sem orçamento.

> **Por que um script, e não `az consumption budget create`?**
> O grupo de comandos `consumption` está em preview, e o corpo que a CLI monta hoje
> está fora de sincronia com o serviço: devolve
> `(400) Invalid budget configuration, please use filter interface with
> 2019-05-01-preview version`, sem que haja nada de errado com os seus parâmetros.
> É bug conhecido e aberto ([azure-cli#29950](https://github.com/Azure/azure-cli/issues/29950)).
> O script conversa direto com a API de budgets, na versão `2024-08-01`.
>
> Isso é conteúdo de aula, não rodapé: **preview quer dizer bom para aprender,
> arriscado para prometer em contrato** — e vale para o comando de CLI tanto quanto
> para a Memória e as Skills do Foundry.

### 3 · Conferir antes de seguir

O próprio script já mostra a confirmação no fim. Para checar de novo depois:

```bash
SUB=$(az account show --query id -o tsv)
az rest --method get \
  --url "https://management.azure.com/subscriptions/$SUB/providers/Microsoft.Consumption/budgets/orc-aula-05-continuo?api-version=2024-08-01" \
  --query "properties.{valor:amount, grao:timeGrain, inicio:timePeriod.startDate, fim:timePeriod.endDate}" \
  -o table
```

E lembre do que o orçamento é e do que ele não é: **ele avisa, não freia.** O Azure não
tem limite rígido de gasto. O freio que interrompe de verdade é a **cota** — tokens por
minuto por implantação. O orçamento serve para alguém descobrir no segundo dia, e não
na fatura.

---

## O que mais mudou

- **Passo 0 é novo.** O manual começava depois do clone, e quem chegava por link do
  GitHub tentava `git clone` na URL de navegação.
- **`date -d` é GNU.** O `00-orcamento.sh` detecta e usa `date -v` no macOS.
- **O e-mail do alerta sai do `az login`**, então o mesmo comando serve para a turma
  inteira sem edição — cada aluno recebe o próprio aviso.
