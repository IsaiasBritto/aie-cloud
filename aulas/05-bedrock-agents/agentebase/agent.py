"""
Agente base — esqueleto mínimo.

Este é o núcleo do agente. Ele não sabe nada sobre interface: pode ser
usado pelo terminal (o `main()` no fim do arquivo), pelo `app.py`
(Streamlit), por um teste ou por uma API.

Estrutura, na ordem em que as coisas acontecem:

    1. CONFIGURAÇÃO   — chave e modelo, vindos do .env
    2. CONTEXTO       — agent.md (quem ele é) + memory.md (o que sabe)
    3. FERRAMENTAS    — o que ele consegue FAZER além de falar
    4. O LOOP         — o coração do agente
    5. O TERMINAL     — a interface mais simples possível

Rode com:  python agent.py
"""

import json
import os
import sys
from typing import cast
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

# ==========================================================================
# 1. CONFIGURAÇÃO
# ==========================================================================

load_dotenv()

RAIZ = Path(__file__).resolve().parent
AGENT_MD = RAIZ / "agent.md"
MEMORY_MD = RAIZ / "memory.md"

MODELO = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURA = float(os.getenv("AGENTE_TEMPERATURA", "0.7"))
MAX_ITERACOES = int(os.getenv("AGENTE_MAX_ITERACOES", "5"))

_cliente = None


def get_cliente() -> OpenAI:
    """Instancia o cliente da OpenAI — uma vez só, na primeira chamada.

    AQUI que o modelo entra no projeto. Trocar de provedor começa por aqui.
    """
    global _cliente
    if _cliente is None:
        chave = os.getenv("OPENAI_API_KEY")
        if not chave:
            raise RuntimeError(
                "OPENAI_API_KEY não encontrada. Copie .env.example para .env e coloque sua chave."
            )
        _cliente = OpenAI(api_key=chave)
    return _cliente


# ==========================================================================
# 2. CONTEXTO
# ==========================================================================


def carregar_contexto() -> str:
    """Monta o prompt de sistema a partir dos dois arquivos de contexto.

    agent.md  = identidade e regras do agente
    memory.md = o que ele sabe sobre o usuário (persiste entre execuções)

    Editar esses arquivos muda o comportamento sem tocar em Python.
    """
    identidade = AGENT_MD.read_text(encoding="utf-8") if AGENT_MD.exists() else "Você é um assistente."
    memoria = MEMORY_MD.read_text(encoding="utf-8") if MEMORY_MD.exists() else ""
    return f"{identidade}\n\n---\n\n# Memória\n\n{memoria}"


# ==========================================================================
# 3. FERRAMENTAS
# ==========================================================================
#
# Uma ferramenta tem duas metades:
#   - a DECLARAÇÃO (o JSON em FERRAMENTAS): é o que o modelo lê para decidir
#     se chama. A `description` importa mais que o código.
#   - a FUNÇÃO Python: é o que realmente roda na sua máquina.
#
# O modelo NUNCA executa nada. Ele só devolve "quero chamar X com estes
# argumentos" — quem executa é o seu código, no passo 4.
#
# >>> A ferramenta abaixo é só um EXEMPLO. Apague e coloque as suas. <<<


def somar(a: float, b: float) -> dict:
    """Exemplo de ferramenta. Modelos erram conta; Python não."""
#    print(f"[somar] executando de verdade: {a} + {b}")
    return {"resultado": a + b}


FERRAMENTAS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "somar",
            "description": "Soma dois números. Use sempre que precisar de uma adição exata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "Primeiro número."},
                    "b": {"type": "number", "description": "Segundo número."},
                },
                "required": ["a", "b"],
            },
        },
    }
]

EXECUTORES = {
    "somar": somar,
}


def executar_ferramenta(nome: str, argumentos: dict) -> str:
    """Executa uma ferramenta e devolve SEMPRE uma string (o modelo só lê texto).

    Erro vira mensagem de erro para o modelo, não crash do programa — assim
    ele consegue tentar outro caminho.
    """
    funcao = EXECUTORES.get(nome)
    if funcao is None:
        return json.dumps({"erro": f"Ferramenta '{nome}' não existe."}, ensure_ascii=False)
    try:
        return json.dumps(funcao(**argumentos), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"erro": f"Falha em '{nome}': {exc}"}, ensure_ascii=False)


# ==========================================================================
# 4. O LOOP DO AGENTE
# ==========================================================================


def responder(mensagens: list[ChatCompletionMessageParam], verboso: bool = False) -> str:
    """O agente propriamente dito.

    O que diferencia um agente de uma simples chamada de API é ESTE loop:

        manda a conversa + as ferramentas para o modelo
          -> pediu ferramenta? executa, anexa o resultado, repete
          -> respondeu em texto?  acabou, essa é a resposta

    `mensagens` é modificada no lugar, então o histórico (incluindo as
    chamadas de ferramenta) fica preservado entre turnos.
    """
    cliente = get_cliente()

    for _ in range(MAX_ITERACOES):
        resposta = cliente.chat.completions.create(
            model=MODELO,
            messages=mensagens,
            tools=FERRAMENTAS,
            temperature=TEMPERATURA,
        )
        recado = resposta.choices[0].message

        # Caso 1: respondeu em texto. Fim.
        if not recado.tool_calls:
            mensagens.append({"role": "assistant", "content": recado.content})
            return recado.content or ""

        # Caso 2: quer usar ferramentas.
        mensagens.append(cast(ChatCompletionMessageParam, recado.model_dump(exclude_none=True)))

        for chamada in recado.tool_calls:
            funcao = getattr(chamada, "function", None)
            if funcao is None:
                nome = getattr(chamada, "name", "desconhecida")
                argumentos = {}
            else:
                nome = funcao.name
                try:
                    argumentos = json.loads(funcao.arguments or "{}")
                except json.JSONDecodeError:
                    argumentos = {}

            if verboso:
                print(f"  [ferramenta] {nome}({argumentos})")

            mensagens.append(
                {
                    "role": "tool",
                    "tool_call_id": chamada.id,
                    "content": executar_ferramenta(nome, argumentos),
                }
            )

    return "Atingi o limite de iterações sem concluir. Tente reformular a pergunta."


# ==========================================================================
# 5. O TERMINAL
# ==========================================================================


def main() -> None:
    try:
        get_cliente()  # falha cedo e com mensagem clara se não houver chave
    except RuntimeError as exc:
        print(f"ERRO: {exc}")
        sys.exit(1)

    mensagens: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": carregar_contexto()}
    ]
    print(f"Agente base — {MODELO}. Digite /sair para encerrar.\n")

    while True:
        try:
            entrada = input("você> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté mais.")
            return

        if not entrada:
            continue
        if entrada in ("/sair", "/quit", "/exit"):
            print("Até mais.")
            return

        mensagens.append({"role": "user", "content": entrada})
        try:
            print(f"\nagente> {responder(mensagens, verboso=True)}\n")
        except Exception as exc:
            print(f"\n[erro ao chamar o modelo] {exc}\n")
            mensagens.pop()  # descarta o turno que falhou


if __name__ == "__main__":
    main()
