# Guia de Laboratório — Aula 5

**Tema:** MLOps na Nuvem
**Plataforma:** AWS — **AWS Academy Learner Lab**
**Ambiente:** **AWS CloudShell** + console do **Amazon SageMaker AI**

---

## Visão geral do lab

```
Atividade 1 — Provisionar bucket versionado + Model Registry (Terraform)  ~20 min  (L₁)
Atividade 2 — Treinar local no CloudShell + tracking (MLflow local)      ~25 min  (L₂)
Atividade 3 — Training Job reproduzível + registro no Model Registry      ~45 min  (L₃)
Atividade 4 — Endpoint (serverless) a partir da versão APROVADA           ~20 min  (L₄)
Wrap-up   — Apagar endpoint e Registry (CRÍTICO) + terraform destroy      ~5 min
```

**Pré-requisito:** apenas o `produtos.csv` da Aula 2 (já está commitado em
[`../../02-storage-bancos/lab/data/produtos.csv`](../../02-storage-bancos/lab/data/produtos.csv)).
**Não precisa ter a Aula 2 viva.**

> **⚠️ Alerta de custo:** o Training Job cobra **só os minutos** em que a máquina
> existe (~2–4 min de ml.m5.large por job, centavos). O endpoint **serverless** cobra
> por requisição e escala a zero. Se você usar `--tipo instancia`, a ml.m5.large custa
> ~US$ 0,115/h **ligada 24 h** — apague no fim da Atividade 4.

### De-para com a versão Azure

| Azure ML | SageMaker AI | O que muda na prática |
|---|---|---|
| Workspace + Storage + Key Vault + App Insights + ACR | **nada a provisionar** — o serviço já está na região | o Terraform cria só bucket e Registry |
| Compute Cluster (min 0 nós) | **Training Job** — a máquina nasce e morre com o job | não existe cluster para esquecer ligado |
| Data Asset versionado | objeto S3 com **versionamento** | o job registra o `VersionId` numa tag |
| `job.yml` + `conda.yml` | `create_training_job` + container de scikit-learn da AWS | o ambiente é uma imagem pronta, versionada |
| MLflow do Workspace | **métricas do job** (regex no log → CloudWatch) + MLflow **local** | sem servidor de tracking pago |
| Model Registry + stage *Production* | **Model Package Group** + status **Approved** | aprovação é um campo, com quem e quando |
| Managed Online Endpoint | **Endpoint** (serverless ou instância) | serverless escala a zero |

---

## 📘 Bem-vindo à Aula 5 — leia antes de começar

Esta aula ensina **MLOps em cloud** — **não algoritmos de Machine Learning**.

**O que você precisa saber:** copiar/colar comandos no CloudShell e os conceitos das
Aulas 1–4 (Terraform, S3, containers).

**O que você NÃO precisa saber (e está OK!):** como funciona o `NearestNeighbors`, o
que é similaridade de cosseno, como redes neurais são treinadas, detalhes de
embeddings.

O modelo de recomendação é só o **veículo**. Você vai:

1. Provisionar o **bucket versionado** e o **Model Registry**
2. **Rodar um script pronto** que treina o modelo — primeiro na sua máquina (CloudShell)
3. Ver params e métricas **rastreados**
4. Rodar **o mesmo script** como **Training Job** reproduzível
5. **Registrar** e **aprovar** uma versão no Registry
6. Fazer **deploy** da versão aprovada como endpoint e chamá-lo

---

## Preparação (5 min)

1. Learner Lab → **Start Lab** → bolinha **verde** → **AWS** → região **us-east-1**.
2. Abra o **CloudShell**:

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git ~/aie-cloud 2>/dev/null || git -C ~/aie-cloud pull
terraform -version || { bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh && source ~/.bashrc; }

mkdir -p ~/qc-aula05
cp ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv ~/qc-aula05/
cd ~/aie-cloud/aulas/05-mlops/lab
```

---

## Atividade 1 — Bucket versionado + Model Registry (L₁)

### Passo 1 — Aplicar Terraform

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/terraform
terraform init
terraform apply -auto-approve
terraform output
cd ..
```

Cria **três coisas** (compare com as seis da versão Azure):

| Recurso | Para quê |
|---|---|
| bucket `qc-aula05-<sufixo>-ml` (versionado, privado) | dados, código do treino, artefatos |
| objeto `dados/produtos/produtos.csv` | o dataset — com `VersionId` |
| Model Package Group `recomendador-qc-<sufixo>` | o Model Registry |

### Passo 2 — Ver a versão do dado

```bash
BUCKET=$(terraform -chdir=terraform output -raw bucket)
aws s3api list-object-versions --bucket "$BUCKET" --prefix dados/produtos/ \
  --query 'Versions[].{versao: VersionId, atual: IsLatest, data: LastModified}' --output table
```

