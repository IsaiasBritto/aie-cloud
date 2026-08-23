"""
Function App — Aula 4 Quantum Commerce
Rotas cognitivas via Managed Identity (Language, Vision) e Key Vault (Speech):
  GET  /api/health
  GET  /api/transcrever?blob=<nome>&container=audios&idioma=pt-BR
  POST /api/analisar-reviews?limit=10
  GET  /api/analisar-imagem?blob=<nome>&container=imagens

Rotas que recebem o arquivo NO CORPO da requisicao (usadas pelo app Streamlit):
  POST /api/tts     JSON {texto, voz, idioma}  -> audio/wav
  POST /api/stt     corpo = bytes do WAV       -> JSON {transcricao}
  POST /api/visao   corpo = bytes da imagem    -> JSON {tags, texto, objetos}

As rotas com "blob=" leem do Storage por Managed Identity e servem as atividades
do lab. As rotas acima recebem os bytes direto, para que um front-end nao precise
de credencial de Storage — so fala HTTP com a Function.
"""
import json
import logging
import os
import requests
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

AI_ENDPOINT          = os.environ["AI_ENDPOINT"]
AI_REGION            = os.environ.get("AI_REGION", "eastus2")
AI_KEY               = os.environ.get("AI_KEY", "")  # Key Vault reference resolvida pelo runtime
DATA_STORAGE_ACCOUNT = os.environ["DATA_STORAGE_ACCOUNT"]
MONGODB_URI          = os.environ["MONGODB_URI"]

_credential = DefaultAzureCredential()
_blob_service = BlobServiceClient(
    f"https://{DATA_STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=_credential,
)


