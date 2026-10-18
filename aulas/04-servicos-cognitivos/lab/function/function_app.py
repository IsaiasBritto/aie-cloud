"""
Lambda — Aula 4 Quantum Commerce: serviços de IA da AWS por trás de uma Function URL.

Sem chave em lugar nenhum: Transcribe, Polly, Comprehend e Rekognition são APIs
da conta, autorizadas pela execution role da função (no Learner Lab, a LabRole).
A senha do MongoDB vem do Secrets Manager, lida em runtime.

Rotas das atividades (arquivos no bucket de dados):
  GET  /health
  POST /transcrever?arquivo=audio-teste.mp3&idioma=pt-BR   (Transcribe, S3 audios/)
  POST /analisar-reviews?limit=10                           (Comprehend + MongoDB)
  GET  /analisar-imagem?arquivo=produto.jpg                 (Rekognition, S3 imagens/)

Rotas que recebem o arquivo NO CORPO (usadas pelo app Streamlit):
  POST /tts     JSON {texto, voz}           -> audio/wav (Polly)
  POST /stt     corpo = bytes do áudio       -> JSON {transcricao} (Transcribe)
  POST /visao   corpo = bytes da imagem      -> JSON {tags, texto, objetos} (Rekognition)

GET também é aceito em /transcrever e /analisar-reviews para testar pelo navegador.
"""
import base64
import io
import json
import os
import time
import urllib.request
import uuid
import wave

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver, Response

logger = Logger()
app = LambdaFunctionUrlResolver(serializer=lambda o: json.dumps(o, ensure_ascii=False, default=str))

DATA_BUCKET = os.environ["DATA_BUCKET"]
MONGO_SECRET_ID = os.environ.get("MONGO_SECRET_ID", "")

# Clientes criados fora do handler: reaproveitados entre invocações quentes
s3 = boto3.client("s3")
transcribe = boto3.client("transcribe")
polly = boto3.client("polly")
comprehend = boto3.client("comprehend")
rekognition = boto3.client("rekognition")

VOZES = {"Camila": "pt-BR", "Vitoria": "pt-BR", "Thiago": "pt-BR", "Joanna": "en-US", "Lucia": "es-ES"}
FORMATOS_AUDIO = {"mp3", "mp4", "wav", "flac", "ogg", "amr", "webm", "m4a"}


# ------------------------------------------------------------------ utilidades

def _corpo_bytes() -> bytes:
    """Bytes do corpo da requisição (a Function URL manda binário em base64)."""
    ev = app.current_event.raw_event
    corpo = ev.get("body") or ""
    return base64.b64decode(corpo) if ev.get("isBase64Encoded") else corpo.encode()


def _erro(msg: str, status: int = 500, **extra) -> Response:
    return Response(status_code=status, content_type="application/json",
                    body=json.dumps({"erro": msg, **extra}, ensure_ascii=False))


def _transcrever_s3(chave: str, idioma: str, formato: str) -> dict:
    """Job assíncrono do Transcribe sobre um objeto do S3; espera terminar (áudios curtos)."""
    job = f"qc-{uuid.uuid4().hex[:8]}"
    transcribe.start_transcription_job(
        TranscriptionJobName=job,
        LanguageCode=idioma,
        MediaFormat=formato,
        Media={"MediaFileUri": f"s3://{DATA_BUCKET}/{chave}"},
    )
    inicio = time.time()
    while True:
        st = transcribe.get_transcription_job(TranscriptionJobName=job)["TranscriptionJob"]
        if st["TranscriptionJobStatus"] in ("COMPLETED", "FAILED"):
            break
        if time.time() - inicio > 50:  # a Lambda tem 60 s; deixa margem para responder
            return {"status": "IN_PROGRESS", "job": job,
                    "dica": f"áudio longo: consulte depois com aws transcribe get-transcription-job --transcription-job-name {job}"}
        time.sleep(2)

    if st["TranscriptionJobStatus"] == "FAILED":
        return {"status": "FAILED", "job": job, "motivo": st.get("FailureReason")}

    # O resultado fica num bucket da AWS, acessível por URL pré-assinada
    with urllib.request.urlopen(st["Transcript"]["TranscriptFileUri"], timeout=10) as r:
        resultado = json.load(r)
    texto = " ".join(t["transcript"] for t in resultado["results"]["transcripts"])
    return {"status": "COMPLETED", "job": job, "transcricao": texto,
            "segundos": round(time.time() - inicio, 1)}


