"""
Eva (Azure) — o agente pronto para rodar em produção no Azure.

Mesma Eva. O que muda é o entorno:

  - autentica por IDENTIDADE (Managed Identity no container, `az login` na
    sua máquina). Sem chave em lugar nenhum no caminho feliz.
  - a chave só existe como FALLBACK, guardada no Key Vault.
  - cada chamada ao modelo vira telemetria no Application Insights:
    latência, tokens e custo estimado.

O loop, as ferramentas, o agent.md e o memory.md continuam iguais aos da
primeira Eva. Toda a diferença mora em `get_cliente()` e no `telemetria.py`.

    1. CONFIGURAÇÃO   — endpoint, deployment e autenticação
    2. CONTEXTO       — agent.md (quem ela é) + memory.md (o que ela sabe)
    3. FERRAMENTAS    — o que ela consegue FAZER além de falar
    4. O LOOP         — o coração do agente (inalterado)
    5. O CHAT         — a interface no terminal

Local:  python verificar.py  →  python eva.py  ou  streamlit run app.py
Nuvem:  veja GUIA-DEPLOY-CLI.md ou GUIA-DEPLOY-PORTAL.md
"""

import datetime
import json
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import telemetria

# ==========================================================================
# 1. CONFIGURAÇÃO
# ==========================================================================

load_dotenv()

log = logging.getLogger("eva")

RAIZ = Path(__file__).resolve().parent
AGENT_MD = RAIZ / "agent.md"
MEMORY_MD = RAIZ / "memory.md"

def _normalizar_endpoint(bruto: str) -> str:
    """Aceita qualquer uma das URLs que o portal do Foundry mostra e devolve só o host.

    O portal exibe endpoints diferentes em telas diferentes, e é fácil colar o
    errado. Todos estes viram `https://meu-recurso.services.ai.azure.com`:

        https://meu-recurso.services.ai.azure.com/api/projects/meu-projeto
        https://meu-recurso.services.ai.azure.com/openai/deployments/gpt-5.4-mini/...
        https://meu-recurso.services.ai.azure.com/

    Os dois domínios (.openai.azure.com e .services.ai.azure.com) servem a rota
    /openai/v1/ — não precisa trocar um pelo outro.
    """
    url = (bruto or "").strip().rstrip("/")
    if not url:
        return ""
    # Corta qualquer caminho depois do host (o código acrescenta /openai/v1/).
    if "://" in url:
        esquema, resto = url.split("://", 1)
        host = resto.split("/", 1)[0]
        return f"{esquema}://{host}"
    return url


# Endpoint do SEU recurso no Foundry.
# Ex.: https://meu-recurso.services.ai.azure.com  (ou .openai.azure.com)
ENDPOINT_BRUTO = os.getenv("AZURE_FOUNDRY_ENDPOINT", "")
ENDPOINT = _normalizar_endpoint(ENDPOINT_BRUTO)

# ATENÇÃO: aqui vai o NOME DO DEPLOYMENT, não o nome do modelo.
# Foi você quem escolheu esse nome ao implantar o modelo no portal.
DEPLOYMENT = os.getenv("AZURE_FOUNDRY_DEPLOYMENT", "gpt-5.4-mini")

# "entra" (padrão: Managed Identity no container, az login na sua máquina)
# ou "chave" (força o uso da chave, útil para depurar).
AUTENTICACAO = os.getenv("AZURE_FOUNDRY_AUTH", "entra").strip().lower()

# Preenchido por get_cliente() com o que REALMENTE funcionou. A interface mostra
# isso — se aparecer "chave (fallback)" em produção, a Managed Identity está
# quebrada e alguém precisa saber.
MODO_ATIVO = "(ainda não conectado)"

TEMPERATURA = float(os.getenv("EVA_TEMPERATURA", "0.7"))
MAX_ITERACOES = int(os.getenv("EVA_MAX_ITERACOES", "5"))

# Compatibilidade com o resto do código, que fala "MODELO".
# No Azure, o que você passa em `model=` é o nome do deployment.
MODELO = DEPLOYMENT

_cliente = None
# Preenchido só quando a autenticação é por identidade. Guardado porque o token
# do Entra expira (~1h) e precisa ser renovado — ver `chamar_modelo()`.
_token_provider = None


