"""
QC Cognitive Studio — front-end da Aula 4.

Explora os quatro serviços cognitivos do lab (TTS, STT, Visão e localização
espacial) por DOIS caminhos diferentes, lado a lado:

  A) via Function App  — o app só fala HTTP; quem tem identidade é a Function
  B) direto no AI Services — o app carrega a chave e chama a Azure ele mesmo

A comparação é o ponto da atividade. Os dois devolvem o mesmo resultado; o que
muda é onde a credencial vive e quem pode usá-la.

Rodar:
    pip install -r requirements.txt
    streamlit run app.py
"""
import io
import json
import time
import wave

import numpy as np
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="QC Cognitive Studio", page_icon="🧠", layout="wide")

VOZES = {
    "Antônio (masculina)": "pt-BR-AntonioNeural",
    "Francisca (feminina)": "pt-BR-FranciscaNeural",
    "Thalita (feminina)": "pt-BR-ThalitaNeural",
}

IDIOMAS = {"Português (BR)": "pt-BR", "Inglês (US)": "en-US", "Espanhol (ES)": "es-ES"}

# Paleta para as caixas — cores distintas por objeto detectado.
CORES = ["#E8175D", "#3DD68C", "#4A90D9", "#E8B04B", "#A78BFA", "#38BDF8"]


# ---------------------------------------------------------------- barra lateral

st.sidebar.title("⚙️ Configuração")

st.sidebar.caption(
    "Pegue estes valores rodando `source exportar-outputs.sh` no Cloud Shell."
)

func_host = st.sidebar.text_input(
    "Function App (FUNC_HOSTNAME)",
    placeholder="https://func-qc-aula04-xxxxx.azurewebsites.net",
    help="Sem barra no final.",
).rstrip("/")

st.sidebar.divider()
st.sidebar.caption("Só para o caminho **direto** — o caminho via Function não usa.")

ai_endpoint = st.sidebar.text_input(
    "AI_ENDPOINT",
    placeholder="https://ai-qc-xxxxx.cognitiveservices.azure.com/",
).rstrip("/")
ai_region = st.sidebar.text_input("AI_REGION", value="eastus2")
ai_key = st.sidebar.text_input("AI_KEY", type="password")

st.sidebar.divider()
caminho = st.sidebar.radio(
    "Caminho",
    ["Via Function App", "Direto no AI Services", "Comparar os dois"],
    help="'Comparar' executa os dois e mostra tempo e resultado lado a lado.",
)


def precisa(via_function: bool) -> bool:
    """Confere se a configuração necessária para aquele caminho está preenchida."""
    if via_function and not func_host:
        st.error("Preencha **Function App** na barra lateral.")
        return False
    if not via_function and not (ai_endpoint and ai_key):
        st.error("Preencha **AI_ENDPOINT** e **AI_KEY** na barra lateral.")
        return False
    return True


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
    Converte o áudio para WAV PCM 16-bit MONO a 16 kHz — o único formato que o
    endpoint REST do Speech aceita.

    Por que isto existe: a gravação do navegador sai em 48 kHz (e às vezes
    estéreo). Mandar 48 kHz declarando `samplerate=16000` no cabeçalho faz o
    Azure recusar, e o erro chega como 500 genérico, sem dizer que o problema é
    o formato. Cinco segundos de fala a 48 kHz dão ~490 KB; a 16 kHz mono, ~160.

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


def _speech_token() -> str:
    """Troca a chave por um token de 10 min. Só no caminho direto."""
    r = requests.post(
        f"https://{ai_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
        headers={"Ocp-Apim-Subscription-Key": ai_key, "Content-Length": "0"},
        timeout=10,
    )
    r.raise_for_status()
    return r.text


def tts_function(texto: str, voz: str, idioma: str) -> bytes:
    r = requests.post(
        f"{func_host}/api/tts",
        json={"texto": texto, "voz": voz, "idioma": idioma},
        timeout=60,
    )
    r.raise_for_status()
    return r.content


