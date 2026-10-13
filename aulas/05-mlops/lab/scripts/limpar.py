"""
Wrap-up — apagar o que os scripts criaram (o Terraform não sabe que existe).

Ordem: endpoint → configs → models → versões do Registry. Só depois disso o
`terraform destroy` consegue apagar o Model Package Group (grupo com versões
não é apagado).

Uso:
    python3 scripts/limpar.py              # endpoint, configs e models
    python3 scripts/limpar.py --registro   # + todas as versões do Registry
"""
import argparse
import time

from comum import nome_endpoint, saidas, sm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registro", action="store_true", help="apaga também as versões do Registry")
    args = parser.parse_args()

    tf = saidas()
    endpoint = nome_endpoint(tf["sufixo"])

    try:
        sm.delete_endpoint(EndpointName=endpoint)
        print(f"✓ Endpoint {endpoint} apagado (a cobrança para aqui)")
        time.sleep(5)
    except sm.exceptions.ClientError:
        print(f"· Endpoint {endpoint} não existe")

    for config in sm.list_endpoint_configs(NameContains=endpoint)["EndpointConfigs"]:
        sm.delete_endpoint_config(EndpointConfigName=config["EndpointConfigName"])
        print(f"✓ EndpointConfig {config['EndpointConfigName']}")
    for modelo in sm.list_models(NameContains=endpoint)["Models"]:
        sm.delete_model(ModelName=modelo["ModelName"])
        print(f"✓ Model {modelo['ModelName']}")

    if args.registro:
        grupo = tf["model_package_group"]
        for versao in sm.list_model_packages(ModelPackageGroupName=grupo)["ModelPackageSummaryList"]:
            sm.delete_model_package(ModelPackageName=versao["ModelPackageArn"])
            print(f"✓ Registry: versão {versao['ModelPackageVersion']}")

    print("\nAgora pode rodar:  terraform -chdir=terraform destroy -auto-approve")


if __name__ == "__main__":
    main()
