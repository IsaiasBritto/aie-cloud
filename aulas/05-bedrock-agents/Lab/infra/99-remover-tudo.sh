#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# Deva3 · Passo final — apagar o laboratório inteiro
#
# É por isso que tudo foi criado dentro de um único grupo de recursos:
# um comando apaga a aula toda e nada continua cobrando.
#
# Uso:  bash infra/99-remover-tudo.sh
# ─────────────────────────────────────────────────────────────────────────

source "$(dirname "$0")/00-variaveis.sh"
exigir_az
mostrar_alvo

vermelho "ATENÇÃO: isto apaga o grupo ${GRUPO} e TUDO que existe dentro dele,"
vermelho "incluindo as imagens no registro e as fotos gravadas no Blob."
echo
echo "Recursos que serão apagados:"
az resource list -g "$GRUPO" --query "[].{nome:name, tipo:type}" -o table 2>/dev/null \
  || { amarelo "O grupo ${GRUPO} não existe. Nada a fazer."; exit 0; }
echo
amarelo "Digite o nome do grupo para confirmar (${GRUPO}):"
read -r confirmacao
[[ "$confirmacao" == "$GRUPO" ]] || { echo "Cancelado."; exit 0; }

az group delete --name "$GRUPO" --yes --no-wait
verde "✔ Remoção iniciada em segundo plano."
verde "  Acompanhe com:  az group show -n ${GRUPO}"
verde "  Quando responder 'not found', acabou."
verde ""
verde "  Confira o gasto no dia seguinte em: Gerenciamento de Custos → Análise de custos."
