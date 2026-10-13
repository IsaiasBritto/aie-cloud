"""
Eva (AWS) — o agente pronto para rodar em produção no ECS Fargate.

Mesma Eva. O que muda é o entorno:

  - autentica por IDENTIDADE: no container, a task role do ECS; na sua
    máquina, o `aws configure`. Nenhuma chave da aplicação no caminho feliz.
  - quando o Bedrock não está disponível (o AWS Academy Learner Lab não o
    libera), o provedor `openai` entra com uma chave de API — guardada no
    Secrets Manager e injetada pelo ECS, nunca na imagem.
  - cada chamada ao modelo vira uma linha JSON no CloudWatch Logs:
    turno, latência, tokens e custo estimado.

O loop, as ferramentas, o agent.md e o memory.md continuam iguais aos da
Eva-local-to-bedrock. Toda a diferença mora em `get_cliente()` e no `telemetria.py`.

    1. CONFIGURAÇÃO   — provedor, região, modelo e credencial
    2. CONTEXTO       — agent.md (quem ela é) + memory.md (o que ela sabe)
    3. FERRAMENTAS    — o que ela consegue FAZER além de falar
    4. O LOOP         — o coração do agente (inalterado)
    5. O CHAT         — a interface no terminal

Local:  python verificar.py  →  python eva.py  ou  streamlit run app.py
Nuvem:  veja Documentacao/GUIA-DEPLOY-CLI.md
"""

import datetime
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

import telemetria

# ==========================================================================
# 1. CONFIGURAÇÃO
# ==========================================================================

load_dotenv()

RAIZ = Path(__file__).resolve().parent
AGENT_MD = RAIZ / "agent.md"
MEMORY_MD = RAIZ / "memory.md"

log = logging.getLogger("eva")

# "bedrock" (padrão: credencial AWS, sem chave) ou "openai" (chave de API,
# para quando o Bedrock não está liberado — caso do Learner Lab).
PROVEDOR = os.getenv("EVA_PROVEDOR", "bedrock").strip().lower()

REGIAO = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

# O MODEL ID do catálogo do Bedrock — ou, melhor, o ID de um PERFIL DE
# INFERÊNCIA (começa com "us." ou "global."). Vários modelos novos só aceitam
# chamada pelo perfil; o ID "nu" devolve ValidationException.
# Ex.: us.amazon.nova-lite-v1:0 · us.anthropic.claude-haiku-4-5-20251001-v1:0
MODELO = (
    os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if PROVEDOR == "openai"
    else os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
)

TEMPERATURA = float(os.getenv("EVA_TEMPERATURA", "0.7"))
MAX_ITERACOES = int(os.getenv("EVA_MAX_ITERACOES", "5"))
MAX_TOKENS = int(os.getenv("EVA_MAX_TOKENS", "1024"))

# Compatibilidade com o app.py, que mostra "DEPLOYMENT" na barra lateral.
DEPLOYMENT = MODELO

_cliente = None

# Preenchido por get_cliente() com o que REALMENTE está em uso. A interface
# mostra isso — se aparecer "chave de API" num ambiente que deveria usar a
# task role, alguém precisa saber.
MODO_ATIVO = "(ainda não conectado)"


