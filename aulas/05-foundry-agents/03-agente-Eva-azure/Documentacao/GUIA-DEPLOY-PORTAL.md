# Guia — publicar a Eva pelo portal do Azure

O mesmo resultado do guia da CLI, clicando. **Comece por aqui**: clicando você
vê o que cada recurso é e como eles se ligam. Depois a CLI vira automação de
algo que você já entende.

> Os nomes de menu do portal mudam de tempos em tempos. Se um botão não estiver
> exatamente onde este guia diz, procure pelo nome do recurso na barra de busca
> do topo — a estrutura continua a mesma.

---

## Antes de começar

Você já tem, do projeto anterior:

- um recurso do **Microsoft Foundry** com um modelo implantado
- o **nome do deployment** (aquele que vai em `model=`)

E vai criar cinco recursos novos:

| Recurso | Para quê |
| --- | --- |
| Container Registry (ACR) | guardar a imagem da aplicação |
| Log Analytics + Application Insights | telemetria: latência, tokens, custo |
| Key Vault | a chave do Foundry, como fallback |
| Container Apps Environment | a fronteira de rede e logs |
| Container App | a aplicação em si |

---

## Passo 0 — A marcação (tags) que você vai repetir em tudo

Antes de criar o primeiro recurso, decida a marcação. **Todo assistente de
criação do portal tem uma aba `Tags`**, entre a última aba de configuração e o
`Review + create` — e é ela que quase todo mundo pula.

Sem marcação, a pergunta "quanto custou a aula de agentes?" não tem resposta:
o Cost Management mostra seis linhas com nomes crus e você adivinha.

Anote estas sete linhas em algum lugar — você vai colar as mesmas em cada
recurso:

| Name (nome) | Value (valor) | A pergunta que ela responde |
| --- | --- | --- |
| `projeto` | `eva-agente` | a que iniciativa esse gasto pertence? |
| `ambiente` | `aula` | isso é produção ou experimento? |
| `centro-custo` | `fiap-mba-ia` | quem paga? |
| `responsavel` | seu e-mail, minúsculo | a quem eu pergunto antes de apagar? |
| `criado-por` | `portal` | veio de automação ou alguém fez na mão? |
| `criado-em` | a data de hoje, `2026-09-06` | há quanto tempo isso existe? |
| `descartavel` | `sim` | posso apagar sem consultar ninguém? |

As duas últimas raramente aparecem nos exemplos e são as que mais economizam
dinheiro em ambiente de aprendizado: são elas que permitem varrer, no fim do
semestre, o que ficou esquecido ligado.

> **`criado-por=portal` aqui, `criado-por=deploy.ps1` no guia da CLI.** Não é
> capricho: quando você tiver os dois caminhos rodando, essa tag é o que
> responde "isso aqui foi provisionado ou alguém criou na mão?". É a primeira
> métrica de maturidade de qualquer time de plataforma.

**Evite espaço e acento no valor.** O Cost Analysis agrupa por texto exato, e
o CSV exportado fica mais fácil de tratar.

---

## Passo 1 — Grupo de recursos

1. Portal → busque **Resource groups** → **+ Create**
2. Nome: `rg-eva-azure` · Região: `East US`
3. Aba **Tags** → cole as sete linhas do passo 0
4. **Review + create** → **Create**

Tudo vai para dentro dele, e apagar o grupo apaga tudo junto no fim da aula.

---

## Passo 2 — Container Registry

1. Busque **Container registries** → **+ Create**
2. Grupo: `rg-eva-azure` · Nome: `evaacr` + algo único (ex.: suas iniciais e a data)
3. SKU: **Basic**
4. Aba **Tags** → as mesmas sete linhas
5. **Review + create** → **Create**

> O nome precisa ser único no **mundo**, não só na sua conta. `evaacr` sozinho
> já foi usado por alguém.

---

## Passo 3 — Enviar a imagem para o registry

Este é o único passo que **não dá para fazer pelo portal** — o portal não
compila imagem. São dois comandos no PowerShell, e depois você volta para a tela:

