"""
QC Cognitive Studio — front-end da Aula 4.

Explora os serviços de IA do lab (Polly, Transcribe e Rekognition) por DOIS
caminhos diferentes, lado a lado:

  A) via Lambda  — o app só fala HTTP; quem tem identidade é a função (LabRole)
  B) direto na AWS — o app carrega credenciais e chama os serviços ele mesmo

A comparação é o ponto da atividade. Os dois devolvem o mesmo resultado; o que
muda é onde a credencial vive e quem pode usá-la.

Rodar:
    pip install -r requirements.txt
    streamlit run app.py
"""
import io
import json
import time
import uuid
import urllib.request
import wave

import boto3
import numpy as np
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="QC Cognitive Studio", page_icon="🧠", layout="wide")

# Vozes neurais do Amazon Polly (cada voz já tem o seu idioma)
VOZES = {
    "Camila (feminina, pt-BR)": "Camila",
    "Vitória (feminina, pt-BR)": "Vitoria",
    "Thiago (masculino, pt-BR)": "Thiago",
    "Joanna (feminina, en-US)": "Joanna",
    "Lucia (feminina, es-ES)": "Lucia",
}

IDIOMAS = {"Português (BR)": "pt-BR", "Inglês (US)": "en-US", "Espanhol (ES)": "es-ES"}

# Paleta para as caixas — cores distintas por objeto detectado.
CORES = ["#E8175D", "#3DD68C", "#4A90D9", "#E8B04B", "#A78BFA", "#38BDF8"]


# ---------------------------------------------------------------- barra lateral

st.sidebar.title("⚙️ Configuração")

st.sidebar.caption(
    "Pegue estes valores rodando `source exportar-outputs.sh` no CloudShell."
)

func_url = st.sidebar.text_input(
    "Function URL da Lambda (FUNC_URL)",
    placeholder="https://xxxxxxxx.lambda-url.us-east-1.on.aws/",
).rstrip("/")

st.sidebar.divider()
st.sidebar.caption(
    "Só para o caminho **direto** — o caminho via Lambda não usa. "
    "Learner Lab → **AWS Details** → **AWS CLI: Show**."
)
aws_key_id = st.sidebar.text_input("aws_access_key_id")
aws_secret = st.sidebar.text_input("aws_secret_access_key", type="password")
aws_token = st.sidebar.text_input("aws_session_token", type="password")
aws_region = st.sidebar.text_input("Região", value="us-east-1")
data_bucket = st.sidebar.text_input(
    "DATA_BUCKET", help="O Transcribe só lê áudio do S3: o caminho direto precisa do bucket."
)

st.sidebar.divider()
caminho = st.sidebar.radio(
    "Caminho",
    ["Via Lambda", "Direto na AWS", "Comparar os dois"],
    help="'Comparar' executa os dois e mostra tempo e resultado lado a lado.",
)


def precisa(via_lambda: bool) -> bool:
    """Confere se a configuração necessária para aquele caminho está preenchida."""
    if via_lambda and not func_url:
        st.error("Preencha a **Function URL** na barra lateral.")
        return False
    if not via_lambda and not (aws_key_id and aws_secret):
        st.error("Preencha as credenciais da AWS na barra lateral.")
        return False
    return True


def cliente(servico: str):
    """Cliente boto3 com as credenciais coladas na barra lateral — a 'chave no cliente'."""
    return boto3.client(
        servico,
        region_name=aws_region,
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_secret,
        aws_session_token=aws_token or None,
    )


def cronometrar(fn, *args, **kwargs):
    """Executa e devolve (resultado, erro, segundos)."""
    inicio = time.perf_counter()
    try:
        return fn(*args, **kwargs), None, time.perf_counter() - inicio
    except Exception as e:  # noqa: BLE001 — queremos mostrar qualquer falha na tela
        return None, str(e), time.perf_counter() - inicio


