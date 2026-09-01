"""A tela onde o aluno VÊ o agente aprender.

Quatro abas, cada uma respondendo a uma pergunta que a turma faz em voz alta:

* **Painel** — "ele está trabalhando agora?"
* **Memória** — "o que ele já sabe?" (com o que entrou hoje em destaque)
* **Propostas** — "o que ele quer aprender e ainda não pode?"
* **Exceções** — "o que ele não conseguiu resolver sozinho?"

A aba **Propostas** é o coração da aula: é ali que o aluno clica em *Aprovar* e vê a
linha atravessar para a aba Memória. Uma linha de markdown mudando de lugar explica
governança de IA melhor do que qualquer slide.

    streamlit run web/aplicacao.py
"""
from __future__ import annotations

import os
from datetime import datetime

import requests
import streamlit as st

API = os.getenv("DEVA_API", "http://localhost:8000").rstrip("/")
SEGREDO = os.getenv("DEVA_SEGREDO_AUDITOR", "")

# Paleta FIAP
FUNDO, PAINEL, LINHA = "#15151A", "#1C1C22", "#2E2E38"
TEXTO, TEXTO2, APAGADO = "#F4F3EF", "#C3C1BA", "#7A7872"
ROSA, CIANO, AMBAR = "#EB0B4F", "#03E3FD", "#FFD579"

st.set_page_config(page_title="Deva · memória e fila", page_icon="🧾", layout="wide")

st.markdown(f"""
<style>
  .stApp {{ background:{FUNDO}; color:{TEXTO}; }}
  header[data-testid="stHeader"] {{ background:transparent; height:0; }}
  div[data-testid="stToolbar"] {{ display:none; }}
  div[data-testid="stDecoration"] {{ display:none; }}
  section[data-testid="stSidebar"] {{ background:{PAINEL};
      border-right:1px solid {LINHA}; }}
  section[data-testid="stSidebar"] * {{ color:{TEXTO2}; }}
  .block-container {{ padding-top:2.2rem; }}
  h1,h2,h3,h4 {{ color:{TEXTO} !important; }}
  p, span, label, li {{ color:{TEXTO2}; }}
  /* botões e campos: escuros, para a tela não piscar branco no projetor */
  .stButton > button {{ background:{PAINEL}; color:{TEXTO}; border:1px solid {LINHA};
      border-radius:3px; font-weight:600; }}
  .stButton > button:hover:enabled {{ border-color:{CIANO}; color:{CIANO}; }}
  .stButton > button:disabled {{ color:{APAGADO}; border-color:{LINHA}; }}
  input, textarea {{ background:{PAINEL} !important; color:{TEXTO} !important;
      border:1px solid {LINHA} !important; }}
  div[data-testid="stExpander"] details {{ background:{PAINEL}; border:1px solid {LINHA}; }}
  div[data-baseweb="tab-list"] {{ background:transparent; border-bottom:1px solid {LINHA}; }}
  button[data-baseweb="tab"] {{ color:{APAGADO}; }}
  button[data-baseweb="tab"][aria-selected="true"] {{ color:{ROSA}; }}
  div[data-testid="stDataFrame"] {{ border:1px solid {LINHA}; }}
  /* o markdown do MEMORY.md quebra linha em vez de sumir para a direita */
  div[data-testid="stCode"] pre, pre {{ background:#101014 !important;
      border:1px solid {LINHA}; border-radius:4px;
      white-space:pre-wrap !important; word-break:break-word; }}
  div[data-testid="stCode"] code, pre code {{ color:{TEXTO2} !important;
      font-size:12.5px; white-space:pre-wrap !important; word-break:break-word; }}
  .cartao {{ background:{PAINEL}; border:1px solid {LINHA}; border-radius:4px;
             padding:14px 16px; margin-bottom:10px; }}
  .cartao.nova {{ border-color:{CIANO}; background:#12222A; }}
  .cartao.pendente {{ border-color:{AMBAR}; background:#221E14; }}
  .cartao.excecao {{ border-color:{ROSA}; background:#22161B; }}
  .rot {{ font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase;
          color:{APAGADO}; margin-bottom:6px; }}
  .rot.c {{ color:{CIANO}; }} .rot.a {{ color:{AMBAR}; }} .rot.r {{ color:{ROSA}; }}
  .regra {{ font-size:15px; line-height:1.5; color:{TEXTO}; }}
  .meta {{ font-size:12px; color:{APAGADO}; margin-top:6px; }}
  .numero {{ font-size:34px; font-weight:700; color:{TEXTO}; line-height:1; }}
  .numero.r {{ color:{ROSA}; }} .numero.a {{ color:{AMBAR}; }} .numero.c {{ color:{CIANO}; }}
  code {{ color:{CIANO}; }}
</style>
""", unsafe_allow_html=True)


