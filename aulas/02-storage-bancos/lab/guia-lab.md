# Guia de Laboratório — Aula 2

**Tema:** Storage & Bancos de Dados na Nuvem
**Plataforma:** Microsoft Azure (Azure for Students)
**Ambiente:** **Azure Cloud Shell** — tudo no browser, sem instalar nada localmente

---

## Visão geral do lab

Este lab é intercalado com a teoria. Cada atividade corresponde a um momento do cronograma.

```
Preparação — detectar regiões, registry e terraform apply         ~15 min
Atividade 1 — Storage Account + upload de CSV ao Blob              ~15 min  (L₁)
Atividade 2 — Azure SQL + Key Vault + Python (T_PRODUTOS)          ~30 min  (L₂)
Atividade 3 — Cosmos DB / MongoDB + Azure AI Search                ~55 min  (L₃)
Wrap-up     — terraform destroy + verificação custo zero           ~10 min
```

> **Regra de ouro:** sempre encerrar com `terraform destroy`. Custo zero ao final.

### Por que `terraform apply` de uma vez só, antes das atividades?

A camada de dados completa da QC é uma **declaração única** — provisionar tudo de uma vez (~8 min) reflete como IaC funciona na vida real e libera o lab para focar em **explorar cada peça** via Python. Enquanto o Terraform roda, você lê os arquivos `.tf` para entender o que está sendo construído.

---

## Pré-requisitos

- ✅ Aula 1 concluída (Cloud Shell funcional, Terraform rodando, conta Azure ativa)
- ✅ Repositório `aie-cloud` clonado no Cloud Shell (`git clone https://github.com/elthonf/aie-cloud.git`)
- ✅ Esboço da arquitetura QC do grupo commitado no fork

Se não fez algum desses passos, ver [pre-aula da Aula 1](../../01-fundamentos-iac/pre-aula.md) e [pos-aula-git](../../01-fundamentos-iac/pos-aula-git.md).

---

## Preparação (15 min — antes do L₁)

### Passo 0 — Detecte as regiões válidas para a SUA assinatura

Contas Azure for Students têm uma policy que limita onde você pode criar
recursos — e **a lista muda de assinatura para assinatura**. Pior: estar na
lista de permitidas não garante que o serviço provisiona ali, porque cota de
SKU free varia ao longo do dia.

O script sonda cada serviço criando e apagando um recurso de teste, e escreve
o `terraform.tfvars` com o que realmente funcionou:

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
bash detectar-regioes.sh
```

Leva cerca de 3 minutos. No final, confira o resultado:

```bash
grep "^location" terraform.tfvars
```

> **Por que isso vem primeiro:** sem esse passo, o `apply` roda por dois minutos
> e falha com `RequestDisallowedByAzure`. Três erros diferentes podem aparecer,
> e a ação muda para cada um:
>
> | Código | Mensagem | Significa | Ação |
> |---|---|---|---|
> | 403 | `RequestDisallowedByAzure` | região fora da policy | trocar de região |
> | 403 | `ProvisioningDisabled` | serviço bloqueado nessa região | trocar de região |
> | 400 | `InsufficientResourcesAvailable` | região ok, sem cota agora | trocar de região ou tentar mais tarde |

---

### Passo 1 — Clone e atualize o repositório

```bash
cd ~
git clone https://github.com/isaiasbritto/aie-cloud.git 2>/dev/null || (cd ~/aie-cloud && git pull origin main)

cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
ls
```

Leia rapidamente cada `.tf` (5 min) — entenda o que será provisionado.

---

### Passo 2 — Instale as dependências Python

O `~/.local` do Cloud Shell é apagado quando a sessão encerra, então isso
precisa ser refeito a cada aula:

```bash
pip install --user -r ../scripts/requirements.txt

