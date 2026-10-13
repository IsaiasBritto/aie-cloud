"""
Atividade 3 (fim) — Registrar o modelo treinado no Model Registry.

Cria uma VERSÃO nova no Model Package Group do recomendador, apontando para:
  - o model.tar.gz que o job gerou;
  - a imagem de inferência (o mesmo container de scikit-learn);
  - o código de inferência (inference.py, dentro do sourcedir do job).

A versão nasce `PendingManualApproval`. Promover a `Approved` é uma decisão
humana — é o equivalente ao "Production" do MLflow na versão Azure:

    python3 scripts/registrar_modelo.py --aprovar 1

Uso:
    python3 scripts/registrar_modelo.py --job <nome-do-job>
    python3 scripts/registrar_modelo.py --listar
"""
import argparse

from comum import IMAGEM_SKLEARN, imprimir, saidas, sm


def registrar(nome_job: str, grupo: str) -> None:
    job = sm.describe_training_job(TrainingJobName=nome_job)
    if job["TrainingJobStatus"] != "Completed":
        raise SystemExit(f"O job {nome_job} está {job['TrainingJobStatus']}, não Completed.")

    hp = job["HyperParameters"]
    metricas = {m["MetricName"]: m["Value"] for m in job.get("FinalMetricDataList", [])}
    resposta = sm.create_model_package(
        ModelPackageGroupName=grupo,
        ModelPackageDescription=(
            f"job={nome_job} n_neighbors={hp.get('n_neighbors')} vetorizador={hp.get('vetorizador')} "
            f"precision_at_k_proxy={metricas.get('precision_at_k_proxy')}"
        )[:1000],
        InferenceSpecification={
            "Containers": [{
                "Image": IMAGEM_SKLEARN,
                "ModelDataUrl": job["ModelArtifacts"]["S3ModelArtifacts"],
                # Diz ao container QUAL script usar na inferência e onde ele está.
                "Environment": {
                    "SAGEMAKER_PROGRAM": "inference.py",
                    "SAGEMAKER_SUBMIT_DIRECTORY": hp["sagemaker_submit_directory"].strip('"'),
                },
            }],
            "SupportedContentTypes": ["application/json"],
            "SupportedResponseMIMETypes": ["application/json"],
            "SupportedRealtimeInferenceInstanceTypes": ["ml.m5.large", "ml.t2.medium"],
        },
        ModelApprovalStatus="PendingManualApproval",
        CustomerMetadataProperties={
            "training_job": nome_job,
            "precision_at_k_proxy": str(metricas.get("precision_at_k_proxy")),
        },
    )
    arn = resposta["ModelPackageArn"]
    print(f"✓ Registrado: {arn}")
    print(f"  Versão {arn.rsplit('/', 1)[-1]} — PendingManualApproval")
    print(f"\nPara promover:  python3 scripts/registrar_modelo.py --aprovar {arn.rsplit('/', 1)[-1]}")


def listar(grupo: str) -> None:
    versoes = sm.list_model_packages(ModelPackageGroupName=grupo, SortBy="CreationTime",
                                     SortOrder="Descending")["ModelPackageSummaryList"]
    imprimir(f"Versões em {grupo}:", [
        {"versao": v["ModelPackageVersion"], "status": v["ModelApprovalStatus"],
         "criado": v["CreationTime"], "descricao": v.get("ModelPackageDescription", "")}
        for v in versoes
    ])


def aprovar(grupo: str, versao: int, rejeitar: bool = False) -> None:
    arn_grupo = sm.describe_model_package_group(ModelPackageGroupName=grupo)["ModelPackageGroupArn"]
    arn = arn_grupo.replace(":model-package-group/", ":model-package/") + f"/{versao}"
    status = "Rejected" if rejeitar else "Approved"
    sm.update_model_package(ModelPackageArn=arn, ModelApprovalStatus=status,
                            ApprovalDescription="decisão registrada pelo script da Aula 5")
    print(f"✓ Versão {versao} → {status}")


def main() -> None:
    parser = argparse.ArgumentParser()
    grupo_acao = parser.add_mutually_exclusive_group(required=True)
    grupo_acao.add_argument("--job", help="registrar o modelo deste training job")
    grupo_acao.add_argument("--listar", action="store_true")
    grupo_acao.add_argument("--aprovar", type=int, metavar="VERSAO")
    grupo_acao.add_argument("--rejeitar", type=int, metavar="VERSAO")
    args = parser.parse_args()

    grupo = saidas()["model_package_group"]
    if args.job:
        registrar(args.job, grupo)
    elif args.listar:
        listar(grupo)
    elif args.aprovar:
        aprovar(grupo, args.aprovar)
    else:
        aprovar(grupo, args.rejeitar, rejeitar=True)


if __name__ == "__main__":
    main()
