# Job reproduzível — Aula 5 (Atividade 3)

Pipeline reproduzível que roda no **Compute Cluster** do Azure ML, com **environment** versionado e **dataset versionado**.

## Arquivos

| Arquivo | O que é |
|---------|---------|
| [train.py](train.py) | Mesmo treino do notebook, mas recebe parâmetros via CLI (`--input-data`, `--n-neighbors`) |
| [conda.yml](conda.yml) | Environment do job — Python 3.11 + ML stack (mlflow, sklearn, sentence-transformers, torch) |
| [data-asset.yml](data-asset.yml) | Data Asset versionado `produtos-qc:1` apontando para `workspaceblobstore` |
| [job.yml](job.yml) | Spec do command job — referencia `produtos-qc:1` + `cpu-cluster` + environment com `conda.yml` |

## Pré-requisitos

- Terraform aplicado (Workspace + Compute Cluster prontos)
- Variáveis exportadas: `RESOURCE_GROUP`, `WORKSPACE_NAME`, `ML_STORAGE` (ver [`../terraform/README.md`](../terraform/README.md))

## Passo a passo

### 1. Subir o `produtos.csv` ao datastore default do Workspace

O `data-asset.yml` aponta para `azureml://datastores/workspaceblobstore/paths/aula05/produtos.csv`. Antes de criar o data asset, faça o upload:

```bash
# Pegar o nome do container do workspaceblobstore
WS_CONTAINER=$(az ml datastore show \
  --name workspaceblobstore \
  --workspace-name "$WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query container_name -o tsv)

# Upload do CSV (da Aula 2) para o caminho 'aula05/produtos.csv' no datastore
az storage blob upload \
  --account-name "$ML_STORAGE" \
  --container-name "$WS_CONTAINER" \
  --name aula05/produtos.csv \
  --file ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv \
  --auth-mode login --overwrite
# Nota: se você seguiu o guia-lab.md, o arquivo está em ~/qc-aula05/produtos.csv — use esse caminho.
```

### 2. Criar o Data Asset versionado

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/job
az ml data create --file data-asset.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

### 3. Submeter o job

```bash
az ml job create --file job.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Tempo (primeira execução):

- Cluster acorda do scale-to-zero: **~2 min**
- Build do environment (image + conda): **~3-5 min** (cacheado nas próximas execuções)
- Execução do treino: **~30 s**
- **Total: ~5-8 min**

Execuções subsequentes (mesmo environment) são bem mais rápidas: ~1-2 min.

### 4. Re-submeter com outro parâmetro

Edite `job.yml`, mude `n_neighbors: 5` para `n_neighbors: 10`, salve, e:

```bash
az ml job create --file job.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

No Studio, **Jobs** → experimento `recomendacao-qc-pipeline` → compare os 2 runs lado a lado: qual `precision_at_k_proxy` ficou maior?

### 5. Validar no Studio

1. **Jobs** → status `Completed`
2. Aba **Outputs + logs**: `outputs/nn_model.pkl`
3. Aba **Metrics**: `precision_at_k_proxy`
4. **Models**: nova versão (`recomendador-qc:2` e `:3` se Atividade 2 foi feita; `:1` e `:2` caso contrário)

## Lição central

Comparando o notebook (treino local) com o job:

| Aspecto | Local (notebooks/) | Job (este folder) |
|---------|---------------------|--------------------|
| Onde roda | Cloud Shell do aluno | Compute Cluster |
| Dataset | Caminho local do filesystem | Data Asset versionado (`produtos-qc:1`) |
| Environment | `pip install --user` ad-hoc | `conda.yml` versionado, imagem cacheada |
| Reproduzível | Não — depende do estado da máquina | Sim — mesmos inputs = mesmos outputs |
| Auditável | Só os logs do MLflow | Logs + spec do job + versão do dataset + versão do environment |

**Por que isso importa?** Quando alguém precisa retreinar daqui a 6 meses com dados novos, o job roda exatamente igual. O notebook local provavelmente quebra (dependências atualizadas, dataset movido, etc.).
