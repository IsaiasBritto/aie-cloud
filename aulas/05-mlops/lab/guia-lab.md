# Guia de Laboratório — Aula 5

**Tema:** MLOps na Nuvem
**Plataforma:** Microsoft Azure (Azure for Students)
**Ambiente:** **Azure Cloud Shell** + **Azure ML Studio** (https://ml.azure.com)

---

## Visão geral do lab

```
Atividade 1 — Provisionar Azure ML Workspace + Compute Cluster        ~30 min  (L₁)
Atividade 2 — Treinar recomendador local + MLflow tracking + Registry ~35 min  (L₂)
Atividade 3 — Job reproduzível no Compute Cluster (env + data asset)  ~50 min  (L₃)
Atividade 4 — Managed Online Endpoint + consumo via REST              ~10 min  (L₄)
Wrap-up   — Deletar endpoint (CRÍTICO) + terraform destroy            ~5 min
```

**Pré-requisito:** apenas o `produtos.csv` da Aula 2 (já está commitado em [`../../02-storage-bancos/lab/data/produtos.csv`](../../02-storage-bancos/lab/data/produtos.csv)). **Não precisa ter a Aula 2 viva.**

> **⚠️ Alerta de custo:** Online Endpoint custa **~$0,30/h** (Standard_DS3_v2). **DELETAR ao final do L₄**, antes do `terraform destroy`. Esquecer = ~$7/dia consumindo seu crédito.

---

## 📘 Bem-vindo à Aula 5 — leia antes de começar

Esta aula tem um **objetivo bem específico**: ensinar **MLOps em cloud** — **não algoritmos de Machine Learning**.

**O que você precisa saber:**

- Copiar/colar comandos no Cloud Shell ✅
- Conceitos básicos do que vimos nas Aulas 1-4 (Terraform, Function, Storage) ✅

**O que você NÃO precisa saber (e está OK!):**

- Como funciona o algoritmo `NearestNeighbors` ❌
- O que é "cosine similarity" ❌
- Como redes neurais são treinadas ❌
- Detalhes de embeddings ❌

**Por quê?** O modelo de recomendação aqui é apenas um **veículo didático** para ensinar o ciclo MLOps. Você vai:

1. Provisionar o **Workspace de ML**
2. **Rodar um script pronto** que treina o modelo
3. Ver o **MLflow** registrando params, métricas, artefatos
4. Ver o modelo **versionado no Registry**
5. Submeter um **Job reproduzível** com environment + dataset versionados
6. Fazer **deploy** como endpoint REST

Isso é o que MLOps faz. O algoritmo em si é coberto na disciplina **AI Foundation and Learning Models**.

> Se você sentir falta de explicação sobre algum termo de ML, marque a dúvida no chat — vamos esclarecer rapidamente. Mas **não bloqueie seu progresso por isso**.

---

## Preparação (5 min)

### Confirmar ferramentas

```bash
az account show --query "{nome:name, id:id}" -o table
terraform -version

# Azure ML CLI v2 (instalar/atualizar se faltar)
az extension add -n ml 2>/dev/null || az extension update -n ml
az ml --version
```

### Criar workspace local para o lab

```bash
mkdir -p ~/qc-aula05
cd ~/qc-aula05

# Copiar o produtos.csv da Aula 2 (já commitado no repo)
cp ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv .
ls -la
```

---

## Atividade 1 — Provisionar Azure ML Workspace + Compute Cluster

**Objetivo:** Workspace + Compute Cluster com **scale-to-zero** via Terraform. Tudo gratuito quando idle.

### Passo 1 — Aplicar Terraform

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/terraform

terraform init
terraform apply -auto-approve
```

Tempo: **~5 min** (Workspace é o mais lento — múltiplas dependências). Comece este `apply` cedo na aula; ele pode rodar enquanto você lê a teoria.

### Passo 2 — Exportar outputs

```bash
export SUBSCRIPTION_ID=$(terraform output -raw subscription_id)
export RESOURCE_GROUP=$(terraform output -raw resource_group_name)
export WORKSPACE_NAME=$(terraform output -raw workspace_name)
export ML_STORAGE=$(terraform output -raw storage_account_name)

echo "Workspace: $WORKSPACE_NAME"
echo "Storage:   $ML_STORAGE"
echo "RG:        $RESOURCE_GROUP"
```

### Passo 3 — Confirmar no Studio

1. Abrir https://ml.azure.com
2. Selecionar o Workspace `mlw-qc-xxxxxx`
3. Menu lateral → **Compute** → confirmar `cpu-cluster` listado com **0 nodes** (scale-to-zero ativo)
4. Menu lateral → **Data** → confirmar datastore `workspaceblobstore` criado automaticamente

**✅ Checkpoint L₁:** Workspace + Compute Cluster com 0 nodes no Studio?

---

## Atividade 2 — Treinar recomendador local + MLflow tracking + Registry

**Objetivo:** Treinar o recomendador da QC no Cloud Shell com **MLflow apontando para o Workspace remoto**. Ver params, metrics, artifacts aparecerem no Studio em tempo real e modelo versionado no Registry.

### Passo 1 — Instalar dependências

```bash
pip install --user mlflow azureml-mlflow azure-ai-ml azure-identity \
                    sentence-transformers scikit-learn pandas
```

> Primeira execução baixa o modelo de embedding (~80 MB) para `~/.cache/huggingface` — cacheado entre sessões.

### Passo 2 — Configurar variáveis e rodar

```bash
# Variáveis para o script
export DATA_PATH=~/qc-aula05/produtos.csv

cd ~/aie-cloud/aulas/05-mlops/lab/notebooks
python3 treinar_recomendador.py
```

Tempo: ~1 min (após o cache do modelo).

### Passo 3 — Validar no Studio

1. Abrir Azure ML Studio
2. **Jobs** → experimento `recomendacao-qc` → seu run
3. Aba **Metrics:** `precision_at_k_proxy`, `num_produtos`, `embedding_dim`
4. Aba **Outputs + logs:** `nn_model.pkl` em `model/`
5. Menu lateral → **Models** → `recomendador-qc:1`

### Passo 4 — Marcar v1 como Production

```bash
az ml model update --name recomendador-qc --version 1 \
  --set tags.stage=Production \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

> **Nota:** Azure ML CLI v2 não tem mais o conceito de "stage" explícito (foi descontinuado em favor de tags + Endpoints). Usamos `tags.stage` por convenção.

**✅ Checkpoint L₂:** Modelo no Registry com tag `stage=Production`?

---

## Atividade 3 — Pipeline reproduzível no Azure ML

**Objetivo:** Transformar o script local num **job submetido ao Compute Cluster**, com **environment** versionado e **data asset** versionado.

### Parte A — Upload do dataset + Data Asset (10 min)

O job vai puxar o `produtos.csv` do datastore default do Workspace via Data Asset `produtos-qc:1`. Primeiro faça upload, depois crie o Data Asset.

```bash
# Pegar o nome do container do workspaceblobstore
WS_CONTAINER=$(az ml datastore show \
  --name workspaceblobstore \
  --workspace-name "$WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query container_name -o tsv)

# Upload do CSV
az storage blob upload \
  --account-name "$ML_STORAGE" \
  --container-name "$WS_CONTAINER" \
  --name aula05/produtos.csv \
  --file ~/qc-aula05/produtos.csv \
  --auth-mode login --overwrite

# Criar o Data Asset versionado
cd ~/aie-cloud/aulas/05-mlops/lab/job
az ml data create --file data-asset.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Confirmar no Studio → **Data** → `produtos-qc` v1.

### Parte B — Submeter o job (15 min)

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/job

az ml job create --file job.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Tempo (primeira execução):

- Cluster acorda do scale-to-zero: **~2 min**
- Build do environment: **~3-5 min** (cacheado nas próximas)
- Execução: **~30 s**
- **Total: ~5-8 min** primeira vez

Acompanhe no Studio: **Jobs** → seu job → logs em tempo real.

### Parte C — Validar (5 min)

1. Job aparece em **Jobs** com status `Completed`
2. Aba **Outputs + logs**: `outputs/nn_model.pkl`
3. Aba **Metrics**: `precision_at_k_proxy`
4. **Models**: nova versão (`recomendador-qc:2` se Atividade 2 foi feita; `:1` caso contrário)

### Parte D — Re-submeter com outro parâmetro (10 min)

Edite `job.yml`: mude `n_neighbors: 5` para `n_neighbors: 10`.

```bash
az ml job create --file job.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

No Studio, compare os 2 runs lado a lado: qual `precision_at_k_proxy` ficou maior? Modelo v3 deve aparecer no Registry.

**✅ Checkpoint L₃:** 2 runs comparáveis no Studio? Modelo versionado (v2 e v3 se Atividade 2 foi feita; v1 e v2 caso contrário)?

---

## Atividade 4 — Managed Online Endpoint

**Objetivo:** Deploy do modelo como endpoint REST. **CRÍTICO:** deletar imediatamente após testar — endpoint custa ~$0,30/h ativo.

### Passo 1 — Definir um nome único

Nome de Online Endpoint é **global no Azure**. Substitua o placeholder nos YAMLs:

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/endpoint

# Gerar sufixo único
SUFIXO="$(whoami | tr -cd 'a-z0-9')-$RANDOM"
export ENDPOINT_NAME="rec-qc-$SUFIXO"
echo "Endpoint: $ENDPOINT_NAME"

# Substituir nos YAMLs (sed in-place)
sed -i "s/rec-qc-<sufixo-unico>/$ENDPOINT_NAME/g" endpoint.yml deployment.yml
```

### Passo 2 — Criar endpoint + deployment

```bash
# 1. Envelope do endpoint
az ml online-endpoint create --file endpoint.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"

# 2. Deployment (instância de compute) — ~5 min
az ml online-deployment create --file deployment.yml \
  --endpoint-name "$ENDPOINT_NAME" \
  --all-traffic \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

> **⚠️ A partir daqui o endpoint custa ~$0,30/h.** Siga direto para o teste e o destroy.

### Passo 3 — Testar

```bash
ENDPOINT_URL=$(az ml online-endpoint show --name "$ENDPOINT_NAME" \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP" --query scoring_uri -o tsv)

ENDPOINT_KEY=$(az ml online-endpoint get-credentials --name "$ENDPOINT_NAME" \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP" --query primaryKey -o tsv)

# Chamar
curl -X POST "$ENDPOINT_URL" \
  -H "Authorization: Bearer $ENDPOINT_KEY" \
  -H "Content-Type: application/json" \
  -d @request.json
```

Esperado: JSON com produtos similares ao produto 5.

**✅ Checkpoint L₄:** Endpoint responde com recomendações?

---

## Wrap-up — Destroy (5 min)

### Passo 1 — DELETAR ENDPOINT (PRIMEIRO!)

```bash
az ml online-endpoint delete --name "$ENDPOINT_NAME" --yes \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Aguarde ~2 min. **Não pule este passo — endpoint custa $/hora.**

### Passo 2 — Terraform destroy

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/terraform
terraform destroy -auto-approve
```

Tempo: ~5 min (Workspace é o mais lento para destruir).

### Passo 3 — Verificar custo

Portal → **Cost Management** → análise de hoje. Esperado: **< $1** (compute cluster acorda só durante jobs; endpoint foi vivo por <30 min se você seguiu o cronograma).

### Passo 4 — Reverter alterações no clone

Você editou `endpoint.yml` e `deployment.yml` com o nome único do seu endpoint. Para deixar o clone limpo para o próximo `git pull`:

```bash
cd ~/aie-cloud
git checkout aulas/05-mlops/lab/endpoint/endpoint.yml aulas/05-mlops/lab/endpoint/deployment.yml aulas/05-mlops/lab/job/job.yml
```

---

## Conexão com o projeto Quantum Commerce

**Saída desta aula:**

- Workspace Azure ML provisionado via IaC
- Compute Cluster com scale-to-zero
- Modelo `recomendador-qc` versionado no Registry (v1, v2, v3)
- Pipeline reproduzível (Job YAML + Environment + Data Asset)
- Endpoint REST testado (e deletado)

**Para os agentes da QC:**

Uma 5ª tool da Function da Aula 3 — `/recomendar` — chamaria o Online Endpoint via REST e retornaria top-N produtos similares. Em produção real, manter o endpoint ligado custa $216/mês por instância — decisão de produto a justificar na entrega final. Esta integração é o **Exercício N2.2** desta aula.

---

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| `terraform apply` falha no Workspace | Quota de Storage Account na região | Mudar `location` para `eastus2` (`-var=location=eastus2`) |
| `sentence-transformers` muito lento | Modelo (~80 MB) baixando | Aguardar; cache em `~/.cache/huggingface` |
| Job em "Queued" eternamente | Compute Cluster falhou ao escalar | Verificar quota de vCPUs na subscription |
| Job falhou com "Image not found" | `conda.yml` inválido | Conferir indentação do YAML |
| `az ml model update --set tags` falha | CLI v2 antiga | `az extension update -n ml` |
| Endpoint deployment falhou | Modelo precisa de scoring script | Modelo registrado via `mlflow.pyfunc.log_model` já vem com scoring built-in — se falhar, conferir versão do MLflow |
| Endpoint retorna 500 | Faltam libs no environment | Adicionar `sentence-transformers` no `conda_file` do deployment |
| Custo > $5 no fim do dia | Endpoint esquecido | Sempre `az ml online-endpoint delete` antes do `terraform destroy` |

---

## Referências

- [Azure Machine Learning — Get Started](https://learn.microsoft.com/azure/machine-learning/quickstart-create-resources)
- [MLflow + Azure ML](https://learn.microsoft.com/azure/machine-learning/how-to-use-mlflow-cli-runs)
- [Model Registry — Azure ML](https://learn.microsoft.com/azure/machine-learning/how-to-manage-models)
- [Online Endpoints](https://learn.microsoft.com/azure/machine-learning/how-to-deploy-online-endpoints)
- [Compute Cluster](https://learn.microsoft.com/azure/machine-learning/how-to-create-attach-compute-cluster)
- [Sentence Transformers](https://www.sbert.net/)
- [Azure ML Pricing](https://azure.microsoft.com/pricing/details/machine-learning/)