def tts_direto(texto: str, voz: str, idioma: str) -> bytes:
    seguro = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ssml = (
        f"<speak version='1.0' xml:lang='{idioma}'>"
        f"<voice xml:lang='{idioma}' name='{voz}'>{seguro}</voice></speak>"
    )
    r = requests.post(
        f"https://{ai_region}.tts.speech.microsoft.com/cognitiveservices/v1",
        headers={
            "Authorization": f"Bearer {_speech_token()}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
            "User-Agent": "qc-studio",
        },
        data=ssml.encode("utf-8"),
        timeout=60,
    )
    r.raise_for_status()
    return r.content


def stt_function(audio: bytes, idioma: str) -> dict:
    r = requests.post(
        f"{func_host}/api/stt",
        params={"idioma": idioma},
        data=audio,
        headers={"Content-Type": "application/octet-stream"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def stt_direto(audio: bytes, idioma: str) -> dict:
    r = requests.post(
        f"https://{ai_region}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1",
        headers={
            "Authorization": f"Bearer {_speech_token()}",
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
        },
        params={"language": idioma, "format": "detailed"},
        data=audio,
        timeout=60,
    )
    r.raise_for_status()
    d = r.json()
    texto = d["NBest"][0]["Display"] if d.get("NBest") else d.get("DisplayText", "")
    return {"transcricao": texto, "status_stt": d.get("RecognitionStatus", "")}


def visao_function(imagem: bytes) -> dict:
    r = requests.post(
        f"{func_host}/api/visao",
        data=imagem,
        headers={"Content-Type": "application/octet-stream"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def visao_direto(imagem: bytes) -> dict:
    r = requests.post(
        f"{ai_endpoint}/computervision/imageanalysis:analyze",
        params={"api-version": "2024-02-01", "features": "tags,read,objects"},
        headers={
            "Ocp-Apim-Subscription-Key": ai_key,
            "Content-Type": "application/octet-stream",
        },
        data=imagem,
        timeout=60,
    )
    r.raise_for_status()
    d = r.json()

    tags = [
        {"name": t["name"], "confidence": round(t["confidence"], 3)}
        for t in d.get("tagsResult", {}).get("values", [])
    ]
    texto = "\n".join(
        line["text"]
        for block in d.get("readResult", {}).get("blocks", [])
        for line in block.get("lines", [])
    )
    objetos = []
    for o in d.get("objectsResult", {}).get("values", []):
        b = o["boundingBox"]
        t0 = (o.get("tags") or [{}])[0]
        objetos.append({
            "label": t0.get("name", "objeto"),
            "confidence": round(t0["confidence"], 3) if "confidence" in t0 else None,
            "box": {"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"]},
        })
    return {
        "tags": tags[:15],
        "texto": texto,
        "objetos": objetos,
        "largura": d.get("metadata", {}).get("width"),
        "altura": d.get("metadata", {}).get("height"),
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
    st.subheader("Texto → Fala (Speech TTS)")

    texto = st.text_area(
        "Texto para sintetizar",
        "A Quantum Commerce é uma plataforma de e-commerce que opera em doze países.",
        height=110,
    )
    c1, c2 = st.columns(2)
    voz = VOZES[c1.selectbox("Voz", list(VOZES))]
    idioma_tts = IDIOMAS[c2.selectbox("Idioma", list(IDIOMAS), key="idioma_tts")]

    if st.button("Sintetizar", type="primary", key="btn_tts"):
        if caminho in ("Via Function App", "Comparar os dois") and precisa(True):
            audio, erro, t = cronometrar(tts_function, texto, voz, idioma_tts)
            st.markdown("#### Via Function App")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Function", t, "nenhuma no cliente")
                st.audio(audio, format="audio/wav")
                st.download_button("Baixar WAV", audio, "tts-function.wav", "audio/wav")

        if caminho in ("Direto no AI Services", "Comparar os dois") and precisa(False):
            audio, erro, t = cronometrar(tts_direto, texto, voz, idioma_tts)
            st.markdown("#### Direto no AI Services")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Direto", t, "AI_KEY no cliente")
                st.audio(audio, format="audio/wav")
                st.download_button("Baixar WAV", audio, "tts-direto.wav", "audio/wav")

# ---------------------------------------------------------------------- STT
with aba_stt:
    st.subheader("Fala → Texto (Speech STT)")

    st.info(
        "O Speech REST aceita **WAV PCM 16 kHz mono**. A gravação do navegador sai "
        "em 48 kHz — o app converte automaticamente antes de enviar, e mostra "
        "abaixo o que foi feito.",
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
        if caminho in ("Via Function App", "Comparar os dois") and precisa(True):
            r, erro, t = cronometrar(stt_function, audio_bytes, idioma_stt)
            st.markdown("#### Via Function App")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Function", t, "nenhuma no cliente")
                st.success(r.get("transcricao") or "_(transcrição vazia)_")
                st.caption(f"status: {r.get('status_stt')}")

        if caminho in ("Direto no AI Services", "Comparar os dois") and precisa(False):
            r, erro, t = cronometrar(stt_direto, audio_bytes, idioma_stt)
            st.markdown("#### Direto no AI Services")
            if erro:
                st.error(erro)
            else:
                painel_tempo("Direto", t, "AI_KEY no cliente")
                st.success(r.get("transcricao") or "_(transcrição vazia)_")
                st.caption(f"status: {r.get('status_stt')}")

# -------------------------------------------------------------------- VISÃO
with aba_visao:
    st.subheader("Visão: tags, OCR e localização espacial")

    arquivo = st.file_uploader("Imagem", type=["jpg", "jpeg", "png"])

    if arquivo and st.button("Analisar", type="primary", key="btn_visao"):
        imagem = arquivo.getvalue()

        resultados = []
        if caminho in ("Via Function App", "Comparar os dois") and precisa(True):
            r, erro, t = cronometrar(visao_function, imagem)
            resultados.append(("Via Function App", r, erro, t, "nenhuma no cliente"))
        if caminho in ("Direto no AI Services", "Comparar os dois") and precisa(False):
            r, erro, t = cronometrar(visao_direto, imagem)
            resultados.append(("Direto no AI Services", r, erro, t, "AI_KEY no cliente"))

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

| | Via Function App | Direto no AI Services |
|---|---|---|
| Onde está a chave | Key Vault; a Function resolve em runtime | **nesta máquina**, na barra lateral |
| Quem se autentica | a Managed Identity da Function | você, com a chave |
| Se o código vazar | nada de útil: só a URL da Function | a chave vai junto |
| Revogar acesso | tirar a role da identidade | rotacionar a chave e avisar todo mundo |
| Auditoria | log identifica **qual** identidade chamou | só "alguém com a chave" |
| Latência | um salto a mais | um salto a menos |

O caminho direto é mais rápido — e é exatamente por isso que ele é tentador.
Compare os tempos nas abas: a diferença costuma ser de dezenas de milissegundos.
É esse o preço de não ter a chave na máquina do cliente.

**Perguntas para discussão**

1. Este app roda no seu notebook. Se ele virasse uma página web pública, o
   caminho direto continuaria possível? O que aconteceria com a chave?
2. A Function usa Managed Identity para Vision e chave para Speech. Por que a
   diferença? (dica: `Cognitive Services Speech User`)
3. Se um aluno commitar este projeto no GitHub com a chave preenchida, o que
   precisa ser feito? Basta remover o arquivo?
        """
    )

    if func_host:
        st.divider()
        if st.button("Testar /api/health"):
            try:
                r = requests.get(f"{func_host}/api/health", timeout=20)
                st.json(r.json())
            except Exception as e:  # noqa: BLE001
                st.error(str(e))
