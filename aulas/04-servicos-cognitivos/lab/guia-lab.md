# Guia de Laboratório — Aula 4
## Serviços Cognitivos & APIs

**Disciplina:** Cloud & Cognitive Environments
**MBA:** AI Engineering & Multi-Agents — FIAP
**Plataforma:** Microsoft Azure (Azure for Students)
**Ambiente:** **Azure Cloud Shell** — tudo no browser

---

## Visão geral do lab

```
Preparação   — terraform apply (infra autocontida, sem deps de aulas anteriores)  ~10 min
Atividade 1  — Provisionar recursos e semear MongoDB com reviews QC               ~15 min  (L₁)
Atividade 2  — Speech-to-Text com áudio gerado via TTS                            ~30 min  (L₂)
Atividade 3  — Language: pipeline de reviews QC (MongoDB ACI)                     ~30 min  (L₃)
Atividade 4  — Vision: classificação + OCR de imagem de produto                   ~20 min  (L₄)
Wrap-up      — terraform destroy + verificação custo zero                         ~5 min
```

> **Nota de região:** Esta aula usa `eastus2` (padrão). Contas **Azure for Students** têm políticas de região — se `eastus2` falhar no `terraform apply`, tente `westeurope`.

> **Regra de ouro:** `terraform destroy` ao final. AI Services S0 cobra por chamada — sem chamadas = sem custo extra.

---

## Preparação (5 min — antes do L₁)


```bash
# Passo 1 — Clone e atualize o repositório
cd ~
git clone https://github.com/isaiasbritto/aie-cloud.git 2>/dev/null || (cd ~/aie-cloud && git pull origin main)

# Confirmar autenticação
az account show --query "{nome:name, id:id}" -o

# Criar pasta de trabalho do grupo
mkdir -p ~/qc-grupo-NN/aula04
cd ~/qc-grupo-NN/aula04

# Copiar os arquivos do lab
cp -r ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform terraform/
cp -r ~/aie-cloud/aulas/04-servicos-cognitivos/lab/function  function/
cp -r ~/aie-cloud/aulas/04-servicos-cognitivos/lab/scripts   scripts/

cd terraform
code .
```

---

## Atividade 1 — Provisionar Infraestrutura (Autocontida)

**Objetivo:** Criar todos os recursos da Aula 4 com um único `terraform apply`.
Inclui: AI Services, Key Vault, Storage, MongoDB via ACI, e Function App.

### Por que ACI em vez de VM para MongoDB?

Azure Container Instances é mais simples, mais rápido (inicialização em ~2 min), e evita problemas de capacidade de SKU de VM que ocorrem em algumas regiões com contas Azure for Students.

### Passo 1 — Aplicar Terraform

```bash
cd ~/qc-grupo-NN/aula04/terraform
terraform init
terraform apply -auto-approve
```

Tempo: ~5-8 min. Observe os recursos sendo criados no portal Azure em paralelo.

### Passo 2 — Exportar outputs

```bash
export AI_ENDPOINT=$(terraform output -raw ai_endpoint)
export AI_REGION="eastus2"
export KEY_VAULT_NAME=$(terraform output -raw key_vault_name)
export DATA_STORAGE=$(terraform output -raw data_storage_account_name)
export MONGO_IP=$(terraform output -raw mongodb_public_ip)
export FUNC_NAME=$(terraform output -raw function_app_name)
export HOSTNAME=$(terraform output -raw function_app_hostname)

echo "AI Services: $AI_ENDPOINT"
echo "MongoDB IP:  $MONGO_IP"
echo "Mongo Express: http://$MONGO_IP:8081"
echo "Function:    $HOSTNAME"
```

### Passo 3 — Conferir o que foi provisionado

No portal Azure → Resource Group `rg-qc-aula04-*`:

- 2 × Storage Account (Function runtime + dados do lab)
- 1 × App Service Plan (Y1 Consumption)
- 1 × **Cognitive Services** (multi-service S0 com custom subdomain)
- 1 × **Key Vault** (com segredo `ai-services-key`)
- 1 × **Container Group ACI** (MongoDB 7.0 + Mongo Express)
- 1 × **Function App** (Python 3.11, Managed Identity SystemAssigned)

Em `cognitive.tf`, observe **`custom_subdomain_name`** — é o que permite Managed Identity autenticar no AI Services.

### Passo 4 — Semear reviews no MongoDB

```bash
cd ~/qc-grupo-NN/aula04
pip install --user pymongo -q

export MONGO_IP  # já exportado acima
python3 scripts/semear_reviews.py
```

Saída esperada:
```
✓ MongoDB pronto!
✓ 10 reviews inseridas em qc-db.reviews
```

Abra **`http://<MONGO_IP>:8081`** no browser — abre direto, sem login. Navegue até `qc-db → reviews` para ver os documentos.

**✅ Checkpoint L₁:** 10 reviews visíveis no Mongo Express?

---

## Atividade 2 — Speech-to-Text