class _ClienteOpenAI:
    """Adaptador: fala com a OpenAI, mas expõe `converse()` e `converse_stream()`.

    Por que um adaptador e não um segundo loop: o loop do agente é o ativo
    mais valioso deste código. Duplicá-lo por provedor seria pagar duas vezes
    cada correção. Aqui a tradução fica numa borda só — a mesma ideia do
    `_preparar()`, um nível acima.

    O streaming é SIMULADO (uma chamada normal, emitida como eventos): mantém o
    adaptador curto, e o provedor openai é o caminho de contingência.
    """

    def __init__(self, chave: str) -> None:
        from openai import OpenAI

        self._cli = OpenAI(api_key=chave)

    @staticmethod
    def _para_openai(params: dict) -> dict:
        msgs = [{"role": "system", "content": b["text"]} for b in params.get("system", [])]
        for m in params["messages"]:
            textos = "".join(b.get("text", "") for b in m["content"]).strip()
            if m["role"] == "assistant":
                usos = [b["toolUse"] for b in m["content"] if "toolUse" in b]
                item = {"role": "assistant", "content": textos or None}
                if usos:
                    item["tool_calls"] = [
                        {"id": u["toolUseId"], "type": "function",
                         "function": {"name": u["name"],
                                      "arguments": json.dumps(u.get("input") or {})}}
                        for u in usos
                    ]
                msgs.append(item)
                continue
            for b in m["content"]:
                if "toolResult" in b:
                    r = b["toolResult"]
                    msgs.append({"role": "tool", "tool_call_id": r["toolUseId"],
                                 "content": "".join(c.get("text", "") for c in r["content"])})
            if textos:
                msgs.append({"role": "user", "content": textos})

        modelo = params["modelId"]
        kwargs = {"model": modelo, "messages": msgs,
                  "max_completion_tokens": params["inferenceConfig"]["maxTokens"]}
        # Modelos de raciocínio (gpt-5, o-series) só aceitam a temperatura padrão.
        if not modelo.startswith(("gpt-5", "o1", "o3", "o4")):
            kwargs["temperature"] = params["inferenceConfig"]["temperature"]
        if "toolConfig" in params:
            kwargs["tools"] = [
                {"type": "function", "function": {
                    "name": t["toolSpec"]["name"],
                    "description": t["toolSpec"]["description"],
                    "parameters": t["toolSpec"]["inputSchema"]["json"]}}
                for t in params["toolConfig"]["tools"]
            ]
        return kwargs

    def converse(self, **params) -> dict:
        r = self._cli.chat.completions.create(**self._para_openai(params))
        msg = r.choices[0].message
        blocos = [{"text": msg.content}] if msg.content else []
        for tc in msg.tool_calls or []:
            try:
                entrada = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                entrada = {}
            blocos.append({"toolUse": {"toolUseId": tc.id, "name": tc.function.name,
                                       "input": entrada}})
        uso = r.usage
        return {
            "output": {"message": {"role": "assistant", "content": blocos or [{"text": " "}]}},
            "stopReason": "tool_use" if msg.tool_calls else "end_turn",
            "usage": {"inputTokens": getattr(uso, "prompt_tokens", 0),
                      "outputTokens": getattr(uso, "completion_tokens", 0)},
        }

    def converse_stream(self, **params) -> dict:
        r = self.converse(**params)

        def eventos():
            for i, b in enumerate(r["output"]["message"]["content"]):
                if "toolUse" in b:
                    u = b["toolUse"]
                    yield {"contentBlockStart": {"contentBlockIndex": i, "start": {
                        "toolUse": {"toolUseId": u["toolUseId"], "name": u["name"]}}}}
                    yield {"contentBlockDelta": {"contentBlockIndex": i, "delta": {
                        "toolUse": {"input": json.dumps(u["input"])}}}}
                else:
                    yield {"contentBlockDelta": {"contentBlockIndex": i, "delta": {"text": b["text"]}}}
            yield {"messageStop": {"stopReason": r["stopReason"]}}
            yield {"metadata": {"usage": r["usage"]}}

        return {"stream": eventos()}


