"""
Eva — agente básico em Python.

Um arquivo só, de propósito. Tudo que um agente precisa está aqui, na ordem
em que acontece:

    1. CONFIGURAÇÃO   — chave e modelo vindos do .env
    2. CONTEXTO       — agent.md (quem ela é) + memory.md (o que ela sabe de você)
    3. FERRAMENTAS    — o que ela consegue FAZER além de falar
    4. O LOOP         — o coração do agente
    5. O CHAT         — a interface no terminal

Rode com:  python eva.py
"""

import datetime
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
TEMPERATURA = float(os.getenv("EVA_TEMPERATURA", "0.7"))
MAX_ITERACOES = int(os.getenv("EVA_MAX_ITERACOES", "5"))

_cliente = None


def get_cliente() -> OpenAI:
    """Instancia o cliente da OpenAI — uma vez só, na primeira chamada.

    É nessa função que o modelo entra no projeto.
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
# 2. CONTEXTO — agent.md e memory.md
# ==========================================================================


def carregar_contexto() -> str:
    """Monta o system prompt lendo os dois arquivos de contexto.

    agent.md  = identidade e regras da Eva (quem ela é)
    memory.md = o que ela sabe sobre você (persiste entre execuções)

    Editar esses arquivos muda o comportamento dela sem tocar em Python.
    Isso é de propósito: é o que torna o agente evoluível.
    """
    identidade = AGENT_MD.read_text(encoding="utf-8") if AGENT_MD.exists() else "Você é a Eva."
    memoria = MEMORY_MD.read_text(encoding="utf-8") if MEMORY_MD.exists() else ""

    return f"{identidade}\n\n---\n\n# Memória sobre o usuário\n\n{memoria}"


def salvar_na_memoria(nota: str) -> None:
    """Acrescenta uma linha em memory.md, na seção 'Fatos sobre o usuário'."""
    if not MEMORY_MD.exists():
        MEMORY_MD.write_text("# memory.md — Eva\n\n## Fatos sobre o usuário\n", encoding="utf-8")

    texto = MEMORY_MD.read_text(encoding="utf-8")
    data = datetime.date.today().isoformat()
    linha = f"- [{data}] {nota.strip()}"

    cabecalho = "## Fatos sobre o usuário"
    if cabecalho in texto:
        # Insere logo abaixo do cabeçalho (fato mais recente primeiro).
        antes, depois = texto.split(cabecalho, 1)
        texto = f"{antes}{cabecalho}\n\n{linha}\n{depois.lstrip(chr(10))}"
    else:
        texto = f"{texto.rstrip()}\n\n{cabecalho}\n{linha}\n"

    MEMORY_MD.write_text(texto, encoding="utf-8")


# ==========================================================================
# 3. FERRAMENTAS
# ==========================================================================
#
# Uma tool tem duas metades:
#   - a DECLARAÇÃO (o JSON abaixo): é o que o modelo lê para decidir se chama;
#   - a FUNÇÃO Python: é o que realmente roda na sua máquina.
#
# O modelo nunca executa nada. Ele só devolve "quero chamar X com esses
# argumentos" — quem executa é o seu código, no passo 4.
#
# Para adicionar uma tool nova: escreva a função, adicione a declaração em
# FERRAMENTAS e registre em EXECUTORES. Só isso.


DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]


def que_horas_sao(fuso: str = "America/Sao_Paulo") -> dict:
    """Data e hora atuais. O modelo não sabe que horas são — a tool sabe."""
    try:
        from zoneinfo import ZoneInfo

        agora = datetime.datetime.now(ZoneInfo(fuso))
    except Exception:
        # Fuso inválido ou base de fusos ausente (Windows sem tzdata):
        # cai para a hora local em vez de quebrar.
        agora = datetime.datetime.now()
        fuso = "local"

    return {
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M"),
        "dia_da_semana": DIAS[agora.weekday()],
        "fuso": fuso,
    }


FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "que_horas_sao",
            "description": (
                "Retorna a data e a hora atuais. Use sempre que a pergunta depender "
                "de 'hoje', 'agora', 'que dia é' ou de qualquer cálculo com datas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fuso": {
                        "type": "string",
                        "description": "Fuso IANA, ex: America/Sao_Paulo. Padrão: America/Sao_Paulo.",
                    }
                },
                "required": [],
            },
        },
    }
]

EXECUTORES = {
    "que_horas_sao": que_horas_sao,
}


def executar_ferramenta(nome: str, argumentos: dict) -> str:
    """Executa uma tool e devolve SEMPRE uma string (o modelo só lê texto).

    Erro de tool vira mensagem de erro para o modelo, não crash do programa —
    assim ele pode tentar outro caminho.
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