**Objetivo:** Gerar um áudio em PT-BR via TTS e transcrevê-lo com Azure Speech STT.

### Passo 1 — Exportar a chave do AI Services

```bash
export AI_KEY=$(az keyvault secret show \
  --vault-name "$KEY_VAULT_NAME" \
  --name ai-services-key \
  --query value -o tsv)

echo "AI_KEY exportado (${#AI_KEY} chars)"
```

### Passo 2 — Gerar áudio via TTS

```bash
cd ~/qc-grupo-NN/aula04
pip install --user requests -q

python3 scripts/gerar_audio_tts.py
# Saída: /tmp/audio-teste.wav
```

### Passo 3 — Upload do áudio para Blob

```bash
az storage blob upload \
  --account-name "$DATA_STORAGE" \
  --container-name audios \
  --name audio-teste.wav \
  --file /tmp/audio-teste.wav \
  --auth-mode login \
  --overwrite

echo "✓ audio-teste.wav no container 'audios'"
```

### Passo 4 — Deploy da Function App

```bash
cd ~/qc-grupo-NN/aula04/function

# Empacotar e publicar (remote build instala o requirements.txt no Azure)
zip -r /tmp/function.zip .

az functionapp deployment source config-zip \
  --resource-group $(cd ../terraform && terraform output -raw resource_group_name) \
  --name "$FUNC_NAME" \
  --src /tmp/function.zip \
  --build-remote true \
  --timeout 300
```

Tempo: ~3-5 min. O Azure instala os pacotes do `requirements.txt` no servidor — não é necessário ter nada instalado localmente.

### Passo 5 — Testar STT

```bash
# Aguardar cold start da Function
until curl -s -o /dev/null -w "%{http_code}" "$HOSTNAME/api/health" | grep -q "200"; do
  echo "aguardando..."; sleep 5; done
echo "Function online!"

# Transcrever
curl -s "$HOSTNAME/api/transcrever?blob=audio-teste.wav&idioma=pt-BR" | python3 -m json.tool
```

Esperado:
```json
{
  "transcricao": "A Quantum Commerce é uma plataforma de e-commerce que opera em doze países...",
  "idioma": "pt-BR",
  "status_stt": "Success"
}
```

> **Por que chave para Speech e MI para Language/Vision?** O endpoint de Speech STT exige a role `Cognitive Services Speech User` separada para AAD/MI. Para evitar complexidade extra, a aula usa a chave (armazenada no Key Vault e lida pela Function via KV reference) para o Speech, e MI para os demais serviços.

**✅ Checkpoint L₂:** Transcrição retornou texto coerente em PT-BR?

---

## Atividade 3 — Language: Pipeline de Reviews

**Objetivo:** Analisar sentimento e entidades das reviews do MongoDB com Azure Language via Managed Identity.

### Passo 1 — Chamar a rota `/analisar-reviews`

```bash
curl -s -X POST "$HOSTNAME/api/analisar-reviews?limit=10" | python3 -m json.tool
```

Esperado:
```json
{
  "total_analisadas": 10,
  "positivas": 6,
  "negativas": 4,
  "neutras": 0,
  "exemplos": [...]
}
```

> **Nota de batch:** A API de Language aceita no máximo **5 documentos por chamada** no tier S0. O código divide em batches de 5 automaticamente.

### Passo 2 — Validar no Mongo Express

Abra `http://<MONGO_IP>:8081` → `qc-db → reviews`. Cada review agora tem os campos:
- `sentimento_label`: `"positive"` / `"negative"` / `"neutral"`
- `sentimento_score`: `{"positive": 0.98, "neutral": 0.01, "negative": 0.01}`
- `entidades`: `[{"text": "Quantum Commerce", "category": "Organization"}, ...]`

> Segunda chamada retorna `"msg": "Nenhuma review nova para analisar. Todas já processadas."` — comportamento idempotente correto.

**✅ Checkpoint L₃:** Reviews enriquecidas com sentimento e entidades no Mongo Express?

---

## Atividade 4 — Vision: Classificação + OCR

**Objetivo:** Analisar uma imagem de produto com Azure AI Vision 4.0 via Managed Identity.

### Passo 1 — Upload de imagem de produto

```bash
# Baixar uma imagem de produto (JPG/PNG)
curl -sL "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800" \
  -o /tmp/produto.jpg 2>/dev/null || \
  echo "Use o botão de upload do Cloud Shell para enviar uma imagem do seu computador"

# Upload para Blob
az storage blob upload \
  --account-name "$DATA_STORAGE" \
  --container-name imagens \
  --name produto.jpg \
  --file /tmp/produto.jpg \
  --auth-mode login \
  --overwrite

echo "✓ produto.jpg no container 'imagens'"
```

### Passo 2 — Testar Vision

```bash
curl -s "$HOSTNAME/api/analisar-imagem?blob=produto.jpg" | python3 -m json.tool
```

