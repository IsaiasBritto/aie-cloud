// ─────────────────────────────────────────────────────────────────────────
// Deva3 · Infraestrutura como código (Bicep)
//
// Alternativa declarativa aos scripts. Cria a base do laboratório:
// armazenamento + container de blobs, recurso de visão, registro de
// containers e o ambiente de Container Apps.
//
// Implantar:
//   az group create -n rg-aula-05 -l eastus
//   az deployment group create -g rg-aula-05 \
//      --template-file infra/principal.bicep --parameters sufixo=fiap01
//
// Os dois Container Apps ficam fora deste arquivo de propósito: eles dependem
// de imagens que só existem depois do `az acr build`. Didaticamente, separa o
// que é "infraestrutura" do que é "entrega da aplicação".
// ─────────────────────────────────────────────────────────────────────────

@description('Sufixo único de 4 a 6 caracteres. Nome de Storage e de ACR é global.')
@minLength(4)
@maxLength(6)
param sufixo string

@description('Região dos recursos.')
param regiao string = resourceGroup().location

@description('Nível do recurso de visão. F0 é gratuito e limitado a 20 chamadas por minuto.')
@allowed(['F0', 'S1'])
param nivelVisao string = 'F0'

var nomeContaArmazenamento = 'stdeva3${sufixo}'
var nomeContainerBlob = 'deteccoes'
var nomeRecursoVisao = 'cv-deva3-${sufixo}'
var nomeRegistro = 'acrdeva3${sufixo}'
var nomeAmbienteApps = 'cae-aula-05'
var nomeAnalise = 'log-aula-05'

var etiquetas = {
  disciplina: 'cloud'
  aula: '05'
  projeto: 'deva3'
}

// ── Armazenamento ────────────────────────────────────────────────────────
resource contaArmazenamento 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: nomeContaArmazenamento
  location: regiao
  tags: etiquetas
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource servicoBlob 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: contaArmazenamento
  name: 'default'
}

resource containerDeteccoes 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: servicoBlob
  name: nomeContainerBlob
  properties: {
    publicAccess: 'None'
  }
}

// ── Visão computacional ──────────────────────────────────────────────────
resource recursoVisao 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: nomeRecursoVisao
  location: regiao
  tags: etiquetas
  kind: 'ComputerVision'
  sku: { name: nivelVisao }
  properties: {
    customSubDomainName: nomeRecursoVisao
    publicNetworkAccess: 'Enabled'
  }
}

// ── Registro de containers ───────────────────────────────────────────────
resource registro 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: nomeRegistro
  location: regiao
  tags: etiquetas
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: true
  }
}

// ── Observabilidade + ambiente de Container Apps ─────────────────────────
resource analise 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: nomeAnalise
  location: regiao
  tags: etiquetas
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource ambienteApps 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: nomeAmbienteApps
  location: regiao
  tags: etiquetas
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: analise.properties.customerId
        sharedKey: analise.listKeys().primarySharedKey
      }
    }
  }
}

// ── Saídas usadas pelos scripts de entrega ───────────────────────────────
output endpointVisao string = recursoVisao.properties.endpoint
output servidorRegistro string = registro.properties.loginServer
output nomeRegistro string = registro.name
output nomeAmbienteApps string = ambienteApps.name
output nomeContaArmazenamento string = contaArmazenamento.name
output nomeContainerBlob string = nomeContainerBlob
