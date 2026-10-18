# Multi-stage build para imagem leve.
# Base do ECR Public (espelho oficial do Docker Hub): sem limite de pull anônimo.
FROM public.ecr.aws/docker/library/python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# Imagem final
FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app
COPY --from=builder /install /usr/local/lib/python3.12/site-packages
COPY app.py .

# Não rodar como root dentro do container
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8080

# Invoca uvicorn como MÓDULO: o pip install --target só copia os pacotes para
# site-packages, não o executável 'uvicorn' para o PATH.
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
