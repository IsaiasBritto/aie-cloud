# Manual 2 — Provisionar por script (az CLI e Bicep)

> O mesmo laboratório do manual anterior, em **três comandos**.
> Use esta trilha depois que a turma já entendeu o que cada recurso é — senão o
> script vira mágica, e mágica não se depura.
>
> Acompanhe com o [diagrama de arquitetura](imagens/02-arquitetura.png) aberto ao lado:
> cada script corresponde a uma seta numerada do desenho (1 · `az acr build`,
> 2 · `az containerapp create/update`).
>
> Tempo estimado: **10 a 15 minutos**.

---

## 0 · Preparar a máquina

```bash
# 1. Instalar a CLI (uma vez por máquina)
#    Windows:  winget install -e --id Microsoft.AzureCLI
#    macOS:    brew install azure-cli
#    Linux:    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

az version
az login                      # abre o navegador
az account show -o table      # confira se a assinatura é a certa

# 2. Se você tem mais de uma assinatura:
az account list -o table
az account set --subscription "Azure for Students"

# 3. Extensão e provedores (uma vez por assinatura)
az extension add --name containerapp --upgrade
az provider register -n Microsoft.App --wait
az provider register -n Microsoft.OperationalInsights --wait
az provider register -n Microsoft.ContainerRegistry --wait
az provider register -n Microsoft.CognitiveServices --wait
```

⚠️ Pular o `az provider register -n Microsoft.App` faz a criação do ambiente de
Container Apps falhar com uma mensagem que **não** diz que foi isso. É o erro nº 1
desta trilha.

---

## 1 · Os três comandos

```bash
git clone <url-do-repositorio> 05-foundry-agents
cd 05-foundry-agents/Lab

export SUFIXO=fiap01          # 4 a 6 caracteres, únicos no mundo
export REGIAO=eastus2
export VERSAO=v1

bash infra/01-criar-recursos.sh     # grupo, storage+blob, visão, ACR, ambiente
bash infra/02-publicar-imagens.sh   # constrói as duas imagens dentro do ACR
bash infra/03-implantar-apps.sh     # cria/atualiza os dois Container Apps
```

Ao final, o terceiro script imprime as duas URLs públicas.

---

## 2 · O que cada script faz, linha por linha

### `infra/00-variaveis.sh`

Não roda sozinho: os outros carregam com `source`. Concentra os nomes num lugar só.

| Variável | Padrão | Observação |
|---|---|---|
| `SUFIXO` | `fiap01` | **o único que você precisa mudar** |
| `REGIAO` | `eastus2` | decide quais serviços existem |
| `GRUPO` | `rg-aula-05` | tudo mora aqui |
| `VERSAO` | `v1` | etiqueta da imagem. **Nunca `latest`** |
| `NIVEL_VISAO` | `F0` | gratuito, 20 chamadas/minuto |

### `infra/01-criar-recursos.sh`

Cria, nesta ordem (que é a ordem da dependência):

1. Registra provedores e a extensão de Container Apps.
2. **Grupo de recursos** `rg-aula-05`, com etiquetas de disciplina/aula/projeto.
3. **Conta de armazenamento** `Standard_LRS`, TLS 1.2 mínimo, **sem acesso público**,
   e o container privado `deteccoes`.
4. **Recurso de visão** `ComputerVision`, nível `F0`, com subdomínio próprio.
5. **Registro de containers** `Basic`, com usuário administrador ligado.
6. **Ambiente de Container Apps** `cae-aula-05`.
7. Grava o arquivo **`.env`** local já preenchido — e o `.env` está no `.gitignore`.

O script **pede confirmação digitada** antes de criar qualquer coisa. Isso é de
propósito: script que cria recurso sem perguntar é como você perde crédito dormindo.

Note esta linha, que evita o erro mais comum do laboratório:

```bash
VISAO_ENDPOINT="${VISAO_ENDPOINT%/}"   # a Azure devolve com barra; a nossa API não aceita
```

### `infra/02-publicar-imagens.sh`

```bash
az acr build --registry $ACR --image deva3-api:$VERSAO --file api/Dockerfile .
az acr build --registry $ACR --image deva3-web:$VERSAO --file web/Dockerfile .
```