# ── acesso à API ─────────────────────────────────────────────────────────────

def _cabecalhos(auditor: str | None = None) -> dict:
    cab = {}
    if auditor:
        cab["X-Auditor"] = auditor
    if SEGREDO:
        cab["X-Segredo"] = SEGREDO
    return cab


def buscar(caminho: str, auditor: str | None = None):
    try:
        resposta = requests.get(f"{API}{caminho}", headers=_cabecalhos(auditor), timeout=15)
    except requests.RequestException as erro:
        st.error(f"Não consegui falar com o serviço em {API}.")
        st.info("**Como resolver:** confira se a API está no ar (`GET /saude`) e se a "
                "variável `DEVA_API` aponta para ela.")
        st.caption(str(erro))
        st.stop()
    if resposta.status_code >= 400:
        mostrar_erro(resposta)
        st.stop()
    return resposta.json()


def enviar(caminho: str, corpo: dict, auditor: str):
    try:
        return requests.post(f"{API}{caminho}", json=corpo,
                             headers=_cabecalhos(auditor), timeout=20)
    except requests.RequestException as erro:
        st.error("Não consegui falar com o serviço.")
        st.caption(str(erro))
        return None


def mostrar_erro(resposta) -> None:
    try:
        dados = resposta.json()
    except Exception:
        st.error(f"HTTP {resposta.status_code}")
        return
    st.error(f"**{dados.get('erro')}** — {dados.get('mensagem')}")
    if dados.get("detalhe"):
        st.caption(dados["detalhe"])
    if dados.get("como_resolver"):
        st.info(f"**Como resolver:** {dados['como_resolver']}")


def quando(texto: str | None) -> str:
    if not texto:
        return "—"
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00")).strftime("%d/%m %H:%M")
    except ValueError:
        return texto


# ── barra lateral ────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Deva · continuidade")
    st.caption("Aula 02 · módulo do agente contínuo")
    auditor = st.text_input("Você é o auditor:", value="",
                            placeholder="Camila Rocha",
                            help="Aprovar e liberar exigem um nome. O agente não tem um.")
    st.divider()
    saude = buscar("/saude")
    st.markdown(f"""<div class="cartao">
      <div class="rot">Serviço</div>
      <div class="regra">versão {saude['versao']}</div>
      <div class="meta">armazenamento: {saude['armazenamento']}</div>
    </div>""", unsafe_allow_html=True)
    if st.button("Atualizar", use_container_width=True):
        st.rerun()
    st.caption(f"API: `{API}`")


st.markdown("## O agente entre uma conversa e outra")
st.caption("Ele lê a memória, propõe o que aprendeu e para quando precisa de gente. "
           "Nada aqui vira regra sem alguém clicar.")

painel, memoria_aba, propostas_aba, excecoes_aba = st.tabs(
    ["Painel", "Memória", "Propostas", "Exceções"])


# ── Painel ───────────────────────────────────────────────────────────────────

