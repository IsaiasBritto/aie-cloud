"""Deva3 · Interface web em Streamlit.

O aluno abre a página, arrasta a própria foto, escolhe o modo, marca o
consentimento e vê a caixa desenhada em cima da imagem com a pontuação de
confiança ao lado. O JSON cru fica visível o tempo todo — é ele que ensina.
"""

from __future__ import annotations

import io
import json
import os

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

ENDERECO_API = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
TEMPO_LIMITE = int(os.getenv("TEMPO_LIMITE_SEGUNDOS", "60"))

# Paleta FIAP — a mesma do material da aula
COR_FUNDO = "#15151A"
COR_MAGENTA = "#EB0B4F"
COR_CIANO = "#03E3FD"
COR_AMBAR = "#FFD579"
COR_TEXTO = "#F4F3EF"
COR_APAGADA = "#7A7872"

st.set_page_config(
    page_title="Deva3 · Validação Biométrica Básica",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {COR_FUNDO}; color: {COR_TEXTO}; }}
      h1, h2, h3 {{ color: {COR_TEXTO} !important; }}
      .sobrancelha {{ color: {COR_APAGADA}; font-size: 0.82rem;
                      letter-spacing: .12em; text-transform: uppercase; }}
      .regua {{ border-top: 1px solid #3A3A46; margin: .4rem 0 1.4rem 0; }}
      .cartao {{ background:#1C1C22; border:1px solid #2E2E38; padding:1rem 1.1rem; }}
      .rotulo {{ color:{COR_MAGENTA}; font-size:.78rem; letter-spacing:.1em;
                 text-transform:uppercase; font-weight:700; }}
      .numerao {{ font-size:2.4rem; font-weight:700; color:{COR_MAGENTA}; line-height:1; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ───────────────────────────── funções de apoio ──────────────────────────

def consultar_saude() -> dict | None:
    """Pergunta à API se ela está de pé e quais modos existem."""
    try:
        resposta = requests.get(f"{ENDERECO_API}/saude", timeout=8)
        resposta.raise_for_status()
        return resposta.json()
    except requests.RequestException:
        return None


def enviar_para_deteccao(arquivo, modo: str, consentimento: bool) -> tuple[int, dict]:
    """Envia a imagem para a API e devolve (status, corpo)."""
    arquivos = {"imagem": (arquivo.name, arquivo.getvalue(),
                           arquivo.type or "application/octet-stream")}
    parametros = {"modo": modo, "consentimento": str(consentimento).lower()}
    resposta = requests.post(
        f"{ENDERECO_API}/detectar", files=arquivos, params=parametros,
        timeout=TEMPO_LIMITE,
    )
    try:
        return resposta.status_code, resposta.json()
    except ValueError:
        return resposta.status_code, {"erro": "resposta_invalida",
                                      "mensagem": resposta.text[:400]}


def desenhar_caixas(imagem_bytes: bytes, deteccoes: list[dict],
                    limiar: float) -> Image.Image:
    """Desenha o retângulo e a etiqueta de cada detecção sobre a foto."""
    figura = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
    pincel = ImageDraw.Draw(figura)

    espessura = max(2, round(min(figura.size) * 0.006))
    tamanho_fonte = max(14, round(min(figura.size) * 0.035))
    try:
        fonte = ImageFont.truetype("DejaVuSans-Bold.ttf", tamanho_fonte)
    except OSError:
        fonte = ImageFont.load_default()

    for deteccao in deteccoes:
        caixa = deteccao["caixa"]
        confianca = deteccao.get("confianca")
        acima = deteccao.get("acima_do_limiar", False)
        cor = COR_CIANO if acima else COR_AMBAR

        esquerda, topo = caixa["x"], caixa["y"]
        direita = esquerda + caixa["largura"]
        base = topo + caixa["altura"]
        pincel.rectangle([esquerda, topo, direita, base], outline=cor, width=espessura)

        rotulo = (f"#{deteccao['indice']} · {confianca:.0%}" if confianca is not None
                  else f"#{deteccao['indice']} · sem confiança")
        caixa_texto = pincel.textbbox((0, 0), rotulo, font=fonte)
        largura_texto = caixa_texto[2] - caixa_texto[0] + 12
        altura_texto = caixa_texto[3] - caixa_texto[1] + 10
        topo_etiqueta = max(0, topo - altura_texto)
        pincel.rectangle(
            [esquerda, topo_etiqueta, esquerda + largura_texto, topo_etiqueta + altura_texto],
            fill=cor,
        )
        pincel.text((esquerda + 6, topo_etiqueta + 4), rotulo, fill=COR_FUNDO, font=fonte)

    return figura


# ──────────────────────────────── cabeçalho ──────────────────────────────

st.markdown('<div class="sobrancelha">▶ FIAP · MBA AI Engineering &amp; Multi-Agents · Aula 05</div>',
            unsafe_allow_html=True)
st.markdown("# Deva3 · Validação Biométrica Básica")
st.markdown('<div class="regua"></div>', unsafe_allow_html=True)

estado = consultar_saude()

with st.sidebar:
    st.markdown('<div class="rotulo">Ambiente</div>', unsafe_allow_html=True)
    st.caption(f"API: `{ENDERECO_API}`")

    if estado is None:
        st.error(
            "A API não respondeu.\n\n"
            "**Como resolver:** confira se o container da API está de pé e se a "
            "variável `API_URL` aponta para ele."
        )
        modos = ["pessoas"]
    else:
        situacao = estado.get("situacao")
        (st.success if situacao == "saudavel" else st.warning)(
            f"API {situacao} · versão {estado.get('versao')} · ambiente {estado.get('ambiente')}"
        )
        modos = estado.get("modos_disponiveis") or ["pessoas"]
        st.caption(f"Limiar de confiança: **{estado.get('limiar_confianca')}**")
        st.caption(f"Blob configurado: **{estado.get('armazenamento_configurado')}**")

    st.markdown('<div class="rotulo">Configuração</div>', unsafe_allow_html=True)
    modo = st.radio(
        "Modo de detecção",
        options=modos,
        format_func=lambda m: ("Pessoas · Image Analysis 4.0" if m == "pessoas"
                               else "Rostos · Azure AI Face"),
        help=("'pessoas' devolve caixa e confiança de verdade. "
              "'rostos' devolve o retângulo do rosto, mas sem confiança de detecção."),
    )

    st.markdown('<div class="rotulo">Consentimento</div>', unsafe_allow_html=True)
    consentimento = st.checkbox(
        "Autorizo guardar esta imagem no Blob Storage",
        value=False,
        help=("Imagem de rosto é dado pessoal sensível (LGPD, art. 5º, II). "
              "Sem esta autorização, apenas o resultado em JSON é gravado."),
    )
    st.caption(
        "Sem consentimento, a foto **não** é gravada — só o JSON do resultado. "
        "No fim da aula, o grupo de recursos inteiro é apagado."
    )

# ──────────────────────────────── conteúdo ───────────────────────────────

coluna_envio, coluna_resultado = st.columns([1, 1.25], gap="large")

with coluna_envio:
    st.markdown('<div class="rotulo">1 · Envie uma foto</div>', unsafe_allow_html=True)
    arquivo = st.file_uploader(
        "Arraste ou selecione uma imagem",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        label_visibility="collapsed",
    )
    if arquivo is not None:
        st.image(arquivo, caption=f"{arquivo.name} · {len(arquivo.getvalue())/1024:.0f} KB",
                 use_container_width=True)

    analisar = st.button("Analisar imagem", type="primary", use_container_width=True,
                         disabled=arquivo is None)

with coluna_resultado:
    st.markdown('<div class="rotulo">2 · Resposta do serviço cognitivo</div>',
                unsafe_allow_html=True)

    if arquivo is not None and analisar:
        with st.spinner("Chamando a Azure..."):
            try:
                situacao, corpo = enviar_para_deteccao(arquivo, modo, consentimento)
            except requests.RequestException as erro:
                st.error(f"Não foi possível falar com a API.\n\n`{erro}`")
                situacao, corpo = 0, {}

        if situacao == 200:
            colunas = st.columns(4)
            colunas[0].metric("Detecções", corpo["total_detectado"])
            colunas[1].metric("Acima do limiar", corpo["total_acima_do_limiar"])
            colunas[2].metric("Tempo", f"{corpo['duracao_ms']} ms")
            colunas[3].metric("Imagem", f"{corpo['dimensoes']['largura']}×"
                                        f"{corpo['dimensoes']['altura']}")

            if corpo["deteccoes"]:
                st.image(
                    desenhar_caixas(arquivo.getvalue(), corpo["deteccoes"],
                                    corpo["limiar_confianca"]),
                    caption="Ciano = acima do limiar · âmbar = abaixo",
                    use_container_width=True,
                )

            for aviso in corpo.get("avisos", []):
                st.warning(aviso)

            if corpo["deteccoes"]:
                st.markdown('<div class="rotulo">Coordenadas</div>', unsafe_allow_html=True)
                st.dataframe(
                    [
                        {
                            "#": d["indice"],
                            "x": d["caixa"]["x"],
                            "y": d["caixa"]["y"],
                            "largura": d["caixa"]["largura"],
                            "altura": d["caixa"]["altura"],
                            "confiança": (f"{d['confianca']:.1%}"
                                          if d["confianca"] is not None else "—"),
                            "acima do limiar": "sim" if d["acima_do_limiar"] else "não",
                            "% da imagem": f"{d['proporcao_da_imagem']:.1%}",
                        }
                        for d in corpo["deteccoes"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            if corpo.get("caminho_blob"):
                st.caption(f"Gravado em `{corpo['caminho_blob']}` · "
                           f"imagem persistida: **{corpo['imagem_persistida']}**")

            st.markdown('<div class="rotulo">Payload JSON</div>', unsafe_allow_html=True)
            st.code(json.dumps(corpo, ensure_ascii=False, indent=2), language="json")

        elif situacao:
            st.error(f"**{corpo.get('erro', 'erro')}** — {corpo.get('mensagem', '')}")
            if corpo.get("como_resolver"):
                st.info(f"**Como resolver:** {corpo['como_resolver']}")
            if corpo.get("detalhe"):
                with st.expander("Detalhe técnico"):
                    st.code(corpo["detalhe"])
    else:
        st.info(
            "Envie uma foto e clique em **Analisar imagem**.\n\n"
            "Sugestão para a aula: comece com uma foto sua, depois teste uma foto de "
            "grupo, uma foto de costas e uma imagem sem nenhuma pessoa. Compare as "
            "confianças — é aí que a conversa fica interessante."
        )

st.markdown('<div class="regua"></div>', unsafe_allow_html=True)
st.caption(
    "Deva3 detecta presença e devolve coordenadas. Ele **não** identifica pessoas, "
    "não compara rostos e não guarda template biométrico. "
    "FIAP · MBA AI Engineering & Multi-Agents · uso exclusivo para fins acadêmicos."
)