def _get_speech_token(region: str) -> str:
    """
    Troca a subscription key (do Key Vault) por speech token.
    Speech exige a role 'Cognitive Services Speech User' para MI — usamos key por simplicidade.
    """
    resp = requests.post(
        f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
        headers={"Ocp-Apim-Subscription-Key": AI_KEY, "Content-Length": "0"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.text


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({
            "status": "ok",
            "service": "qc-cognitive",
            "rotas": [
                "/api/health", "/api/transcrever", "/api/analisar-reviews", "/api/analisar-imagem",
                "/api/tts", "/api/stt", "/api/visao",
            ],
            "ai_endpoint": AI_ENDPOINT,
        }),
        mimetype="application/json",
    )


@app.route(route="transcrever", methods=["GET", "POST"])
def transcrever(req: func.HttpRequest) -> func.HttpResponse:
    """
    Transcreve áudio WAV do Blob via Azure Speech STT (REST API).
    GET /api/transcrever?blob=audio-teste.wav&idioma=pt-BR
    """
    blob_name = req.params.get("blob", "audio-teste.wav")
    container = req.params.get("container", "audios")
    idioma    = req.params.get("idioma", "pt-BR")

    try:
        # 1. Baixar áudio do Blob via MI
        blob_client = _blob_service.get_blob_client(container=container, blob=blob_name)
        audio_bytes = blob_client.download_blob().readall()

        # 2. Obter speech token via key (do Key Vault)
        token = _get_speech_token(AI_REGION)
        resp = requests.post(
            f"https://{AI_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                "Accept": "application/json",
            },
            params={"language": idioma, "format": "detailed"},
            data=audio_bytes,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        transcricao = ""
        if "NBest" in data and data["NBest"]:
            transcricao = data["NBest"][0].get("Display", "")
        elif "DisplayText" in data:
            transcricao = data["DisplayText"]

        return func.HttpResponse(
            json.dumps({
                "transcricao": transcricao,
                "idioma": idioma,
                "blob": blob_name,
                "status_stt": data.get("RecognitionStatus", ""),
            }, ensure_ascii=False),
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Falha em /transcrever")
        return func.HttpResponse(json.dumps({"erro": str(e)}), mimetype="application/json", status_code=500)


@app.route(route="analisar-reviews", methods=["GET", "POST"])
def analisar_reviews(req: func.HttpRequest) -> func.HttpResponse:
    """
    Lê reviews do MongoDB, analisa sentimento + entidades via Language (MI),
    e atualiza os documentos com os resultados.
    POST /api/analisar-reviews?limit=10
    """
    limit = int(req.params.get("limit", 10))

    try:
        from pymongo import MongoClient
        from azure.ai.textanalytics import TextAnalyticsClient

        # 1. MongoDB
        mongo = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        col = mongo["qc-db"]["reviews"]

        items = list(col.find({"sentimento_label": {"$exists": False}}).limit(limit))
        if not items:
            return func.HttpResponse(
                json.dumps({"msg": "Nenhuma review nova para analisar. Todas já processadas."}),
                mimetype="application/json",
            )

        # 2. Language via MI
        ta_client = TextAnalyticsClient(endpoint=AI_ENDPOINT, credential=_credential)
        documentos = [item["texto"] for item in items]

        # 3. Batch de no máximo 5 (limite do tier S0)
        BATCH_SIZE = 5
        sentimentos, entidades = [], []
        for i in range(0, len(documentos), BATCH_SIZE):
            batch = documentos[i:i + BATCH_SIZE]
            sentimentos.extend(ta_client.analyze_sentiment(batch, language="pt"))
            entidades.extend(ta_client.recognize_entities(batch, language="pt"))

        # 4. Atualizar MongoDB
        resultados = []
        for i, item in enumerate(items):
            sent = sentimentos[i]
            ent  = entidades[i]
            if sent.is_error or ent.is_error:
                continue
            update = {
                "sentimento_label": sent.sentiment,
                "sentimento_score": {
                    "positive": round(sent.confidence_scores.positive, 3),
                    "neutral":  round(sent.confidence_scores.neutral,  3),
                    "negative": round(sent.confidence_scores.negative, 3),
                },
                "entidades": [
                    {"text": e.text, "category": e.category, "confidence": round(e.confidence_score, 3)}
                    for e in ent.entities
                ],
            }
            col.update_one({"_id": item["_id"]}, {"$set": update})
            resultados.append({"id": item.get("id"), "produto": item.get("produto"), "sentimento": sent.sentiment})

        positivos = sum(1 for r in resultados if r["sentimento"] == "positive")
        negativos = sum(1 for r in resultados if r["sentimento"] == "negative")

        return func.HttpResponse(
            json.dumps({
                "total_analisadas": len(resultados),
                "positivas": positivos,
                "negativas": negativos,
                "neutras":   len(resultados) - positivos - negativos,
                "exemplos":  resultados[:3],
            }, ensure_ascii=False),
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Falha em /analisar-reviews")
        return func.HttpResponse(json.dumps({"erro": str(e)}), mimetype="application/json", status_code=500)


@app.route(route="analisar-imagem", methods=["GET", "POST"])
def analisar_imagem(req: func.HttpRequest) -> func.HttpResponse:
    """
    Analisa imagem do Blob com Vision 4.0 (Tags + OCR + Objects) via MI.
    GET /api/analisar-imagem?blob=produto.jpg
    """
    blob_name = req.params.get("blob", "produto.jpg")
    container = req.params.get("container", "imagens")

    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        from azure.ai.vision.imageanalysis.models import VisualFeatures

        # 1. Baixar imagem do Blob via MI
        blob_client = _blob_service.get_blob_client(container=container, blob=blob_name)
        image_data = blob_client.download_blob().readall()

        # 2. Vision 4.0 via MI
        vision_client = ImageAnalysisClient(endpoint=AI_ENDPOINT, credential=_credential)

        # Caption não disponível em eastus2 — usar DENSE_CAPTIONS em eastus/westus2/westeurope
        result = vision_client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.TAGS, VisualFeatures.READ, VisualFeatures.OBJECTS],
        )

        tags = [{"name": t.name, "confidence": round(t.confidence, 3)} for t in (result.tags.list if result.tags else [])]
        texto_extraido = ""
        if result.read:
            texto_extraido = "\n".join(line.text for block in result.read.blocks for line in block.lines)

        objetos = []
        if result.objects and result.objects.list:
            for obj in result.objects.list:
                box = obj.bounding_box
                objetos.append({"label": obj.tags[0].name if obj.tags else "obj",
                                 "box": {"x": box.x, "y": box.y, "w": box.width, "h": box.height}})

        return func.HttpResponse(
            json.dumps({"caption": "", "tags": tags[:10], "texto_extraido": texto_extraido,
                        "objetos_detectados": objetos, "blob": blob_name}, ensure_ascii=False),
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Falha em /analisar-imagem")
        return func.HttpResponse(json.dumps({"erro": str(e)}), mimetype="application/json", status_code=500)


# ===========================================================================
# Rotas para o front-end (app Streamlit da Atividade 5)
#
# Diferenca das rotas acima: recebem o arquivo NO CORPO, em vez de um nome de
# blob. Isso e deliberado — assim o front-end nao precisa de credencial de
# Storage nenhuma. Ele fala HTTP com a Function, e quem tem identidade para
# chamar Vision, Speech e Storage e a Function, nao o cliente.
# ===========================================================================

VOZES_PT = {
    "Antonio (masculina)": "pt-BR-AntonioNeural",
    "Francisca (feminina)": "pt-BR-FranciscaNeural",
    "Thalita (feminina)": "pt-BR-ThalitaNeural",
}


@app.route(route="tts", methods=["POST"])
def tts(req: func.HttpRequest) -> func.HttpResponse:
    """
    Texto -> Fala. Devolve o WAV em bytes.
    POST /api/tts  {"texto": "...", "voz": "pt-BR-AntonioNeural", "idioma": "pt-BR"}
    """
    try:
        body = req.get_json()
        texto = (body.get("texto") or "").strip()
        if not texto:
            return func.HttpResponse(
                json.dumps({"erro": "campo 'texto' vazio"}),
                mimetype="application/json", status_code=400,
            )

        voz    = body.get("voz", "pt-BR-AntonioNeural")
        idioma = body.get("idioma", "pt-BR")

        # escape de XML: sem isso, um "&" ou "<" no texto do aluno quebra o SSML
        # com um erro 400 que nao explica nada.
        seguro = (texto.replace("&", "&amp;")
                       .replace("<", "&lt;")
                       .replace(">", "&gt;"))

        ssml = (
            f"<speak version='1.0' xml:lang='{idioma}'>"
            f"<voice xml:lang='{idioma}' name='{voz}'>{seguro}</voice>"
            f"</speak>"
        )

        resp = requests.post(
            f"https://{AI_REGION}.tts.speech.microsoft.com/cognitiveservices/v1",
            headers={
                "Authorization": f"Bearer {_get_speech_token(AI_REGION)}",
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
                "User-Agent": "qc-aula04",
            },
            data=ssml.encode("utf-8"),
            timeout=30,
        )
        resp.raise_for_status()

        return func.HttpResponse(resp.content, mimetype="audio/wav", status_code=200)

    except Exception as e:
        logging.exception("Falha em /tts")
        return func.HttpResponse(json.dumps({"erro": str(e)}), mimetype="application/json", status_code=500)


@app.route(route="stt", methods=["POST"])
def stt(req: func.HttpRequest) -> func.HttpResponse:
    """
    Fala -> Texto. Recebe os bytes do WAV no corpo.
    POST /api/stt?idioma=pt-BR   (corpo = audio/wav)
    """
    try:
        idioma = req.params.get("idioma", "pt-BR")
        audio = req.get_body()
        if not audio:
            return func.HttpResponse(
                json.dumps({"erro": "corpo vazio — envie os bytes do WAV"}),
                mimetype="application/json", status_code=400,
            )

        resp = requests.post(
            f"https://{AI_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1",
            headers={
                "Authorization": f"Bearer {_get_speech_token(AI_REGION)}",
                # O Speech REST so aceita WAV PCM 16 kHz mono. Áudio de outro
                # formato retorna 400 ou transcricao vazia.
                "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                "Accept": "application/json",
            },
            params={"language": idioma, "format": "detailed"},
            data=audio,
            timeout=30,
        )

        # NAO use raise_for_status aqui. O Speech responde 400 quando o audio nao
        # esta em WAV PCM 16 kHz mono, e o motivo vem no CORPO da resposta. Deixar
        # a excecao subir transforma um diagnostico claro num 500 mudo — foi
        # exatamente o que aconteceu na primeira versao desta rota.
        if resp.status_code >= 400:
            return func.HttpResponse(
                json.dumps({
                    "erro": "Speech recusou o audio",
                    "http": resp.status_code,
                    "detalhe": resp.text[:500],
                    "dica": ("O endpoint REST aceita WAV PCM 16 bits, MONO, 8 ou 16 kHz. "
                             "Gravacao de navegador costuma sair em 48 kHz."),
                    "bytes_recebidos": len(audio),
                }, ensure_ascii=False),
                mimetype="application/json", status_code=400,
            )

        data = resp.json()

        transcricao = ""
        if data.get("NBest"):
            transcricao = data["NBest"][0].get("Display", "")
        elif "DisplayText" in data:
            transcricao = data["DisplayText"]

        return func.HttpResponse(
            json.dumps({
                "transcricao": transcricao,
                "idioma": idioma,
                "status_stt": data.get("RecognitionStatus", ""),
                "bytes_recebidos": len(audio),
            }, ensure_ascii=False),
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Falha em /stt")
        return func.HttpResponse(json.dumps({"erro": str(e)}), mimetype="application/json", status_code=500)


@app.route(route="visao", methods=["POST"])
def visao(req: func.HttpRequest) -> func.HttpResponse:
    """
    Analise de imagem. Recebe os bytes da imagem no corpo.
    POST /api/visao   (corpo = image/jpeg ou image/png)

    Devolve tags, texto (OCR) e objetos com bounding box em PIXELS, mais as
    dimensoes da imagem — o cliente precisa das duas coisas para desenhar as
    caixas na escala certa.
    """
    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        from azure.ai.vision.imageanalysis.models import VisualFeatures

        image_data = req.get_body()
        if not image_data:
            return func.HttpResponse(
                json.dumps({"erro": "corpo vazio — envie os bytes da imagem"}),
                mimetype="application/json", status_code=400,
            )

        vision_client = ImageAnalysisClient(endpoint=AI_ENDPOINT, credential=_credential)
        result = vision_client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.TAGS, VisualFeatures.READ, VisualFeatures.OBJECTS],
        )

        tags = [{"name": t.name, "confidence": round(t.confidence, 3)}
                for t in (result.tags.list if result.tags else [])]

        texto = ""
        if result.read:
            texto = "\n".join(line.text for block in result.read.blocks for line in block.lines)

        objetos = []
        if result.objects and result.objects.list:
            for obj in result.objects.list:
                b = obj.bounding_box
                objetos.append({
                    "label": obj.tags[0].name if obj.tags else "objeto",
                    "confidence": round(obj.tags[0].confidence, 3) if obj.tags else None,
                    "box": {"x": b.x, "y": b.y, "w": b.width, "h": b.height},
                })

        return func.HttpResponse(
            json.dumps({
                "tags": tags[:15],
                "texto": texto,
                "objetos": objetos,
                "largura": result.metadata.width,
                "altura": result.metadata.height,
            }, ensure_ascii=False),
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Falha em /visao")
        return func.HttpResponse(json.dumps({"erro": str(e)}), mimetype="application/json", status_code=500)