Edite uma linha do CSV, rode `terraform apply` de novo e repita: **duas versões**. É o
"Data Asset versionado" — o job da Atividade 3 grava qual versão usou.

### Passo 3 — Confirmar no console

**SageMaker AI** → **Models** → **Model registry** (ou **Governance → Model registry**,
conforme a versão do console) → o grupo `recomendador-qc-<sufixo>`, ainda vazio.

---

## Atividade 2 — Treino local + tracking (L₂)

### Passo 1 — Dependências (leves: sem torch)

```bash
pip3 install --user --quiet "scikit-learn" pandas joblib "mlflow-skinny<3"
```

> O `$HOME` do CloudShell tem 1 GB. `mlflow-skinny` é o MLflow sem o servidor web:
> dá para rastrear e consultar runs, sem a interface gráfica.

### Passo 2 — Rodar duas vezes, com parâmetros diferentes

```bash
python3 codigo/train.py --n_neighbors 5
python3 codigo/train.py --n_neighbors 3
```

Cada execução imprime `precision_at_k_proxy=...` e cria um **run** no MLflow local
(`./mlruns`).

### Passo 3 — Comparar os runs

```bash
python3 - <<'EOF'
import mlflow
runs = mlflow.search_runs(experiment_names=["recomendacao-qc"])
print(runs[["run_id", "params.n_neighbors", "params.vetorizador",
            "metrics.precision_at_k_proxy"]].to_string(index=False))
EOF
```

**Pergunta para o grupo:** qual run você mandaria para produção, e por quê? Guarde a
resposta — o Registry da Atividade 3 é onde essa decisão fica **registrada**.

> 💡 Repare que o `train.py` lê `SM_CHANNEL_TREINO` e `SM_MODEL_DIR` com padrões
> locais. É isso que permite o **mesmo arquivo** rodar aqui e no Training Job.

---

## Atividade 3 — Training Job reproduzível + Registry (L₃)

### Parte A — Submeter o job (15 min)

```bash
python3 scripts/submeter_job.py
```

O script mostra cada mudança de estado:

```
  14:02:11  InProgress  Starting
  14:03:26  InProgress  Downloading
  14:03:41  InProgress  Training
  14:04:12  Completed   Completed
Métricas finais: { "precision_at_k_proxy": 0.54 }
Faturado:  71 s de ml.m5.large
```

O que aconteceu, peça por peça:

| Peça do job | Equivalente Azure | Onde ver |
|---|---|---|
| `sourcedir.tar.gz` no S3 | `code: .` do `job.yml` | S3 → `codigo/<job>/` |
| imagem `sagemaker-scikit-learn:1.2-1-cpu-py3` | `environment` + `conda.yml` | job → *Algorithm* |
| canal `treino` → `dados/produtos/` | `inputs.produtos` (Data Asset) | job → *Input data configuration* |
| `MetricDefinitions` (regex) | `mlflow.log_metric` | job → *Metrics* e CloudWatch |
| tag `dados_versao` | versão do Data Asset | job → *Tags* |
| `model.tar.gz` | `outputs/` | S3 → `modelos/<job>/output/` |

### Parte B — Ver no console e no log (5 min)

**SageMaker AI** → **Training** → **Training jobs** → o seu job:
*Hyperparameters*, *Metrics*, *Monitor* (link para os logs no CloudWatch).

```bash
aws logs tail /aws/sagemaker/TrainingJobs --log-stream-name-prefix rec-qc --since 30m
```

### Parte C — Registrar e aprovar (10 min)

```bash
python3 scripts/registrar_modelo.py --job <nome-do-job>     # o script anterior imprimiu
python3 scripts/registrar_modelo.py --listar
python3 scripts/registrar_modelo.py --aprovar 1
```

A versão nasce **PendingManualApproval**. Aprovar é um ato explícito, que fica
registrado no Registry — é o "stage Production" da versão Azure, com trilha de
auditoria.

Pela CLI pura, o mesmo:

```bash
GRUPO=$(terraform -chdir=terraform output -raw model_package_group)
aws sagemaker list-model-packages --model-package-group-name "$GRUPO" \
  --query 'ModelPackageSummaryList[].{v: ModelPackageVersion, status: ModelApprovalStatus}' --output table
```

### Parte D — Re-submeter com outro parâmetro (15 min)

```bash
python3 scripts/submeter_job.py --n_neighbors 3
python3 scripts/registrar_modelo.py --job <novo-job>
python3 scripts/registrar_modelo.py --listar
```

Agora há **v1 (Approved)** e **v2 (Pending)**. Compare as descrições: cada versão
carrega o job, os hiperparâmetros e a métrica que a geraram. É a **linhagem**.

> 🔴 **Opcional (perfil ML):** `python3 scripts/submeter_job.py --vetorizador embeddings`
> usa *sentence-transformers*. O job instala torch (CPU) antes de treinar — leva uns
> 5 minutos a mais. Compare o `precision_at_k_proxy` com o TF-IDF.