def _cliente_entra(base_url: str):
    """Cliente autenticado por identidade — SEM chave nenhuma.

    `DefaultAzureCredential` tenta várias fontes, em ordem. As duas que
    importam aqui:

      - dentro do Container App: a Managed Identity do próprio container.
        Ninguém digitou credencial em lugar nenhum; o Azure entrega o token.
      - na sua máquina: a sessão do `az login`.

    O mesmo código roda nos dois lugares. É por isso que "funciona local" e
    "funciona na nuvem" deixam de ser dois caminhos diferentes.

    Usa o cliente `OpenAI` comum — o MESMO do modo chave, com a MESMA rota.
    Só muda a credencial: em vez da chave, um token do Entra no header
    `Authorization: Bearer`.

    NÃO troque para `AzureOpenAI` aqui. Ele foi feito para a rota clássica
    (`/openai/deployments/<nome>/...`) e reescreve o caminho da URL, inserindo
    `/deployments/<modelo>/`. Com a base_url da v1 o resultado é uma rota
    híbrida que não existe:

        certo:    .../openai/v1/chat/completions
        quebrado: .../openai/v1/deployments/eva-aula/chat/completions  → 404

    O erro que aparece é `404 Resource not found`, que engana: parece nome de
    deployment errado ou falta de permissão, e não é nenhum dos dois.

    A contrapartida — o token expira em ~1h e o `OpenAI` não renova sozinho —
    está resolvida no `chamar_modelo()`, que renova antes de cada requisição.
    """
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    global _token_provider
    # O provider tem cache interno: só vai à rede quando falta pouco para
    # expirar. Chamá-lo a cada requisição é barato.
    _token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return OpenAI(base_url=base_url, api_key=_token_provider())


def _cliente_chave(base_url: str, chave: str):
    """Cliente autenticado por chave — o caminho de fallback."""
    return OpenAI(base_url=base_url, api_key=chave)


def get_cliente():
    """Conecta ao Foundry: identidade primeiro, chave só se a identidade falhar.

    A ordem importa, e é a razão de este projeto existir:

      1. IDENTIDADE (padrão). Nenhum segredo no código, no .env, na imagem nem
         nas variáveis de ambiente. O container prova quem é, e o Azure decide
         se pode.

      2. CHAVE (fallback). Vem do Key Vault, entregue como variável de ambiente
         pelo Container Apps. Só entra em cena se a identidade falhar — e
         quando entra, a interface avisa, porque isso é um problema a
         investigar, não um estado normal.

    Um fallback silencioso seria pior que não ter fallback nenhum: a aplicação
    seguiria de pé com a Managed Identity quebrada e ninguém saberia.
    """
    global _cliente, MODO_ATIVO
    if _cliente is not None:
        return _cliente

    if not ENDPOINT:
        raise RuntimeError(
            "AZURE_FOUNDRY_ENDPOINT não configurado. Local: copie .env.example para .env. "
            "No Azure: é uma variável de ambiente do Container App."
        )

    # A rota /openai/v1/ é a superfície compatível com OpenAI do Foundry.
    base_url = f"{ENDPOINT}/openai/v1/"
    chave = os.getenv("AZURE_FOUNDRY_API_KEY")

    # Modo chave explícito: pula a identidade de propósito (útil para depurar).
    if AUTENTICACAO == "chave":
        if not chave:
            raise RuntimeError("AZURE_FOUNDRY_AUTH=chave, mas AZURE_FOUNDRY_API_KEY está vazia.")
        _cliente = _cliente_chave(base_url, chave)
        MODO_ATIVO = "chave (escolhido)"
        return _cliente

    try:
        _cliente = _cliente_entra(base_url)
        MODO_ATIVO = "identidade (Managed Identity / az login)"
        return _cliente
    except Exception as exc:  # noqa: BLE001 — qualquer falha vira tentativa de fallback
        log.warning("Autenticação por identidade falhou: %s", exc)
        if not chave:
            raise RuntimeError(
                "Não consegui autenticar por identidade e não há chave de fallback.\n"
                f"Causa: {exc}\n"
                "No Azure: confira se o Container App tem Managed Identity e a role "
                "'Cognitive Services OpenAI User' no recurso do Foundry.\n"
                "Na sua máquina: rode `az login`."
            ) from exc
        _cliente = _cliente_chave(base_url, chave)
        MODO_ATIVO = "chave (FALLBACK — a identidade falhou)"
        return _cliente