```powershell
cd C:\FIAP-Projects\AI\Agentes\Eva-azure
az acr build --registry <nome-do-seu-acr> --image eva:v1 .
```

O build acontece **no Azure**, não na sua máquina — não precisa de Docker
instalado.

Confira no portal: seu ACR → **Repositories** → deve aparecer `eva` com a tag `v1`.

---

## Passo 4 — Application Insights

1. Busque **Application Insights** → **+ Create**
2. Grupo: `rg-eva-azure` · Nome: `eva-appi` · Região: a mesma
3. Em **Log Analytics Workspace**, clique em **Create new** → `eva-logs`
4. Aba **Tags** → as mesmas sete linhas
5. **Review + create** → **Create**

> O workspace criado por dentro do `Create new` **não** passa pela aba Tags —
> ele nasce sem marcação. É exatamente o tipo de recurso que a conferência do
> fim deste guia pega.

Depois de criado, abra o recurso e na tela **Overview** copie a
**Connection String**. Guarde — vai no passo 8.

---

## Passo 5 — Key Vault

1. Busque **Key vaults** → **+ Create**
2. Grupo: `rg-eva-azure` · Nome: `eva-kv` + algo único · Região: a mesma
3. Aba **Access configuration** → marque **Azure role-based access control (RBAC)**
4. Aba **Tags** → as mesmas sete linhas
5. **Review + create** → **Create**

> RBAC em vez das antigas *access policies*: é o modelo atual e é o que permite
> dar permissão para a Managed Identity mais adiante.

### Dar a si mesmo permissão de escrita

Ser Owner da assinatura **não basta** — o plano de dados do Key Vault é separado.

1. No Key Vault → **Access control (IAM)** → **+ Add** → **Add role assignment**
2. Role: **Key Vault Secrets Officer** → **Next**
3. **Members** → **User, group, or service principal** → **+ Select members** →
   escolha você mesmo → **Review + assign**
4. **Espere um ou dois minutos** antes do próximo passo

### Guardar a chave do Foundry

1. Vá ao seu recurso do **Foundry** → **Keys and Endpoint** → copie a **KEY 1**
2. Volte ao Key Vault → **Objects → Secrets** → **+ Generate/Import**
3. Nome: `foundry-api-key` · Value: cole a chave → **Create**
4. Clique no segredo criado, depois na versão, e copie o **Secret Identifier**
   (uma URL `https://.../secrets/foundry-api-key/<versão>`).
   **Apague a parte da versão no fim** — você quer
   `https://<seu-kv>.vault.azure.net/secrets/foundry-api-key`

> **Por que sem a versão:** com versão, o app fica preso àquela versão do
> segredo; se você rotacionar a chave, ele continua lendo a antiga.

---

## Passo 6 — Container App

1. Busque **Container Apps** → **+ Create** → **Container App**
2. Aba **Basics**:
   - Grupo: `rg-eva-azure` · Nome: `eva-app` · Região: a mesma
   - **Container Apps Environment** → **Create new** → nome `eva-env` → **Create**
     (demora alguns minutos)
3. Aba **Container**:
   - **desmarque** "Use quickstart image"
   - Registry: seu ACR · Image: `eva` · Tag: `v1`
   - CPU/memória: `0.5 CPU / 1 Gi` já basta
4. Aba **Ingress**:
   - marque **Enabled**
   - Traffic: **Accepting traffic from anywhere**
   - **Target port: `8501`** ← o Streamlit escuta nessa porta
5. Aba **Tags** → as mesmas sete linhas
6. **Review + create** → **Create**

> O **ambiente** do Container Apps, criado ali pelo `Create new`, também não
> passa pela aba Tags. Mais um para a conferência do fim.
> **O app provavelmente vai falhar ao subir agora.** É esperado: ele ainda não
> tem identidade para puxar a imagem do ACR. Resolvemos no passo 7. Se o portal
> reclamar já na criação, deixe a imagem quickstart e troque depois do passo 7.

---

## Passo 7 — Managed Identity e as três permissões

### Ligar a identidade