def get_cliente():
    """Conecta ao provedor do modelo. Identidade primeiro; chave só por escolha.

    1. BEDROCK (padrão). Nenhuma chave da aplicação. O boto3 acha a credencial
       pela cadeia de sempre — no ECS Fargate, a TASK ROLE (o agente do ECS
       entrega credenciais temporárias ao container); na sua máquina, o
       `aws configure`. Quem decide se pode é a política IAM da role.

    2. OPENAI (`EVA_PROVEDOR=openai`). Para quando o Bedrock não está liberado
       — o Learner Lab. Aí existe um segredo: a chave de API. Ela mora no
       Secrets Manager e o ECS a injeta como variável de ambiente na partida
       do container (`secrets` na task definition). Nunca no código, no .env
       da imagem ou no Terraform em texto puro.

    A interface mostra qual dos dois está ativo. Um provedor trocado em
    silêncio seria pior que um erro: o custo e o contrato de dados mudam junto.
    """
    global _cliente, MODO_ATIVO
    if _cliente is not None:
        return _cliente

    if PROVEDOR == "openai":
        chave = os.getenv("OPENAI_API_KEY", "").strip()
        if not chave:
            raise RuntimeError(
                "EVA_PROVEDOR=openai, mas OPENAI_API_KEY está vazia. Local: preencha o .env. "
                "No ECS: confira o segredo no Secrets Manager e o bloco `secrets` da task definition."
            )
        try:
            _cliente = _ClienteOpenAI(chave)
        except ImportError as exc:
            raise RuntimeError("Falta o pacote openai. Rode: pip install -r requirements.txt") from exc
        MODO_ATIVO = "openai · chave de API (Secrets Manager)"
        return _cliente

    if PROVEDOR != "bedrock":
        raise RuntimeError(f"EVA_PROVEDOR='{PROVEDOR}' não existe. Use bedrock ou openai.")

    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise RuntimeError("Falta o boto3. Rode: pip install -r requirements.txt") from exc

    sessao = boto3.Session(region_name=REGIAO)
    credencial = sessao.get_credentials()
    if credencial is None:
        raise RuntimeError(
            "Nenhuma credencial AWS encontrada. Local: rode `aws configure`. "
            "No ECS: confira o taskRoleArn da task definition."
        )

    # Retentativa adaptativa: o Bedrock devolve ThrottlingException quando a
    # cota de tokens por minuto estoura. O boto3 espera e tenta de novo.
    _cliente = sessao.client(
        "bedrock-runtime",
        config=Config(retries={"mode": "adaptive", "max_attempts": 6}, read_timeout=120),
    )
    MODO_ATIVO = f"bedrock · identidade ({credencial.method})"
    return _cliente


def descrever_conexao() -> dict[str, str]:
    """Resumo da configuração ativa — usado pelo app.py e pelo verificar.py."""
    origem = "(sem credencial)"
    try:
        import boto3

        cred = boto3.Session(region_name=REGIAO).get_credentials()
        if cred is not None:
            origem = cred.method  # env, shared-credentials-file, sso, container-role...
    except Exception:  # noqa: BLE001 — descrição nunca derruba a aplicação
        pass
    return {
        "regiao": REGIAO,
        "modelo": MODELO,
        "credencial": origem,
        "perfil": os.getenv("AWS_PROFILE", "(padrão)"),
        "provedor": PROVEDOR,
        "modo_ativo": MODO_ATIVO,
        "rota": (
            "https://api.openai.com/v1/chat/completions"
            if PROVEDOR == "openai"
            else f"https://bedrock-runtime.{REGIAO}.amazonaws.com/model/{MODELO}/converse"
        ),
    }


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
# O modelo nunca executa nada. Ele só devolve um bloco `toolUse` dizendo
# "quero chamar X com estes argumentos" — quem executa é o seu código, no passo 4.
#
# No Bedrock a declaração se chama `toolSpec` e o JSON Schema vai dentro de
# `inputSchema.json`. É o mesmo schema da versão OpenAI, em outra embalagem.

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
        "toolSpec": {
            "name": "que_horas_sao",
            "description": (
                "Retorna a data e a hora atuais. Use sempre que a pergunta depender "
                "de 'hoje', 'agora', 'que dia é' ou de qualquer cálculo com datas."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "fuso": {
                            "type": "string",
                            "description": "Fuso IANA, ex: America/Sao_Paulo. Padrão: America/Sao_Paulo.",
                        }
                    },
                    "required": [],
                }
            },
        }
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
        return json.dumps(funcao(**(argumentos or {})), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"erro": f"Falha em '{nome}': {exc}"}, ensure_ascii=False)


# ==========================================================================
# 4. O LOOP DO AGENTE
# ==========================================================================
#
# O histórico (`mensagens`) segue a convenção das outras Evas: o primeiro item
# é {"role": "system", "content": "<texto>"} e o usuário entra como
# {"role": "user", "content": "<texto>"}. A API Converse quer outra coisa —
# o system prompt num parâmetro separado e o conteúdo sempre em blocos — e
# `_preparar()` faz essa tradução na hora da chamada. Assim o app.py e o
# terminal não precisam saber que formato o provedor usa.