python3 -c "import pyodbc; print(pyodbc.drivers())"
```

Precisa listar `ODBC Driver 18 for SQL Server`. O `ERROR` sobre
`ansible-core requires packaging` que o pip mostra é ruído da imagem do Cloud
Shell — pode ignorar.

---

### Passo 3 — Crie o registry das imagens do MongoDB

Este script cria um Azure Container Registry **na sua própria assinatura** e
importa as imagens do MongoDB para lá:

```bash
bash setup-registry-aluno.sh
source ~/.qc-registry.env

echo "registry=[$TF_VAR_registry_server]"
```

A última linha precisa mostrar um endereço terminado em `.azurecr.io`.

> **Por que este passo existe:** o Azure Container Instances puxa a imagem do
> Docker Hub usando IPs de saída compartilhados da região, e o Docker Hub limita
> pulls anônimos a 100 por 6 horas **por IP**. Com a turma rodando junto, esse
> limite estoura e o `apply` falha com `409 RegistryErrorResponse`. Com um
> registry próprio, o pull sai do backbone da Azure e o problema desaparece.
>
> O script é **idempotente**: o nome do registry vem do ID da sua assinatura,
> então rodar de novo reaproveita o que já existe.

---

### Passo 4 — Defina a senha do SQL

```bash
export TF_VAR_sql_admin_password="$(openssl rand -base64 24)"
echo "Senha gerada (anote): $TF_VAR_sql_admin_password"
```

**Anote o valor.** Se a sessão cair, você precisa exportar exatamente a mesma
senha — caso contrário o Terraform troca a senha do servidor no meio do lab e a
connection string do Key Vault fica inconsistente.

> **Por que `TF_VAR_` e não `-var=`:** o Terraform lê variáveis com esse prefixo
> automaticamente, então nenhum comando seguinte precisa repetir a senha. Menos
> digitação e menos chance de aplicar com valor diferente do anterior.

Confirme que nada ficou vazio antes de seguir:

```bash
echo "senha=${#TF_VAR_sql_admin_password}  registry=[$TF_VAR_registry_server]"
```

---

### Passo 5 — Provisione

```bash
terraform init
terraform plan
```

**Leia o plan antes de aplicar.** Confira três coisas:

- `Plan: 25 to add, 0 to change, 0 to destroy`
- as imagens do MongoDB começam com o endereço do seu registry, não com `mongo:7.0` puro
- as regiões batem com o que o Passo 0 detectou

```bash
terraform apply -auto-approve
```

Leva de 6 a 8 minutos — aproveite para reler os `.tf`.

Perto do fim você verá o semantic ranker sendo habilitado:

```
terraform_data.search_semantic (local-exec): Habilitando semantic ranker...
terraform_data.search_semantic (local-exec): Semantic ranker habilitado.
```

> **Não pressione `Ctrl+C` nem `Ctrl+Z` durante o apply.** Interromper deixa
> recursos pela metade: uma conta Cosmos em estado `Failed`, por exemplo,
> reserva o nome e impede recriar. Se você parou sem querer, veja o
> troubleshooting.

**Lições neste passo:**

- Você gerou uma **senha forte com `openssl`** em vez de inventar.
- A senha nunca tocou um arquivo — foi por variável de ambiente. No L₂ veremos
  como o Key Vault assume esse papel para os serviços.

---

### Passo 6 — Exporte os outputs

Os scripts Python das atividades precisam destes valores:

```bash
export STORAGE_ACCOUNT_NAME=$(terraform output -raw storage_account_name)
export KEY_VAULT_NAME=$(terraform output -raw key_vault_name)
export COSMOS_ENDPOINT=$(terraform output -raw cosmos_endpoint)
export SEARCH_ENDPOINT=$(terraform output -raw search_endpoint)
export MONGO_IP=$(terraform output -raw mongodb_public_ip)

