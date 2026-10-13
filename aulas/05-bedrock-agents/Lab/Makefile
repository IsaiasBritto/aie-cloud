# Atalhos do Deva3. Digite `make` para ver a lista.

.DEFAULT_GOAL := ajuda
.PHONY: ajuda instalar testar api web subir descer construir publicar limpar

ajuda:  ## Mostra esta lista
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

instalar:  ## Instala as dependências das duas aplicações
	python -m pip install -r api/requirements.txt -r web/requirements.txt pytest

testar:  ## Roda os testes
	python -m pytest

api:  ## Sobe só a API, com recarga automática
	uvicorn api.principal:aplicacao --reload --port 8000

web:  ## Sobe só a interface
	API_URL=http://localhost:8000 streamlit run web/aplicacao.py

subir:  ## Sobe API + interface com docker compose
	docker compose up --build

descer:  ## Derruba os containers locais
	docker compose down

construir:  ## Constrói as duas imagens localmente
	docker build -f api/Dockerfile -t deva3-api:v1 .
	docker build -f web/Dockerfile -t deva3-web:v1 .

publicar:  ## Constrói no ACR e implanta nos Container Apps
	bash infra/02-publicar-imagens.sh
	bash infra/03-implantar-apps.sh

limpar:  ## Apaga o grupo de recursos inteiro na Azure
	bash infra/99-remover-tudo.sh