def responder(
    mensagens: list[dict],
    verboso: bool = False,
    modelo: str | None = None,
    temperatura: float | None = None,
    max_iteracoes: int | None = None,
) -> str:
    """O agente propriamente dito.

    O que diferencia um agente de uma simples chamada de API é ESTE loop:

        manda a conversa + as ferramentas para o modelo
          -> se ele pediu ferramenta: executa, anexa o resultado, repete
          -> se ele respondeu em texto: acabou, essa é a resposta

    `mensagens` é modificada no lugar, então o histórico da conversa
    (incluindo as chamadas de ferramenta) fica preservado entre turnos.
    """
    cliente = get_cliente()

    for _ in range(max_iteracoes or MAX_ITERACOES):
        resposta = cliente.chat.completions.create(
            model=modelo or MODELO,
            messages=cast(list[ChatCompletionMessageParam], mensagens),
            tools=cast(list[ChatCompletionToolParam], FERRAMENTAS),
            temperature=TEMPERATURA if temperatura is None else temperatura,
        )
        recado = resposta.choices[0].message

        # Caso 1: o modelo respondeu em texto. Fim.
        if not recado.tool_calls:
            mensagens.append({"role": "assistant", "content": recado.content})
            return recado.content or ""

        # Caso 2: o modelo quer usar ferramentas.
        mensagens.append(recado.model_dump(exclude_none=True))

        for chamada in recado.tool_calls:
            # A API também pode retornar chamadas do tipo "custom", que não
            # possuem o atributo `function`.
            if chamada.type != "function":
                continue
            nome = chamada.function.name
            try:
                argumentos = json.loads(chamada.function.arguments or "{}")
            except json.JSONDecodeError:
                argumentos = {}

            if verboso:
                print(f"  [tool] {nome}({argumentos})")

            mensagens.append(
                {
                    "role": "tool",
                    "tool_call_id": chamada.id,
                    "content": executar_ferramenta(nome, argumentos),
                }
            )

    return "Atingi o limite de iterações sem concluir. Tente reformular a pergunta."


