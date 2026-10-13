# Guia de Laboratório — Aula 4
## Serviços de IA da AWS & APIs

**Disciplina:** Cloud & Cognitive Environments
**MBA:** AI Engineering & Multi-Agents — FIAP
**Plataforma:** Amazon Web Services (AWS Academy Learner Lab)
**Ambiente:** **AWS CloudShell** — tudo no browser · região `us-east-1`

---

## Visão geral do lab

```
Atividade 1  — terraform apply + semear reviews no MongoDB                       ~25 min  (L₁)
Atividade 2  — Polly (texto → fala) e Transcribe (fala → texto) via Lambda       ~30 min  (L₂)
Atividade 3  — Comprehend: pipeline de reviews (sentimento + entidades)          ~30 min  (L₃)
Atividade 4  — Rekognition: rótulos, objetos e texto de imagem de produto        ~20 min  (L₄)
Atividade 5  — Front-end Streamlit: os serviços + comparação de arquitetura      ~30 min  (L₅)
Wrap-up      — terraform destroy + verificação de custo                          ~5 min
```

> **Na AWS os serviços de IA não precisam de recurso provisionado:** Transcribe, Polly, Comprehend e Rekognition são APIs da conta, liberadas por IAM. O Terraform sobe só o que é seu: bucket, Lambda, MongoDB e o segredo.

> **Regra de ouro:** `terraform destroy` ao final. Os serviços de IA cobram por chamada — sem chamadas, sem custo; a EC2 do Mongo cobra por hora.

---

## Atividade 1 — Provisionar e semear (L₁)

### Passo 1 — Repositório e Terraform

```bash
cd ~ && rm -rf aie-cloud
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/04-servicos-cognitivos/lab/terraform

bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
export PATH="$HOME/bin:$PATH" TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"

terraform init
terraform apply -auto-approve
```

Enquanto o Terraform trabalha (~3 min), leia os arquivos:

| Arquivo | O que define |
|---------|--------------|
| [main.tf](terraform/main.tf) | Providers, tags, locals (credenciais Mongo), data source da LabRole |
| [variables.tf](terraform/variables.tf) | `region` (padrão `us-east-1`) |
| [outputs.tf](terraform/outputs.tf) | Todos os outputs consumidos pelo guia e pelos scripts |
| [storage.tf](terraform/storage.tf) | Bucket de dados + prefixos `audios/` e `imagens/` |
| [lambda.tf](terraform/lambda.tf) | Lambda Python 3.12 + Function URL + LabRole (timeout 60 s) |
| (nenhum) | Nada a criar: Transcribe, Polly, Comprehend e Rekognition são APIs da conta |
| [secrets.tf](terraform/secrets.tf) | Secrets Manager com as credenciais do Mongo |
| [mongodb.tf](terraform/mongodb.tf) | EC2 com Docker: MongoDB 7.0 + Mongo Express 1.0.2 |

### Passo 2 — Exportar os outputs

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab
source exportar-outputs.sh
```

> Abriu um terminal novo? Rode `source exportar-outputs.sh` de novo — as variáveis não sobrevivem à sessão.

### Passo 3 — Semear reviews no MongoDB

```bash
pip install --user pymongo -q

# Obtém o IP do Mongo DB (o exportar-outputs.sh já fez isso)
export MONGO_IP=$(cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform && terraform output -raw mongodb_public_ip)
echo "IP do Mongo: $MONGO_IP"

# Execução do script (confira o diretório atual: lab/)
python3 scripts/semear_reviews.py
```

Abra o Mongo Express (`http://$MONGO_IP:8081`, usuário `qcadmin`, senha `QCview2024!`) → `qc-db` → `reviews`.

> **Você identificou alguma falha de segurança no `semear_reviews.py`? Como consertar?** (compare com a Lambda, que lê a mesma conexão do Secrets Manager)

**✅ Checkpoint L₁:** 10 reviews em `qc-db.reviews`?

---

## Atividade 2 — Texto → fala e fala → texto (L₂)

### Passo 1 — Gerar um áudio com o Amazon Polly

```bash
pip install --user boto3 -q

# Sem chave: o boto3 usa a credencial do CloudShell (LabRole)
aws sts get-caller-identity --query Arn --output text

python3 scripts/gerar_audio_tts.py      # → /tmp/audio-teste.mp3
```

### Passo 2 — Copiar os áudios para o bucket

```bash
echo "Data Bucket: $DATA_BUCKET"

aws s3 cp /tmp/audio-teste.mp3 s3://$DATA_BUCKET/audios/audio-teste.mp3

# Um trecho real de podcast da BBC Brasil (já no repositório)
aws s3 cp ~/aie-cloud/aulas/04-servicos-cognitivos/lab/data/bbc_exemplo.mp3 \
  s3://$DATA_BUCKET/audios/bbc_exemplo.mp3
```

