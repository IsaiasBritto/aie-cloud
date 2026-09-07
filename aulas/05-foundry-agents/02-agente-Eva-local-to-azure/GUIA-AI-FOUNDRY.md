# Guia — criar e implantar um modelo no Microsoft Foundry

Do zero até a Eva conversando com um modelo hospedado no Azure.

> **Nome:** o serviço se chamava *Azure AI Foundry* e agora aparece como
> **Microsoft Foundry**. Você ainda vai ver as duas grafias na documentação e
> no portal. É o mesmo produto.

---

## 1. Os quatro conceitos que confundem todo mundo

Antes de clicar em qualquer coisa, vale separar quatro palavras que parecem
sinônimos e não são:

| Conceito | O que é | Exemplo |
| --- | --- | --- |
| **Recurso** | O objeto do Azure que você paga e que tem endpoint e chaves | `fiap-foundry` |
| **Projeto** | Um agrupamento dentro do recurso (organização, permissões) | `curso-agentes` |
| **Modelo** | O modelo em si, do catálogo | `gpt-5.4-mini` |
| **Deployment** | Uma **instância** daquele modelo, com nome e cota que **você** define | `eva-aula` |

---

## 2. O que você precisa antes de começar

- Estar com sua assinatura **Azure for Students** ou outra ativa
- Permissão de **Contributor** ou **Owner** na assinatura ou no grupo de recursos
- Uma região com cota disponível para o modelo que você quer

> **Sobre a Azure for Students:** a cota é pequena. Prefira modelos `mini` e um
> TPM baixo (10K já basta para a aula). Se um modelo não aparecer para implantar,
> quase sempre é cota ou região, não permissão.

---

## 3. Criar o recurso e o projeto (portal)

