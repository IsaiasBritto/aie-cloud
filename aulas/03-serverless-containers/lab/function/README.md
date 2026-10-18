# Código da Lambda — Aula 3

Duas versões da API HTTP de catálogo da QC, em Python 3.12, expostas por uma **Function URL**:

| Pasta | Quando | Características |
|-------|--------|-----------------|
| [v1-mock/](v1-mock/) | L₁ | 5 produtos no próprio código. Sem dependências. Valida que o deploy funciona. |
| [v2-s3/](v2-s3/) | L₂ | Lê os 20 produtos reais de `catalogo/produtos.csv` no **S3**, com a credencial da execution role (LabRole) — **sem chave no código**. |

Cada pasta é **self-contained** (`lambda_function.py` + `requirements.txt`). O handler configurado no Terraform é `lambda_function.lambda_handler`.

## Rotas

| Rota | O que faz |
|------|-----------|
| `GET /` ou `GET /produtos?categoria=&nome=` | Lista os produtos, com filtros opcionais |
| `GET /health` | Status e origem dos dados (`mock` ou `s3`) |

## Como fazer deploy

```bash
# Nome da função
FUNC_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw lambda_name)

# v1 (mock)
cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v1-mock
zip -qr /tmp/v1-mock.zip . && aws lambda update-function-code --function-name "$FUNC_NAME" --zip-file fileb:///tmp/v1-mock.zip

# v2 (S3)
cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v2-s3
zip -qr /tmp/v2-s3.zip . && aws lambda update-function-code --function-name "$FUNC_NAME" --zip-file fileb:///tmp/v2-s3.zip
```

Cada `update-function-code` substitui o código da função. Espere `aws lambda wait function-updated --function-name "$FUNC_NAME"` antes de testar.

## Como testar

```bash
FUNC_URL=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_url)

curl -s "${FUNC_URL}health" | python3 -m json.tool
curl -s "${FUNC_URL}produtos?categoria=moveis" | python3 -m json.tool
curl -s "${FUNC_URL}produtos?nome=cadeira" | python3 -m json.tool
```

> **Cold start:** a primeira chamada depois de um tempo parada leva ~1 s. As seguintes são milissegundos.

## Lição central

Compare a v1 com a v2: a v2 **lê do S3 com a identidade da função** e em nenhum momento aparece chave, senha ou segredo no código. É o padrão para tudo que os agentes da QC vão consumir.
