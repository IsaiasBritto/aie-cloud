# ---------------------------------------------------------------------------
# Mesmo raciocínio do `purgar_ai_soft_deleted` no cognitive.tf, aplicado ao
# Key Vault — mas com um sintoma bem diferente, e por isso mais confuso.
#
# `recover_soft_deleted_key_vaults` é `true` por padrão no provider. Então, se o
# vault está em soft-delete, o Terraform NÃO reclama: ele RECUPERA o vault
# antigo, com os segredos antigos dentro. O `apply` só quebra um passo depois:
#
#   Error: A resource with the ID ".../secrets/ai-services-key" already exists
#          - to be managed via Terraform this resource needs to be imported
#
# Ou seja, o erro aparece no SEGREDO, enquanto a causa está no VAULT. Purgar
# antes de criar faz o vault nascer realmente vazio.
# ---------------------------------------------------------------------------
resource "terraform_data" "purgar_kv_soft_deleted" {
  triggers_replace = [timestamp()]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      NOME="kv-aula04-${random_string.sufixo.result}"

      LOC=$(az keyvault list-deleted \
        --query "[?name=='$NOME'].properties.location | [0]" -o tsv 2>/dev/null || true)

      if [ -z "$LOC" ] || [ "$LOC" = "None" ]; then
        echo "Nenhum Key Vault '$NOME' em soft-delete."
        exit 0
      fi

      echo "Purgando Key Vault '$NOME' em $LOC ..."
      # Vault com purge_protection_enabled = true NAO pode ser purgado antes do
      # fim da retencao. Por isso o lab cria com a protecao desligada.
      az keyvault purge --name "$NOME" --location "$LOC" --output none
      echo "Purgado."
    EOT
  }
}

# Key Vault para guardar a chave do AI Services
# (uso didático — em produção, prefira Managed Identity direto no recurso)
resource "azurerm_key_vault" "kv" {
  name                       = "kv-aula04-${random_string.sufixo.result}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = local.tags

  # O nome só está livre depois da purga.
  depends_on = [terraform_data.purgar_kv_soft_deleted]
}

# Concede ao usuário autenticado permissão de gerenciar segredos
resource "azurerm_role_assignment" "kv_admin" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Espera a role propagar antes de criar o segredo
resource "time_sleep" "wait_rbac" {
  depends_on      = [azurerm_role_assignment.kv_admin]
  create_duration = "30s"
}

# Chave primária do AI Services como segredo no Vault
resource "azurerm_key_vault_secret" "ai_key" {
  name         = "ai-services-key"
  value        = azurerm_cognitive_account.ai.primary_access_key
  key_vault_id = azurerm_key_vault.kv.id
  depends_on   = [time_sleep.wait_rbac]
}