1. No Container App → **Settings → Identity**
2. Aba **System assigned** → Status: **On** → **Save**
3. Copie o **Object (principal) ID** que aparece

Pronto: a aplicação agora tem identidade própria no Entra ID.

### Permissão 1 — puxar a imagem (ACR)

1. Vá ao seu **Container Registry** → **Access control (IAM)**
2. **+ Add → Add role assignment** → role **AcrPull** → **Next**
3. **Members** → **Managed identity** → **+ Select members** →
   tipo *Container App* → escolha `eva-app` → **Review + assign**

### Permissão 2 — ler o segredo (Key Vault)

1. No **Key Vault** → **Access control (IAM)** → **+ Add → Add role assignment**
2. Role **Key Vault Secrets User** → mesma seleção por Managed identity

### Permissão 3 — chamar o modelo (Foundry)

1. No recurso do **Foundry** → **Access control (IAM)** → **+ Add → Add role assignment**
2. Role **Cognitive Services OpenAI User** → mesma seleção

> **Esta terceira é a que substitui a API key.** É por causa dela que a
> aplicação vai funcionar sem chave nenhuma.

**Espere de um a dois minutos.** Atribuição de role demora a propagar; seguir
na hora produz um 403 que se resolve sozinho enquanto você investiga.

### Apontar o registry para a identidade

1. Container App → **Settings → Registries** (ou **Container registries**)
2. Adicione seu ACR e escolha autenticação por **Managed Identity → System assigned**
3. Salve

---

## Passo 8 — Segredo e variáveis de ambiente

### O segredo que aponta para o Key Vault

1. Container App → **Settings → Secrets** → **+ Add**
2. Key: `foundry-key`
3. Tipo: **Key Vault reference** (ou "Reference from Key Vault")
4. Cole o **Secret Identifier sem a versão** (passo 5)
5. Identidade: **System assigned**
6. **Add**

O valor não fica guardado no Container App — ele é buscado no Key Vault, com a
identidade da aplicação, na hora de usar.

### As variáveis

1. Container App → **Application → Containers** → **Edit and deploy**
2. Selecione o container → **Environment variables** → adicione:

| Nome | Origem | Valor |
| --- | --- | --- |
| `AZURE_FOUNDRY_ENDPOINT` | Manual entry | `https://seu-recurso.services.ai.azure.com` |
| `AZURE_FOUNDRY_DEPLOYMENT` | Manual entry | o nome do seu deployment |
| `AZURE_FOUNDRY_AUTH` | Manual entry | `entra` |
| `AZURE_FOUNDRY_API_KEY` | **Reference a secret** | `foundry-key` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Manual entry | a connection string do passo 4 |

1. Confirme que a imagem é a sua (`<seu-acr>.azurecr.io/eva:v1`)
2. **Save** → **Create** (cria uma nova revisão)

---

## Passo 9 — Abrir e conferir

1. Container App → **Overview** → clique na **Application Url**
2. A Eva deve abrir no navegador

Na barra lateral, confira:

- **🔐 identidade (Managed Identity / az login)** → está tudo certo
- **🔑 chave (FALLBACK — a identidade falhou)** → a permissão 3 do passo 7 não
  está valendo. Espere mais um pouco, ou confira a role no Foundry.
- **📊 telemetria ligada** → o Application Insights está recebendo

Converse com a Eva e pergunte *"que dia é hoje?"* — ela vai chamar a ferramenta,
e a chamada vai virar telemetria.

---

## Passo 10 — Ver a telemetria

Application Insights → **Monitoring → Logs**:

```kusto
dependencies
| where name == "eva.chamada_modelo"
| summarize p50=percentile(duration,50), p95=percentile(duration,95), n=count()
    by tostring(customDimensions["eva.deployment"])
```

```kusto
customMetrics
| where name in ("eva.tokens", "eva.custo.estimado")
| summarize total=sum(value) by name
```

Leva alguns minutos para os primeiros dados aparecerem.

> O custo sai zerado até você preencher as variáveis `EVA_PRECO_ENTRADA_POR_1M`
> e `EVA_PRECO_SAIDA_POR_1M` com os preços do seu modelo.

