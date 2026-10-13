"""
Atividade 3 — Submeter o treino como SageMaker Training Job.

O que acontece, na ordem:
  1. a pasta codigo/ vira um sourcedir.tar.gz no S3 (o "código do job");
  2. create_training_job pede uma ml.m5.large, o container de scikit-learn da AWS,
     o canal "treino" apontando para o produtos.csv e os hiperparâmetros;
  3. a máquina sobe, instala o requirements.txt, roda train.py, salva
     /opt/ml/model em model.tar.gz no S3 — e DESLIGA. Paga-se só os minutos usados;
  4. o script espera e imprime as métricas capturadas do log.

Uso (de dentro de aulas/05-mlops/lab):
    python3 scripts/submeter_job.py
    python3 scripts/submeter_job.py --n_neighbors 3
    python3 scripts/submeter_job.py --vetorizador embeddings     # mais lento (instala torch)
"""
import argparse
import io
import json
import tarfile
import time

from comum import CODIGO, IMAGEM_SKLEARN, imprimir, s3, saidas, sm


def empacotar_codigo(bucket: str, chave: str, com_dependencias: bool) -> str:
    """Compacta codigo/ e sobe no S3. Devolve a URI.

    O requirements.txt só entra com --vetorizador embeddings: se ele estiver no
    pacote, o container instala torch ANTES de qualquer treino — minutos a mais
    (e dinheiro a mais) num job TF-IDF que não precisa dele.
    """
    arquivos = ["train.py", "inference.py"] + (["requirements.txt"] if com_dependencias else [])
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for arquivo in arquivos:
            tar.add(CODIGO / arquivo, arcname=arquivo)
    s3.put_object(Bucket=bucket, Key=chave, Body=buffer.getvalue())
    return f"s3://{bucket}/{chave}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_neighbors", type=int, default=5)
    parser.add_argument("--vetorizador", choices=["tfidf", "embeddings"], default="tfidf")
    parser.add_argument("--instancia", default="ml.m5.large")
    args = parser.parse_args()

    tf = saidas()
    carimbo = time.strftime("%Y%m%d-%H%M%S")
    nome_job = f"rec-qc-{tf['sufixo']}-{carimbo}"
    codigo_uri = empacotar_codigo(tf["bucket"], f"codigo/{nome_job}/sourcedir.tar.gz",
                                  com_dependencias=args.vetorizador == "embeddings")
    print(f"→ Código do job em {codigo_uri}")

    # O container de framework lê CADA hiperparâmetro como JSON — por isso o
    # json.dumps: "train.py" vira '"train.py"', 5 vira '5'.
    hiperparametros = {
        "sagemaker_program": "train.py",
        "sagemaker_submit_directory": codigo_uri,
        "n_neighbors": args.n_neighbors,
        "vetorizador": args.vetorizador,
    }

    sm.create_training_job(
        TrainingJobName=nome_job,
        RoleArn=tf["role_arn"],
        AlgorithmSpecification={
            "TrainingImage": IMAGEM_SKLEARN,
            "TrainingInputMode": "File",
            # Cada regex vira uma métrica do job: console do SageMaker + CloudWatch.
            "MetricDefinitions": [
                {"Name": "precision_at_k_proxy", "Regex": r"precision_at_k_proxy=([0-9\.]+)"},
                {"Name": "dimensao_vetor", "Regex": r"dimensao_vetor=([0-9\.]+)"},
                {"Name": "num_produtos", "Regex": r"num_produtos=([0-9\.]+)"},
            ],
        },
        HyperParameters={k: json.dumps(v) for k, v in hiperparametros.items()},
        InputDataConfig=[{
            "ChannelName": "treino",
            "DataSource": {"S3DataSource": {
                "S3DataType": "S3Prefix",
                "S3Uri": tf["dados_s3_uri"],
                "S3DataDistributionType": "FullyReplicated",
            }},
            "ContentType": "text/csv",
        }],
        OutputDataConfig={"S3OutputPath": f"s3://{tf['bucket']}/modelos/"},
        ResourceConfig={"InstanceType": args.instancia, "InstanceCount": 1, "VolumeSizeInGB": 10},
        # Teto de custo: se travar, morre em 30 min.
        StoppingCondition={"MaxRuntimeInSeconds": 1800},
        Tags=[
            {"Key": "projeto", "Value": "quantum-commerce"},
            {"Key": "aula", "Value": "5"},
            {"Key": "dados_versao", "Value": str(tf.get("dados_versao") or "sem-versao")},
        ],
    )
    print(f"→ Job {nome_job} submetido ({args.instancia}). Acompanhe no console:")
    print("  SageMaker AI → Training → Training jobs")

    estado_anterior = None
    while True:
        job = sm.describe_training_job(TrainingJobName=nome_job)
        estado = (job["TrainingJobStatus"], job.get("SecondaryStatus"))
        if estado != estado_anterior:
            print(f"  {time.strftime('%H:%M:%S')}  {estado[0]:<11} {estado[1]}")
            estado_anterior = estado
        if job["TrainingJobStatus"] in ("Completed", "Failed", "Stopped"):
            break
        time.sleep(15)

    if job["TrainingJobStatus"] != "Completed":
        print(f"\n✗ O job terminou como {job['TrainingJobStatus']}: {job.get('FailureReason')}")
        print("  Log: CloudWatch → /aws/sagemaker/TrainingJobs → stream com o nome do job")
        raise SystemExit(1)

    imprimir("Métricas finais:", {m["MetricName"]: m["Value"] for m in job.get("FinalMetricDataList", [])})
    print(f"\nArtefato:  {job['ModelArtifacts']['S3ModelArtifacts']}")
    print(f"Faturado:  {job.get('BillableTimeInSeconds')} s de {args.instancia}")
    print(f"\nPróximo passo:  python3 scripts/registrar_modelo.py --job {nome_job}")


if __name__ == "__main__":
    main()