> **Challenge:** o formato do áudio vem da extensão do arquivo. E com um `.m4a`?

### Passo 3 — Deploy da Lambda

```bash
echo "Lambda: $FUNC_NAME"
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/function

# Empacota COM as dependências (a Lambda não instala o requirements.txt sozinha).
# Os flags baixam pacotes compilados para o Python 3.12 da Lambda — o CloudShell tem outro Python.
rm -rf pacote && mkdir pacote
pip install -r requirements.txt -t pacote -q \
  --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
cp function_app.py pacote/
(cd pacote && zip -qr /tmp/function.zip .)
aws lambda update-function-code --function-name "$FUNC_NAME" --zip-file fileb:///tmp/function.zip
aws lambda wait function-updated --function-name "$FUNC_NAME"
```

Explore o [function_app.py](function/function_app.py): as rotas `health` e `transcrever` (Lab 2), `analisar-reviews` (Lab 3) e `analisar-imagem` (Lab 4).

### Passo 4 — Transcrever

```bash
curl -s "${FUNC_URL}health" | python3 -m json.tool

curl -s -X POST "${FUNC_URL}transcrever?arquivo=audio-teste.mp3&idioma=pt-BR" | python3 -m json.tool
curl -s -X POST "${FUNC_URL}transcrever?arquivo=bbc_exemplo.mp3" | python3 -m json.tool
```

O Transcribe é **assíncrono**: a rota inicia um job e espera ele terminar (áudios curtos levam ~10-20 s). Áudio longo devolve `IN_PROGRESS` com o nome do job — consulte depois com `aws transcribe get-transcription-job`.

> ⚠️ **Esperado, não é falha:** a primeira chamada leva ~1-2 s a mais (cold start).

**✅ Checkpoint L₂:** a transcrição do `audio-teste.mp3` volta em português?

---

## Atividade 3 — Comprehend: pipeline de reviews (L₃)

### Passo 1 — Analisar as reviews

```bash
echo "URL para avaliar reviews: ${FUNC_URL}analisar-reviews?limit=10"
curl -s -X POST "${FUNC_URL}analisar-reviews?limit=10" | python3 -m json.tool
```

A rota lê do MongoDB as reviews **sem** o campo `sentimento` (filtro `{"sentimento": {"$exists": false}}` — evita reprocessar e pagar de novo), roda `batch_detect_sentiment` e `batch_detect_entities` do Comprehend em lotes de até 25, e grava o resultado de volta em cada documento.

Rode de novo: a resposta é "Nenhuma review nova para analisar" — o filtro funcionou.

### Passo 2 — Validar no Mongo Express

`qc-db` → `reviews`: cada documento ganhou `sentimento`, `sentimento_score` e `entidades`.

**✅ Checkpoint L₃:** a distribuição de sentimentos bate com as estrelas das reviews?

---

## Atividade 4 — Rekognition: imagem de produto (L₄)

### Passo 1 — Upload da imagem

```bash
aws s3 cp ~/aie-cloud/aulas/04-servicos-cognitivos/lab/data/produto.jpg \
  s3://$DATA_BUCKET/imagens/produto.jpg
```

### Passo 2 — Analisar

```bash
echo "URL para analisar imagem: ${FUNC_URL}analisar-imagem?arquivo=produto.jpg"
curl -s "${FUNC_URL}analisar-imagem?arquivo=produto.jpg" | python3 -m json.tool
```

A resposta traz `tags` (rótulos com confiança), `objetos` (rótulos com caixa — em proporção da imagem, de 0 a 1) e `texto` (o que o Rekognition leu na imagem).

**✅ Checkpoint L₄:** o Rekognition reconheceu o produto e leu o texto da imagem?

---

## Atividade 5 — Front-end: QC Cognitive Studio (~30 min)

**Objetivo:** sair do `curl` e ver os serviços numa interface — e comparar **duas arquiteturas de acesso à IA** com o mesmo resultado e riscos completamente diferentes.

### Passo 1 — Rodar na SUA máquina

Não é no CloudShell: o navegador só libera o microfone em `localhost` ou HTTPS.

```bash
# no seu notebook, dentro do repositório clonado
cd aulas/04-servicos-cognitivos/lab/app
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`.

### Passo 2 — Preencher a barra lateral

**Comece preenchendo só a Function URL** (`echo $FUNC_URL` no CloudShell), escolha **Via Lambda** e use as três primeiras abas. Elas funcionam sem nenhuma credencial no seu notebook — essa é a demonstração.

