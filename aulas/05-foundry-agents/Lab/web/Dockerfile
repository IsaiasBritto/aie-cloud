# Imagem da interface do Deva3 (Streamlit)
#
#   docker build -f web/Dockerfile -t deva3-web:v1 .

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /aplicacao

# A fonte usada para escrever a etiqueta em cima da foto.
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

COPY web/requirements.txt ./web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt

COPY web ./web

RUN useradd --create-home --uid 1001 deva && chown -R deva:deva /aplicacao
USER deva

EXPOSE 8501

CMD ["streamlit", "run", "web/aplicacao.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
