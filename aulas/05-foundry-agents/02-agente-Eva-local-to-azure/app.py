"""
Eva — interface visual em Streamlit.

Este arquivo é SÓ interface. Toda a inteligência continua no eva.py:
o loop, as ferramentas e a leitura do agent.md/memory.md são importados
de lá. A regra que vale a pena manter enquanto o projeto cresce:

    eva.py  = o agente        (roda no terminal, num teste, num servidor)
    app.py  = uma das caras   (Streamlit hoje; amanhã pode ser uma API)

Rode com:  streamlit run app.py
"""

import json

import streamlit as st
from streamlit.runtime import exists as st_runtime_ativo

import eva

# ==========================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================================

# Um app Streamlit precisa ser iniciado pelo comando `streamlit run`. Com
# `python app.py` o script roda sem o runtime: nada aparece na tela e o
# terminal vira uma parede de "missing ScriptRunContext". O aviso abaixo troca
# essa confusão por uma instrução.
if not st_runtime_ativo():
    print("\nEste arquivo é um app Streamlit — não rode com `python app.py`.\n")
    print("Use:\n    streamlit run app.py\n")
    print("Para a versão de terminal, rode:  python eva.py\n")
    raise SystemExit(1)

st.set_page_config(page_title="Eva no Foundry", page_icon="☁️", layout="centered")

# A chave é checada aqui, uma vez. get_cliente() é preguiçoso justamente
# para que este arquivo possa decidir como mostrar o erro.
try:
    getattr(eva, "get_cliente")()
except RuntimeError as erro:
    st.error(str(erro))
    st.info(
        "Copie `.env.example` para `.env` e preencha o endpoint, o deployment e a chave "
        "do seu recurso no Foundry. Depois rode `python verificar.py` no terminal."
    )
    st.stop()


# ==========================================================================
# ESTADO DA SESSÃO
# ==========================================================================
#
# O Streamlit re-executa este arquivo INTEIRO a cada interação. Tudo que
# precisa sobreviver a isso mora em st.session_state.
#
# São duas listas, de propósito:
#   mensagens -> o histórico no formato da API (inclui as chamadas de tool)
#   tela      -> o que o usuário vê (não mostramos JSON de tool como balão)


def iniciar_conversa() -> None:
    st.session_state.mensagens = [{"role": "system", "content": eva.carregar_contexto()}]
    st.session_state.tela = []


if "mensagens" not in st.session_state:
    iniciar_conversa()


def recarregar_contexto() -> None:
    """Reinjeta agent.md + memory.md no prompt, sem perder a conversa."""
    st.session_state.mensagens[0] = {"role": "system", "content": eva.carregar_contexto()}


# ==========================================================================
# BARRA LATERAL — configuração e edição do contexto
# ==========================================================================