def _visao(imagem: dict, largura: int | None = None, altura: int | None = None) -> dict:
    """Rekognition: rótulos (com caixas) + texto na imagem."""
    labels = rekognition.detect_labels(Image=imagem, MaxLabels=15, MinConfidence=60)["Labels"]
    textos = rekognition.detect_text(Image=imagem)["TextDetections"]

    tags = [{"name": l["Name"], "confidence": round(l["Confidence"] / 100, 3)} for l in labels]
    texto = "\n".join(t["DetectedText"] for t in textos if t["Type"] == "LINE")

    objetos = []
    for l in labels:
        for inst in l.get("Instances", []):
            b = inst["BoundingBox"]  # proporções 0–1 da imagem
            caixa = {"x": b["Left"], "y": b["Top"], "w": b["Width"], "h": b["Height"]}
            if largura and altura:  # converte para pixels quando sabemos o tamanho
                caixa = {"x": round(b["Left"] * largura), "y": round(b["Top"] * altura),
                         "w": round(b["Width"] * largura), "h": round(b["Height"] * altura)}
            objetos.append({"label": l["Name"], "confidence": round(inst["Confidence"] / 100, 3), "box": caixa})
    return {"tags": tags, "texto": texto, "objetos": objetos, "largura": largura, "altura": altura}


# ------------------------------------------------------------------- rotas lab

@app.get("/health")
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "qc-cognitivo",
        "rotas": ["/health", "/transcrever", "/analisar-reviews", "/analisar-imagem", "/tts", "/stt", "/visao"],
        "bucket": DATA_BUCKET,
    }


@app.get("/transcrever")
@app.post("/transcrever")
def transcrever():
    """
    Transcreve um áudio do S3 via Amazon Transcribe.
    POST /transcrever?arquivo=audio-teste.mp3&idioma=pt-BR
    """
    q = app.current_event
    arquivo = q.get_query_string_value("arquivo", "audio-teste.mp3")
    idioma = q.get_query_string_value("idioma", "pt-BR")

    formato = arquivo.rsplit(".", 1)[-1].lower()  # o formato vem da extensão
    if formato not in FORMATOS_AUDIO:
        return _erro(f"formato '{formato}' não suportado", 400, aceitos=sorted(FORMATOS_AUDIO))
    try:
        r = _transcrever_s3(f"audios/{arquivo}", idioma, formato)
        return {**r, "arquivo": arquivo, "idioma": idioma}
    except Exception as e:  # noqa: BLE001
        logger.exception("Falha em /transcrever")
        return _erro(str(e))


_mongo_client = None


def _colecao_reviews():
    """Conecta no MongoDB com a URI do Secrets Manager (uma vez por ambiente quente)."""
    global _mongo_client
    from pymongo import MongoClient  # import tardio: só esta rota precisa

    if _mongo_client is None:
        segredo = boto3.client("secretsmanager").get_secret_value(SecretId=MONGO_SECRET_ID)
        _mongo_client = MongoClient(json.loads(segredo["SecretString"])["uri"], serverSelectionTimeoutMS=5000)
    return _mongo_client["qc-db"]["reviews"]


@app.get("/analisar-reviews")
@app.post("/analisar-reviews")
def analisar_reviews():
    """
    Lê reviews ainda não analisadas do MongoDB, roda sentimento + entidades no
    Amazon Comprehend (em lote) e grava o resultado de volta no documento.
    POST /analisar-reviews?limit=10
    """
    limit = int(app.current_event.get_query_string_value("limit", "10"))
    try:
        col = _colecao_reviews()
        # O filtro evita reprocessar (e pagar de novo por) reviews já analisadas
        items = list(col.find({"sentimento": {"$exists": False}}).limit(limit))
        if not items:
            return {"msg": "Nenhuma review nova para analisar. Todas já processadas."}

        textos = [i["texto"] for i in items]
        # Lote de até 25 documentos por chamada (limite do Comprehend). O Index de
        # cada resultado é relativo ao lote: somamos o início do lote.
        sentimentos, entidades = {}, {}
        for ini in range(0, len(textos), 25):
            lote = textos[ini:ini + 25]
            for r in comprehend.batch_detect_sentiment(TextList=lote, LanguageCode="pt")["ResultList"]:
                sentimentos[ini + r["Index"]] = r
            for r in comprehend.batch_detect_entities(TextList=lote, LanguageCode="pt")["ResultList"]:
                entidades[ini + r["Index"]] = r

        resultados = []
        for idx, item in enumerate(items):
            s = sentimentos.get(idx)
            if s is None:  # item foi para a ErrorList (texto vazio, longo demais...)
                continue
            e = entidades.get(idx, {"Entities": []})
            col.update_one({"_id": item["_id"]}, {"$set": {
                "sentimento": s["Sentiment"],
                "sentimento_score": {k.lower(): round(v, 3) for k, v in s["SentimentScore"].items()},
                "entidades": [{"text": x["Text"], "type": x["Type"], "score": round(x["Score"], 3)}
                              for x in e["Entities"]],
            }})
            resultados.append({"id": item.get("id"), "produto": item.get("produto"), "sentimento": s["Sentiment"]})

        contagem = {k: sum(1 for r in resultados if r["sentimento"] == k)
                    for k in ("POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED")}
        return {"total_analisadas": len(resultados), **{k.lower(): v for k, v in contagem.items()},
                "exemplos": resultados[:3]}
    except Exception as e:  # noqa: BLE001
        logger.exception("Falha em /analisar-reviews")
        return _erro(str(e))


