# docker build -f web/Dockerfile .
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY web/requisitos.txt ./web/requisitos.txt
RUN pip install --no-cache-dir -r web/requisitos.txt

COPY web ./web

RUN useradd --create-home --uid 1001 deva && chown -R deva /app
USER deva

EXPOSE 8501
CMD ["streamlit", "run", "web/aplicacao.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
