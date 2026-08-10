# Container code — Aula 3

Versão **FastAPI** da API de catálogo da QC, com mesma lógica de negócio da Function `v2-blob`, mas empacotada num **container Docker** para rodar no Azure Container Instances (ACI).

## Arquivos

| Arquivo | O que é |
|---------|---------|
| [app.py](app.py) | API FastAPI com endpoints `/health` e `/produtos` |
| [requirements.txt](requirements.txt) | Dependências (FastAPI + Uvicorn + azure-identity + azure-storage-blob) |
| [Dockerfile](Dockerfile) | Multi-stage build, imagem final leve (~150 MB) |

## Por que não buildar no Cloud Shell?

Nas contas **Azure for Students**, o **ACR Tasks é bloqueado** (`az acr build` → `TasksOperationsNotAllowed`) e o **Cloud Shell não tem daemon Docker** (`docker build` não roda). Por isso a imagem é **construída e publicada uma vez no GHCR pelo professor**, e cada aluno só **importa** a imagem pronta para o seu ACR via `az acr import` (operação permitida, sem Tasks e sem Docker local).

## Passo A — Publicar no GHCR (PROFESSOR, 1× por turma)

Feito numa máquina/Codespace **com Docker** (Codespaces já é `linux/amd64`, ideal):

Antes, crie um **PAT do GitHub** (Settings → Developer settings → Personal access
tokens → **Tokens (classic)** → escopo **`write:packages`**) e exporte:

```bash
export GHCR_PAT=ghp_seu_token_aqui   # sem isto, o login abaixo dá "Cannot perform an interactive login from a non TTY device"
```

```bash
cd aulas/03-serverless-containers/lab/docker

# Login no GHCR (alternativa: 'docker login ghcr.io -u elthonf' e colar o PAT no prompt)
echo "$GHCR_PAT" | docker login ghcr.io -u elthonf --password-stdin

# IMPORTANTE: ACI roda linux/amd64 — force a plataforma (essencial em Mac ARM)
docker build --platform linux/amd64 -t ghcr.io/elthonf/produtos-api:v1 .
docker push ghcr.io/elthonf/produtos-api:v1
```

Depois, **torne o package público** — todo package novo no GHCR nasce **privado**,
e o `az acr import` do aluno (acesso anônimo) falharia com `403 DENIED` se ficar privado:

GitHub → **Packages → produtos-api → Package settings → Danger Zone → Change visibility → Public**

> Se preferir manter privado, o aluno teria de passar `--username elthonf --password <PAT read:packages>` no `az acr import` (menos prático para a turma).

> Ajuste `elthonf` para o owner real do GHCR, se for outro.

## Passo B — Importar a imagem no seu ACR (ALUNO, no Cloud Shell)

```bash
ACR_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw acr_name)

az acr import \
  --name "$ACR_NAME" \
  --source ghcr.io/elthonf/produtos-api:v1 \
  --image produtos-api:v1 \
  --force

# Confirmar
az acr repository list -n "$ACR_NAME" -o table
```

## Depois da importação, habilitar o ACI

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
terraform apply -auto-approve -var="aci_enabled=true"
```

## Testar o ACI

```bash
ACI_FQDN=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw aci_fqdn)

sleep 60   # aguardar a MI propagar
curl "http://$ACI_FQDN:8080/health"
curl "http://$ACI_FQDN:8080/produtos?categoria=moveis"
```

> **`/health` verde não significa API funcionando.** O `/health` não toca no
> Storage — ele responde mesmo com a identidade quebrada. Quem prova que a MI
> está correta é o `/produtos`. E como o `restart_policy` é `Always`, um container
> que morre no boot reinicia em loop sem o Terraform reclamar:
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

## Autenticação: nenhuma senha em lugar nenhum

Duas coisas precisam de credencial aqui, e as duas usam a **mesma** Managed
Identity user-assigned — com atribuições separadas e mínimas:

| O quê | Papel | Escopo |
|-------|-------|--------|
| Puxar a imagem | `AcrPull` | só o ACR |
| Ler o `produtos.csv` | `Storage Blob Data Reader` | só o Storage do catálogo |

Por isso o ACR está com `admin_enabled = false` e o `image_registry_credential`
no Terraform não tem `username`/`password`, só `user_assigned_identity_id`.

⚠️ **O detalhe que quebra na prática:** com identidade **user-assigned** o
`DefaultAzureCredential` não tem como adivinhar qual identidade usar — é preciso
passar `AZURE_CLIENT_ID` como variável de ambiente do container (já está no
`containers.tf`). Com identidade *system-assigned*, como a da Function, existe só
uma opção e o SDK acerta sozinho — é a diferença entre os dois runtimes que mais
confunde.

> **Nota:** ACI não tem HTTPS built-in. Em produção, colocar Front Door, Application Gateway ou Azure Container Apps na frente (ou usar Container Apps direto, que tem TLS gerenciado).

## Comparação com a Function (mesma lógica, runtime diferente)

| Aspecto | Function v2-blob | ACI (este container) |
|---------|------------------|----------------------|
| URL | `https://<func>.azurewebsites.net/api/produtos` | `http://<aci>:8080/produtos` |
| TLS | ✅ Built-in | ❌ Não (manual) |
| Cold start | 1-3s | Não há (sempre on) |
| Custo idle | $0 | $$ pay-per-second mesmo idle |
| Auto-scale | ✅ 0-200 | ❌ 1 réplica fixa |
| Linguagem | Python/.NET/JS/Java | Qualquer |
| Identidade | System-assigned MI | User-assigned MI |
