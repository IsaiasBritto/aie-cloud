# Guia de Laboratório — Aula 3

**Tema:** Serverless & Containers
**Plataforma:** Microsoft Azure (Azure for Students)
**Ambiente:** **Azure Cloud Shell** — tudo no browser, sem instalar nada

---

## Visão geral do lab

```
Atividade 1 — Function HTTP via Terraform + deploy com 'func'        ~30 min  (L₁)
Atividade 2 — Function lendo Blob (CSV QC) via Managed Identity      ~45 min  (L₂)
Atividade 3 — Mesmo código em container: import no ACR + ACI         ~50 min  (L₃)
Wrap-up    — terraform destroy + verificação custo zero              ~10 min
```

> **Regra de ouro:** sempre encerrar com `terraform destroy`. Custo zero ao final.

---

## Pré-requisitos

- ✅ Aula 1 concluída (Cloud Shell funcional, Terraform rodando)
- ✅ Repositório `aie-cloud` clonado no Cloud Shell

> **Aula independente:** esta aula **não depende da Aula 2**. O Terraform cria
> seu próprio Storage Account de catálogo e já sobe o `produtos.csv` no `apply`
> (de [lab/data/produtos.csv](data/produtos.csv)). Nada de exportar outputs da Aula 2.

---

## Preparação (5 min)

### Confirmar ferramentas no Cloud Shell

```bash
az account show --query "{nome:name, id:id}" -o table
terraform -version
func --version
docker --version
```

