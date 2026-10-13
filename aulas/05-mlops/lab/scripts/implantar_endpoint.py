"""
Atividade 4 — Publicar a versão APROVADA do Registry como endpoint.

Três objetos, nesta ordem (é assim que o SageMaker separa as responsabilidades):
  1. Model           — "o quê": a versão do Registry (imagem + artefato + código)
  2. EndpointConfig  — "em quê": serverless ou instância dedicada
  3. Endpoint        — "onde": a URL que recebe as requisições

Dois tipos de compute, e a escolha é de FinOps:
  --tipo serverless  (padrão) cobra por requisição e ESCALA A ZERO. Primeira
                     chamada depois de parado: cold start de alguns segundos.
  --tipo instancia   ml.m5.large ligada 24 h — ~US$ 0,115/h, com ou sem uso.
                     Use se o serverless não for aceito na sua conta.

Uso:
    python3 scripts/implantar_endpoint.py
    python3 scripts/implantar_endpoint.py --tipo instancia
"""
import argparse
import time

from comum import nome_endpoint, saidas, sm


def versao_aprovada_mais_recente(grupo: str) -> str:
    versoes = sm.list_model_packages(
        ModelPackageGroupName=grupo, ModelApprovalStatus="Approved",
        SortBy="CreationTime", SortOrder="Descending",
    )["ModelPackageSummaryList"]
    if not versoes:
        raise SystemExit(
            "Nenhuma versão APROVADA no Registry. Rode:\n"
            "  python3 scripts/registrar_modelo.py --listar\n"
            "  python3 scripts/registrar_modelo.py --aprovar <versao>"
        )
    return versoes[0]["ModelPackageArn"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipo", choices=["serverless", "instancia"], default="serverless")
    parser.add_argument("--instancia", default="ml.m5.large")
    args = parser.parse_args()

    tf = saidas()
    endpoint = nome_endpoint(tf["sufixo"])
    carimbo = time.strftime("%Y%m%d-%H%M%S")
    pacote = versao_aprovada_mais_recente(tf["model_package_group"])
    print(f"→ Versão aprovada: {pacote}")

    nome_modelo = f"{endpoint}-{carimbo}"
    sm.create_model(
        ModelName=nome_modelo,
        ExecutionRoleArn=tf["role_arn"],
        Containers=[{"ModelPackageName": pacote}],
    )

    variante = {"VariantName": "blue", "ModelName": nome_modelo}
    if args.tipo == "serverless":
        variante["ServerlessConfig"] = {"MemorySizeInMB": 2048, "MaxConcurrency": 2}
    else:
        variante.update({"InstanceType": args.instancia, "InitialInstanceCount": 1,
                         "InitialVariantWeight": 1.0})
    sm.create_endpoint_config(EndpointConfigName=nome_modelo, ProductionVariants=[variante])

    existe = True
    try:
        sm.describe_endpoint(EndpointName=endpoint)
    except sm.exceptions.ClientError:
        existe = False

    if existe:
        # Troca a config de um endpoint que já existe: é o "novo deployment".
        sm.update_endpoint(EndpointName=endpoint, EndpointConfigName=nome_modelo)
        print(f"→ Atualizando {endpoint} para a config {nome_modelo}")
    else:
        sm.create_endpoint(EndpointName=endpoint, EndpointConfigName=nome_modelo,
                           Tags=[{"Key": "projeto", "Value": "quantum-commerce"}])
        print(f"→ Criando {endpoint} ({args.tipo}) — leva de 3 a 8 minutos")

    inicio = time.time()
    while True:
        estado = sm.describe_endpoint(EndpointName=endpoint)
        if estado["EndpointStatus"] not in ("Creating", "Updating"):
            break
        print(f"  {int(time.time() - inicio):>4}s  {estado['EndpointStatus']}")
        time.sleep(30)

    if estado["EndpointStatus"] != "InService":
        print(f"\n✗ {estado['EndpointStatus']}: {estado.get('FailureReason')}")
        print("  Logs: CloudWatch → /aws/sagemaker/Endpoints/" + endpoint)
        raise SystemExit(1)

    print(f"\n✓ {endpoint} InService")
    print("\nTestar:")
    print(f"  aws sagemaker-runtime invoke-endpoint --endpoint-name {endpoint} \\")
    print("    --content-type application/json --body fileb://endpoint/request.json resposta.json && cat resposta.json")
    print("\n⚠️  Ao terminar:  python3 scripts/limpar.py")


if __name__ == "__main__":
    main()
