# Storage para dados do lab (áudios e imagens) — independente de aulas anteriores
resource "azurerm_storage_account" "data" {
  name                     = "stdata04${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

# Permissão de PLANO DE DADOS para VOCÊ (o usuário do Cloud Shell).
#
# O function.tf já concede este mesmo papel à identidade da Function
# (azurerm_role_assignment.fn_blob_contributor). Mas quem faz o upload do áudio
# e da imagem nas Atividades 2 e 4 é você, pelo `az storage blob upload`.
#
# Ser Owner da assinatura NÃO basta: Owner é plano de CONTROLE (cria, configura e
# apaga a conta de storage), enquanto ler e escrever blob é plano de DADOS, com
# sistema de autorização próprio. Sem esta atribuição:
#
#   You do not have the required permissions needed to perform this operation.
#
# A alternativa que o próprio `az` sugere, `--auth-mode key`, funciona mas usa a
# chave da conta — que é all-or-nothing e não identifica quem acessou. É
# exatamente o que a disciplina argumenta contra.
resource "azurerm_role_assignment" "user_blob_data" {
  scope                = azurerm_storage_account.data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_storage_container" "audios" {
  name               = "audios"
  storage_account_id = azurerm_storage_account.data.id
}

resource "azurerm_storage_container" "imagens" {
  name               = "imagens"
  storage_account_id = azurerm_storage_account.data.id
}
