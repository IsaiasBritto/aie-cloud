#!/usr/bin/env bash
# shellcheck disable=SC2016  # aspas simples de propósito: o .bashrc expande depois
# Instala o Terraform no $HOME do AWS CloudShell (o $HOME persiste entre sessões).
# Uso: bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh [versao]
set -euo pipefail

VERSAO="${1:-1.9.8}"
DESTINO="$HOME/bin"

if command -v terraform >/dev/null 2>&1 && terraform -version | head -1 | grep -q "v${VERSAO}"; then
  echo "✓ Terraform ${VERSAO} já instalado em $(command -v terraform)"
  exit 0
fi

case "$(uname -m)" in
  x86_64)  ARQ=amd64 ;;
  aarch64) ARQ=arm64 ;;
  *) echo "Arquitetura não suportada: $(uname -m)"; exit 1 ;;
esac

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
URL="https://releases.hashicorp.com/terraform/${VERSAO}/terraform_${VERSAO}_linux_${ARQ}.zip"

echo "→ Baixando Terraform ${VERSAO} (${ARQ})..."
curl -fsSL "$URL" -o "$TMP/terraform.zip"
mkdir -p "$DESTINO"
unzip -o -q "$TMP/terraform.zip" -d "$DESTINO"
chmod +x "$DESTINO/terraform"

# Garante o ~/bin no PATH nas próximas sessões (aspas simples de propósito)
if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
fi
export PATH="$DESTINO:$PATH"

# Cache único de providers: o provider aws tem centenas de MB e o $HOME do
# CloudShell tem só 1 GB. Sem o cache, cada pasta de lab baixaria uma cópia.
mkdir -p "$HOME/.terraform.d/plugin-cache"
if ! grep -q 'TF_PLUGIN_CACHE_DIR' "$HOME/.bashrc" 2>/dev/null; then
  echo 'export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"' >> "$HOME/.bashrc"
fi
export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"

terraform -version | head -1
echo "✓ Pronto. Em um terminal novo o PATH já vem ajustado; neste, rode:"
echo "  export PATH=\"\$HOME/bin:\$PATH\" TF_PLUGIN_CACHE_DIR=\"\$HOME/.terraform.d/plugin-cache\""
