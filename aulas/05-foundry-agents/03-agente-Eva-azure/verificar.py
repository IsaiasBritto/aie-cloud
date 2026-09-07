"""
Diagnóstico da conexão com o Microsoft Foundry.

Rode ANTES da Eva, sempre que algo não funcionar:

    python verificar.py

Ele checa uma coisa de cada vez e diz exatamente o que está errado —
muito melhor que ler um traceback de HTTP 401 no meio do chat.
"""

import sys

import eva
import telemetria


def linha(rotulo: str, valor: str, ok: bool | None = None) -> None:
    marca = {True: "[ok]  ", False: "[ERRO]", None: "      "}[ok]
    print(f"{marca} {rotulo:<14} {valor}")


def listar_deployments(cliente, procurado: str) -> None:
    """Pergunta ao Foundry quais deployments existem de verdade.

    É a resposta direta para o 404: em vez de você caçar o nome no portal,
    o próprio recurso diz o que tem.
    """
    print("\nPerguntando ao Foundry quais deployments existem...")
    try:
        modelos = list(cliente.models.list())
    except Exception as exc:
        print(f"  não consegui listar ({type(exc).__name__}: {exc})")
        print("  Confira no portal: Build > Models > clique no deployment > o nome está no topo.")
        return

    if not modelos:
        print("  Nenhum deployment encontrado neste recurso.")
        print("  Implante um modelo no portal antes de continuar (veja o GUIA-AI-FOUNDRY.md).")
        return

    nomes = sorted({getattr(m, "id", str(m)) for m in modelos})
    print(f"  Encontrados {len(nomes)}:")
    for n in nomes:
        marca = "  <-- é este que está no seu .env" if n == procurado else ""
        print(f"    - {n}{marca}")

    print(f"\n  No .env você tem: AZURE_FOUNDRY_DEPLOYMENT={procurado}")
    parecidos = [n for n in nomes if _parecido(n, procurado)]
    if parecidos:
        print(f"  Parece que você quis dizer: {parecidos[0]}")
    print("  Copie um nome da lista acima para o .env e rode de novo.")


def _parecido(a: str, b: str) -> bool:
    """Compara ignorando pontuação — pega erros de digitação como vírgula no lugar do ponto."""
    limpa = str.maketrans("", "", ".,-_ ")
    return a.lower().translate(limpa) == b.lower().translate(limpa)


def main() -> int:
    print("\n=== Configuração ===")
    conf = eva.descrever_conexao()

    endpoint_ok = conf["endpoint"].startswith("https://")
    linha("endpoint", conf["endpoint"], endpoint_ok)
    if conf["endpoint_bruto"] != conf["endpoint"]:
        linha("no .env", conf["endpoint_bruto"])
        print("       ^ o caminho extra foi ignorado — só o host importa. Pode limpar o .env.")
    linha("rota", conf["rota"])
    linha("deployment", conf["deployment"], bool(conf["deployment"]))

    auth_ok = conf["autenticacao"] in ("chave", "entra")
    linha("autenticação", conf["autenticacao"], auth_ok)
    if not auth_ok:
        print('\nAZURE_FOUNDRY_AUTH aceita só "chave" ou "entra". Corrija no .env.')
        return 1

    if not endpoint_ok:
        print("\nO endpoint precisa começar com https://.")
        print("Pegue no portal do Foundry: seu deployment > Endpoint.")
        return 1

    print("\n=== Cliente ===")
    try:
        cliente = eva.get_cliente()
        linha("cliente", type(cliente).__name__, True)
        modo = eva.descrever_conexao()["modo_ativo"]
        linha("modo", modo, "FALLBACK" not in modo)
        if "FALLBACK" in modo:
            print("       ^ a identidade falhou e o app caiu para a chave.")
            print("         Local: rode `az login`. No Azure: confira a Managed Identity")
            print("         e a role 'Cognitive Services OpenAI User' no recurso do Foundry.")
    except RuntimeError as exc:
        linha("cliente", str(exc), False)
        return 1

    print("\n=== Chamada de teste ===")
    try:
        resposta = eva.chamar_modelo(
            cliente,
            model=conf["deployment"],
            messages=[{"role": "user", "content": "Responda apenas: ok"}],
            max_tokens=20,
        )
    except Exception as exc:
        linha("chamada", f"{type(exc).__name__}: {exc}", False)

        if "DeploymentNotFound" in str(exc) or "404" in str(exc):
            listar_deployments(cliente, conf["deployment"])
        else:
            print("\nTraduzindo os erros mais comuns:")
            print("  401 / Unauthorized ....... chave errada, ou faltou `az login` no modo entra")
            print("  429 / Rate limit ......... TPM do deployment esgotado; aumente ou espere")
            print("  Connection error ......... endpoint errado, ou rede/proxy bloqueando")
        return 1

    linha("resposta", (resposta.choices[0].message.content or "").strip(), True)
    linha("modelo", resposta.model or "(não informado)")
    for antigo, novo in eva._ajustes_aprendidos.items():
        destino = f"virou '{novo}'" if novo else "foi removido"
        linha("ajuste", f"'{antigo}' {destino} (este modelo não aceita)")
    if resposta.usage:
        linha("tokens", f"{resposta.usage.prompt_tokens} entrada / {resposta.usage.completion_tokens} saída")

    print("\n=== Ferramentas (tool calling) ===")
    try:
        teste = eva.chamar_modelo(
            cliente,
            model=conf["deployment"],
            messages=[{"role": "user", "content": "Que horas são agora?"}],
            tools=eva.FERRAMENTAS,
        )
        chamou = bool(teste.choices[0].message.tool_calls)
        linha("tool calling", "o modelo pediu a ferramenta" if chamou else
              "o modelo NÃO pediu a ferramenta (verifique se o deployment suporta tools)", chamou)
    except Exception as exc:
        linha("tool calling", f"{type(exc).__name__}: {exc}", False)
        return 1

    print("\n=== Telemetria (Application Insights) ===")
    tel = telemetria.resumo()
    if telemetria.iniciar("eva-verificar"):
        linha("telemetria", "ligada — spans e métricas vão para o Application Insights", True)
    else:
        linha("telemetria", f"desligada (connection string {tel['connection_string']})")
        print("       Normal na sua máquina. No Azure, o Container App recebe a")
        print("       APPLICATIONINSIGHTS_CONNECTION_STRING como variável de ambiente.")
    if not tel["precos_definidos"]:
        linha("preços", "não configurados — o custo estimado sairá zerado")
        print("       Preencha EVA_PRECO_ENTRADA_POR_1M e EVA_PRECO_SAIDA_POR_1M")
        print("       com os valores do seu modelo na página de preços do Azure.")

    print("\nTudo certo. Rode: python eva.py   ou   streamlit run app.py\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
