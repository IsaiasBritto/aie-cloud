# ---------------------------------------------------------------------------
# Limpeza de soft-delete ANTES de criar a conta.
#
# Erro que isto evita:
#
#   409 FlagMustBeSetForRestore: An existing resource with ID '...' has been
#   soft-deleted. To restore the resource, you must specify 'restore' to be
#   'true' ... If you don't want to restore existing resource, please purge it.
#
# Contas de Cognitive Services entram em soft-delete ao serem apagadas, e o NOME
# fica reservado enquanto o registro existir. O provider já purga sozinho no
# `terraform destroy` (`cognitive_account.purge_soft_delete_on_destroy` é `true`
# por padrão), então quem sempre destrói pelo Terraform nunca vê este erro.
#
# O problema é o caminho que a turma realmente usa: apagar o resource group pelo
# portal ou com `az group delete`. Isso soft-deleta a conta SEM purgar, o
# Terraform nem fica sabendo, e o próximo `apply` para no 409 acima — falando de
# um recurso que já não aparece em lugar nenhum do portal.
#
# `timestamp()` no gatilho é deliberado: este recurso precisa rodar em TODO
# apply. Se o gatilho fosse o nome da conta, ele não rodaria de novo justamente
# no cenário que interessa — nome igual, conta apagada por fora. O custo é uma
# chamada de CLI de ~2 s e uma linha a mais no plano.
# ---------------------------------------------------------------------------
resource "terraform_data" "purgar_ai_soft_deleted" {
  triggers_replace = [timestamp()]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      NOME="ai-qc-${random_string.sufixo.result}"

      # Procuramos pelo NOME em toda a assinatura, e não por
      # `show-deleted --location`, porque o registro de exclusão fica na região
      # ONDE A CONTA FOI CRIADA. Quem trocou de região entre execuções não
      # acharia nada com a região nova e receberia o 409 assim mesmo.
      REGISTROS=$(az cognitiveservices account list-deleted \
        --query "[?name=='$NOME'].[location,resourceGroup]" -o tsv 2>/dev/null || true)

      if [ -z "$REGISTROS" ]; then
        echo "Nenhuma conta AI '$NOME' em soft-delete."
        exit 0
      fi

      echo "$REGISTROS" | while read -r loc rg; do
        [ -z "$loc" ] && continue
        echo "Purgando conta AI '$NOME' em $loc / $rg ..."
        az cognitiveservices account purge \
          --name "$NOME" --resource-group "$rg" --location "$loc" --output none
        echo "Purgada."
      done
    EOT
  }
}

# Azure AI Services multi-service:
# 1 endpoint + 1 conjunto de chaves para Speech, Language, Vision, Document Intelligence, etc.
resource "azurerm_cognitive_account" "ai" {
  name                = "ai-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  kind                = "CognitiveServices"
  sku_name            = "S0"

  # CRÍTICO para usar Managed Identity:
  # AI Services exige um custom subdomain para validar tokens AAD.
  custom_subdomain_name = "ai-qc-${random_string.sufixo.result}"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags

  # O nome só está livre depois da purga.
  depends_on = [terraform_data.purgar_ai_soft_deleted]
}