Esperado:
```json
{
  "caption": "",
  "tags": [
    {"name": "furniture", "confidence": 0.982},
    {"name": "chair", "confidence": 0.967}
  ],
  "texto_extraido": "",
  "objetos_detectados": [{"label": "chair", "box": {"x": 10, "y": 5, "w": 200, "h": 300}}],
  "blob": "produto.jpg"
}
```

> **Nota sobre Caption:** O recurso `Caption` da Vision 4.0 não está disponível em `eastus2`. Para Caption/Dense Captions, use `eastus`, `westus2`, ou `westeurope` (verifique a política de região da sua conta Azure for Students).

**✅ Checkpoint L₄:** Imagem analisada com tags retornadas?

---

## Wrap-up — Destroy e Custo Zero (5 min)

### Passo 1 — Destruir todos os recursos da Aula 4

```bash
cd ~/qc-grupo-NN/aula04/terraform
terraform destroy -auto-approve
```

Tempo: ~2-3 min. Todos os 17 recursos são destruídos.

### Passo 2 — Commitar no repo do grupo

```bash
cd ~/qc-grupo-NN
git add aula04/
git commit -m "feat(aula04): pipeline cognitivo QC (Speech + Language + Vision)"
git push origin main
```

### Passo 3 — Verificar custo

Portal → **Cost Management** → filtrar por tag `aula=4`.
Esperado: < R$1 (AI Services S0 só cobra por chamadas; as poucas chamadas do lab custam centavos).

---

## Conexão com o Projeto Quantum Commerce

A Function da QC agora tem **4 tools cognitivas**:

```
GET  /api/health                    ← status e roteamento
GET  /api/transcrever?blob=...      ← STT em PT-BR (atendimento por voz)
POST /api/analisar-reviews?limit=N  ← Language (sentimento de reviews)
GET  /api/analisar-imagem?blob=...  ← Vision (busca visual de produtos)
```

Os agentes podem agora:
- Ouvir o cliente no atendimento por voz → `transcrever`
- Entender o sentimento das reviews para recomendar produtos → `analisar-reviews`
- Analisar a imagem que o cliente enviou para encontrar o produto → `analisar-imagem`

---

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| `RequestDisallowedByAzure` no `terraform apply` | Política de região da conta Azure for Students | Tentar outra região: `terraform apply -auto-approve -var="location=westeurope"` |
| `SkuNotAvailable` | Capacidade esgotada na região | Já resolvido: usamos ACI em vez de VM para MongoDB |
| Speech 401 em `/transcrever` | `AI_KEY` não resolvido (KV reference falhou) | Verificar se a Function tem a role `Key Vault Secrets User` — `terraform output` e portal → Function → Identity |
| Language batch error | Limite de 5 docs/batch no tier S0 | Já corrigido no código com loop de batches de 5 |
| Vision `Caption` não disponível | Caption não suportado em `eastus2` | Já removido do código — usar Tags + OCR. Para Caption: `westeurope` |
| `/analisar-reviews` "Nenhuma review nova" | Todas já analisadas | Correto — rodar `semear_reviews.py` novamente para reinserir |
| MongoDB não responde no semear | ACI ainda iniciando | Aguardar 2-3 min após `terraform apply`; o script tenta automaticamente 10x |
| Function 404 após deploy | Build remoto não concluído | Aguardar cold start (~3-5 min); verificar se `--build-remote true` foi usado |
| `az storage blob upload` retorna 403 | Role RBAC ainda propagando | Aguardar 1-2 min e tentar novamente |

---

## Tarefa Pós-Aula

Antes da Aula 5:

1. **Commitar `aula04/` no repo do grupo**
2. **Atualizar `entrega-grupo-aula04.md`** com:
   - Trecho da transcrição obtida em PT-BR
   - Distribuição de sentimentos das 10 reviews (positivas / negativas / neutras)
   - JSON de saída de uma análise de imagem de produto da QC
   - Diagrama atualizado da arquitetura QC com a camada cognitiva
3. **Resolver pelo menos N1 + N2** dos exercícios

---

## Referências

- [Azure AI Services — autenticação com Entra ID](https://learn.microsoft.com/azure/ai-services/authentication?tabs=powershell)
- [Speech REST API — STT](https://learn.microsoft.com/azure/ai-services/speech-service/rest-speech-to-text)
- [Language SDK Python](https://learn.microsoft.com/python/api/overview/azure/ai-textanalytics-readme)
- [Image Analysis SDK 4.0](https://learn.microsoft.com/azure/ai-services/computer-vision/how-to/call-analyze-image-40)
- [Custom subdomain — requisito para MI](https://learn.microsoft.com/azure/ai-services/cognitive-services-custom-subdomains)
- [Azure Container Instances — múltiplos containers](https://learn.microsoft.com/azure/container-instances/container-instances-multi-container-yaml)

---

*Lab validado em 21/06/2026 — região eastus2, Azure for Students | Cloud & Cognitive Environments | Aula 4*
