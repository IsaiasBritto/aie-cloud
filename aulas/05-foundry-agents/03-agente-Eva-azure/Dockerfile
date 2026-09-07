# Imagem da Eva para o Azure Container Apps.
#
# Três decisões que valem explicar:
#
# 1. `slim` em vez de `alpine`. Alpine usa musl em vez de glibc, e vários
#    pacotes Python só têm wheel para glibc — no Alpine eles compilam do zero,
#    o build fica lento e às vezes quebra. Slim é o meio-termo certo.
#
# 2. requirements.txt copiado ANTES do resto do código. O Docker guarda cache
#    por camada: enquanto o requirements não mudar, a camada de `pip install`
#    é reaproveitada. Se copiássemos tudo de uma vez, cada alteração no eva.py
#    reinstalaria todas as dependências.
#
# 3. Usuário não-root. Se alguém escapar da aplicação, escapa como `eva`, não
#    como root. Custa duas linhas.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuário sem privilégios.
RUN useradd --create-home --uid 1000 eva && chown -R eva:eva /app
USER eva

# O Container Apps encaminha o tráfego para esta porta (--target-port 8501).
EXPOSE 8501

# O Container Apps tem os próprios health probes, mas este HEALTHCHECK ajuda
# quando você roda a imagem localmente com `docker run`.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# --server.address=0.0.0.0 é obrigatório: sem isso o Streamlit escuta só em
#   127.0.0.1 e nada de fora do container consegue chegar nele.
# --server.headless=true evita que ele tente abrir um navegador.
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
