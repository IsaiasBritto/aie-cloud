# Código da Lambda — Aula 4

API HTTP da QC com as **rotas de IA**, servida por uma Function URL. Roteamento com o **Powertools for AWS Lambda** (`LambdaFunctionUrlResolver`).

| Rota | Atividade | Serviço |
|------|-----------|---------|
| `GET /health` | — | Status + lista de rotas |
| `POST /transcrever?arquivo=...&idioma=pt-BR` | L₂ | Amazon Transcribe (áudio em `audios/` do bucket) |
| `POST /analisar-reviews?limit=10` | L₃ | Amazon Comprehend (sentimento + entidades) + MongoDB |
| `GET /analisar-imagem?arquivo=...` | L₄ | Amazon Rekognition (imagem em `imagens/`) |
| `POST /tts` | L₅ (app) | Amazon Polly — JSON `{texto, voz}` → WAV |
| `POST /stt?idioma=` | L₅ (app) | Transcribe — corpo = bytes do áudio |
| `POST /visao` | L₅ (app) | Rekognition — corpo = bytes da imagem |

## Credenciais

Nenhuma no código. A função usa a **execution role** (LabRole) para S3, Transcribe, Polly, Comprehend e Rekognition, e lê a URI do MongoDB do **Secrets Manager** (`MONGO_SECRET_ID`).

## Deploy (AWS CloudShell)

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab && source exportar-outputs.sh
cd function
rm -rf pacote && mkdir pacote
pip install -r requirements.txt -t pacote -q \
  --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
cp function_app.py pacote/
(cd pacote && zip -qr /tmp/function.zip .)
aws lambda update-function-code --function-name "$FUNC_NAME" --zip-file fileb:///tmp/function.zip
aws lambda wait function-updated --function-name "$FUNC_NAME"
```

> **Por que os flags no `pip`?** O CloudShell roda outro Python (3.9). Sem `--platform`/`--python-version`, um pacote com parte compilada (o `pymongo`) viria montado para o Python errado.

## Testar

```bash
curl -s "${FUNC_URL}health" | python3 -m json.tool
curl -s -X POST "${FUNC_URL}transcrever?arquivo=audio-teste.mp3" | python3 -m json.tool
curl -s -X POST "${FUNC_URL}analisar-reviews?limit=10" | python3 -m json.tool
curl -s "${FUNC_URL}analisar-imagem?arquivo=produto.jpg" | python3 -m json.tool
```