echo "Storage:  $STORAGE_ACCOUNT_NAME"
echo "KeyVault: $KEY_VAULT_NAME"
echo "Cosmos:   $COSMOS_ENDPOINT"
echo "Search:   $SEARCH_ENDPOINT"
echo "MongoDB:  $MONGO_IP:27017  |  Mongo Express: $(terraform output -raw mongo_express_url)"
```

---

> ### Se a sessão do Cloud Shell cair
>
> A infraestrutura continua no ar. Refaça apenas:
>
> ```bash
> cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
> pip install --user -r ../scripts/requirements.txt      # Passo 2
> source ~/.qc-registry.env                              # Passo 3
> export TF_VAR_sql_admin_password="<a senha anotada>"   # Passo 4
> ```
>
> E repita o Passo 6. O Passo 5 não precisa ser refeito.

---

## Atividade 1 — Storage Account + Blob (CSV do catálogo QC)

**Objetivo:** Entender a estrutura de Object Storage e fazer upload do CSV de produtos da QC ao container `catalogo`.

### Passo 1 — Conferir o que foi provisionado

Abra o [storage.tf](terraform/storage.tf) e observe:

- **`azurerm_storage_account.qc`** — a "conta" do storage (nome globalmente único)
- **3 containers** dentro dela: `catalogo`, `imagens`, `logs`
- **`azurerm_storage_management_policy`** — política de lifecycle que migra automaticamente os blobs do prefixo `logs/`: Hot → Cool (30 dias) → Archive (90 dias) → delete (365 dias)

No portal Azure, busque o Storage Account criado e clique em **Containers** para visualizar os 3.

### Passo 2 — Upload do CSV de produtos

O CSV de 20 produtos da QC já está no repo em [data/produtos.csv](data/produtos.csv). Fazer upload:

```bash
az storage blob upload \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --container-name catalogo \
  --name produtos.csv \
  --file ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv \
  --auth-mode login \
  --overwrite

# Listar para confirmar
az storage blob list \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --container-name catalogo \
  --auth-mode login \
  --output table
```

> **Se aparecer "AuthorizationPermissionMismatch"**: você está autenticado mas seu papel ainda não permite Data Plane no Storage. Conceda a role:
> ```bash
> az role assignment create \
>   --assignee $(az ad signed-in-user show --query id -o tsv) \
>   --role "Storage Blob Data Contributor" \
>   --scope $(az storage account show -n "$STORAGE_ACCOUNT_NAME" --query id -o tsv)
> ```
> Aguardar 30s e tentar de novo.

**✅ Checkpoint L₁:** Você consegue listar `produtos.csv` dentro do container `catalogo`?

---

## Atividade 2 — Azure SQL Serverless + Key Vault + Python

**Objetivo:** Popular a tabela `T_PRODUTOS` no Azure SQL **lendo a connection string do Key Vault** (sem hardcoded) e os dados do **CSV no Blob**.

### Passo 1 — Conferir o que foi provisionado

Abra [sql.tf](terraform/sql.tf) e [keyvault.tf](terraform/keyvault.tf). Observe:

- **`azurerm_mssql_database.qc`** — banco SQL **General Purpose Serverless** (`GP_S_Gen5_2`) com **auto-pause** após 60 min de inatividade: pausado, paga-se só o storage (centavos), e com o destroy ao final o custo é desprezível. *(A "oferta gratuita" do Azure SQL ainda não tem suporte no provider azurerm liberado — [PR #32055](https://github.com/hashicorp/terraform-provider-azurerm/pull/32055) — por isso usamos serverless com auto-pause.)*
- **`azurerm_mssql_firewall_rule.cloud_shell`** — libera o IP do Cloud Shell automaticamente (usando o data source `http.meu_ip`).
- **`azurerm_key_vault.qc`** — Vault com **RBAC habilitado** (sem usar Access Policies legadas).
- **`azurerm_key_vault_secret.sql_connection`** — a connection string completa, armazenada como segredo.

> **Por que `time_sleep` antes do segredo?** RBAC tem ~30-60s de propagação. Sem o sleep, o `apply` falha porque a role ainda não está ativa quando o Terraform tenta criar o segredo.

### Passo 2 — Dependências Python

Já instaladas na Preparação (Passo 2). Se a sessão do Cloud Shell caiu desde
então, o `~/.local` foi apagado — refaça aquele passo antes de continuar.

### Passo 3 — Rodar o script

O script [popular_produtos.py](scripts/popular_produtos.py) já está pronto. Ele:

1. Lê a connection string do Key Vault (usando a identidade do Cloud Shell)
2. Baixa o CSV do Blob
3. Conecta no SQL e cria a tabela `T_PRODUTOS`
4. Insere os 20 produtos
5. Mostra o top 3 mais caros

Execute:

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 popular_produtos.py
```