def responder_stream(
    mensagens: list[dict],
    modelo: str | None = None,
    temperatura: float | None = None,
    max_iteracoes: int | None = None,
):
    """Mesmo loop, em streaming — usado pela interface Streamlit.

    É um GERADOR: em vez de devolver a resposta pronta, ele vai emitindo
    eventos conforme as coisas acontecem. Quem consome decide o que fazer
    com cada um:

        ("ferramenta", {"nome", "argumentos", "resultado"})
        ("texto", "pedaço da resposta")

    A parte chata do streaming com ferramentas: a OpenAI manda a chamada de
    ferramenta em PEDAÇOS (o nome vem numa hora, os argumentos vão chegando
    em fatias de texto). Por isso o dicionário `parciais` abaixo — ele
    remonta cada chamada antes de executar.
    """
    cliente = get_cliente()

    for _ in range(max_iteracoes or MAX_ITERACOES):
        stream = cliente.chat.completions.create(
            model=modelo or MODELO,
            messages=cast(list[ChatCompletionMessageParam], mensagens),
            tools=cast(list[ChatCompletionToolParam], FERRAMENTAS),
            temperature=TEMPERATURA if temperatura is None else temperatura,
            stream=True,
        )

        conteudo = ""
        parciais: dict[int, dict] = {}

        for pedaco in stream:
            if not pedaco.choices:
                continue  # chunk de uso/metadados, sem conteúdo
            delta = pedaco.choices[0].delta

            if delta.content:
                conteudo += delta.content
                yield ("texto", delta.content)

            for tc in delta.tool_calls or []:
                slot = parciais.setdefault(tc.index, {"id": "", "nome": "", "argumentos": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["nome"] += tc.function.name
                if tc.function and tc.function.arguments:
                    slot["argumentos"] += tc.function.arguments

        # Nenhuma ferramenta pedida: a resposta acabou.
        if not parciais:
            mensagens.append({"role": "assistant", "content": conteudo})
            return

        # Registra no histórico o que o modelo pediu...
        chamadas = [parciais[i] for i in sorted(parciais)]
        mensagens.append(
            {
                "role": "assistant",
                "content": conteudo or None,
                "tool_calls": [
                    {
                        "id": c["id"],
                        "type": "function",
                        "function": {"name": c["nome"], "arguments": c["argumentos"] or "{}"},
                    }
                    for c in chamadas
                ],
            }
        )

        # ...e executa cada uma.
        for c in chamadas:
            try:
                argumentos = json.loads(c["argumentos"] or "{}")
            except json.JSONDecodeError:
                argumentos = {}

            resultado = executar_ferramenta(c["nome"], argumentos)
            yield ("ferramenta", {"nome": c["nome"], "argumentos": argumentos, "resultado": resultado})

            mensagens.append({"role": "tool", "tool_call_id": c["id"], "content": resultado})

    yield ("texto", "\n\n_Atingi o limite de iterações sem concluir._")


# ==========================================================================
# 5. O CHAT
# ==========================================================================

AJUDA = """
Comandos:
  /sair              encerra
  /lembrar <fato>    grava um fato em memory.md (persiste entre execuções)
  /memoria           mostra o conteúdo de memory.md
  /limpar            esquece a conversa atual (a memória em arquivo continua)
  /verboso           liga/desliga a exibição das chamadas de ferramenta
  /ajuda             esta lista
"""


def main() -> None:
    try:
        get_cliente()  # falha cedo e com mensagem clara se não houver chave
    except RuntimeError as exc:
        print(f"ERRO: {exc}")
        sys.exit(1)

    mensagens = [{"role": "system", "content": carregar_contexto()}]
    verboso = False

    print(f"Eva — {MODELO}")
    print("Digite /ajuda para ver os comandos.\n")

    while True:
        try:
            entrada = input("você> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté mais.")
            return

        if not entrada:
            continue

        # --- comandos locais (não vão para o modelo) ---
        if entrada in ("/sair", "/quit", "/exit"):
            print("Até mais.")
            return

        if entrada == "/ajuda":
            print(AJUDA)
            continue

        if entrada == "/limpar":
            mensagens = [{"role": "system", "content": carregar_contexto()}]
            print("[conversa reiniciada]\n")
            continue

        if entrada == "/verboso":
            verboso = not verboso
            print(f"[verboso {'ligado' if verboso else 'desligado'}]\n")
            continue

        if entrada == "/memoria":
            print(MEMORY_MD.read_text(encoding="utf-8") if MEMORY_MD.exists() else "[vazia]")
            continue

        if entrada.startswith("/lembrar "):
            nota = entrada[len("/lembrar ") :]
            salvar_na_memoria(nota)
            # Recarrega o system prompt para a Eva já usar o fato novo agora.
            mensagens[0] = {"role": "system", "content": carregar_contexto()}
            print(f"[gravado em memory.md] {nota}\n")
            continue

        # --- turno normal ---
        mensagens.append({"role": "user", "content": entrada})
        try:
            print(f"\neva> {responder(mensagens, verboso=verboso)}\n")
        except Exception as exc:
            print(f"\n[erro ao chamar o modelo] {exc}\n")
            mensagens.pop()  # descarta o turno que falhou


if __name__ == "__main__":
    main()
