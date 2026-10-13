"""
Diagnóstico da conexão com o Amazon Bedrock.

Rode ANTES da Eva, sempre que algo não funcionar:

    python verificar.py

Ele checa uma coisa de cada vez e diz exatamente o que está errado —
muito melhor que ler um traceback de AccessDeniedException no meio do chat.
"""

import sys

import eva


def linha(rotulo: str, valor: str, ok: bool | None = None) -> None:
    marca = {True: "[ok]  ", False: "[ERRO]", None: "      "}[ok]
    print(f"{marca} {rotulo:<14} {valor}")


def listar_modelos(procurado: str) -> None:
    """Pergunta ao Bedrock quais perfis de inferência e modelos existem na região.

    É a resposta direta para o ValidationException de "model identifier is
    invalid": em vez de você caçar o ID no console, a própria API diz o que tem.
    Usa o plano de CONTROLE (`bedrock`), não o de dados (`bedrock-runtime`).
    """
    import boto3

    print("\nPerguntando ao Bedrock o que existe nesta região...")
    controle = boto3.client("bedrock", region_name=eva.REGIAO)
    nomes: list[str] = []
    try:
        perfis = controle.list_inference_profiles(maxResults=100)["inferenceProfileSummaries"]
        nomes += [p["inferenceProfileId"] for p in perfis]
    except Exception as exc:  # noqa: BLE001
        print(f"  não consegui listar perfis ({type(exc).__name__}: {exc})")
    try:
        modelos = controle.list_foundation_models(byOutputModality="TEXT")["modelSummaries"]
        nomes += [m["modelId"] for m in modelos if "ON_DEMAND" in m.get("inferenceTypesSupported", [])]
    except Exception as exc:  # noqa: BLE001
        print(f"  não consegui listar modelos ({type(exc).__name__}: {exc})")

    if not nomes:
        print("  Nada listado. Confira a região e a permissão bedrock:List* da sua credencial.")
        return

    familia = procurado.split(".")[-1].split("-")[0] if "." in procurado else procurado
    parecidos = sorted(n for n in nomes if familia and familia in n)
    print(f"  {len(nomes)} IDs disponíveis. Os da mesma família de '{procurado}':")
    for n in parecidos[:15] or sorted(nomes)[:15]:
        print(f"    - {n}")
    print("\n  Copie um ID para BEDROCK_MODEL_ID no .env e rode de novo.")
    print("  Prefira o perfil de inferência (us. / global.) ao ID nu do modelo.")


def main() -> int:
    print("\n=== Configuração ===")
    conf = eva.descrever_conexao()
    linha("região", conf["regiao"], bool(conf["regiao"]))
    linha("modelo", conf["modelo"], bool(conf["modelo"]))
    linha("perfil AWS", conf["perfil"])
    linha("credencial", conf["credencial"], conf["credencial"] != "(sem credencial)")
    linha("rota", conf["rota"])

    print("\n=== Identidade ===")
    try:
        import boto3

        quem = boto3.client("sts", region_name=eva.REGIAO).get_caller_identity()
        linha("conta", quem["Account"], True)
        linha("arn", quem["Arn"], True)
        if "voclabs" in quem["Arn"] or "LabRole" in quem["Arn"]:
            print("       ^ isto é o AWS Academy Learner Lab — ele NÃO libera o Bedrock.")
            print("         A chamada abaixo vai falhar com AccessDenied. Use uma conta comum.")
    except Exception as exc:  # noqa: BLE001
        linha("sts", f"{type(exc).__name__}: {exc}", False)
        print("\nSem credencial válida. Rode `aws configure` ou `aws sso login` e tente de novo.")
        return 1

    print("\n=== Cliente ===")
    try:
        cliente = eva.get_cliente()
        linha("cliente", "bedrock-runtime", True)
    except RuntimeError as exc:
        linha("cliente", str(exc), False)
        return 1

    print("\n=== Chamada de teste ===")
    try:
        resposta = eva.chamar_modelo(
            cliente,
            [{"role": "user", "content": "Responda apenas: ok"}],
            ferramentas=False,
            max_tokens=20,
        )
    except Exception as exc:  # noqa: BLE001
        codigo = getattr(exc, "response", {}).get("Error", {}).get("Code", type(exc).__name__)
        linha("chamada", f"{codigo}: {exc}", False)

        if codigo == "ValidationException" and "model" in str(exc).lower():
            listar_modelos(conf["modelo"])
        else:
            print("\nTraduzindo os erros mais comuns:")
            print("  AccessDeniedException .... falta bedrock:InvokeModel na sua política IAM,")
            print("                             ou o acesso ao modelo não foi liberado na conta")
            print("  ResourceNotFound ......... modelo descontinuado (legacy) — escolha outro")
            print("  ThrottlingException ...... cota de tokens/requisições por minuto estourada")
            print("  UnrecognizedClient ....... credencial expirada: refaça o login")
        return 1

    texto = "".join(b.get("text", "") for b in resposta["output"]["message"]["content"])
    linha("resposta", texto.strip(), True)
    uso = resposta.get("usage", {})
    linha("tokens", f"{uso.get('inputTokens', 0)} entrada / {uso.get('outputTokens', 0)} saída")
    linha("latência", f"{resposta.get('metrics', {}).get('latencyMs', '?')} ms")

    print("\n=== Ferramentas (tool use) ===")
    try:
        teste = eva.chamar_modelo(
            cliente, [{"role": "user", "content": "Que horas são agora?"}], temperatura=0
        )
        chamou = teste.get("stopReason") == "tool_use"
        linha("tool use", "o modelo pediu a ferramenta" if chamou else
              "o modelo NÃO pediu a ferramenta (este modelo suporta tool use na Converse?)", chamou)
    except Exception as exc:  # noqa: BLE001
        linha("tool use", f"{type(exc).__name__}: {exc}", False)
        return 1

    print("\nTudo certo. Rode: python eva.py   ou   streamlit run app.py\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