Esperado: 20 produtos inseridos, lista do top 3 mais caros.

> **Erro comum 1:** "Login failed for user 'sqladminqc'" — a senha tem caractere especial que o shell mascarou. Ver troubleshooting.
>
> **Erro comum 2:** "The client with object id ... does not have authorization to perform action..." no Key Vault — espera 1 min e tenta de novo (a RBAC ainda está propagando, embora o Terraform já tenha esperado 60s).

**✅ Checkpoint L₂:** Você inseriu 20 produtos no Azure SQL **lendo o segredo do Key Vault**?

### Passo 4 — Discussão (3 min)

Anote no `respostas-aula02.md` do seu fork:

1. O que aconteceria se a `conn_str` viesse hardcoded no `popular_produtos.py` e o arquivo fosse commitado num repo público?
2. Como você protegeria esse mesmo segredo se ele fosse usado por um agente AI rodando em Azure Function?
3. Qual o papel do `DefaultAzureCredential` aqui? Por que ele "simplesmente funciona" no Cloud Shell mas não funcionaria no notebook local?

---

## Atividade 3 — Cosmos DB / MongoDB + Azure AI Search

**Objetivo:** Inserir reviews dos clientes da QC num banco NoSQL (Cosmos DB **ou** MongoDB) e indexar o catálogo no Azure AI Search com semantic ranking — base para o RAG dos agentes.

> **Cosmos DB indisponível na sua região?** O ambiente provisiona automaticamente os dois bancos. Se o `terraform apply` criou o Cosmos com sucesso, siga a **Parte A**. Se recebeu `RequestDisallowedByAzure` ou `No region available` para o Cosmos, pule para a **Parte A.2 — MongoDB**.

### Parte A — Cosmos DB (20 min)

#### Passo 1 — Conferir o que foi provisionado

Abra [cosmos.tf](terraform/cosmos.tf):

- **`azurerm_cosmosdb_account.qc`** — conta Cosmos em modo **Serverless** (paga por operação). Custo das 4h de aula ≈ centavos.
- **Container `reviews`** particionado por `/produto_id`.

> **Por que não Free Tier?** O Free Tier do Cosmos só beneficia *provisioned throughput* (não serverless) e o Azure permite **apenas 1 conta free-tier por assinatura** — o que trava o `apply` se já houver outra. Por isso o lab usa serverless sem free-tier (`var.cosmos_free_tier = false`). Para ligar mesmo assim: `terraform apply -var="cosmos_free_tier=true"`.

#### Passo 2 — Como o script autentica no Cosmos (key via Key Vault)

Aqui há uma **pegadinha importante do Cloud Shell**: ele **não consegue emitir token AAD** para a audience de data-plane do Cosmos (`https://<conta>.documents.azure.com`) — qualquer tentativa de `DefaultAzureCredential` falha com `AudienceNotSupported`. Diferente de Key Vault, Blob e AI Search, que têm audience suportada.

Por isso o [popular_reviews.py](scripts/popular_reviews.py) autentica no Cosmos com a **key**, lida do **Key Vault** (segredo `cosmos-primary-key`, provisionado pelo Terraform em [keyvault.tf](terraform/keyvault.tf)). É o mesmo padrão "segredo no Vault" do SQL — sem chave hardcoded no código.

> **E a role data-plane?** O `cosmos.tf` também cria `azurerm_cosmosdb_sql_role_assignment` — mas ela serve para o cenário de **produção**: uma Function/Container com **Managed Identity** própria consegue token AAD para o Cosmos e usaria `DefaultAzureCredential` direto (sem key). A limitação é só do Cloud Shell.

#### Passo 3 — Rodar o script de reviews