@app.get("/analisar-imagem")
@app.post("/analisar-imagem")
def analisar_imagem():
    """
    Analisa uma imagem do S3 com o Amazon Rekognition (rótulos, objetos e texto).
    GET /analisar-imagem?arquivo=produto.jpg
    """
    arquivo = app.current_event.get_query_string_value("arquivo", "produto.jpg")
    try:
        r = _visao({"S3Object": {"Bucket": DATA_BUCKET, "Name": f"imagens/{arquivo}"}})
        return {**r, "arquivo": arquivo, "caixas_em": "proporção da imagem (0–1)"}
    except Exception as e:  # noqa: BLE001
        logger.exception("Falha em /analisar-imagem")
        return _erro(str(e))


# --------------------------------------------------------- rotas do front-end
# Recebem o arquivo NO CORPO: o app não precisa de credencial nenhuma de S3 ou
# de IA — só fala HTTP com a Lambda, que é quem tem identidade.

@app.post("/tts")
def tts():
    """Texto → fala com o Amazon Polly. Devolve WAV 16 kHz mono."""
    corpo = app.current_event.json_body or {}
    texto = (corpo.get("texto") or "").strip()
    if not texto:
        return _erro("campo 'texto' vazio", 400)
    voz = corpo.get("voz", "Camila")
    try:
        pcm = polly.synthesize_speech(Text=texto, VoiceId=voz, Engine="neural",
                                      OutputFormat="pcm", SampleRate="16000")["AudioStream"].read()
        saida = io.BytesIO()
        with wave.open(saida, "wb") as w:  # PCM cru → WAV (o navegador toca)
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(pcm)
        return Response(status_code=200, content_type="audio/wav", body=saida.getvalue())
    except Exception as e:  # noqa: BLE001
        logger.exception("Falha em /tts")
        return _erro(str(e))


@app.post("/stt")
def stt():
    """Fala → texto. Corpo = bytes do áudio. O Transcribe lê do S3, então o áudio passa por lá."""
    audio = _corpo_bytes()
    if not audio:
        return _erro("corpo vazio — envie os bytes do áudio", 400)
    idioma = app.current_event.get_query_string_value("idioma", "pt-BR")
    formato = app.current_event.get_query_string_value("formato", "wav")
    chave = f"audios/stt-{uuid.uuid4().hex[:8]}.{formato}"
    try:
        s3.put_object(Bucket=DATA_BUCKET, Key=chave, Body=audio)
        r = _transcrever_s3(chave, idioma, formato)
        return {**r, "idioma": idioma, "bytes_recebidos": len(audio)}
    except Exception as e:  # noqa: BLE001
        logger.exception("Falha em /stt")
        return _erro(str(e))
    finally:
        s3.delete_object(Bucket=DATA_BUCKET, Key=chave)


@app.post("/visao")
def visao():
    """Análise de imagem. Corpo = bytes da imagem. Caixas em PIXELS."""
    imagem = _corpo_bytes()
    if not imagem:
        return _erro("corpo vazio — envie os bytes da imagem", 400)
    largura = altura = None
    try:
        largura, altura = _dimensoes(imagem)
    except Exception:  # noqa: BLE001 — sem dimensão, as caixas saem em proporção
        pass
    try:
        return _visao({"Bytes": imagem}, largura, altura)
    except Exception as e:  # noqa: BLE001
        logger.exception("Falha em /visao")
        return _erro(str(e))


def _dimensoes(img: bytes) -> tuple[int, int]:
    """Largura e altura de PNG/JPEG sem depender do Pillow (que não está no runtime)."""
    if img[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(img[16:20], "big"), int.from_bytes(img[20:24], "big")
    i = 2
    while i < len(img):
        if img[i] != 0xFF:
            i += 1
            continue
        marcador = img[i + 1]
        tamanho = int.from_bytes(img[i + 2:i + 4], "big")
        if marcador in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(img[i + 7:i + 9], "big"), int.from_bytes(img[i + 5:i + 7], "big")
        i += 2 + tamanho
    raise ValueError("formato de imagem não reconhecido")


@logger.inject_lambda_context
def lambda_handler(event, context):
    return app.resolve(event, context)
