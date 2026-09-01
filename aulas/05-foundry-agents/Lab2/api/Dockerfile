# Construído a partir da RAIZ do projeto:  docker build -f api/Dockerfile .
# Construir de dentro de api/ deixa o pacote de fora e o container sobe com
# ModuleNotFoundError. Armadilha já registrada no MEMORY.md do Deva3.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY api/requisitos.txt ./api/requisitos.txt
RUN pip install --no-cache-dir -r api/requisitos.txt

COPY api ./api

RUN useradd --create-home --uid 1001 deva && mkdir -p /app/dados && chown -R deva /app
USER deva

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/saude').status==200 else 1)"

CMD ["uvicorn", "api.principal:app", "--host", "0.0.0.0", "--port", "8000"]
