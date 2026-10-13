---
name: provisionar-ambiente-da-aula
description: Provisiona do zero o ambiente do Deva3 na Azure — grupo rg-aula-05, conta de armazenamento com container de blobs, recurso de visão, registro de containers e os dois Container Apps.
---

# Provisionar o ambiente da aula

## Quando usar

Antes da aula, ou quando o ambiente foi apagado e precisa voltar.

⚠️ Esta skill **cria recursos que geram custo**. O `AGENTS.md` §6 proíbe executar
qualquer `az` de criação sem confirmação humana explícita. Peça, espere o "pode ir",
e só então rode.

## Pré-requisitos

- `az login` feito, assinatura correta selecionada.
- Extensão de Container Apps e provedores registrados:
  ```bash
  az extension add --name containerapp --upgrade
  az provider register -n Microsoft.App --wait
  az provider register -n Microsoft.OperationalInsights --wait
  ```
- Um sufixo único de 4 a 6 caracteres, porque nome de Storage e de ACR é global.

## Passos

1. **Confirmar com o professor.** Diga o que será criado, em qual região e a estimativa
   de custo (ACR Basic é o único item com custo fixo relevante).

2. **Rodar os scripts na ordem**, que é a mesma da dependência entre recursos:
   ```bash
   export SUFIXO=fiap01
   bash infra/01-criar-recursos.sh     # grupo, storage+container, visão, ACR, ambiente
   bash infra/02-publicar-imagens.sh   # az acr build das duas imagens
   bash infra/03-implantar-apps.sh     # os dois Container Apps + variáveis
   ```

3. **Guardar as duas URLs** que o script imprime no final. São elas que vão para o slide.

4. **Testar como o aluno vai testar**, de fora:
   ```bash
   curl -s https://$URL_API/saude | jq
   ```

5. **Anotar em `MEMORY.md`** o sufixo usado, a região e a data — a próxima turma vai
   perguntar.

## Verificação antes de dizer que terminou

- [ ] `az resource list -g rg-aula-05 -o table` mostra os cinco recursos esperados
- [ ] `GET /saude` responde `200` com `modos_disponiveis` contendo `pessoas`
- [ ] A interface abre em HTTPS e conversa com a API
- [ ] O container `deteccoes` existe na conta de armazenamento
- [ ] O orçamento com alerta está criado na assinatura

## Saída

Grupo `rg-aula-05` provisionado e duas URLs públicas.

## Armadilhas

- Nome de Storage e de ACR é **global**: sem sufixo único, o script falha com
  "already taken".
- O F0 do Vision é **um por assinatura por região**. Se já existir, o script falha —
  use S1 ou outra região.
- Esquecer `az provider register -n Microsoft.App`: a criação do ambiente de Container
  Apps falha com uma mensagem que não diz isso claramente.
- Terminar a aula sem rodar `infra/99-remover-tudo.sh`. O ACR continua cobrando.