Só depois preencha as credenciais (Learner Lab → **AWS Details** → **AWS CLI: Show**) e o `DATA_BUCKET`, e experimente **Comparar os dois**.

### Passo 3 — Explorar

| Aba | O que fazer |
|---|---|
| 🔊 Texto → Fala | Sintetize uma frase com o Polly. Baixe o WAV — ele serve de entrada para a próxima aba |
| 🎤 Fala → Texto | Grave do microfone ou envie o WAV baixado (o Transcribe processa em lote: aguarde) |
| 🖼️ Visão + Espacial | Envie uma foto de produto: rótulos, texto e caixas desenhadas sobre a imagem |
| 🏛️ Arquitetura | A comparação e as perguntas de discussão |

### Passo 4 — Comparar (10 min, em grupo)

Marque **Comparar os dois**. Os resultados são iguais; os tempos, não — o caminho direto tem um salto a menos.

**A pergunta que fecha a aula:** se o caminho direto é mais rápido e mais simples, por que a arquitetura da disciplina insiste no outro? Discuta com a tabela da aba **Arquitetura**.

**✅ Checkpoint L₅:** as três primeiras abas funcionam com as credenciais em branco? Você consegue explicar por quê?

---

## Wrap-up — Destroy e custo zero (5 min)

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform
terraform destroy -auto-approve
```

Confira o crédito consumido na página do Learner Lab. Os jobs do Transcribe ficam listados no console por 90 dias, mas não cobram nada depois de concluídos.

---

## Conexão com o projeto Quantum Commerce

A Lambda da QC agora tem **tools de IA**:

```
GET  /health                              ← status
POST /transcrever?arquivo=...&idioma=...  ← Transcribe (atendimento por voz)
POST /analisar-reviews?limit=N            ← Comprehend (sentimento das reviews)
GET  /analisar-imagem?arquivo=...         ← Rekognition (busca visual de produtos)
```

Os agentes podem: ouvir o cliente no atendimento por voz, entender o sentimento das reviews para recomendar produtos e analisar a foto que o cliente enviou para achar o produto.

---

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| `{"status": "placeholder"}` em qualquer rota | O código real ainda não foi publicado | Passo 3 da Atividade 2 |
| `Runtime.ImportModuleError: No module named 'aws_lambda_powertools'` | O zip foi feito sem as dependências | Refaça o Passo 3 (pasta `pacote/` com `pip install -t`) |
| `403 Forbidden` na Function URL | Falta uma das duas permissões da URL pública | `terraform apply` de novo; `aws lambda get-policy --function-name "$FUNC_NAME"` |
| `/transcrever` → `BadRequestException ... media format` | Extensão diferente do formato real do áudio | Renomeie o arquivo ou converta |
| `/transcrever` → `IN_PROGRESS` | Áudio longo para os 60 s da Lambda | `aws transcribe get-transcription-job --transcription-job-name <job>` |
| `/analisar-reviews` → `ServerSelectionTimeoutError` | EC2 do Mongo ainda subindo | Aguarde 2-3 min após o apply |
| `/analisar-reviews` → "Nenhuma review nova" | Todas já analisadas | Correto — rode `semear_reviews.py` para reinserir |
| `semear_reviews.py` não conecta | `MONGO_IP` vazio | `source exportar-outputs.sh` |
| `AccessDeniedException` no Comprehend/Rekognition | Sessão do Learner Lab expirou | **Start Lab** e CloudShell novo |
| Mongo Express pede senha | Basic auth ligado de propósito | `qcadmin` / `QCview2024!` |

---

## Tarefa pós-aula

1. Atualizar o `entrega-grupo-aula04.md` com:
   - Trecho da transcrição em PT-BR
   - Distribuição de sentimentos das 10 reviews
   - JSON de uma análise de imagem de produto
   - Diagrama da arquitetura QC com a camada de IA
2. Resolver pelo menos N1 + N2 dos exercícios

---

## Referências

- [Amazon Transcribe — jobs em lote](https://docs.aws.amazon.com/transcribe/latest/dg/batch-med-transcription.html)
- [Amazon Polly — vozes disponíveis](https://docs.aws.amazon.com/polly/latest/dg/available-voices.html)
- [Amazon Comprehend — idiomas suportados](https://docs.aws.amazon.com/comprehend/latest/dg/supported-languages.html)
- [Amazon Rekognition — rótulos e texto](https://docs.aws.amazon.com/rekognition/latest/dg/labels.html)
- [Powertools for AWS Lambda (Python) — Event Handler](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/)
- [Pacotes .zip de Lambda com dependências](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)
