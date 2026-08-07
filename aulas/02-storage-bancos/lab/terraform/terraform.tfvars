# ATENCAO: estes valores sao um PONTO DE PARTIDA, nao uma configuracao valida
# para toda assinatura. A policy "Allowed resource deployment regions" varia de
# conta para conta, e a cota de SKU free varia ao longo do dia.
#
# Rode isto antes do primeiro apply para gerar o arquivo correto para a SUA
# assinatura (as regioes sao validadas por sonda, nao chutadas):
#
#   bash detectar-regioes.sh
#
# Por que a regiao e separada por servico: cada um falha por um motivo proprio.
#   403 RequestDisallowedByAzure        -> regiao fora da policy
#   403 ProvisioningDisabled            -> servico bloqueado nessa regiao
#   400 InsufficientResourcesAvailable  -> regiao ok, mas sem cota agora

location        = "eastus2"
location_sql    = "canadacentral"
location_search = "brazilsouth"
location_aci    = "eastus2"

# A senha do SQL NAO fica aqui. Passe por variavel de ambiente:
#   export TF_VAR_sql_admin_password="$(openssl rand -base64 24)"
#
# Registry das imagens do ACI (rode setup-registry-aluno.sh):
#   source ~/.qc-registry.env
