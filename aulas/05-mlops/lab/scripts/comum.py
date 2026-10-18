"""Peças comuns aos scripts da Aula 5: outputs do Terraform, clientes e nomes.

Os scripts usam só boto3 (já instalado no CloudShell). O SageMaker Python SDK
faria o mesmo em menos linhas — e esconderia exatamente as chamadas de API que
esta aula quer mostrar.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import boto3

LAB = Path(__file__).resolve().parent.parent
TERRAFORM = LAB / "terraform"
CODIGO = LAB / "codigo"
REGIAO = os.environ.get("AWS_REGION", "us-east-1")

# Container de scikit-learn mantido pela AWS (treino E inferência).
# Conta 683313688378 = imagens do SageMaker em us-east-1. Outras regiões têm
# outra conta: veja "Docker Registry Paths and Example Code" na doc do SageMaker.
VERSAO_SKLEARN = os.environ.get("SKLEARN_VERSAO", "1.2-1")
IMAGEM_SKLEARN = os.environ.get(
    "SKLEARN_IMAGEM",
    f"683313688378.dkr.ecr.{REGIAO}.amazonaws.com/sagemaker-scikit-learn:{VERSAO_SKLEARN}-cpu-py3",
)

sm = boto3.client("sagemaker", region_name=REGIAO)
s3 = boto3.client("s3", region_name=REGIAO)


def saidas() -> dict:
    """Lê `terraform output -json` uma vez."""
    try:
        bruto = subprocess.run(
            ["terraform", f"-chdir={TERRAFORM}", "output", "-json"],
            check=True, capture_output=True, text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as erro:
        sys.exit(f"Não consegui ler os outputs do Terraform ({erro}). Rode o terraform apply antes.")
    return {k: v["value"] for k, v in json.loads(bruto).items()}


def nome_endpoint(sufixo: str) -> str:
    return f"rec-qc-{sufixo}"


def imprimir(titulo: str, dados) -> None:
    print(f"\n{titulo}")
    print(json.dumps(dados, ensure_ascii=False, indent=2, default=str))
