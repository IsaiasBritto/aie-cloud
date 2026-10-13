# Terraform — Aula 4

| Arquivo | O que define |
|---------|--------------|
| [main.tf](main.tf) | Providers, tags, locals (credenciais Mongo do lab), data source da LabRole |
| [variables.tf](variables.tf) | `region` (padrão `us-east-1`) e tipo da EC2 do Mongo |
| [outputs.tf](outputs.tf) | `data_bucket_name`, `lambda_name`, `function_url`, `mongodb_public_ip`, `mongo_express_url`, `mongo_secret_id` |
| [storage.tf](storage.tf) | Bucket de dados + prefixos `audios/` e `imagens/` |
| [lambda.tf](lambda.tf) | Lambda Python 3.12 + Function URL + LabRole (timeout 60 s) + log group |
| (nenhum) | Nada a criar: Transcribe, Polly, Comprehend e Rekognition são APIs da conta |
| [secrets.tf](secrets.tf) | Secrets Manager com a URI do MongoDB (lida pela Lambda) |
| [mongodb.tf](mongodb.tf) | EC2 Amazon Linux 2023 com Docker: MongoDB 7.0 + Mongo Express 1.0.2 |

## Como usar

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform
export PATH="$HOME/bin:$PATH" TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
terraform init && terraform apply -auto-approve
cd .. && source exportar-outputs.sh
# ...labs...
cd terraform && terraform destroy -auto-approve
```

## Decisões de projeto

- **Sem recurso de IA:** na AWS os serviços de IA são APIs da conta. O acesso é IAM puro — a LabRole da Lambda.
- **Placeholder na Lambda:** o Terraform publica um handler mínimo; o código real, com dependências, é publicado no Lab 2. `ignore_changes` impede o `apply` seguinte de desfazer o deploy.
- **MongoDB na internet (com senha):** a Lambda roda fora da VPC e sai por IPs da AWS que mudam, então a porta 27017 fica aberta. Em produção: Lambda na VPC, Mongo em subnet privada e regra entre security groups (exercício 1.3).
- **Function URL pública:** duas permissões na política da função (`InvokeFunctionUrl` e `InvokeFunction` com `InvokedViaFunctionUrl`), exigidas desde out/2025.