def descrever_conexao() -> dict[str, str]:
    """Resumo da configuração ativa — usado pelo app.py e pelo verificar.py."""
    return {
        "endpoint": ENDPOINT or "(não configurado)",
        "endpoint_bruto": ENDPOINT_BRUTO.strip() or "(não configurado)",
        "deployment": DEPLOYMENT,
        "autenticacao": AUTENTICACAO,
        "modo_ativo": MODO_ATIVO,
        "chave_disponivel": "sim" if os.getenv("AZURE_FOUNDRY_API_KEY") else "não",
        "rota": f"{ENDPOINT}/openai/v1/" if ENDPOINT else "(não configurado)",
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


# --------------------------------------------------------------------------
# Compatibilidade entre famílias de modelo
# --------------------------------------------------------------------------
#
# Nem todo modelo aceita os mesmos parâmetros. Os modelos de raciocínio mais
# novos (família GPT-5, o1/o3) recusam `max_tokens` (querem
# `max_completion_tokens`) e, alguns, `temperature` diferente do padrão.
#
# Em vez de você decorar essa tabela, o código aprende sozinho: na primeira
# recusa ele lê QUAL parâmetro o serviço rejeitou, ajusta e repete a chamada.
# O ajuste fica guardado, então isso acontece no máximo uma vez por parâmetro.

RENOMEAR = {"max_tokens": "max_completion_tokens"}
_ajustes_aprendidos: dict[str, str | None] = {}   # parâmetro -> novo nome, ou None = remover


def _param_recusado(exc: Exception) -> str | None:
    """Descobre qual parâmetro o serviço recusou, lendo o corpo do erro."""
    corpo = getattr(exc, "body", None)
    if isinstance(corpo, dict):
        erro = corpo.get("error") or {}
        if erro.get("code") in ("unsupported_parameter", "unsupported_value") and erro.get("param"):
            return str(erro["param"])
    achado = re.search(r"[Uu]nsupported (?:parameter|value): '([^']+)'", str(exc))
    return achado.group(1) if achado else None


def _criar_adaptando(cliente, **kwargs):
    """Faz a chamada, ajustando parâmetros que este modelo recusar."""
    for antigo, novo in _ajustes_aprendidos.items():
        if antigo in kwargs:
            valor = kwargs.pop(antigo)
            if novo:
                kwargs[novo] = valor

    for _ in range(4):  # no máximo 4 ajustes; evita laço infinito
        try:
            return cliente.chat.completions.create(**kwargs)
        except Exception as exc:
            param = _param_recusado(exc)
            if not param or param not in kwargs:
                raise
            novo = RENOMEAR.get(param)
            _ajustes_aprendidos[param] = novo
            valor = kwargs.pop(param)
            if novo:
                kwargs[novo] = valor
    raise RuntimeError("Não consegui ajustar os parâmetros para este modelo.")


def chamar_modelo(cliente, **kwargs):
    """Chama o modelo: adapta os parâmetros E mede a chamada.

    É o único ponto do código que fala com a API — então compatibilidade e
    telemetria valem para `responder()` e `responder_stream()` de graça.

    Chamada em streaming NÃO é medida aqui: a resposta é um gerador que só
    será consumido depois, então o tempo real e os tokens só se conhecem lá
    na frente. Quem instrumenta o streaming é `responder_stream()`.
    """
    # Autenticação por identidade: o token vale ~1h. Sem isto, um container que
    # fica de pé o dia todo começa a tomar 401 depois da primeira hora.
    if _token_provider is not None:
        cliente.api_key = _token_provider()

    if kwargs.get("stream"):
        return _criar_adaptando(cliente, **kwargs)

    with telemetria.medir_chamada(kwargs.get("model", "?"), streaming=False) as medicao:
        resposta = _criar_adaptando(cliente, **kwargs)
        uso = getattr(resposta, "usage", None)
        if uso:
            medicao.registrar_uso(
                entrada=getattr(uso, "prompt_tokens", 0),
                saida=getattr(uso, "completion_tokens", 0),
            )
        return resposta


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
        resposta = chamar_modelo(
            cliente,
            model=modelo or MODELO,
            messages=mensagens,
            tools=FERRAMENTAS,
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
    alvo = modelo or MODELO

    for _ in range(max_iteracoes or MAX_ITERACOES):
        conteudo = ""
        parciais: dict[int, dict] = {}

        # A medição envolve o CONSUMO do stream, não só a criação dele —
        # senão mediríamos o tempo até o primeiro byte, não a chamada inteira.
        with telemetria.medir_chamada(alvo, streaming=True) as medicao:
            stream = chamar_modelo(
                cliente,
                model=alvo,
                messages=mensagens,
                tools=FERRAMENTAS,
                temperature=TEMPERATURA if temperatura is None else temperatura,
                stream=True,
                # Pede o resumo de tokens no último chunk. Sem isso, chamada em
                # streaming não reporta uso nenhum — e o painel de custo ficaria
                # cego justamente no caminho que a interface web usa.
                stream_options={"include_usage": True},
            )

            for pedaco in stream:
                uso = getattr(pedaco, "usage", None)
                if uso:
                    medicao.registrar_uso(
                        entrada=getattr(uso, "prompt_tokens", 0),
                        saida=getattr(uso, "completion_tokens", 0),
                    )
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

    print(f"Eva no Foundry — deployment '{DEPLOYMENT}' · auth por {AUTENTICACAO}")
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
