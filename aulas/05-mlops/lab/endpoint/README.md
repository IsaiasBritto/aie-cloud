# Online Endpoint — Aula 5 (Atividade 4)

Publica o modelo `recomendador-qc:1` como **Managed Online Endpoint** REST.

## ⚠️ ALERTA DE CUSTO

O Online Endpoint custa **~$0,15/h** (Standard_DS2_v2). Esquecer ligado = **~$3,60/dia** do seu crédito do Azure for Students.

**SEMPRE delete o endpoint ANTES do `terraform destroy`:**

```bash
az ml online-endpoint delete --name <seu-endpoint> --yes \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Esta ordem é importante: `terraform destroy` pode falhar/demorar se o endpoint ainda estiver ativo.

## Arquivos

| Arquivo | O que é |
|---------|---------|
| [endpoint.yml](endpoint.yml) | Envelope do endpoint (nome + auth_mode) |
| [deployment.yml](deployment.yml) | Deployment `blue` apontando para `recomendador-qc:1` no environment do job |
| [request.json](request.json) | Payload de teste (produto_id=5, n_recomendacoes=5) |

## ⚠️ Antes de aplicar: substitua o nome do endpoint

O nome de Online Endpoint é **único globalmente no Azure**. Edite `endpoint.yml` E `deployment.yml` substituindo `<sufixo-unico>` por algo único, por exemplo `rec-qc-jdoe-7421`. Use o mesmo nome nos dois arquivos.

```bash
SUFIXO="$(whoami | tr -cd 'a-z0-9')-$RANDOM"
ENDPOINT_NAME="rec-qc-$SUFIXO"
echo "Endpoint: $ENDPOINT_NAME"

# Substituir nos YAMLs (sed in-place)
sed -i "s/rec-qc-<sufixo-unico>/$ENDPOINT_NAME/g" endpoint.yml deployment.yml
```

## Passo a passo

### 1. Criar o endpoint (envelope)

```bash
cd ~/aie-cloud/aulas/05-mlops/lab/endpoint

az ml online-endpoint create --file endpoint.yml \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Tempo: ~1 min.

### 2. Criar o deployment (instância de compute)

```bash
az ml online-deployment create --file deployment.yml \
  --endpoint-name "$ENDPOINT_NAME" \
  --all-traffic \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Tempo: **~5 min**. Provisão da instância DS2_v2 + pull da imagem MLflow do modelo.

> **A partir daqui o endpoint custa ~$0,15/h.** Siga direto para o teste e o destroy. Não interrompa o lab.

### 3. Testar

```bash
# Pegar URL e key
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

Esperado: JSON com lista de produtos similares ao produto 5.

### 4. DELETAR (CRÍTICO)

```bash
az ml online-endpoint delete --name "$ENDPOINT_NAME" --yes \
  -w "$WORKSPACE_NAME" -g "$RESOURCE_GROUP"
```

Aguarde ~2 min. Confirme no Studio que sumiu.

## Lição central

Online Endpoint é o **deploy "produtizado"** de um modelo — diferente de:

| Padrão | Custo idle | Cold start | Escala |
|--------|------------|------------|--------|
| **Online Endpoint dedicado** (este lab) | $$ pay-per-second mesmo idle | Não há (sempre on) | Auto-scale por CPU/req |
| **Function HTTP** (Aula 3) | $0 | 1-3 s primeira chamada | 0-200 instâncias |
| **ACI** (Aula 3) | $$ pay-per-second mesmo idle | Não há | 1 réplica fixa |

Para um agente da QC que chama o recomendador, em **MVP** a melhor escolha costuma ser **Function** consumindo o modelo embedded (sem endpoint dedicado). Em **produção com tráfego constante** alto, Online Endpoint vence pela ausência de cold start. Decisão de produto a ser justificada na entrega final.