[popular_reviews.py](scripts/popular_reviews.py) insere 30 reviews fictícias com diferentes scores.

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 popular_reviews.py
```

Esperado: 30 reviews inseridas + listagem de reviews score ≥ 4 do produto 5.

#### Passo 4 — Explorar no portal

1. Portal → seu Cosmos account → **Data Explorer**
2. Expandir `qc-db` → `reviews` → **Items**
3. Visualizar os documentos JSON inseridos

**✅ Checkpoint L₃-A:** Você vê 30 reviews no Data Explorer do Cosmos?

---

### Parte A.2 — MongoDB via ACI (alternativa regional)

> Se o Cosmos DB foi criado com sucesso, você pode pular para a **Parte B**. Se recebeu **"No region available"** ou **"RequestDisallowedByAzure"** no Cosmos, use este caminho — o MongoDB já foi provisionado junto com os demais recursos (mesmo `terraform apply`).

O `terraform apply` criou um **Azure Container Instance** com **MongoDB 7.0** + **Mongo Express** (interface web). É a mesma abordagem da Aula 4.

#### Passo 1 — Conferir o que foi provisionado

Abra [mongodb.tf](terraform/mongodb.tf):

- **`azurerm_container_group.mongodb`** — ACI com dois containers (MongoDB + Mongo Express) compartilhando rede do grupo.
- **Portas expostas:** 27017 (MongoDB) e 8081 (Mongo Express).
- **Autenticação vs Cosmos:** conexão TCP direta com usuário/senha — sem token AAD, sem Key Vault. Padrão de laboratório; em produção a senha viria do Key Vault (mesmo padrão do SQL aqui).

#### Passo 2 — Aguardar o container estar pronto (~2 min)

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
echo "MongoDB  : $MONGO_IP:27017"
echo "Mongo Web: $(terraform output -raw mongo_express_url)"
# Abrir a URL do Mongo Express no browser — se carregar, o container está pronto
```

O script já tenta por até 100 segundos automaticamente — não é necessário aguardar manualmente.

#### Passo 3 — Rodar o script de reviews

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 popular_reviews_mongo.py
```

Esperado: 30 reviews inseridas + listagem de reviews score ≥ 4 do produto 5. **Os dados são idênticos ao Cosmos** (mesmo seed, mesmos campos `produto_id` / `score` / `texto` / `cliente`) — facilita comparar os dois modelos NoSQL.

#### Passo 4 — Explorar no Mongo Express

1. Recuperar o endereço do servidor do Mongo
```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
terraform output mongo_express_url
```
3. Com o valor apresentado (ex.: `http://20.x.x.x:8081`), copie para abrir no browser
4. Clicar em **qc-db** → **reviews** → **View**
5. Observar os documentos JSON — mesma estrutura do Cosmos (sem o overhead de `_ts`, `_etag`, `_rid`)

**✅ Checkpoint L₃-A.2:** Você vê 30 reviews no Mongo Express?

---

### Parte B — Azure AI Search (25 min)

#### Passo 1 — Conferir o que foi provisionado

Abra [search.tf](terraform/search.tf):

- **`azurerm_search_service.qc`** — Search service SKU **free** (3 índices, 50 MB), com **autenticação AAD/RBAC habilitada no data-plane** (`authentication_failure_mode`). Sem isso, o `DefaultAzureCredential` dos scripts levaria **403 Forbidden** mesmo com as roles.
- **2 role assignments**: `Search Service Contributor` (gerencia índices) e `Search Index Data Contributor` (indexa/consulta documentos).
- **`terraform_data.search_semantic`** — habilita o **semantic ranker** (plano free, 1000 queries/mês) chamando `az search service update` via `local-exec`, logo após o search service subir.