# ------------------------------------------------------------------- chamadas
# Cada capacidade tem duas implementações com a MESMA assinatura. É o que permite
# rodar as duas e comparar sem código condicional espalhado pela interface.


def preparar_wav(audio: bytes, destino_hz: int = 16000) -> tuple[bytes, str]:
    """
    Converte o áudio para WAV PCM 16-bit MONO a 16 kHz.

    O Transcribe aceita 48 kHz, mas o arquivo fica 3× maior para nada: fala não
    precisa de mais que 16 kHz. Cinco segundos de fala a 48 kHz dão ~490 KB; a
    16 kHz mono, ~160. Menos bytes = upload mais rápido para o S3.

    Devolve (bytes_convertidos, descricao_do_que_foi_feito).
    """
    try:
        with wave.open(io.BytesIO(audio), "rb") as w:
            canais, largura, taxa, quadros = (
                w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            )
            bruto = w.readframes(quadros)
    except wave.Error:
        # Não é RIFF/WAV (WebM, Ogg, MP3...). Não dá para converter sem ffmpeg —
        # melhor avisar do que enviar e receber um 500 sem explicação.
        return audio, "formato não reconhecido como WAV — envio sem conversão"

    if largura != 2:
        return audio, f"WAV de {largura * 8} bits — só converto 16 bits"

    if canais == 1 and taxa == destino_hz:
        return audio, "já estava em 16 kHz mono — nada a fazer"

    amostras = np.frombuffer(bruto, dtype=np.int16)

    if canais > 1:
        amostras = amostras.reshape(-1, canais).mean(axis=1).astype(np.int16)

    if taxa != destino_hz:
        # Reamostragem linear. Para fala em banda estreita é suficiente, e evita
        # trazer scipy/librosa só por causa disso.
        n_destino = int(len(amostras) * destino_hz / taxa)
        idx = np.linspace(0, len(amostras) - 1, n_destino)
        amostras = np.interp(idx, np.arange(len(amostras)), amostras).astype(np.int16)

    saida = io.BytesIO()
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(destino_hz)
        w.writeframes(amostras.tobytes())

    return saida.getvalue(), f"convertido de {taxa} Hz / {canais} canal(is) → 16 kHz mono"


def tts_lambda(texto: str, voz: str) -> bytes:
    r = requests.post(f"{func_url}/tts", json={"texto": texto, "voz": voz}, timeout=60)
    r.raise_for_status()
    return r.content


def tts_direto(texto: str, voz: str) -> bytes:
    pcm = cliente("polly").synthesize_speech(
        Text=texto, VoiceId=voz, Engine="neural", OutputFormat="pcm", SampleRate="16000"
    )["AudioStream"].read()
    saida = io.BytesIO()
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(pcm)
    return saida.getvalue()


def stt_lambda(audio: bytes, idioma: str) -> dict:
    r = requests.post(
        f"{func_url}/stt",
        params={"idioma": idioma, "formato": "wav"},
        data=audio,
        headers={"Content-Type": "application/octet-stream"},
        timeout=70,
    )
    r.raise_for_status()
    return r.json()


def stt_direto(audio: bytes, idioma: str) -> dict:
    if not data_bucket:
        raise ValueError("Preencha DATA_BUCKET: o Transcribe só lê áudio do S3.")
    s3, transcribe = cliente("s3"), cliente("transcribe")
    chave = f"audios/studio-{uuid.uuid4().hex[:8]}.wav"
    job = f"qc-studio-{uuid.uuid4().hex[:8]}"
    s3.put_object(Bucket=data_bucket, Key=chave, Body=audio)
    try:
        transcribe.start_transcription_job(
            TranscriptionJobName=job, LanguageCode=idioma, MediaFormat="wav",
            Media={"MediaFileUri": f"s3://{data_bucket}/{chave}"},
        )
        while True:
            st_job = transcribe.get_transcription_job(TranscriptionJobName=job)["TranscriptionJob"]
            if st_job["TranscriptionJobStatus"] in ("COMPLETED", "FAILED"):
                break
            time.sleep(2)
        if st_job["TranscriptionJobStatus"] == "FAILED":
            return {"transcricao": "", "status": "FAILED", "motivo": st_job.get("FailureReason")}
        with urllib.request.urlopen(st_job["Transcript"]["TranscriptFileUri"], timeout=10) as r:
            dados = json.load(r)
        texto = " ".join(t["transcript"] for t in dados["results"]["transcripts"])
        return {"transcricao": texto, "status": "COMPLETED"}
    finally:
        s3.delete_object(Bucket=data_bucket, Key=chave)