1. Acesse **[ai.azure.com](https://ai.azure.com)** e entre com sua conta Azure.
2. Crie um **projeto** (`+ Create` / `New project`). O portal cria junto o
   **recurso** por trás dele, se você ainda não tiver um.
3. Preencha:
   - **Nome do projeto** — ex.: `curso-agentes`
   - **Assinatura** e **grupo de recursos** — crie um novo, ex.: `rg-fiap-agentes`
   - **Região** — East US 2. Caso não esteja disponível, escolha outra região.
4. Confirme e espere o provisionamento (alguns minutos).

### Preferindo linha de comando (Azure CLI)

```bash
az login

az group create --name rg-fiap-agentes --location eastus2

az cognitiveservices account create \
  --name fiap-foundry \
  --resource-group rg-fiap-agentes \
  --kind AIServices \
  --sku S0 \
  --location eastus2 \
  --custom-domain fiap-foundry \
  --allow-project-management

az cognitiveservices account project create \
  --name fiap-foundry \
  --resource-group rg-fiap-agentes \
  --project-name curso-agentes \
  --location eastus2
```

Dois detalhes que travam quem tenta na mão:

- `--allow-project-management` **não pode ser mudado depois**. Sem ele, o
  recurso não hospeda projetos.
- `--custom-domain` precisa ser **globalmente único** — é ele que vira o
  seu endpoint.

---

## 4. Implantar o modelo (o deployment)

É aqui que "criar um modelo" acontece de fato. Você não treina nada — você
cria uma instância de um modelo do catálogo, com nome e cota próprios.

1. No portal, vá em **Discover → Models** (ou **Model catalog**).
2. Procure o modelo. Para começar, `gpt-5.4-mini`: barato, rápido e **suporta
   tool calling**, que é o que a Eva precisa.
3. Clique em **Deploy**.
4. Configure:

   | Campo | O que colocar | Por quê |
   | --- | --- | --- |
   | **Deployment name** | `eva-aula` (ou o que quiser) | **Anote. É isto que vai no código.** Por padrão vem igual ao nome do modelo — você pode mudar |
   | **Deployment type** | `Global Standard` | Pago por uso, sem reserva de capacidade |
   | **Tokens per minute (TPM)** | 10K é suficiente para a aula | Cota compartilhada da assinatura |
   | **Model version** | a padrão | |

5. Confirme e espere o status ficar **Succeeded**.

> **Escolha do nome do deployment.** Para aprender, usar o mesmo nome do modelo
> (`gpt-5.4-mini`) evita confusão. Para produção, um nome funcional (`eva-prod`)
> é melhor: você troca o modelo por trás sem tocar em `.env` nem em código.
> É indireção — como um CNAME de DNS.

---

## 5. Pegar o endpoint e a chave

1. No portal, **Build → Models** (ou **Deployments**) no menu lateral.
2. Clique no seu deployment.
3. Na página dele estão o **Endpoint** e a **Key**.

Você vai precisar de três valores:

| Valor | Exemplo | Vai para |
| --- | --- | --- |
| Endpoint | `https://fiap-foundry.openai.azure.com` | `AZURE_FOUNDRY_ENDPOINT` |
| Chave | `abc123...` | `AZURE_FOUNDRY_API_KEY` |
| Nome do deployment | `eva-aula` | `AZURE_FOUNDRY_DEPLOYMENT` |

> **Cuidado com o endpoint.** O portal às vezes mostra a URL completa, com
> `/openai/deployments/...` no fim. No `.env` vai **só o host** —
> `https://fiap-foundry.openai.azure.com`. O código acrescenta o resto.
> Endpoint com caminho colado é a causa nº 1 de erro 404 aqui.

Guarde no `.env`:

```env
AZURE_FOUNDRY_ENDPOINT=https://fiap-foundry.openai.azure.com
AZURE_FOUNDRY_DEPLOYMENT=eva-aula
AZURE_FOUNDRY_AUTH=chave
AZURE_FOUNDRY_API_KEY=abc123...
```

E confira antes de rodar a Eva:

```powershell
python verificar.py
```

---

## 6. Sim — você escolhe o modelo pelo código

A resposta curta: **você passa o nome do deployment no parâmetro `model=`**.

```python
resposta = cliente.chat.completions.create(
    model="eva-aula",          # <-- o NOME DO DEPLOYMENT, não "gpt-5.4-mini"
    messages=mensagens,
    tools=FERRAMENTAS,
)
```

Repare que o parâmetro continua se chamando `model` — o SDK é o mesmo da
OpenAI. O que muda é o **significado** do valor: na OpenAI pública é o nome do
modelo; no Azure é o nome do deployment.

### As três formas de trocar de modelo

| Forma | Como | Quando usar |
| --- | --- | --- |
| **No `.env`** | mudar `AZURE_FOUNDRY_DEPLOYMENT` | o padrão do projeto |
| **Na tela** | campo "Deployment" na barra lateral do `app.py` | comparar modelos ao vivo |
| **Por chamada** | `model="outro-deployment"` direto no `create()` | rotear por tarefa |

```python
def escolher_deployment(pergunta: str) -> str:
    """Exemplo de roteamento: barato por padrão, caro só quando precisa."""
    if len(pergunta) > 500 or "analise" in pergunta.lower():
        return "eva-grande"
    return "eva-aula"
```

### O que você NÃO consegue fazer pelo código

Usar um modelo que não tem deployment. Se `gpt-5.4-mini` está no catálogo mas você
não implantou, `model="gpt-5.4-mini"` devolve **404 DeploymentNotFound** — o Azure não
implanta sob demanda. Deployment é um ato administrativo, feito no portal ou
por CLI/IaC, não em tempo de execução.

Esse é o principal contraste com a OpenAI pública, onde qualquer modelo do
catálogo está disponível na hora.

---

## 7. Autenticação: chave ou Entra ID

Este projeto aceita as duas, pela variável `AZURE_FOUNDRY_AUTH`.

### `chave` — para a aula

Simples: a chave está no `.env`, o código manda no header. Funciona em qualquer
máquina, sem `az login`. É o padrão aqui.

O custo: a chave é um segredo de longa duração. Vaza num commit, num print de
tela, num repositório de aluno. Nunca vai para produção.

### `entra` — o caminho de produção

Sem chave nenhuma no `.env`. A autenticação usa sua identidade do Entra ID:

```powershell
pip install azure-identity
az login
```

E no `.env`:

```env
AZURE_FOUNDRY_AUTH=entra
```

### Dar a role ao seu usuário

Você também precisa da role **Cognitive Services OpenAI User** no recurso —
ser Owner da assinatura **não** basta para o plano de dados. São dois planos
diferentes: Owner permite *administrar* o recurso (criar, apagar, ver chaves);
chamar o modelo é outra permissão.

#### Passo 1 — descobrir o Resource ID

O `--scope` do comando não aceita o **nome** do recurso: ele quer o
**Resource ID completo**, aquele caminho que começa com `/subscriptions/`:

```
/subscriptions/<id-da-assinatura>/resourceGroups/<grupo>/providers/Microsoft.CognitiveServices/accounts/<nome-do-recurso>
```

O nome do recurso no fim é o mesmo que aparece no seu endpoint: em
`https://curso-agentes-resource.services.ai.azure.com`, o recurso é
`curso-agentes-resource`.

Em vez de montar isso à mão, peça ao próprio `az` (troque o nome pelo seu):

```powershell
$id = az resource list --name curso-agentes-resource --resource-type "Microsoft.CognitiveServices/accounts" --query "[0].id" -o tsv
echo $id
```

Se voltar vazio, a assinatura ativa não é a do recurso:

```powershell
az account show --query "{assinatura:name, id:id}" -o table
az account set --subscription "<nome-ou-id-da-assinatura-certa>"
```

#### Passo 2 — atribuir a role

```powershell
$objectId = az ad signed-in-user show --query id -o tsv

az role assignment create --role "Cognitive Services OpenAI User" --assignee-object-id $objectId --assignee-principal-type User --scope $id
```

> **Duas armadilhas neste comando.**
>
> A primeira é a **contrabarra de continuação de linha** (`\`), que aparece em
> quase todo exemplo de documentação: ela é do bash. No PowerShell a
> continuação é crase (`` ` ``) — ou escreva tudo em uma linha só, como acima.
>
> A segunda é o `--assignee seu-email@dominio.com`. Funciona em conta pessoal,
> mas falha em tenant institucional, onde o UPN costuma ser diferente do
> e-mail. Por isso usamos `--assignee-object-id`, que é o identificador real e
> não depende de como o seu login está escrito.

#### Passo 3 — conferir

```powershell
az role assignment list --assignee $objectId --scope $id -o table
```

A atribuição **leva alguns minutos para propagar**. Se o app retornar `401`
logo depois de você rodar o comando, espere e tente de novo antes de suspeitar
que errou algo — esse atraso é a causa número um de "fiz tudo certo e não
funcionou".

#### Sobre o escopo — a lição de menor privilégio

O `--scope` decide até onde a permissão vale, e permissão **herda para baixo**:

| Escopo | O que ele libera |
| --- | --- |
| `.../accounts/<recurso>` | só este recurso — **use este** |
| `.../resourceGroups/<grupo>` | todos os recursos do grupo, inclusive os que você criar depois |
| `/subscriptions/<id>` | a assinatura inteira |

Escolher o escopo errado concede acesso a coisas que ainda nem existem. É a
mesma ideia que volta no `Eva-azure`, quando o container recebe exatamente as
três roles de que precisa e nenhuma a mais.

> **Detalhe técnico que vale a aula: qual cliente usar.**
>
> No modo `entra` o código usa o cliente `OpenAI` comum — o **mesmo** do modo
> `chave`, com a **mesma** `base_url`. Só muda a credencial: em vez da chave,
> vai um token do Entra no header `Authorization: Bearer`. A rota
> `/openai/v1/` aceita as duas coisas.
>
> **Não troque para o cliente `AzureOpenAI` aqui.** Ele foi feito para a rota
> clássica (`/openai/deployments/<nome>/...`) e reescreve o caminho da URL,
> inserindo `/deployments/<modelo>/` antes do endpoint. Combinado com a
> `base_url` da v1, o resultado é uma rota híbrida que não existe:
>
> ```
> correto:  .../openai/v1/chat/completions
> quebrado: .../openai/v1/deployments/eva-aula/chat/completions   → 404
> ```
>
> O erro que aparece é `404 - Resource not found`, que engana: parece nome de
> deployment errado ou falta de permissão, e não é nenhum dos dois — a
> requisição nem chega a ser avaliada. Está no SDK, em
> `openai/lib/azure.py`, no `_build_request`.
>
> **A contrapartida:** o token do Entra expira em cerca de uma hora, e o
> cliente `OpenAI` não renova sozinho. Por isso o `eva.py` chama o
> *token provider* antes de cada requisição, dentro do `chamar_modelo()`:
>
> ```python
> if _token_provider is not None:
>     cliente.api_key = _token_provider()
> ```
>
> O provider tem cache — só vai à rede quando falta pouco para expirar. Sem
> essa linha, uma aula de duas horas começa a tomar 401 na segunda metade.
>
> **Cuidado extra:** a documentação da Microsoft mostra um exemplo passando o
> token provider **diretamente** como `api_key=` no cliente `OpenAI`. Testando
> com o SDK `openai` 3.7.0, isso não gera header de autenticação nenhum — a
> chamada sai sem credencial. O `api_key` tem que receber a **string** do
> token (`_token_provider()`), não a função.

---

## 8. Problemas comuns

| Erro | O que costuma ser |
| --- | --- |
| **401 Unauthorized** | Chave errada ou de outro recurso. No modo `entra`: faltou `az login`, falta a role *Cognitive Services OpenAI User*, ou ela ainda está propagando (espere alguns minutos) |
| **401 depois de ~1h funcionando** | Token do Entra expirado. O `chamar_modelo()` renova antes de cada chamada; se você mexeu nessa parte, foi ali |
| **404 DeploymentNotFound** | `AZURE_FOUNDRY_DEPLOYMENT` não bate com o nome no portal, ou o endpoint tem caminho colado |
| **404 Resource not found** (só no modo `entra`) | Cliente errado: `AzureOpenAI` com a `base_url` da v1 insere `/deployments/` na rota. Use o cliente `OpenAI` — ver a seção 7 |
| **CredentialUnavailableError** | `az login` não foi feito, ou está logado em outra conta/tenant |
| **`--scope` vazio ou recurso não encontrado** | A assinatura ativa não é a do recurso. `az account set --subscription ...` |
| **`O token '&&' não é um separador válido`** ou erro com `\` | Copiou comando em bash para o PowerShell. Uma linha por comando; continuação é crase |
| **429 Too Many Requests** | TPM do deployment esgotado. Aumente a cota ou espere |
| **Connection error** | Endpoint com erro de digitação, ou proxy corporativo |
| **O modelo ignora as ferramentas** | O deployment é de um modelo que não suporta tool calling. Use `gpt-5.4-mini` |
| **Modelo não aparece para implantar** | Cota ou região, quase nunca permissão. Tente outra região |

Rode `python verificar.py` — ele testa cada etapa isoladamente e traduz esses
erros.

---

## 9. O que muda no código (e o que não muda)

Comparando com a Eva original:

```diff
- cliente = OpenAI(api_key=chave)
+ cliente = OpenAI(base_url=f"{ENDPOINT}/openai/v1/", api_key=chave)
```

```diff
- model="gpt-5.4-mini"          # nome do modelo
+ model="eva-aula"             # nome do deployment
```

**Só isso.** O loop do agente, as ferramentas, o `agent.md` e o `memory.md` são
idênticos, byte por byte.

E trocar de `chave` para `entra` muda ainda menos — a mesma classe, a mesma
rota, só a credencial:

```diff
- cliente = OpenAI(base_url=f"{ENDPOINT}/openai/v1/", api_key=chave)
+ cliente = OpenAI(base_url=f"{ENDPOINT}/openai/v1/", api_key=token_provider())
```

Essa simetria é de propósito: se mudar a autenticação mudasse também a rota ou
o `api-version`, você nunca saberia qual das três coisas quebrou quando algo
parasse de funcionar. **Um botão, uma variável.**

Vale parar nesse ponto com a turma: a troca de provedor coube em uma função
(`get_cliente()`) porque o projeto já separava núcleo de interface e
configuração de lógica. Num código onde o cliente da OpenAI é instanciado no
meio da regra de negócio, essa mesma migração vira um dia de trabalho.

---

## 10. Próximo passo — subir a aplicação

Hoje o modelo está no Azure e a aplicação na sua máquina. O passo seguinte é
levar a aplicação junto:

1. **Dockerfile** com a aplicação Streamlit
2. **Azure Container Apps** para hospedar
3. **Managed Identity** em vez de chave (o modo `entra`, sem `az login` — a
   identidade é do próprio container)
4. **Key Vault** para o que ainda for segredo
5. **Application Insights** para custo e latência por chamada

O item 3 é a razão de o modo `entra` já estar aqui: em Container Apps você
liga uma Managed Identity, dá a role no recurso do Foundry, e o mesmo código
funciona sem nenhum segredo em lugar nenhum.
