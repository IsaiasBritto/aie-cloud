"""
Interface web mínima, em Streamlit.

Este arquivo é SÓ interface. Toda a lógica está no agent.py.
A regra que vale a pena manter enquanto o projeto cresce:

    agent.py = o agente        (terminal, teste, servidor)
    app.py   = uma das caras   (Streamlit hoje; amanhã uma API)

Rode com:  streamlit run app.py
"""

import streamlit as st
from streamlit.runtime import exists as st_runtime_ativo

import agent

# Um app Streamlit precisa ser iniciado pelo comando `streamlit run`. Com
# `python app.py` o script roda sem o runtime: nada aparece na tela e o
# terminal vira uma parede de "missing ScriptRunContext".
if not st_runtime_ativo():
    print("\nEste arquivo é um app Streamlit — não rode com `python app.py`.\n")
    print("Use:\n    streamlit run app.py\n")
    print("Para a versão de terminal, rode:  python agent.py\n")
    raise SystemExit(1)

st.set_page_config(page_title="Agente base", page_icon="🤖")
st.title("🤖 Agente base")

# A chave é checada aqui. get_cliente() é preguiçoso justamente para que
# este arquivo possa mostrar um erro na tela em vez de uma stack trace.
try:
    agent.get_cliente()
except RuntimeError as erro:
    st.error(str(erro))
    st.stop()

# --------------------------------------------------------------------------
# ESTADO
# --------------------------------------------------------------------------
# O Streamlit re-executa este arquivo INTEIRO a cada interação. Tudo que
# precisa sobreviver a isso mora em st.session_state.
#
# São duas listas, de propósito:
#   mensagens -> histórico no formato da API (inclui as chamadas de ferramenta)
#   tela      -> o que o usuário vê (não mostramos JSON de ferramenta na tela)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = [{"role": "system", "content": agent.carregar_contexto()}]
    st.session_state.tela = []

with st.sidebar:
    st.caption(f"Modelo: `{agent.MODELO}`")
    if st.button("Nova conversa", use_container_width=True):
        st.session_state.mensagens = [{"role": "system", "content": agent.carregar_contexto()}]
        st.session_state.tela = []
        st.rerun()

# --------------------------------------------------------------------------
# HISTÓRICO
# --------------------------------------------------------------------------

for papel, texto in st.session_state.tela:
    with st.chat_message(papel):
        st.markdown(texto)

# --------------------------------------------------------------------------
# NOVO TURNO
# --------------------------------------------------------------------------

pergunta = st.chat_input("Escreva sua mensagem")

if pergunta:
    st.session_state.tela.append(("user", pergunta))
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    # Marca onde a resposta começa. Se der erro no meio, tudo daqui para a
    # frente é descartado — senão sobraria uma chamada de ferramenta sem
    # resultado no histórico, e a PRÓXIMA chamada quebraria por causa disso.
    marca = len(st.session_state.mensagens)

    with st.chat_message("assistant"), st.spinner("Pensando..."):
        try:
            resposta = agent.responder(st.session_state.mensagens)
            st.markdown(resposta)
            st.session_state.tela.append(("assistant", resposta))
        except Exception as erro:
            del st.session_state.mensagens[marca:]
            st.error(f"Erro ao chamar o modelo: {erro}")