> **Por que um `provisioner` e não um recurso declarativo?** O provider `azurerm` recusa `semantic_search_sku` quando o SKU é `free`, e forçar via `azapi` não funciona — a Azure aceita a chamada e reverte para `disabled`, então o `plan` nunca converge. Sem alternativa declarativa, o `provisioner` é o escape hatch legítimo.
>
> O preço: o comando roda **na máquina que executa o Terraform** (precisa de `az` autenticado), e o Terraform **não sabe o estado real** — se alguém desabilitar o semantic pelo portal, nenhum `plan` vai acusar. É por isso que a HashiCorp recomenda evitar `provisioner` sempre que houver outro caminho.

> **Atenção:** AI Search Free também é **1 por subscription**. Mesma lógica do Cosmos.

#### Passo 2 — Rodar o script de indexação

[indexar_produtos.py](scripts/indexar_produtos.py) cria o índice `produtos-index` com **analyzer em português** e configuração de semantic ranking, depois indexa os 20 produtos.

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts

# Aguardar a role RBAC propagar (~30s desde o terraform apply)
sleep 30

python3 indexar_produtos.py
```

> **Se aparecer `Semantic search is not enabled for this service`:** o
> `local-exec` do `terraform_data.search_semantic` não rodou ou falhou. Confira
> o estado real e habilite na mão se preciso:
>
> ```bash
> az search service show --name $(terraform output -raw search_service_name) \
>   -g $(terraform output -raw resource_group_name) --query semanticSearch -o tsv
> ```

Após a execução do script, podemos seguir com o exercício:

```
cd ~/aie-cloud/aulas/02-storage-bancos/lab/scripts
python3 indexar_produtos.py

O script já demonstra 3 tipos de busca:
- **Keyword:** `cadeira escritório`
- **Semantic:** `algo para trabalhar em pé`
- **Filtro + ordenação:** `categoria = moveis` ordenado por preço

#### Passo 3 — Validar no portal

1. Portal → `srch-qc-xxxxxx` → **Search Explorer**
2. Testar query: `cadeira ergonomica` — observar resultados
3. Mudar **Query type** para **Semantic** → testar `produto para dor nas costas`
4. Observar o ranking semântico

**✅ Checkpoint L₃-B:** Você consegue executar buscas semânticas via Python e via Portal?

> **Nota importante:** Aqui usamos **semantic search** (ranking inteligente baseado nos modelos da Microsoft). Para fazer **vector search verdadeira** seria preciso gerar embeddings dos textos — chamando Azure OpenAI ou um modelo de embedding. **Veja Exercício 3.1 do [exercicios.md](../exercicios.md)** se quiser implementar vector search real.

---

## Wrap-up — Destroy e Custo Zero (10 min)

### Passo 1 — Destruir o ambiente

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
terraform destroy -auto-approve -var="sql_admin_password=$SQL_PASSWORD"
```

Tempo: ~5 minutos.

### Passo 2 — Remova o registry

O ACR fica num resource group separado, então o `terraform destroy` não o
alcança:

```bash
az group delete -n rg-qc-registry --yes --no-wait
```

### Passo 3 — Verificar custo zero

1. Portal → **Cost Management** → **Análise de custo** → filtrar por hoje
2. Total deve estar próximo de $0 (serverless/auto-pause + Search free + duração curta do lab)

### Passo 4 — Commitar progresso no seu fork

No seu fork (não no repo `aie-cloud` clonado direto):

```bash
cd ~/aie-cloud-do-meu-fork    # ajuste para o caminho do SEU fork
# Copiar arquivos relevantes para sua estrutura de fork (ou trabalhar direto nele)
git add aula02/
git status
git commit -m "feat(aula02): provisionamento da camada de dados QC"
git push origin main
```

> **NÃO commitar:** O `terraform.tfstate` (já está no `.gitignore`) — ele tem segredos. Se você criou `terraform.tfvars` com a senha, também não commitar.

---

## Conexão com o projeto Quantum Commerce

Saída desta aula — a **camada de dados da QC** está pronta:

```
infrastructure/
  ├── main.tf, variables.tf, outputs.tf
  ├── storage.tf    (Blob: catálogo, imagens, logs)
  ├── sql.tf        (T_PRODUTOS — transacional)
  ├── keyvault.tf   (segredos)
  ├── cosmos.tf     (reviews — NoSQL Cosmos)
  ├── mongodb.tf    (reviews — NoSQL MongoDB via ACI, alternativa regional)
  └── search.tf     (índice de produtos — base de RAG)
