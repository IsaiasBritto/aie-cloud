# Notebooks (treino local) — Aula 5

[treinar_recomendador.py](treinar_recomendador.py) — script Python que roda **localmente no Cloud Shell** e treina o recomendador da QC, com **MLflow tracking** apontando para o Workspace remoto.

Usado na **Atividade 2** do lab. A Atividade 3 transforma esse script em um **job submetido ao Compute Cluster** (ver `../job/`).

## Pré-requisito

Workspace provisionado (Terraform aplicado) + `produtos.csv` copiado para o seu workspace local:

```bash
mkdir -p ~/qc-aula05
cp ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv ~/qc-aula05/produtos.csv
```

## Instalar dependências

```bash
pip install --user mlflow azureml-mlflow azure-ai-ml azure-identity scikit-learn pandas
```

> **Por que não `sentence-transformers`?** O Cloud Shell tem 5 GB de disco — `sentence-transformers` puxa `torch` (~1.5 GB) e esgotaria o espaço. Esta atividade usa TF-IDF (já incluso no scikit-learn) para demonstrar o fluxo MLflow → Registry. A Atividade 3 usa embeddings semânticos no Compute Cluster — compare os `precision_at_k_proxy` das duas abordagens.

## Exportar variáveis

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/terraform
export SUBSCRIPTION_ID=$(terraform output -raw subscription_id)
export RESOURCE_GROUP=$(terraform output -raw resource_group_name)
export WORKSPACE_NAME=$(terraform output -raw workspace_name)
export DATA_PATH=~/qc-aula05/produtos.csv
```

## Rodar

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/notebooks
python3 treinar_recomendador.py
```

Saída esperada:

```
Run ID: <uuid>
→ Carregando produtos de /home/.../produtos.csv...
✓ 20 produtos carregados
→ Vetorizando com TF-IDF...
✓ Matriz TF-IDF: (20, 500)
→ Treinando NearestNeighbors com n=5...
✓ Precision proxy (mesma categoria): 0.70
  → Compare com o valor da Atividade 3 (embeddings semânticos no cluster)
✓ Modelo registrado no Registry como 'recomendador-qc'
```

## Validar no Studio

1. Abrir https://ml.azure.com → seu Workspace
2. **Jobs** → experimento `recomendacao-qc` → seu run
3. Aba **Metrics:** `precision_at_k_proxy`, `num_produtos`, `vocab_size`
4. Aba **Outputs + logs:** `nn_model.pkl` em `model/`
5. **Models** (menu lateral) → `recomendador-qc` v1

## Por que treinar local primeiro?

Pedagogicamente, treinar local mostra o que o MLflow captura **sem o intermediário do job**. Você vê params/metrics/artifacts aparecerem no Studio em tempo real. Na Atividade 3 fazemos o mesmo, mas dentro de um **job reproduzível** com environment versionado e dataset versionado — o padrão para retreino futuro.
