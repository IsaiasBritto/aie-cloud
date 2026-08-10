# Container code — Aula 3

Versão **FastAPI** da API de catálogo da QC, com mesma lógica de negócio da Function `v2-blob`, mas empacotada num **container Docker** para rodar no Azure Container Instances (ACI).

## Arquivos

| Arquivo | O que é |
|---------|---------|
| [app.py](app.py) | API FastAPI com endpoints `/health` e `/produtos` |
| [requirements.txt](requirements.txt) | Dependências (FastAPI + Uvicorn + azure-identity + azure-storage-blob) |
| [Dockerfile](Dockerfile) | Multi-stage build, imagem final leve (~150 MB) |
| [`.github/workflows/publicar-imagem-produtos-api.yml`](../../../../.github/workflows/publicar-imagem-produtos-api.yml) | Workflow que builda e publica a imagem no GHCR (Passo A) |

## Onde cada coisa roda

A imagem **não é construída no Azure**. São dois ambientes distintos, e confundi-los
é a causa de quase todo problema nesta atividade:

| Passo | Onde | Quem | Frequência |
|-------|------|------|------------|
| **A** — build + push no GHCR | GitHub Actions | Professor | **1× e pronto** — só repete se o código mudar |
| **B** — `az acr import` | Cloud Shell | Cada aluno | Toda vez que refizer o lab |

### Por que o build não roda no Cloud Shell

Duas portas fechadas ao mesmo tempo:

- **`docker build`** → `Cannot connect to the Docker daemon`. O Cloud Shell tem o
  *cliente* `docker` instalado, mas nenhum daemon atrás dele. (O `docker login`
  até funciona, porque só grava credencial em arquivo — o que engana.)
- **`az acr build`** → `TasksOperationsNotAllowed`. O ACR Tasks buildaria do lado
  do Azure, sem Docker local, mas é bloqueado em contas Azure for Students.

Sem saída dentro do Azure. Por isso o build acontece no runner do GitHub, que tem
Docker de verdade e é `linux/amd64` nativo — a arquitetura que o ACI exige.

---

## Passo A — Publicar no GHCR (PROFESSOR, 1× e pronto)

Automatizado por
[`.github/workflows/publicar-imagem-produtos-api.yml`](../../../../.github/workflows/publicar-imagem-produtos-api.yml).
**Não há nada para rodar no terminal.**

### A.1 — Disparar o workflow

Ele roda sozinho em qualquer push que altere `lab/docker/**`. Para disparar à mão:

GitHub → aba **Actions** → **Publicar imagem produtos-api no GHCR** → **Run workflow**

Leva ~2 min. O resumo da execução mostra o endereço da imagem publicada.

### A.2 — Tornar o package público (só na primeira vez)

**Este é o único passo manual, e o mais fácil de esquecer.** Todo package novo no
GHCR nasce **privado**, e o `az acr import` do aluno é anônimo — sem isto ele falha
com `403 DENIED`.

<https://github.com/users/IsaiasBritto/packages/container/produtos-api/settings>
→ **Danger Zone** → **Change visibility** → **Public**

> O package pertence à **conta**, não ao repositório — por isso não existe aba
> "Packages" na barra do repo. Pelo caminho manual: seu avatar → **Your profile**
> → aba **Packages** → `produtos-api` → **Package settings**.

> Se preferir manter privado, cada aluno teria de passar
> `--username <owner> --password <PAT read:packages>` no `az acr import` — bem
> menos prático para a turma.

### A.3 — Conferir que ficou acessível

```bash
az acr import --name "$ACR_NAME" \
  --source ghcr.io/isaiasbritto/produtos-api:v1 \
  --image produtos-api:v1 --force

az acr repository show -n "$ACR_NAME" --image produtos-api:v1 \
  --query "{arquitetura:architecture, os:os, criada:createdTime}" -o table
```

`arquitetura` precisa ser **`amd64`**. Se vier `arm64`, o container sobe e morre
com `exec format error` — o workflow força `linux/amd64` justamente para isso.

> **Por que não fazer o Passo A na mão com Docker?** Dá para fazer, num Codespace
> ou numa máquina com Docker Desktop. Mas exige criar um PAT com `write:packages`,
> e o PAT fica gravado em texto puro no `~/.docker/config.json`. O workflow usa o
> `GITHUB_TOKEN`, que é emitido para aquela execução e expira ao terminar — não há
> segredo de longa duração para vazar. É o mesmo raciocínio de Managed Identity
> aplicado ao CI.

---

## Passo B — Importar a imagem no seu ACR (ALUNO, no Cloud Shell)

```bash
ACR_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw acr_name)

az acr import \
  --name "$ACR_NAME" \
  --source ghcr.io/isaiasbritto/produtos-api:v1 \
  --image produtos-api:v1 \
  --force

# Confirmar
az acr repository list -n "$ACR_NAME" -o table
```

> O `--force` está aí de propósito: sem ele, repetir o lab dá
> `(Conflict) Tag produtos-api:v1 already exists in target registry`. Não é erro
> de verdade — é o ACR se recusando a sobrescrever uma tag existente.

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