with painel:
    resumo = buscar("/fila")
    colunas = st.columns(4)
    cartoes = [
        ("Documentos na fila", resumo["total"], ""),
        ("Com o agente", len(resumo["aguardando_o_agente"]), "c"),
        ("Esperando gente", len(resumo["aguardando_humano"]), "r"),
        ("Propostas pendentes", resumo["propostas_pendentes"], "a"),
    ]
    for coluna, (rotulo, valor, cor) in zip(colunas, cartoes):
        coluna.markdown(f"""<div class="cartao">
          <div class="rot">{rotulo}</div>
          <div class="numero {cor}">{valor}</div>
        </div>""", unsafe_allow_html=True)

    if resumo["por_estado"]:
        st.markdown("#### Por estado")
        st.bar_chart(resumo["por_estado"], color=ROSA, height=220)

    st.markdown("#### Documentos")
    documentos = buscar("/fila/documentos")
    if not documentos:
        st.info("A fila está vazia. Suba um arquivo no armazenamento — ou rode "
                "`python gatilho/disparador.py --semear` — e recarregue.")
    else:
        st.dataframe(
            [{"documento": d["identificador"], "arquivo": d["arquivo"],
              "estado": d["estado"], "fornecedor": d["fornecedor"] or "—",
              "valor": d["valor_total"], "confiança": d["confianca"] or "—",
              "atualizado": quando(d["atualizado_em"])} for d in documentos],
            use_container_width=True, hide_index=True)

    st.caption("Repare: nenhum documento sai de **exceção** sozinho. É essa regra que "
               "impede o agente de tentar de novo a madrugada inteira, gastando token.")


# ── Memória ──────────────────────────────────────────────────────────────────

with memoria_aba:
    dados = buscar("/memoria")
    de_hoje = {l["texto"] for l in buscar("/memoria/hoje")}

    esquerda, direita = st.columns([2.1, 1])
    with esquerda:
        st.markdown(f"#### O que o Deva sabe · {dados['total_de_linhas']} regra(s)")
        if not dados["linhas"]:
            st.info("A memória está vazia. **Isso é bom na primeira execução:** o aluno "
                    "vê o agente começar sem experiência nenhuma.")
        for linha in dados["linhas"]:
            nova = linha["texto"] in de_hoje
            classe = "cartao nova" if nova else "cartao"
            selo = ('<span class="rot c">entrou hoje</span>' if nova
                    else f'<span class="rot">{linha["secao"].replace("_", " ")}</span>')
            st.markdown(f"""<div class="{classe}">
              {selo}
              <div class="regra">{linha['texto']}</div>
              <div class="meta">origem: {linha['origem']} · {linha['data']}</div>
            </div>""", unsafe_allow_html=True)

    with direita:
        st.markdown("#### O arquivo")
        st.caption("É este texto que está no `MEMORY.md` do Blob. Abra o portal do Azure "
                   "e compare — é o mesmo arquivo, com a mesma hora de modificação.")
        st.code(dados["markdown"], language="markdown")


# ── Propostas ────────────────────────────────────────────────────────────────

