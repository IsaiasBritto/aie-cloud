# SQL Server (lógico)
#
# ATENÇÃO ao nome. Ele é um nome DNS GLOBAL (`<nome>.database.windows.net`), e a
# Azure mantém a reserva por um tempo depois que uma criação falha. Se você
# tentar recriar o MESMO nome em OUTRA região — que é exatamente o que acontece
# quando o primeiro apply falha com ProvisioningDisabled e você troca de região —
# a resposta é:
#
#   409 InvalidResourceLocation: The resource 'sql-qc-xxxx' already exists in
#   location 'northcentralus'. A resource with the same name cannot be created
#   in location 'canadacentral'.
#
# E não adianta procurar o recurso para apagar: ele não aparece em
# `az resource list` nem em `az sql server list`. Só existe a reserva do nome.
#
# Amarrar um pedaço do nome à região resolve na origem: trocar de região passa a
# gerar um nome novo, sem colisão. O hash é determinístico, então o nome não muda
# sozinho entre applies na mesma região.
resource "azurerm_mssql_server" "qc" {
  name                         = "sql-qc-${random_string.sufixo.result}-${substr(sha1(local.location_sql), 0, 4)}"
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = local.location_sql
  version                      = "12.0"
  administrator_login          = "sqladminqc"
  administrator_login_password = var.sql_admin_password
  minimum_tls_version          = "1.2"
  tags                         = local.tags
}

# Permite serviços Azure conectarem (necessário para a Function da Aula 3
# e para o indexer do AI Search).
# ATENCAO: 0.0.0.0 - 0.0.0.0 NAO e um IP. E o valor magico que o Azure SQL usa
# para "permitir servicos e recursos do Azure". Trocar por um IP real quebra o
# acesso de qualquer outro servico Azure ao banco.
resource "azurerm_mssql_firewall_rule" "azure" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.qc.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Libera o IP atual do Cloud Shell para conexão direta via Python.
# O chomp remove a quebra de linha que alguns servicos de echo-ip devolvem;
# sem ele o Azure rejeita o valor como IP malformado.
data "http" "meu_ip" {
  url = "https://api.ipify.org"
}

resource "azurerm_mssql_firewall_rule" "cloud_shell" {
  name             = "CloudShellAccess"
  server_id        = azurerm_mssql_server.qc.id
  start_ip_address = chomp(data.http.meu_ip.response_body)
  end_ip_address   = chomp(data.http.meu_ip.response_body)
}

# Azure SQL Database — General Purpose Serverless (GP_S_Gen5_2)
# Auto-pausa após 60 min de inatividade: quando pausado, paga-se só o storage
# (centavos). Com o destroy ao final do lab, o custo é desprezível.
# Obs.: a "oferta gratuita" do Azure SQL (use_free_limit) ainda não tem suporte
# no provider azurerm liberado (PR #32055 aberta), por isso não é usada aqui.
resource "azurerm_mssql_database" "qc" {
  name                        = "sqldb-qc"
  server_id                   = azurerm_mssql_server.qc.id
  sku_name                    = "GP_S_Gen5_2"
  auto_pause_delay_in_minutes = 60
  min_capacity                = 0.5
  max_size_gb                 = 32
  tags                        = local.tags
}
