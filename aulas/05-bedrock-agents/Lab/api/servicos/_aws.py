"""Peças comuns às chamadas AWS: cliente boto3 e tradução de erro.

O boto3 é síncrono. Numa API assíncrona (FastAPI), chamada síncrona bloqueia o
laço de eventos e trava TODAS as requisições enquanto espera a AWS. Por isso
cada chamada roda em `asyncio.to_thread()` — um detalhe de duas linhas que
separa uma API que aguenta a turma inteira de uma que fila um por um.

Credencial: nenhuma no código. O boto3 acha sozinho — variáveis de ambiente do
Learner Lab na sua máquina, a task role dentro do ECS.
"""

from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from api.erros import FalhaDeIntegracao


@lru_cache(maxsize=8)
def cliente(servico: str, regiao: str, tempo_limite: int = 30):
    """Um cliente por (serviço, região), reaproveitado entre requisições."""
    return boto3.client(
        servico,
        region_name=regiao,
        config=Config(
            connect_timeout=5,
            read_timeout=tempo_limite,
            retries={"mode": "standard", "max_attempts": 3},
        ),
    )


DICAS = {
    "AccessDeniedException": (
        "A credencial não tem permissão. No Learner Lab, confira se a sessão está "
        "ativa (bolinha verde) e se o ECS usa a LabRole."
    ),
    "AccessDenied": "A credencial não pode gravar neste bucket. Confira a role da tarefa.",
    "UnrecognizedClientException": "Credencial inválida. Refaça o login ou copie de novo as credenciais do Learner Lab.",
    "ExpiredTokenException": "A sessão do Learner Lab expirou (4 h). Copie as credenciais novas de AWS Details.",
    "ExpiredToken": "A sessão do Learner Lab expirou (4 h). Copie as credenciais novas de AWS Details.",
    "InvalidImageFormatException": "O Rekognition aceita só JPEG e PNG. Converta a imagem.",
    "ImageTooLargeException": "Imagem grande demais para o Rekognition (5 MB em bytes). Reduza a resolução.",
    "InvalidParameterException": "A imagem pode ser pequena demais (mínimo de 80 px no lado menor) ou estar corrompida.",
    "ProvisionedThroughputExceededException": "Cota do Rekognition estourada. Espere alguns segundos e tente de novo.",
    "ThrottlingException": "Muitas chamadas por segundo. Espere alguns segundos e tente de novo.",
    "NoSuchBucket": "O bucket não existe. Confira ARMAZENAMENTO_BUCKET (output do Terraform).",
}


def traduzir_erro(servico: str, erro: Exception) -> FalhaDeIntegracao:
    """Converte a exceção do boto3 no formato de erro do Deva — com 'como resolver'."""
    if isinstance(erro, NoCredentialsError):
        return FalhaDeIntegracao(
            servico=servico,
            mensagem="Nenhuma credencial AWS encontrada.",
            detalhe=str(erro),
            como_resolver=(
                "Na sua máquina: exporte AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY e "
                "AWS_SESSION_TOKEN (Learner Lab → AWS Details → Show). No ECS: confira "
                "o taskRoleArn da task definition."
            ),
        )
    if isinstance(erro, ClientError):
        codigo = erro.response.get("Error", {}).get("Code", "Desconhecido")
        situacao = erro.response.get("ResponseMetadata", {}).get("HTTPStatusCode", "?")
        return FalhaDeIntegracao(
            servico=servico,
            mensagem=f"{servico} devolveu {codigo} (HTTP {situacao}).",
            detalhe=str(erro)[:600],
            como_resolver=DICAS.get(codigo, "Leia o campo detalhe: a AWS costuma dizer o que faltou."),
        )
    if isinstance(erro, BotoCoreError):
        return FalhaDeIntegracao(
            servico=servico,
            mensagem=f"Não foi possível falar com {servico}.",
            detalhe=str(erro),
            como_resolver="Confira AWS_REGION e a saída de rede do container (security group, IP público).",
        )
    return FalhaDeIntegracao(servico=servico, mensagem=str(erro), detalhe=repr(erro))