Se algum não responder, ver [Troubleshooting](#troubleshooting--problemas-comuns).

### Ir para o Terraform da Aula 3

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
ls
# main.tf  variables.tf  outputs.tf  function.tf  containers.tf  README.md
```

Leia rapidamente cada `.tf` (3 min) — veja o [README do Terraform](terraform/README.md) para um resumo.

---

## Atividade 1 — Function HTTP via Terraform + deploy

**Objetivo:** Provisionar uma Azure Function App em **Flex Consumption** (plano FC1 — sucessor do Linux Consumption/Y1, que será aposentado em set/2028) e fazer deploy de uma função HTTP simples em Python (versão mock).

### Passo 1 — Phase 1 do Terraform

Provisiona Function App + ACR + identidades + roles. **Não cria o ACI ainda** (a imagem precisa existir primeiro).

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform

terraform init

terraform apply -auto-approve
# aci_enabled=false (default) → ACI não é criado
```

Tempo: ~3-5 min. Isso já cria o Storage do catálogo e sobe o `produtos.csv`. Anote os outputs (`function_app_name`, `acr_login_server`, `catalogo_storage_account_name`).

### Passo 2 — Deploy da versão mock (v1)

A pasta [function/v1-mock/](function/v1-mock/) tem código self-contained (5 produtos hardcoded — bom para validar que o pipeline de deploy funciona).

```bash
# Pegar o nome da Function App
FUNC_NAME=$(terraform output -raw function_app_name)
echo "Deploying em: $FUNC_NAME"

cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v1-mock
func azure functionapp publish "$FUNC_NAME" --python
```

Tempo: ~1-2 min. O `func` empacota o código e envia para o Azure.

### Passo 3 — Testar

```bash
HOSTNAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_app_default_hostname)

curl -s "$HOSTNAME/api/health" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos?categoria=eletronicos" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos?nome=cadeira" | python3 -m json.tool
```

> **Primeira chamada vai demorar 2-3s** — cold start. Chamadas seguintes são milissegundos.

**✅ Checkpoint L₁:** O `curl` retorna JSON com lista de produtos mock?

---

## Atividade 2 — Function lendo Blob via Managed Identity

**Objetivo:** Trocar o mock por dados reais do Blob do catálogo (criado nesta aula). **Sem credenciais no código** — autenticação via Managed Identity SystemAssigned (já criada no Passo 1).

### Conferir o que já foi provisionado

Abra [function.tf](terraform/function.tf) e observe:

- **`identity { type = "SystemAssigned" }`** no Function App — Azure cria automaticamente uma identidade gerenciada
- **`app_settings.STORAGE_ACCOUNT_CATALOGO`** — variável de ambiente já injetada (nome do Storage de catálogo desta aula)
- **`azurerm_role_assignment.fn_blob_reader`** — concede `Storage Blob Data Reader` à Managed Identity no Storage do catálogo

> **Tudo isso já foi aplicado no Passo 1 da Atividade 1.** Não há novo `terraform apply` aqui — só novo deploy de código.

### Passo 1 — Deploy da versão v2-blob

A pasta [function/v2-blob/](function/v2-blob/) tem o código que **lê o Blob via `DefaultAzureCredential`** — sem chaves no código.

```bash
FUNC_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_app_name)

cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v2-blob
func azure functionapp publish "$FUNC_NAME" --python
```

### Passo 2 — Testar

```bash
HOSTNAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_app_default_hostname)

# Agora retorna os 20 produtos REAIS do Blob!
curl -s "$HOSTNAME/api/produtos?categoria=moveis" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos?nome=cadeira" | python3 -m json.tool
```

> **Erro comum:** "AuthorizationFailure" — a role demorou para propagar. Aguarde 1-2 min e tente novamente.

### Passo 3 — Reflexão (3 min)

Anote no `entrega-grupo-aula03.md` do seu grupo:

1. Procure por "key", "password", "credential", "secret" em todo o código da Function v2-blob. O que você encontra?
2. Como a Function consegue ler o Blob "sem credenciais"?
3. Se um agente em produção precisar acessar 5 storage accounts diferentes, qual a estratégia recomendada?

**✅ Checkpoint L₂:** A Function retorna os 20 produtos reais do CSV?

---

## Atividade 3 — Imagem de container no ACR + ACI

**Objetivo:** Levar o **mesmo código** (em FastAPI, empacotado em container) para o seu ACR e rodá-lo no ACI com Managed Identity user-assigned. A imagem já vem pronta (publicada no GHCR pelo professor) — você a **importa** para o ACR e o ACI a executa.

### Conferir o código FastAPI

[docker/app.py](docker/app.py) tem a mesma lógica da Function v2-blob (lê Blob via MI), mas usando FastAPI. O [Dockerfile](docker/Dockerfile) usa **multi-stage build** para imagem leve (~150 MB) — é essa imagem que o professor publica no GHCR.

### Passo 1 — Importar a imagem do GHCR para o seu ACR

> **Por que não buildar aqui?** Nas contas Azure for Students o **ACR Tasks é bloqueado** (`az acr build` falha com `TasksOperationsNotAllowed`) e o **Cloud Shell não tem Docker**. Por isso a imagem é construída **uma vez pelo professor** e publicada no **GHCR** (registry do GitHub); você só a **importa** para o seu ACR — operação permitida, sem Tasks e sem Docker local.

```bash
ACR_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw acr_name)

# Importa a imagem pública do GHCR para o seu ACR (poucos segundos)
az acr import \
  --name "$ACR_NAME" \
  --source ghcr.io/elthonf/produtos-api:v1 \
  --image produtos-api:v1

# Confirmar que a imagem chegou
az acr repository list -n "$ACR_NAME" -o table
```

> O código FastAPI está em [docker/](docker/) para você ler — é a mesma lógica da Function v2-blob. Como ela foi construída/publicada no GHCR está no [docker/README.md](docker/README.md) (Passo A — professor).

### Passo 2 — Phase 2 do Terraform (habilitar ACI)

Com a imagem no ACR, agora habilita o ACI:

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform

terraform apply -auto-approve -var="aci_enabled=true"
```

Tempo: ~1 min. O ACI puxa a imagem do ACR e sobe o container.

> **Repare no que o ACI *não* recebeu:** nenhum usuário, nenhuma senha, nenhuma
> connection string. A mesma Managed Identity user-assigned faz as duas coisas —
> `AcrPull` no ACR para puxar a imagem e `Storage Blob Data Reader` no Storage
> para ler o CSV. Duas atribuições separadas, cada uma no escopo do seu recurso.
> Abra o [containers.tf](terraform/containers.tf) e confira.

### Passo 3 — Testar o ACI

```bash
ACI_FQDN=$(terraform output -raw aci_fqdn)
echo "ACI: $ACI_FQDN"

# Aguardar Managed Identity propagar
sleep 60

curl "http://$ACI_FQDN:8080/health"
curl "http://$ACI_FQDN:8080/produtos?categoria=moveis"
```

> **Cuidado com o falso positivo:** o `/health` não toca no Storage — ele responde
> `ok` mesmo com a identidade quebrada. Quem prova que a autenticação funcionou é
> o `/produtos`. E como o `restart_policy` é `Always`, um container que morre no
> boot fica reiniciando em loop sem o `terraform apply` reclamar de nada:
>
> ```bash
> RG=$(terraform output -raw resource_group_name)
> ACI=$(terraform output -raw aci_name)
>
> az container show -g "$RG" -n "$ACI" \
>   --query "containers[0].instanceView.{estado:currentState.state, reinicios:restartCount}" -o table
>
> az container logs -g "$RG" -n "$ACI"
> ```
>
> `restartCount` maior que zero já denuncia crash loop.

**Pergunta rápida (2 min):** a Function usa MI *system-assigned* e o código não
precisa de nada. O ACI usa MI *user-assigned* e precisa receber `AZURE_CLIENT_ID`
como variável de ambiente. Por quê?

<details>
<summary>Resposta</summary>

O `DefaultAzureCredential` pede o token ao IMDS local sem dizer quem ele é. Com
system-assigned existe **uma** identidade possível e o IMDS resolve sozinho. Com
user-assigned, a identidade é um recurso separado que pode estar anexado a vários
serviços — e vários podem estar anexados ao mesmo container. O SDK precisa
apontar qual, e faz isso pelo `client_id`.

Vale reforçar a diferença: `client_id` é o que vai ao IMDS; `principal_id` é o
objeto no Entra que aparece nas role assignments. Trocar um pelo outro é o erro
mais comum aqui — e o sintoma é justamente `/health` verde com `/produtos` em 500.
</details>

### Passo 4 — Comparação Function vs ACI (5 min)

| Aspecto | Function | ACI |
|---------|----------|-----|
| URL | `https://<func>.azurewebsites.net/api/produtos` | `http://<aci>:8080/produtos` |
| TLS | ✅ Built-in | ❌ Não (manual com Front Door/AppGw) |
| Cold start | 1-3s | Não há (container sempre on) |
| Custo idle | $0 | $$ pay-per-second mesmo idle |
| Auto-scale | ✅ 0-200 | ❌ 1 réplica fixa |
| Linguagem | Python/.NET/JS/Java | Qualquer |
| Identidade | System-assigned MI | User-assigned MI |

**Pergunta para o `entrega-grupo-aula03.md`:**

Para a QC, qual você levaria para produção da API de catálogo? Justifique em 3-5 frases considerando: tráfego esperado, custo, latência aceitável, complexidade operacional.

**✅ Checkpoint L₃:** Você fez deploy do mesmo código em 2 formas (Function + ACI) e ambos respondem `/produtos`?

---

## Wrap-up — Destroy e custo zero (10 min)

### Passo 1 — Destruir o ambiente da Aula 3

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform

terraform destroy -auto-approve -var="aci_enabled=true"
```

Tempo: ~2 min. Tudo desta aula é removido — inclusive o Storage do catálogo (ele é desta aula, não da Aula 2).

### Passo 2 — Verificar custo

Portal → **Cost Management** → **Análise de Custo** → filtrar por hoje. Total deve estar < $1.

---

## Conexão com o projeto Quantum Commerce

**Saída desta aula:**

- Function App + ACR + ACI provisionados via Terraform
- API de catálogo da QC funcionando em **2 sabores** — você decide qual leva para o projeto integrado final

**Para os agentes da QC (Aula 4 e disciplinas seguintes do MBA):**

A API que você implantou é a primeira **tool** que os agentes da QC vão consumir. Spec sugerida:

```json
{
  "name": "buscar_produtos_qc",
  "description": "Busca produtos da Quantum Commerce por categoria ou nome",
  "input_schema": {
    "type": "object",
    "properties": {
      "categoria": {"type": "string", "description": "Categoria (ex: moveis, eletronicos)"},
      "nome":      {"type": "string", "description": "Substring do nome do produto"}
    }
  }
}
```

Na Aula 4 vamos adicionar mais tools (busca por imagem com Vision, transcrição com Speech, etc.).

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| `func: command not found` | Functionalidade não habilitada no Cloud Shell | Executar `npm install -g azure-functions-core-tools@4 --unsafe-perm true` (geralmente já vem por padrão) |
| `func azure functionapp publish` retorna 401 | Cloud Shell não autenticado | `az login` ou `az account set --subscription <id>` |
| Function retorna 403 "AuthorizationFailed" | MI ainda propagando | Aguardar 1-2 min |
| Function retorna 500 "STORAGE_ACCOUNT_CATALOGO not set" | Variável de ambiente não chegou | Verificar `app_settings` no TF + `terraform apply` de novo |
| `az acr build` → `TasksOperationsNotAllowed` | ACR Tasks é bloqueado em contas Azure for Students | Não usar build no aluno — importar a imagem do GHCR com `az acr import` (Passo 1) |
| `az acr import` → `403 DENIED` / "access to the resource is denied" | Imagem do GHCR está **privada** (packages nascem privados) ou não publicada | Professor torna `ghcr.io/elthonf/produtos-api:v1` **público** (Package settings → Change visibility); ou o aluno passa `--username elthonf --password <PAT read:packages>` |
| ACI "Crashed" com `exec format error` | Imagem buildada em arquitetura errada (ex.: ARM no Mac) | Rebuildar com `--platform linux/amd64` e re-publicar no GHCR |
| ACI falha com `InaccessibleImage` / fica em "Pulling image" | A identidade não tem `AcrPull`, ou a imagem não está no ACR | Conferir `az role assignment list --assignee $(terraform output -raw aci_identity_client_id) --all -o table` e `az acr repository list -n <acr>` |
| ACI "Crashed" | App levantou e morreu | `az container logs -n <aci-name> -g <rg>` para ver erro |
| `/health` responde mas `/produtos` dá 500 "falha ao acessar storage" | Falta `AZURE_CLIENT_ID` no container, ou a role `Storage Blob Data Reader` não propagou | Com identidade **user-assigned** o `DefaultAzureCredential` não adivinha qual usar — o env var é obrigatório. Conferir com `az container show ... --query "containers[0].environmentVariables"` |
| ACI mostra `restartCount` > 0 mas o `terraform apply` deu verde | `restart_policy = "Always"` reinicia em loop; o Terraform só garante que o recurso existe, não que a app funciona | `az container show -g <rg> -n <aci> --query "containers[0].instanceView.{estado:currentState.state, reinicios:restartCount}" -o table` |
| ACI retorna timeout no `curl` | DNS ainda propagando | Aguardar 30s |
| FastAPI roda local mas falha no ACI | MI não propagou para subscription | Aguardar 1-2 min e tentar de novo |

---

## Referências

- [Azure Functions Python — programming model v2](https://learn.microsoft.com/azure/azure-functions/functions-reference-python?pivots=python-mode-decorators)
- [Azure Functions Core Tools (`func`)](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [DefaultAzureCredential — chain de autenticação](https://learn.microsoft.com/python/api/overview/azure/identity-readme#defaultazurecredential)
- [Managed Identity overview](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview)
- [Azure Container Registry — quickstart](https://learn.microsoft.com/azure/container-registry/container-registry-get-started-azure-cli)
- [Azure Container Instances overview](https://learn.microsoft.com/azure/container-instances/container-instances-overview)
- [Container Apps vs ACI vs Functions](https://learn.microsoft.com/azure/container-apps/compare-options)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
