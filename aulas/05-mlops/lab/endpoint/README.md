# Endpoint — Aula 5 (Atividade 4)

Publica a versão **aprovada** do `recomendador-qc` (Model Registry) como endpoint do
SageMaker AI, com `scripts/implantar_endpoint.py`.

## ⚠️ Alerta de custo

| Tipo | Como cobra | Parado |
|---|---|---|
| `--tipo serverless` (padrão) | por requisição (tempo × memória) | **US$ 0** — escala a zero |
| `--tipo instancia` | ml.m5.large por hora | ~US$ 0,115/h ≈ US$ 2,76/dia |

**Sempre** apague antes do `terraform destroy`:

```bash
python3 scripts/limpar.py --registro
```

## Arquivos

| Arquivo | O que é |
|---------|---------|
| [request.json](request.json) | Payload de teste: `{"produto_id": 5, "n_recomendacoes": 5}` |
| [../codigo/inference.py](../codigo/inference.py) | `model_fn` · `input_fn` · `predict_fn` · `output_fn` — o contrato do container |

## Chamar

```bash
ENDPOINT=rec-qc-$(terraform -chdir=terraform output -raw sufixo)
aws sagemaker-runtime invoke-endpoint --endpoint-name "$ENDPOINT" \
  --content-type application/json --body fileb://endpoint/request.json resposta.json
python3 -m json.tool resposta.json
```

Resposta:

```json
{
  "produto_id": 5,
  "recomendacoes": [
    {"produto_id": 12, "nome": "Headset Gamer HyperX Cloud II", "categoria": "eletronicos",
     "preco": 599.0, "score_similaridade": 0.0379}
  ]
}
```

Sem chave de API: a chamada é assinada com a sua credencial AWS (SigV4) e autorizada
por `sagemaker:InvokeEndpoint` na política IAM. Uma Lambda chamaria do mesmo jeito,
com a role dela.
