#!/usr/bin/env bash
# Nomes num lugar só. Todo script depois deste faz `source infra/00-variaveis.sh`.
# Troque SUFIXO pelas suas iniciais + turma: export SUFIXO=isb01
: "${SUFIXO:?defina SUFIXO antes, por exemplo: export SUFIXO=isb01}"

export GRUPO="rg-aula-02-continuo"
export REGIAO="eastus2"

export ARMAZENAMENTO="stdeva${SUFIXO}"          # 3-24 caracteres, só minúsculas e números
export CONTAINER_MEMORIA="memoria-do-deva"
export CONTAINER_ENTRADA="entrada"

export REGISTRO="acrdeva${SUFIXO}"
export AMBIENTE="cae-deva-${SUFIXO}"
export APP_API="ca-deva-continuidade"
export APP_WEB="ca-deva-tela"

export IMAGEM_API="deva-continuidade:1.0.0"
export IMAGEM_WEB="deva-tela:1.0.0"

echo "Grupo:        $GRUPO"
echo "Região:       $REGIAO"
echo "Armazenamento:$ARMAZENAMENTO"
echo "Registro:     $REGISTRO"