def visao_lambda(imagem: bytes) -> dict:
    r = requests.post(
        f"{func_url}/visao",
        data=imagem,
        headers={"Content-Type": "application/octet-stream"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def visao_direto(imagem: bytes) -> dict:
    rek = cliente("rekognition")
    labels = rek.detect_labels(Image={"Bytes": imagem}, MaxLabels=15, MinConfidence=60)["Labels"]
    textos = rek.detect_text(Image={"Bytes": imagem})["TextDetections"]
    largura, altura = Image.open(io.BytesIO(imagem)).size

    objetos = []
    for lab in labels:
        for inst in lab.get("Instances", []):
            b = inst["BoundingBox"]  # proporção 0–1 → pixels
            objetos.append({
                "label": lab["Name"],
                "confidence": round(inst["Confidence"] / 100, 3),
                "box": {"x": round(b["Left"] * largura), "y": round(b["Top"] * altura),
                        "w": round(b["Width"] * largura), "h": round(b["Height"] * altura)},
            })
    return {
        "tags": [{"name": lab["Name"], "confidence": round(lab["Confidence"] / 100, 3)} for lab in labels],
        "texto": "\n".join(t["DetectedText"] for t in textos if t["Type"] == "LINE"),
        "objetos": objetos,
        "largura": largura,
        "altura": altura,
    }


# ------------------------------------------------------------------- desenho


def desenhar_caixas(imagem_bytes: bytes, objetos: list) -> Image.Image:
    """
    Desenha as bounding boxes sobre a imagem.

    As coordenadas vêm em PIXELS da imagem original. Se você redimensionar a
    imagem antes de desenhar, as caixas saem fora de lugar — por isso desenhamos
    no tamanho original e deixamos o Streamlit escalar depois.
    """
    img = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)

    espessura = max(2, img.width // 300)
    try:
        fonte = ImageFont.truetype("DejaVuSans.ttf", max(14, img.width // 45))
    except OSError:
        fonte = ImageFont.load_default()

    for i, obj in enumerate(objetos):
        b = obj["box"]
        cor = CORES[i % len(CORES)]
        x0, y0 = b["x"], b["y"]
        x1, y1 = x0 + b["w"], y0 + b["h"]

        draw.rectangle([x0, y0, x1, y1], outline=cor, width=espessura)

        rotulo = obj["label"]
        if obj.get("confidence") is not None:
            rotulo += f" {obj['confidence']:.0%}"

        caixa_texto = draw.textbbox((0, 0), rotulo, font=fonte)
        lt, at = caixa_texto[2] - caixa_texto[0], caixa_texto[3] - caixa_texto[1]

        # Se a caixa está colada no topo, joga o rótulo para dentro dela.
        ty = y0 - at - 6 if y0 - at - 6 > 0 else y0 + 4
        draw.rectangle([x0, ty, x0 + lt + 8, ty + at + 6], fill=cor)
        draw.text((x0 + 4, ty + 2), rotulo, fill="white", font=fonte)

    return img


def painel_tempo(rotulo: str, segundos: float, credencial: str):
    c1, c2 = st.columns(2)
    c1.metric(f"{rotulo} — tempo", f"{segundos:.2f} s")
    c2.metric("Credencial usada", credencial)


# -------------------------------------------------------------------- páginas

st.title("🧠 QC Cognitive Studio")
st.caption("Aula 4 — Serviços Cognitivos · Quantum Commerce")

aba_tts, aba_stt, aba_visao, aba_arq = st.tabs(
    ["🔊 Texto → Fala", "🎤 Fala → Texto", "🖼️ Visão + Espacial", "🏛️ Arquitetura"]
)

# ---------------------------------------------------------------------- TTS
with aba_tts:
    st.subheader("Texto → Fala (Amazon Polly)")

    texto = st.text_area(
        "Texto para sintetizar",
        "A Quantum Commerce é uma plataforma de e-commerce que opera em doze países.",
        height=110,
    )
    voz = VOZES[st.selectbox("Voz", list(VOZES))]

    if st.button("Sintetizar", type="primary", key="btn_tts"):
        if caminho in ("Via Lambda", "Comparar os dois") and precisa(True):
            audio, erro, t = cronometrar(tts_lambda, texto, voz)
            st.markdown("#### Via Lambda")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Lambda", t, "nenhuma no cliente")
                st.audio(audio, format="audio/wav")
                st.download_button("Baixar WAV", audio, "tts-lambda.wav", "audio/wav")

        if caminho in ("Direto na AWS", "Comparar os dois") and precisa(False):
            audio, erro, t = cronometrar(tts_direto, texto, voz)
            st.markdown("#### Direto na AWS")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Direto", t, "access key no cliente")
                st.audio(audio, format="audio/wav")
                st.download_button("Baixar WAV", audio, "tts-direto.wav", "audio/wav")

# ---------------------------------------------------------------------- STT
with aba_stt:
    st.subheader("Fala → Texto (Amazon Transcribe)")

    st.info(
        "A gravação do navegador sai em 48 kHz. O app converte para **WAV 16 kHz mono** "
        "antes de enviar (3× menos bytes, mesma qualidade para fala) e mostra abaixo "
        "o que foi feito. O Transcribe processa em lote: espere alguns segundos.",
        icon="🎚️",
    )

    origem = st.radio("Origem do áudio", ["Gravar do microfone", "Enviar arquivo"],
                      horizontal=True)

    audio_bytes = None
    if origem == "Gravar do microfone":
        gravado = st.audio_input("Grave uma frase")
        if gravado:
            audio_bytes = gravado.getvalue()
    else:
        enviado = st.file_uploader("Arquivo WAV", type=["wav"])
        if enviado:
            audio_bytes = enviado.getvalue()

    idioma_stt = IDIOMAS[st.selectbox("Idioma da fala", list(IDIOMAS), key="idioma_stt")]

    audio_envio = None
    if audio_bytes:
        st.audio(audio_bytes)
        audio_envio, nota = preparar_wav(audio_bytes)
        c1, c2 = st.columns(2)
        c1.metric("Original", f"{len(audio_bytes):,} bytes")
        c2.metric("Enviado", f"{len(audio_envio):,} bytes")
        st.caption(f"🎚️ {nota}")

    if st.button("Transcrever", type="primary", key="btn_stt", disabled=not audio_envio):
        audio_bytes = audio_envio
        if caminho in ("Via Lambda", "Comparar os dois") and precisa(True):
            r, erro, t = cronometrar(stt_lambda, audio_bytes, idioma_stt)
            st.markdown("#### Via Lambda")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Lambda", t, "nenhuma no cliente")
                st.success(r.get("transcricao") or "_(transcrição vazia)_")
                st.caption(f"status: {r.get('status_stt')}")

        if caminho in ("Direto na AWS", "Comparar os dois") and precisa(False):
            r, erro, t = cronometrar(stt_direto, audio_bytes, idioma_stt)
            st.markdown("#### Direto na AWS")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Direto", t, "access key no cliente")
                st.success(r.get("transcricao") or "_(transcrição vazia)_")
                st.caption(f"status: {r.get('status_stt')}")

# -------------------------------------------------------------------- VISÃO
with aba_visao:
    st.subheader("Visão: tags, OCR e localização espacial")

    arquivo = st.file_uploader("Imagem", type=["jpg", "jpeg", "png"])

    if arquivo and st.button("Analisar", type="primary", key="btn_visao"):
        imagem = arquivo.getvalue()

        resultados = []
        if caminho in ("Via Lambda", "Comparar os dois") and precisa(True):
            r, erro, t = cronometrar(visao_lambda, imagem)
            resultados.append(("Via Lambda", r, erro, t, "nenhuma no cliente"))
        if caminho in ("Direto na AWS", "Comparar os dois") and precisa(False):
            r, erro, t = cronometrar(visao_direto, imagem)
            resultados.append(("Direto na AWS", r, erro, t, "access key no cliente"))

        for titulo, r, erro, t, cred in resultados:
            st.markdown(f"#### {titulo}")
            if erro:
                st.error(erro)
                continue

            painel_tempo(titulo.split()[0], t, cred)

            objetos = r.get("objetos", [])
            col_img, col_dados = st.columns([3, 2])

            with col_img:
                if objetos:
                    st.image(desenhar_caixas(imagem, objetos),
                             caption=f"{len(objetos)} objeto(s) localizado(s)",
                             use_container_width=True)
                else:
                    st.image(imagem, use_container_width=True)
                    st.caption("Nenhum objeto localizado — veja as tags ao lado.")

            with col_dados:
                st.markdown("**Objetos e coordenadas**")
                if objetos:
                    st.dataframe(
                        [{
                            "objeto": o["label"],
                            "conf.": o.get("confidence"),
                            "x": o["box"]["x"], "y": o["box"]["y"],
                            "w": o["box"]["w"], "h": o["box"]["h"],
                        } for o in objetos],
                        hide_index=True, use_container_width=True,
                    )
                else:
                    st.write("—")

                st.markdown("**Tags**")
                tags = r.get("tags", [])
                st.write(", ".join(f"{t['name']} ({t['confidence']:.0%})" for t in tags) or "—")

                st.markdown("**Texto extraído (OCR)**")
                st.code(r.get("texto") or "—")

            with st.expander("JSON completo"):
                st.json(r)

# --------------------------------------------------------------- ARQUITETURA
with aba_arq:
    st.subheader("O que muda entre os dois caminhos")

    st.markdown(
        """
Os dois devolvem **o mesmo resultado**. A diferença não está na saída, está em
onde a credencial vive — e isso decide o que acontece quando algo vaza.

| | Via Lambda | Direto na AWS |
|---|---|---|
| Onde está a credencial | na execution role da Lambda (temporária, renovada sozinha) | **nesta máquina**, na barra lateral |
| Quem se autentica | a função, com a LabRole | você, com a access key |
| Se o código vazar | nada de útil: só a URL da função | a credencial vai junto |
| Revogar acesso | mudar a política da role | desativar a access key e avisar todo mundo |
| Auditoria (CloudTrail) | registra a role da função | registra a sua chave, não quem estava usando |
| Latência | um salto a mais | um salto a menos |

O caminho direto é mais rápido — e é exatamente por isso que ele é tentador.
Compare os tempos nas abas: a diferença costuma ser de dezenas de milissegundos.
É esse o preço de não ter credencial na máquina do cliente.

**Perguntas para discussão**

1. Este app roda no seu notebook. Se ele virasse uma página web pública, o
   caminho direto continuaria possível? O que aconteceria com a access key?
2. As credenciais do Learner Lab expiram em ~4 h. Isso é defeito ou proteção?
   Compare com uma access key de usuário IAM, que não expira.
3. Se um aluno commitar este projeto no GitHub com a credencial preenchida, o que
   precisa ser feito? Basta apagar o arquivo?
        """
    )

    if func_url:
        st.divider()
        if st.button("Testar /health"):
            try:
                r = requests.get(f"{func_url}/health", timeout=20)
                st.json(r.json())
            except Exception as e:  # noqa: BLE001
                st.error(str(e))