```

Esses recursos serão consumidos por:

- **Aula 3** — funções serverless que leem do SQL via Key Vault
- **Aula 4** — serviços cognitivos que usam imagens do Blob e o índice do Search
- **Aula 5** — pipeline de MLOps que treina recomendação sobre reviews + produtos
- **Disciplinas paralelas** — Integration Architecture e Knowledge Management consomem `T_PRODUTOS` e o índice de produtos

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| `RequestDisallowedByAzure` (403) | A região não está na policy da sua assinatura | Rode `bash detectar-regioes.sh` — ele sonda e regrava o `terraform.tfvars`. A lista de permitidas muda por assinatura |
| `ProvisioningDisabled` (403) | Região permitida, mas o serviço está bloqueado nela para a sua assinatura | Outra região. Não adianta esperar — é bloqueio, não capacidade |
| `InsufficientResourcesAvailable` (400) | Região permitida, sem cota do SKU free no momento | Outra região, ou tente mais tarde. Cota de free varia ao longo do dia |
| Cosmos: "Free tier has already been applied to another account" | Já existe (ou existiu) outra conta Cosmos free-tier na assinatura | Já tratado: o lab usa serverless sem free-tier por padrão. Se você ligou com `-var="cosmos_free_tier=true"`, volte para `false` |
| AI Search: limite de SKU Free atingido | 1 search service Free por subscription | Destruir o existente em outra subscription, ou usar SKU `basic` (~$60/mês — evite) |
| Python: "Login failed for user 'sqladminqc'" | Senha do shell tinha `$` ou aspas — interpretado errado | Use `openssl rand -base64 24` (não contém caracteres problemáticos) ou guarde em variável escapada |
| Python pyodbc: "Can't open lib 'ODBC Driver 18 for SQL Server'" | Cloud Shell pode ter v17 em vez de v18 | Mudar `driver = "{ODBC Driver 17 for SQL Server}"` no script |
| pyodbc: "Invalid value specified for connection string attribute 'Encrypt'" | Connection string com `Encrypt=true`/`false` (sintaxe .NET); o ODBC exige `yes`/`no` | Já corrigido no `keyvault.tf` (`Encrypt=yes;TrustServerCertificate=no`). Se o segredo foi criado antes do fix, rode `terraform apply` de novo para atualizá-lo |
| Key Vault: "Forbidden — the user does not have ... action" | RBAC ainda não propagou | `sleep 60` e tentar de novo |
| Cosmos: "Request is unauthorized" / `Forbidden` | Role data-plane ainda propagando (já é criada pelo Terraform em `cosmos.tf`) | Aguardar ~1 min e rodar de novo. Conferir: `az cosmosdb sql role assignment list --account-name <cosmos> -g <rg> -o table` |
| Cosmos: `ClientAuthenticationError ... AudienceNotSupported` no Cloud Shell | O Cloud Shell não emite token AAD para a audience de data-plane do Cosmos (nenhuma credencial consegue) | Já tratado: o `popular_reviews.py` autentica por **key** lida do Key Vault (`cosmos-primary-key`). Afeta só o Cosmos (KV/Blob/Search têm audience suportada) |
| AI Search: `Operation returned an invalid status 'Forbidden'` ao indexar | Serviço aceitava só API key no data-plane (token AAD recusado) | Já resolvido no `search.tf` (`authentication_failure_mode`). Em serviço criado antes do fix: `terraform apply` de novo |
| AI Search: `Semantic search is not enabled` / `FeatureNotSupportedInService` | O `local-exec` do `terraform_data.search_semantic` falhou (Azure CLI ausente ou sem autenticação na máquina que rodou o Terraform) | Habilite na mão: `az search service update --name $(terraform output -raw search_service_name) -g $(terraform output -raw resource_group_name) --semantic-search free` |
| `terraform destroy` falha em Key Vault | Purge protection ou soft-delete | Confirmar `purge_protection_enabled = false` no `keyvault.tf` (já está) |
| `AuthorizationPermissionMismatch` no upload Blob | Sem role data plane no Storage | Conceder `Storage Blob Data Contributor` (ver Passo 2 da L₁) |
| MongoDB: `ServerSelectionTimeoutError` após 100s | ACI ainda inicializando | Aguardar 1 min e rodar `python3 popular_reviews_mongo.py` de novo |
| MongoDB: `Authentication failed` | `MONGO_IP` não exportado ou IP errado | `echo $MONGO_IP` — se vazio: `export MONGO_IP=$(terraform output -raw mongodb_public_ip)` |
| Mongo Express: página não carrega | ACI ainda subindo ou porta 8081 | Aguardar 2 min; confirmar URL: `terraform output mongo_express_url` |
| ACI: `409 RegistryErrorResponse` do `index.docker.io` | Rate limit do Docker Hub no IP de saída da região (100 pulls/6h, compartilhado) | Rode o Passo 3 da Preparação e `source ~/.qc-registry.env`. Confirme com `echo $TF_VAR_registry_server` |
| ACI: `InaccessibleImage` | Credencial do registry errada ou truncada | `echo ${#TF_VAR_registry_password}` — a senha do ACR tem ~84 caracteres. Se estiver menor, refaça o `source ~/.qc-registry.env` |
| `Error acquiring the state lock` | Um apply anterior morreu segurando o lock | Antes de destravar, veja se ele vive: `ps aux \| grep [t]erraform`. STAT `T` = parado por Ctrl+Z, use `fg`. Nada listado: `terraform force-unlock <ID>`. **Nunca destrave com o processo vivo** |
| `already exists - needs to be imported` | Recurso criado por um apply que morreu antes de gravar no state | Veja o estado: `az resource show --ids "<ID>" --query properties.provisioningState`. Se `Failed`, apague com `az resource delete --ids "<ID>"`. Se `Succeeded`, adote com `terraform import` |
| `IM002 Data source name not found` no Python | Connection string sem `DRIVER={...}` | O `keyvault.tf` atual já grava com o driver. Se o segredo é antigo, `terraform apply` regrava |
| `terraform destroy`: "Resource Group still contains Resources" | Algo foi criado no RG por fora do Terraform | `az resource list -g <rg> -o table` e remova. **Não** desative `prevent_deletion_if_contains_resources` |
| Senha do SQL vazia / `administrator_login_password -> null` no plan | `$TF_VAR_sql_admin_password` perdida ao reconectar o Cloud Shell | `echo ${#TF_VAR_sql_admin_password}` — se for 0, exporte a senha anotada e reaplique |

---

## Tarefa pós-aula

Antes da Aula 3:

1. **Commitar tudo no fork** (já feito no wrap-up)
2. **Atualizar `respostas-aula02.md`** com:
   - Diagrama da arquitetura QC atualizado (camada de dados detalhada)
   - Respostas às 3 perguntas de reflexão da L₂ (Key Vault)
   - Justificativa: por que esses serviços para esses dados da QC
3. **Resolver pelo menos os exercícios Nível 1** de [exercicios.md](../exercicios.md)

---

## Referências

- [Azure Storage Blob — Lifecycle](https://learn.microsoft.com/azure/storage/blobs/lifecycle-management-overview)
- [Azure SQL Free Offer](https://learn.microsoft.com/azure/azure-sql/database/free-offer)
- [Azure Cosmos DB Free Tier](https://learn.microsoft.com/azure/cosmos-db/free-tier)
- [Azure AI Search — Semantic Ranking](https://learn.microsoft.com/azure/search/semantic-search-overview)
- [Azure AI Search — Vector Search](https://learn.microsoft.com/azure/search/vector-search-overview) (Aula 4 / Exercício 3.1)
- [DefaultAzureCredential — fluxo de autenticação](https://learn.microsoft.com/python/api/overview/azure/identity-readme#defaultazurecredential)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
