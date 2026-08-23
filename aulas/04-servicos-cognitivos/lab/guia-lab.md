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
# Confirmar autenticação
az account show --query "{nome:name, id:id}" -o table

# Criar pasta de trabalho do grupo
mkdir -p ~/qc-grupo-NN/aula04
cd ~/qc-grupo-NN/aula04

# Copiar os arquivos do lab
LAB=~/aie-cloud/aulas/04-servicos-cognitivos/lab
cp -r $LAB/terraform terraform/
cp -r $LAB/function  function/
cp -r $LAB/scripts   scripts/
cp    $LAB/exportar-outputs.sh .

ls
# terraform/  function/  scripts/  exportar-outputs.sh

cd terraform
code .
```

> **Se você já criou a pasta antes desta versão do guia**, o
> `exportar-outputs.sh` não está lá. Copie só ele:
>
> ```bash
> cp ~/aie-cloud/aulas/04-servicos-cognitivos/lab/exportar-outputs.sh ~/qc-grupo-NN/aula04/
> ```

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
cd ~/qc-grupo-NN/aula04
source exportar-outputs.sh
```

Ele imprime todos os valores. Qualquer campo `VAZIO` significa que o `apply` não
completou — resolva antes de seguir.

> **Repita este comando sempre que abrir um terminal novo.** O Cloud Shell
> encerra a sessão após 20 min de inatividade e todos os exports somem junto. Os
> erros que aparecem depois não dizem isso:
>
> | Variável vazia | Erro que você vê |
> |---|---|
> | `KEY_VAULT_NAME` | `az`: `URL has an invalid label` |
> | `MONGO_IP` | o script Python pede o IP e encerra |
> | `AI_ENDPOINT` | erro de conexão, sem explicação |
>
> **Tem que ser `source`, não `bash`.** Script executado com `bash` roda em outro
> processo, e as variáveis morrem com ele.

### Passo 3 — Conferir o que foi provisionado

No portal Azure → Resource Group `rg-qc-aula04-*`:

- 2 × Storage Account (Function runtime + dados do lab)
- 1 × App Service Plan (**FC1 — Flex Consumption**)
- 1 × **Cognitive Services** (multi-service S0 com custom subdomain)
- 1 × **Key Vault** (com segredo `ai-services-key`)
- 1 × **Container Group ACI** (MongoDB 7.0 + Mongo Express)
- 1 × **Function App** (Python 3.12, Managed Identity SystemAssigned)

> **Por que FC1 e não o Y1 clássico:** contas Azure for Students têm cota **zero**
> do plano Y1, e o erro que a Azure devolve é um `401 Unauthorized` — que parece
> problema de autenticação, mas a mensagem diz `Current Limit (Y1 VMs): 0`. O Y1
> também está sendo aposentado em set/2028. FC1 é o sucessor, o mesmo usado na
> Aula 3.

Em `cognitive.tf`, observe **`custom_subdomain_name`** — é o que permite Managed Identity autenticar no AI Services.

### Passo 4 — Semear reviews no MongoDB

```bash
cd ~/qc-grupo-NN/aula04
pip install --user pymongo -q

# Se você abriu um terminal novo desde o Passo 2, recarregue os outputs:
#   source exportar-outputs.sh
echo "MONGO_IP=${MONGO_IP:-VAZIO}"

python3 scripts/semear_reviews.py
```

> **Se der timeout de conexão**, o ACI ainda está subindo — o MongoDB leva cerca
> de um minuto depois do `apply`. Espere e repita.

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
until curl -s -o /dev/null -w "%{http_code}" "$FUNC_HOSTNAME/api/health" | grep -q "200"; do
  echo "aguardando..."; sleep 5; done
echo "Function online!"

# Transcrever
curl -s "$FUNC_HOSTNAME/api/transcrever?blob=audio-teste.wav&idioma=pt-BR" | python3 -m json.tool
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
curl -s -X POST "$FUNC_HOSTNAME/api/analisar-reviews?limit=10" | python3 -m json.tool
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
curl -s "$FUNC_HOSTNAME/api/analisar-imagem?blob=produto.jpg" | python3 -m json.tool
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