def _preparar(mensagens: list[dict]) -> tuple[list[dict], list[dict]]:
    """Converte o histórico para o formato da Converse: (system, messages)."""
    system: list[dict] = []
    conversa: list[dict] = []
    for m in mensagens:
        conteudo = m.get("content")
        if m["role"] == "system":
            if conteudo:
                system.append({"text": conteudo})
            continue
        if isinstance(conteudo, str) or conteudo is None:
            conteudo = [{"text": conteudo or " "}]  # bloco de texto vazio é recusado
        # A Converse exige alternância user/assistant: junta vizinhos de mesmo papel.
        if conversa and conversa[-1]["role"] == m["role"]:
            conversa[-1]["content"] = conversa[-1]["content"] + list(conteudo)
        else:
            conversa.append({"role": m["role"], "content": list(conteudo)})
    return system, conversa


def _parametros(mensagens, modelo, temperatura, ferramentas=True, max_tokens=None) -> dict:
    system, conversa = _preparar(mensagens)
    params = {
        "modelId": modelo or MODELO,
        "messages": conversa,
        "inferenceConfig": {
            "temperature": TEMPERATURA if temperatura is None else temperatura,
            "maxTokens": max_tokens or MAX_TOKENS,
        },
    }
    if system:
        params["system"] = system
    if ferramentas:
        params["toolConfig"] = {"tools": FERRAMENTAS}
    return params


def chamar_modelo(cliente, mensagens, modelo=None, temperatura=None, ferramentas=True,
                  max_tokens=None, turno_id=None, iteracao=1) -> dict:
    """O único ponto do código que chama o modelo sem streaming — e o mede.

    Devolve o dicionário da Converse:
        resposta["output"]["message"]  -> {"role": "assistant", "content": [blocos]}
        resposta["stopReason"]         -> "end_turn" | "tool_use" | "max_tokens" ...
        resposta["usage"]              -> {"inputTokens", "outputTokens", "totalTokens"}

    Como TODA chamada sem streaming passa por aqui, a telemetria vale para
    `responder()` e para o `verificar.py` de graça.
    """
    params = _parametros(mensagens, modelo, temperatura, ferramentas, max_tokens)
    with telemetria.medir_chamada(params["modelId"], streaming=False, turno_id=turno_id,
                                  iteracao=iteracao, provedor=PROVEDOR) as medicao:
        resposta = cliente.converse(**params)
        uso = resposta.get("usage", {})
        medicao.registrar_uso(entrada=uso.get("inputTokens", 0), saida=uso.get("outputTokens", 0))
        return resposta


def _executar_pedidos(blocos: list[dict], verboso: bool = False):
    """Roda cada `toolUse` pedido e devolve (mensagem_de_resultados, eventos)."""
    resultados, eventos = [], []
    for bloco in blocos:
        uso = bloco.get("toolUse")
        if not uso:
            continue
        nome, argumentos = uso["name"], uso.get("input") or {}
        if verboso:
            print(f"  [tool] {nome}({argumentos})")
        resultado = executar_ferramenta(nome, argumentos)
        eventos.append({"nome": nome, "argumentos": argumentos, "resultado": resultado})
        resultados.append(
            {"toolResult": {"toolUseId": uso["toolUseId"], "content": [{"text": resultado}]}}
        )
    # No Bedrock, o resultado da ferramenta volta numa mensagem do papel "user".
    return {"role": "user", "content": resultados}, eventos


