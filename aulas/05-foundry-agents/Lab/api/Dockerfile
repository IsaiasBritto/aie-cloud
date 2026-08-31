# Imagem da API do Deva3 (FastAPI + Uvicorn)
#
# Construção a partir da RAIZ do projeto, porque o pacote `api` precisa ir inteiro:
#   docker build -f api/Dockerfile -t deva3-api:v1 .

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /aplicacao

# Dependências primeiro: assim a camada fica em cache entre builds.
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api ./api

# Usuário sem privilégios — nada roda como root em container de aula.
RUN useradd --create-home --uid 1001 deva && chown -R deva:deva /aplicacao
USER deva

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/saude', timeout=4).status==200 else 1)"

CMD ["uvicorn", "api.principal:aplicacao", "--host", "0.0.0.0", "--port", "8000"]