---

## Atividade 4 — Endpoint da versão aprovada (L₄)

### Passo 1 — Implantar

```bash
python3 scripts/implantar_endpoint.py               # serverless (padrão)
# se a sua conta recusar serverless:
# python3 scripts/implantar_endpoint.py --tipo instancia
```

O script pega a versão **Approved mais recente** do Registry — nunca "a última
treinada". Três objetos nascem: **Model** → **EndpointConfig** → **Endpoint**.

### Passo 2 — Testar

```bash
ENDPOINT=rec-qc-$(terraform -chdir=terraform output -raw sufixo)
aws sagemaker-runtime invoke-endpoint --endpoint-name "$ENDPOINT" \
  --content-type application/json --body fileb://endpoint/request.json resposta.json
python3 -m json.tool resposta.json
```

A primeira chamada no serverless pode levar alguns segundos (**cold start**); a
segunda é rápida. É o trade-off do escala-a-zero, medido por você.

### Passo 3 — Trocar a versão sem trocar o endereço

```bash
python3 scripts/registrar_modelo.py --aprovar 2
python3 scripts/implantar_endpoint.py
```

O endpoint é **atualizado** (`update_endpoint`) para a v2 — mesma URL, modelo novo.
Rollback é aprovar de volta a v1 (e rejeitar a v2) e rodar o script de novo.

---

## Wrap-up — Apagar (5 min)

### Passo 1 — Endpoint e Registry (PRIMEIRO!)

```bash
python3 scripts/limpar.py --registro
```

O Terraform **não sabe** que endpoint, models e versões do Registry existem — os
scripts os criaram. Sem este passo, o `destroy` falha no Model Package Group (grupo
com versões não é apagado) e, pior, um endpoint de instância continuaria cobrando.

### Passo 2 — Terraform destroy

```bash
terraform -chdir=terraform destroy -auto-approve
rm -rf mlruns modelo-local resposta.json
```

### Passo 3 — Conferir que não sobrou nada cobrando

```bash
aws sagemaker list-endpoints --query 'Endpoints[].EndpointName'
aws sagemaker list-training-jobs --status-equals InProgress --query 'TrainingJobSummaries[].TrainingJobName'
```

As duas listas devem vir vazias. (Training jobs concluídos ficam no histórico, sem custo.)

---

## Conexão com o projeto Quantum Commerce

**Saída desta aula:**

- Bucket versionado + Model Registry via IaC
- Treino reproduzível (o mesmo `train.py` local e no Training Job)
- `recomendador-qc` com v1 e v2 no Registry, uma aprovada
- Endpoint testado (e apagado)

**Para os agentes da QC:** uma 5ª tool da Lambda da Aula 3 — `/recomendar` — chamaria
`sagemaker-runtime:InvokeEndpoint` com a role da função (sem chave) e devolveria os
top-N produtos. Com endpoint serverless, o custo parado é zero; com instância
dedicada, ~US$ 84/mês. Decisão de produto a justificar na entrega final — é o
**Exercício N2.2**.

---

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| `AccessDenied ... CreateTrainingJob` | sessão do Learner Lab encerrada | religue o Lab e rode de novo |
| `ResourceLimitExceeded` | tipo de instância fora da cota do Learner Lab | `--instancia ml.m5.large` (treino) ou `--tipo serverless` (endpoint) |
| job `Failed`: `No such file ... produtos.csv` | canal apontando para prefixo vazio | `terraform apply` subiu o CSV? `aws s3 ls s3://$BUCKET/dados/produtos/` |
| job `Failed`: `unrecognized arguments` | hiperparâmetro com nome diferente do `argparse` | o `train.py` usa `--n_neighbors` (sublinhado), como o SageMaker passa |
| endpoint `Failed`: `ModelError` / 500 | erro no `inference.py` | CloudWatch → `/aws/sagemaker/Endpoints/rec-qc-<sufixo>` |
| `ValidationException` no serverless | serverless não liberado na conta | `--tipo instancia` |
| `terraform destroy` falha no Model Package Group | versões ainda no Registry | `python3 scripts/limpar.py --registro` |
| `pip install` sem espaço no CloudShell | `$HOME` de 1 GB | `pip3 cache purge`; use só `mlflow-skinny` |

---

## Referências

- [Amazon SageMaker AI — Training jobs](https://docs.aws.amazon.com/sagemaker/latest/dg/how-it-works-training.html)
- [Use scikit-learn with SageMaker (containers e script mode)](https://docs.aws.amazon.com/sagemaker/latest/dg/sklearn.html)
- [Define training metrics (MetricDefinitions)](https://docs.aws.amazon.com/sagemaker/latest/dg/training-metrics.html)
- [Model Registry — Model Package Groups](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html)
- [Serverless Inference](https://docs.aws.amazon.com/sagemaker/latest/dg/serverless-endpoints.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
