# Terraform — Aula 5 (SageMaker AI)

Cria só o que é nosso; o SageMaker já existe na região.

| Recurso | Para quê |
|---|---|
| `aws_s3_bucket.ml` (+ versionamento, bloqueio público) | dados, código do treino e artefatos dos modelos |
| `aws_s3_object.produtos` | o `produtos.csv` da Aula 2, em `dados/produtos/` |
| `aws_sagemaker_model_package_group.recomendador` | o Model Registry do recomendador |
| `data.aws_iam_role.lab` | a LabRole — role de execução do treino e do endpoint |

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/terraform
terraform init
terraform apply -auto-approve
terraform output
```

O `terraform destroy` **não** apaga endpoint, modelo nem training job: eles são
criados pelos scripts. Rode `python3 scripts/remover_endpoint.py` **antes** do destroy.
