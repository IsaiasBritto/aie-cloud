# Terraform — Aula 5

Provisiona a infraestrutura de MLOps da Quantum Commerce:

- **Resource Group**
- **Storage Account** (datastore default `workspaceblobstore`)
- **Application Insights** (telemetria do Workspace)
- **Key Vault** (segredos do Workspace)
- **Container Registry** (imagens dos environments de treino/serving — pré-provisionado para eliminar delay no primeiro job)
- **Azure Machine Learning Workspace**
- **Compute Cluster** `cpu-cluster` com **scale-to-zero** (min 0 / max 2 nodes, idle 2 min → desliga)

## Como usar (no Azure Cloud Shell)

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/terraform

terraform init

terraform apply -auto-approve
```

Tempo: **~5 min** (Workspace é o mais lento — múltiplas dependências). Vá tomando café enquanto sobe.

> **Dica:** comece este `apply` no início do L₁ — durante o tempo de teoria ele já fica pronto.

## Destroy (regra de ouro — custo zero ao final)

⚠️ **Antes do `terraform destroy`, DELETE o Online Endpoint** (`az ml online-endpoint delete ...`) — endpoint custa $0,30/h, esquecer = $7/dia.

```bash
terraform destroy -auto-approve
```

Tempo: ~5 min (Workspace é o mais lento para destruir).

## Arquivos

| Arquivo | O que define |
|---------|--------------|
| [main.tf](main.tf) | Provider, random_string (sufixo único), Resource Group, locals e tags |
| [storage.tf](storage.tf) | Storage Account (datastore padrão do Workspace) |
| [keyvault.tf](keyvault.tf) | Key Vault (segredos do Workspace) |
| [acr.tf](acr.tf) | Container Registry (pré-provisionado — evita delay de ~20 min no primeiro job) |
| [workspace.tf](workspace.tf) | Application Insights + Azure ML Workspace |
| [compute.tf](compute.tf) | Compute Cluster `cpu-cluster` com scale-to-zero |
| [variables.tf](variables.tf) | `location` (default `eastus2`) |
| [outputs.tf](outputs.tf) | `subscription_id`, `workspace_name`, `resource_group_name`, `storage_account_name`, `compute_cluster_name`, `container_registry_name` |

## Outputs (usados pelos scripts e jobs)

```bash
export SUBSCRIPTION_ID=$(terraform output -raw subscription_id)
export RESOURCE_GROUP=$(terraform output -raw resource_group_name)
export WORKSPACE_NAME=$(terraform output -raw workspace_name)
export ML_STORAGE=$(terraform output -raw storage_account_name)
```

## Observações

- **Scale-to-zero:** o `cpu-cluster` fica em **0 nodes** quando idle. Custo: **$0** durante essa janela. Sobe automaticamente ao receber um job.
- **Região:** algumas subscriptions só permitem ML Workspace em `eastus2` ou similares. Se `terraform apply` falhar no Workspace por quota de Storage, mude `location` para `eastus2` em `variables.tf` (ou via `-var=location=eastus2`).
- **Storage HNS desabilitado:** Workspace requer Storage sem hierarchical namespace.