with st.sidebar:
    st.header("Eva no Foundry")

    # --- qual modelo usar ---
    # No Azure, "escolher o modelo" = escolher o DEPLOYMENT. Se você implantou
    # mais de um modelo no mesmo recurso, troque o nome aqui e a próxima
    # mensagem já vai para o outro. Nada mais no código muda.
    modelo = st.text_input(
        "Deployment",
        value=eva.DEPLOYMENT,
        help="Nome do deployment no Foundry — não o nome do modelo.",
    )

    conexao = eva.descrever_conexao()
    st.caption(f"☁️ {conexao['endpoint']}")
    st.caption(f"🔑 auth por {conexao['autenticacao']}")

    temperatura = st.slider(
        "Temperatura", 0.0, 1.0, eva.TEMPERATURA, 0.1,
        help="0 = objetiva e previsível · 1 = criativa e variada",
    )

    max_iteracoes = st.slider(
        "Máx. de iterações", 1, 10, eva.MAX_ITERACOES,
        help="Quantas rodadas de ferramenta ela pode fazer antes de responder.",
    )

    mostrar_ferramentas = st.checkbox("Mostrar rastro das ferramentas", value=True)

    if st.button("Nova conversa", use_container_width=True):
        iniciar_conversa()
        st.rerun()

    st.divider()

    # --- memory.md ---
    with st.expander("memory.md — o que ela sabe de você"):
        texto_memoria = eva.MEMORY_MD.read_text(encoding="utf-8") if eva.MEMORY_MD.exists() else ""
        novo_memoria = st.text_area("memória", texto_memoria, height=260, label_visibility="collapsed")
        if st.button("Salvar memória", use_container_width=True):
            eva.MEMORY_MD.write_text(novo_memoria, encoding="utf-8")
            recarregar_contexto()
            st.success("Salvo e reinjetado no prompt.")

    # --- agent.md ---
    with st.expander("agent.md — quem ela é"):
        texto_agente = eva.AGENT_MD.read_text(encoding="utf-8") if eva.AGENT_MD.exists() else ""
        novo_agente = st.text_area("identidade", texto_agente, height=260, label_visibility="collapsed")
        if st.button("Salvar identidade", use_container_width=True):
            eva.AGENT_MD.write_text(novo_agente, encoding="utf-8")
            recarregar_contexto()
            st.success("Salvo. Vale a partir da próxima mensagem.")

    st.caption(f"{len(st.session_state.mensagens)} mensagens no contexto")


# ==========================================================================
# RASTRO DAS FERRAMENTAS
# ==========================================================================


def desenhar_ferramenta(uso: dict) -> None:
    """Mostra uma chamada de ferramenta: o que foi pedido e o que voltou."""
    with st.expander(f"🔧 {uso['nome']}", expanded=False):
        st.caption("argumentos")
        st.code(json.dumps(uso["argumentos"], ensure_ascii=False, indent=2), language="json")
        st.caption("resultado")
        try:
            bonito = json.dumps(json.loads(uso["resultado"]), ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            bonito = uso["resultado"]
        st.code(bonito, language="json")


# ==========================================================================
# HISTÓRICO NA TELA
# ==========================================================================

for turno in st.session_state.tela:
    with st.chat_message(turno["papel"]):
        if mostrar_ferramentas:
            for uso in turno.get("ferramentas", []):
                desenhar_ferramenta(uso)
        st.markdown(turno["texto"])


# ==========================================================================
# NOVO TURNO
# ==========================================================================

pergunta = st.chat_input("Fale com a Eva")

if pergunta:
    st.session_state.tela.append({"papel": "user", "texto": pergunta, "ferramentas": []})
    st.session_state.mensagens.append({"role": "user", "content": pergunta})

    # Marca onde a resposta começa. Se der erro no meio, tudo daqui para a
    # frente é descartado — senão sobraria uma chamada de ferramenta sem
    # resultado no histórico, e a PRÓXIMA chamada quebraria por causa disso.
    marca = len(st.session_state.mensagens)

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        area_ferramentas = st.container()  # as tools aparecem acima do texto
        area_texto = st.empty()

        texto = ""
        usos: list[dict] = []

        try:
            fluxo = eva.responder_stream(
                st.session_state.mensagens,
                modelo=modelo,
                temperatura=temperatura,
                max_iteracoes=max_iteracoes,
            )
            for tipo, dado in fluxo:
                if tipo == "ferramenta":
                    if isinstance(dado, dict):
                        usos.append(dado)
                        if mostrar_ferramentas:
                            with area_ferramentas:
                                desenhar_ferramenta(dado)
                elif tipo == "texto":
                    if isinstance(dado, str):
                        texto += dado
                    area_texto.markdown(texto + "▌")  # cursor piscando

            area_texto.markdown(texto)
            st.session_state.tela.append(
                {"papel": "assistant", "texto": texto, "ferramentas": usos}
            )

        except Exception as erro:
            area_texto.empty()
            del st.session_state.mensagens[marca:]  # limpa a resposta pela metade
            st.error(f"Erro ao chamar o modelo: {erro}")
            st.caption("Sua mensagem foi mantida — mande de novo ou reformule.")