`az acr build` envia o contexto e **constrói na nuvem**. O aluno não precisa ter Docker
instalado — é o atalho que salva a aula em laboratório com máquina travada.

Repare no `.` final: o contexto é a **raiz do projeto**, não a pasta `api/`. Sem isso,
o pacote `api` não entra na imagem e o container sobe com `ModuleNotFoundError`.

### `infra/03-implantar-apps.sh`

1. Lê endpoint e chaves dos recursos já criados (não repassa segredo por parâmetro).
2. Cria ou atualiza `ca-deva3-api`:
   - porta `8000`, entrada externa, `0,5 CPU / 1 Gi`
   - `--min-replicas 0` → **escala a zero**: parado, não cobra
   - chave e cadeia de conexão entram como **`--secrets`**, e as variáveis apontam
     para eles com `secretref:` — nunca em texto puro
3. Descobre a URL pública da API e cria/atualiza `ca-deva3-web` já com `API_URL` certa.
4. Chama `GET /saude` para confirmar antes de dizer que terminou.

### `infra/99-remover-tudo.sh`

Lista o que vai ser apagado, **exige que você digite o nome do grupo** e então roda
`az group delete`. É por isso que tudo foi para o mesmo grupo.

---

## 3 · A alternativa declarativa: Bicep

O `infra/principal.bicep` cria a mesma base de forma declarativa:

```bash
az group create -n rg-aula-05 -l eastus2
az deployment group create -g rg-aula-05 \
   --template-file infra/principal.bicep \
   --parameters sufixo=fiap01
```

Os dois Container Apps ficam **fora** do Bicep de propósito: eles dependem de imagens
que só existem depois do `az acr build`. Separar "infraestrutura" de "entrega da
aplicação" é uma decisão de projeto, e vale explicar em aula.

| | Script `.sh` | Bicep |
|---|---|---|
| Curva de aprendizado | baixa | média |
| Rodar duas vezes | pode duplicar efeito | idempotente por natureza |
| Ver o que vai mudar antes | não | `az deployment group what-if` |
| Bom para | aula, protótipo | ambiente que vive |

---

## 4 · Verificar

> 🗺️ Quando algo falhar, localize primeiro **em qual seta** do
> [diagrama de arquitetura](imagens/02-arquitetura.png) o problema está. É mais rápido
> que ler log — e é o que o [manual dos diagramas](00-diagramas.md) treina.

```bash
# O que existe no grupo
az resource list -g rg-aula-05 -o table

# A API está de pé?
URL_API=$(az containerapp show -n ca-deva3-api -g rg-aula-05 \
          --query properties.configuration.ingress.fqdn -o tsv)
curl -s https://$URL_API/saude | jq

# Uma detecção de verdade
curl -s -X POST "https://$URL_API/detectar?modo=pessoas&consentimento=true" \
     -F "imagem=@foto.jpg" | jq '.total_detectado, .deteccoes[0]'

# O que foi gravado no blob
az storage blob list --account-name stdeva3$SUFIXO -c deteccoes \
   --auth-mode login --query "[].name" -o tsv | head

# Log da API
az containerapp logs show -n ca-deva3-api -g rg-aula-05 --tail 50
```

---

## 5 · Atualizar para uma versão nova

```bash
export VERSAO=v2
bash infra/02-publicar-imagens.sh
bash infra/03-implantar-apps.sh     # detecta que os apps existem e faz update
```

O Container Apps cria uma **revisão** nova. Para voltar atrás:

```bash
az containerapp revision list -n ca-deva3-api -g rg-aula-05 -o table
az containerapp revision activate -n ca-deva3-api -g rg-aula-05 --revision <nome>
```

💡 É por isso que a etiqueta nunca é `latest`: com `v1`, `v2`, `v3` você sabe o que
está no ar e consegue voltar. Com `latest`, não.

---

## 6 · Apagar

```bash
bash infra/99-remover-tudo.sh
```

E confira o gasto no dia seguinte. Custo do Azure aparece com atraso — não conclua
"ficou de graça" dez minutos depois do teste.
