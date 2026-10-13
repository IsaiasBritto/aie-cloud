# Scripts auxiliares — Aula 4

| Script | Quando usar |
|--------|-------------|
| [semear_reviews.py](semear_reviews.py) | **Lab 1** — insere 10 reviews no MongoDB da EC2 (tem uma falha de segurança de propósito: ache e conserte) |
| [gerar_audio_tts.py](gerar_audio_tts.py) | **Lab 2** — gera `/tmp/audio-teste.mp3` com o Amazon Polly (voz Camila) para testar a rota `/transcrever` |

## Como usar (AWS CloudShell)

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab
source exportar-outputs.sh            # MONGO_IP, DATA_BUCKET, FUNC_URL...

pip install --user boto3 pymongo -q

python3 scripts/semear_reviews.py
python3 scripts/gerar_audio_tts.py
aws s3 cp /tmp/audio-teste.mp3 s3://$DATA_BUCKET/audios/audio-teste.mp3
```

Depois teste: `curl -X POST "${FUNC_URL}transcrever?arquivo=audio-teste.mp3"`.

> Nenhum dos dois scripts usa chave de API: o boto3 pega a credencial da sessão do CloudShell (LabRole). O `semear_reviews.py`, porém, tem a **senha do MongoDB no código** — é o exercício.