with propostas_aba:
    pendentes = buscar("/memoria/propostas?situacao=pendente")
    st.markdown(f"#### {len(pendentes)} proposta(s) esperando decisão")
    st.caption("Nada nesta aba influencia uma única decisão do agente. Ele propôs; "
               "quem decide é você.")

    if not auditor.strip():
        st.warning("Escreva seu nome na barra lateral para poder aprovar ou descartar. "
                   "Sem nome, o serviço recusa — e recusa também para o agente.")

    if not pendentes:
        st.info("Nenhuma proposta pendente. Corrija o Deva numa conversa e volte aqui.")

    for proposta in pendentes:
        st.markdown(f"""<div class="cartao pendente">
          <div class="rot a">{proposta['secao'].replace('_', ' ')} ·
              {proposta['identificador']}</div>
          <div class="regra">{proposta['texto']}</div>
          <div class="meta">evidência: {proposta['evidencia']}<br>
              proposta por <code>{proposta['proposta_por']}</code> em
              {quando(proposta['proposta_em'])}</div>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 3])
        aprovar = c1.button("Aprovar", key=f"ap-{proposta['identificador']}",
                            use_container_width=True, disabled=not auditor.strip())
        descartar = c2.button("Descartar", key=f"de-{proposta['identificador']}",
                              use_container_width=True, disabled=not auditor.strip())
        motivo = c3.text_input("motivo do descarte", key=f"mo-{proposta['identificador']}",
                               label_visibility="collapsed",
                               placeholder="por que não vira regra (opcional)")

        if aprovar:
            r = enviar(f"/memoria/propostas/{proposta['identificador']}/aprovar",
                       {"auditor": auditor}, auditor)
            if r is not None and r.status_code == 200:
                st.success("Aprovada. Abra a aba **Memória**: a linha está lá, "
                           "destacada como *entrou hoje*.")
                st.rerun()
            elif r is not None:
                mostrar_erro(r)

        if descartar:
            r = enviar(f"/memoria/propostas/{proposta['identificador']}/descartar",
                       {"auditor": auditor, "motivo": motivo or None}, auditor)
            if r is not None and r.status_code == 200:
                st.info("Descartada. O agente não aprende com o que não foi revisado.")
                st.rerun()
            elif r is not None:
                mostrar_erro(r)

    with st.expander("Já decididas"):
        decididas = [p for p in buscar("/memoria/propostas")
                     if p["situacao"] != "pendente"]
        if not decididas:
            st.caption("Nada decidido ainda.")
        for p in decididas:
            marca = "✅" if p["situacao"] == "aprovada" else "🚫"
            st.markdown(f"{marca} **{p['texto']}**  \n"
                        f"<span class='meta'>{p['situacao']} por {p['decidida_por']} em "
                        f"{quando(p['decidida_em'])}"
                        f"{' · ' + p['motivo_do_descarte'] if p.get('motivo_do_descarte') else ''}"
                        f"</span>", unsafe_allow_html=True)


# ── Exceções ─────────────────────────────────────────────────────────────────

with excecoes_aba:
    parados = [d for d in buscar("/fila/documentos") if d["precisa_de_humano"]]
    st.markdown(f"#### {len(parados)} documento(s) esperando uma pessoa")
    st.caption("Automação boa não é a que resolve tudo: é a que devolve **pouca coisa** "
               "para revisão. Se esta aba estiver sempre cheia, o problema é a regra, "
               "não o modelo.")

    if not parados:
        st.success("Nenhuma exceção parada.")

    for documento in parados:
        st.markdown(f"""<div class="cartao excecao">
          <div class="rot r">{documento['estado']} · {documento['identificador']}</div>
          <div class="regra">{documento['arquivo']}
              {'· ' + documento['fornecedor'] if documento['fornecedor'] else ''}
              {'· R$ ' + format(documento['valor_total'], ',.2f') if documento['valor_total'] else ''}
          </div>
          <div class="meta">{documento['justificativa'] or 'sem justificativa registrada'}
              <br>regra: {documento['regra_aplicada'] or '—'} ·
              confiança: {documento['confianca'] or '—'}</div>
        </div>""", unsafe_allow_html=True)

        if st.button("Liberar como conforme", key=f"lib-{documento['identificador']}",
                     disabled=not auditor.strip()):
            r = enviar(f"/fila/documentos/{documento['identificador']}/liberar",
                       {"estado": "conforme"}, auditor)
            if r is not None and r.status_code == 200:
                st.success("Liberado por você — e o histórico do documento registra "
                           "quem foi.")
                st.rerun()
            elif r is not None:
                mostrar_erro(r)

        with st.expander(f"Histórico de {documento['identificador']}"):
            for evento in documento["historico"]:
                st.text(evento)