def _texto(blocos: list[dict]) -> str:
    return "".join(b.get("text", "") for b in blocos)


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
          -> se ele parou com stopReason == "tool_use": executa, anexa, repete
          -> se ele respondeu em texto: acabou, essa é a resposta

    `mensagens` é modificada no lugar, então o histórico da conversa
    (incluindo as chamadas de ferramenta) fica preservado entre turnos.
    """
    cliente = get_cliente()
    turno = telemetria.novo_turno()  # todas as voltas desta pergunta somam no mesmo turno

    for volta in range(1, (max_iteracoes or MAX_ITERACOES) + 1):
        resposta = chamar_modelo(cliente, mensagens, modelo, temperatura,
                                 turno_id=turno, iteracao=volta)
        blocos = resposta["output"]["message"]["content"]
        mensagens.append({"role": "assistant", "content": blocos})

        # Caso 1: o modelo respondeu em texto. Fim.
        if resposta.get("stopReason") != "tool_use":
            return _texto(blocos)

        # Caso 2: o modelo quer usar ferramentas.
        retorno, _ = _executar_pedidos(blocos, verboso)
        mensagens.append(retorno)

    return "Atingi o limite de iterações sem concluir. Tente reformular a pergunta."


def responder_stream(
    mensagens: list[dict],
    modelo: str | None = None,
    temperatura: float | None = None,
    max_iteracoes: int | None = None,
):
    """Mesmo loop, em streaming — usado pela interface Streamlit.

    É um GERADOR: emite eventos conforme as coisas acontecem.

        ("ferramenta", {"nome", "argumentos", "resultado"})
        ("texto", "pedaço da resposta")

    A parte chata do streaming com ferramentas: a `converse_stream` manda o
    pedido de ferramenta em PEDAÇOS — o nome chega no `contentBlockStart` e os
    argumentos vão chegando como fatias de JSON nos `contentBlockDelta`. O
    dicionário `blocos` remonta cada bloco pelo índice antes de executar.
    """
    cliente = get_cliente()
    turno = telemetria.novo_turno()

    for volta in range(1, (max_iteracoes or MAX_ITERACOES) + 1):
        params = _parametros(mensagens, modelo, temperatura)

        blocos: dict[int, dict] = {}
        motivo = None

        # A medição envolve o CONSUMO do stream, não só a abertura dele —
        # senão mediríamos o tempo até o primeiro byte, não a chamada inteira.
        # Os tokens chegam no último evento (`metadata`).
        with telemetria.medir_chamada(params["modelId"], streaming=True, turno_id=turno,
                                      iteracao=volta, provedor=PROVEDOR) as medicao:
            stream = cliente.converse_stream(**params)["stream"]
            for evento in stream:
                if "contentBlockStart" in evento:
                    ini = evento["contentBlockStart"]
                    uso = ini.get("start", {}).get("toolUse")
                    if uso:
                        blocos[ini["contentBlockIndex"]] = {
                            "toolUse": {"toolUseId": uso["toolUseId"], "name": uso["name"], "input": ""}
                        }
                elif "contentBlockDelta" in evento:
                    d = evento["contentBlockDelta"]
                    delta, i = d["delta"], d["contentBlockIndex"]
                    if "text" in delta:
                        blocos.setdefault(i, {"text": ""})["text"] += delta["text"]
                        yield ("texto", delta["text"])
                    elif "toolUse" in delta:
                        blocos[i]["toolUse"]["input"] += delta["toolUse"].get("input", "")
                elif "messageStop" in evento:
                    motivo = evento["messageStop"].get("stopReason")
                elif "metadata" in evento:
                    uso = evento["metadata"].get("usage", {})
                    medicao.registrar_uso(entrada=uso.get("inputTokens", 0),
                                          saida=uso.get("outputTokens", 0))

        # Remonta a mensagem do assistente na ordem dos blocos.
        conteudo = []
        for i in sorted(blocos):
            b = blocos[i]
            if "toolUse" in b:
                try:
                    b["toolUse"]["input"] = json.loads(b["toolUse"]["input"] or "{}")
                except json.JSONDecodeError:
                    b["toolUse"]["input"] = {}
                conteudo.append(b)
            elif b.get("text"):
                conteudo.append(b)
        mensagens.append({"role": "assistant", "content": conteudo or [{"text": " "}]})

        # Nenhuma ferramenta pedida: a resposta acabou.
        if motivo != "tool_use":
            return

        retorno, eventos = _executar_pedidos(conteudo)
        for ev in eventos:
            yield ("ferramenta", ev)
        mensagens.append(retorno)

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
        get_cliente()  # falha cedo e com mensagem clara se não houver credencial
    except RuntimeError as exc:
        print(f"ERRO: {exc}")
        sys.exit(1)

    mensagens = [{"role": "system", "content": carregar_contexto()}]
    verboso = False

    telemetria.iniciar("eva-cli")
    print(f"Eva na AWS — {MODO_ATIVO} · modelo '{MODELO}'")
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
        tamanho = len(mensagens)
        mensagens.append({"role": "user", "content": entrada})
        try:
            print(f"\neva> {responder(mensagens, verboso=verboso)}\n")
        except Exception as exc:
            print(f"\n[erro ao chamar o modelo] {exc}\n")
            del mensagens[tamanho:]  # descarta o turno inteiro que falhou


if __name__ == "__main__":
    main()
