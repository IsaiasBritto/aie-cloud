#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-variaveis.sh"

echo "Isto apaga TUDO em $GRUPO, inclusive a memória do Deva."
echo "Digite o nome do grupo para confirmar:"
read -r digitado
[ "$digitado" = "$GRUPO" ] || { echo "Não bateu. Cancelado."; exit 1; }

az group delete --name "$GRUPO" --yes --no-wait
echo "✓ exclusão iniciada. Confira em alguns minutos: az group exists --name $GRUPO"