Logs da aplicação: Container App → **Monitoring → Log stream**.

---

## Passo 11 — Publicar uma alteração

```powershell
az acr build --registry <seu-acr> --image eva:v2 .
```

Depois, no portal: Container App → **Containers** → **Edit and deploy** →
troque a tag para `v2` → **Save**.

> Use tag nova a cada versão. Com `:latest`, o Container Apps pode não perceber
> que a imagem mudou.

---

## Conferir a marcação — e o custo

### Por que conferir, se você marcou tudo

Porque duas coisas escapam, sempre:

**Tag não é herdada.** Marcar o grupo de recursos **não** marca o que está
dentro dele. É contraintuitivo, e é a causa número um de cobertura furada.
(Existe uma Azure Policy chamada *Inherit a tag from the resource group* que
força isso — bom tema para quem quiser ir além.)

**O Azure cria recursos que você não pediu.** O workspace do Log Analytics e o
ambiente do Container Apps nasceram por dentro de outro assistente, sem passar
pela aba Tags. Eles aparecem na fatura e não na sua lista mental.

### Marcar o que ficou de fora, em lote

1. Portal → **Resource groups** → `rg-eva-azure`
2. Na lista de recursos, marque a caixa do cabeçalho para **selecionar todos**
3. Botão **Assign tags** (no topo)
4. Cole as sete linhas → **Save**

Isso **acrescenta** as tags sem apagar as que já existiam.

### Conferir a cobertura

Ainda na lista de recursos do grupo, use **Manage view → Edit columns** e
acrescente a coluna **Tags**. Um olhar responde se sobrou alguém sem dono.

Pela CLI é uma linha só, e vale mostrar porque é o tipo de coisa que ninguém
faz clicando:

```powershell
az resource list -g rg-eva-azure --query "[?tags.projeto==null].name" -o tsv
```

**Recurso sem tag é custo sem dono** — e custo sem dono ninguém corta.

### Ver o custo por marcação

Portal → **Cost Management + Billing** → **Cost analysis** →
**Group by** → **Tag** → `projeto`.

Filtre por `centro-custo` para separar o que é da turma do que é seu.

> **A marcação só vale a partir do momento em que existe.** O custo já gerado
> antes não é reclassificado retroativamente. É por isso que a aba Tags se
> preenche na criação, e não "depois, quando der" — e é o argumento que faz a
> turma levar isso a sério.

---

## Apagar tudo

Portal → **Resource groups** → `rg-eva-azure` → **Delete resource group**.

O recurso do Foundry está em outro grupo e não é afetado.

---

## Problemas comuns

| Sintoma | Onde olhar |
| --- | --- |
| App não inicia, erro de imagem | Passo 7: role AcrPull e registry por Managed Identity |
| Barra lateral mostra **FALLBACK** | Passo 7, permissão 3 (*Cognitive Services OpenAI User*) |
| Página não abre / erro 502 | Ingress: target port precisa ser **8501** |
| `Unable to get secret` | Role *Key Vault Secrets User*, e o vault tem que estar em RBAC |
| Não consigo criar o segredo no Key Vault | Falta *Key Vault Secrets Officer* para você mesmo |
| Nome do ACR/Key Vault recusado | Precisa ser único no mundo inteiro |
| Primeira resposta muito lenta | Cold start (escala a zero). Suba o mínimo de réplicas para 1 |
| Custo não separa por projeto no Cost analysis | Faltou a aba Tags em algum recurso. Use **Assign tags** em lote no grupo |
| O grupo está marcado mas os recursos não | Tag não é herdada — cada recurso precisa da sua |
| Marquei agora e o custo antigo não mudou | Marcação não é retroativa: vale a partir de quando existe |

---

## Depois: o mesmo pela CLI

Quando este roteiro fizer sentido, faça o [GUIA-DEPLOY-CLI.md](GUIA-DEPLOY-CLI.md).
São os mesmos recursos em ~20 comandos — e aí fica claro por que ninguém
provisiona produção clicando: não é reproduzível, não entra em Git e não roda
num pipeline.
