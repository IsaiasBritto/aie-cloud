<#
    deploy.ps1 - provisiona tudo e publica a Eva no Azure Container Apps.

    E o mesmo roteiro do GUIA-DEPLOY-CLI.md, automatizado.

    SAO TRES COISAS DIFERENTES, e e facil trocar uma pela outra:

      1. O RECURSO do Foundry .......... ex.: curso-agentes-resource
         Onde o modelo mora. E o primeiro pedaco do seu endpoint:
         https://curso-agentes-resource.services.ai.azure.com

      2. O GRUPO DE RECURSOS do Foundry . ex.: rg-alguma-coisa
         Onde esse recurso esta. NAO precisa passar: o script descobre.

      3. O GRUPO DA APLICACAO ........... rg-eva-<seu-login> (automatico)
         Grupo NOVO, que o script CRIA para a Eva. Nada a ver com o Foundry.
         O nome sai da sua identidade, para a turma inteira poder rodar ao
         mesmo tempo sem um aluno sobrescrever o outro. Mude so se quiser:
         -Sufixo <algo-seu>  ou  -ResourceGroup <nome-inteiro>

    Ainda existe um quarto nome que NAO entra aqui: o PROJETO do Foundry
    (o "curso-agentes" do final de .../api/projects/curso-agentes). Projeto
    e organizacao do portal; quem atende a chamada e o recurso.

    Uso mais simples - so o NOME DO SEU RECURSO no Foundry:

        cd infra
        .\deploy.ps1 -FoundryResourceName "<NOME-DO-SEU-RECURSO>"

    Tambem aceita o endpoint inteiro, colado do .env do projeto anterior:

        .\deploy.ps1 -FoundryResourceName "https://<SEU-RECURSO>.services.ai.azure.com"

    ATENCAO: os valores acima entre <> sao para SUBSTITUIR. Se voce rodar com
    "seu-recurso" literal, o script para e lista os recursos que existem de
    verdade na sua assinatura - que e como voce descobre o nome certo.

    Nao sabe os nomes? Rode isto antes:

        az cognitiveservices account list --query "[].{recurso:name, grupo:resourceGroup}" -o table

    Pre-requisitos: Azure CLI instalado e `az login` feito.
    O script e idempotente: rodar de novo reaproveita o que ja existe.
#>

param(
    [string]$Prefixo = "eva",

    # Grupo de recursos que o script CRIA para a aplicacao Eva.
    # NAO e o grupo do Foundry. Veja o cabecalho.
    # Vazio = "rg-eva-<seu-identificador>", derivado de quem esta logado.
    # Isso e o que permite a turma inteira rodar ao mesmo tempo na MESMA
    # assinatura sem um aluno sobrescrever o outro.
    [string]$ResourceGroup = "",

    # Identificador do aluno. Vazio = derivado do seu login no az.
    # Passe algo curto e unico se quiser mandar no nome.
    [string]$Sufixo = "",

    [string]$Local = "eastus2",

    # O recurso do Foundry que JA existe. Aceita o NOME do recurso ou o
    # ENDPOINT inteiro (pode colar direto do .env do projeto anterior).
    [Parameter(Mandatory = $true)][string]$FoundryResourceName,

    # Opcional: se voce nao passar, o script descobre pelo nome do recurso.
    [string]$FoundryResourceGroup = "",

    # Opcional: se o recurso tiver um unico deployment, o script usa aquele.
    [string]$Deployment = "",

    # ---- Marcacao (tags) para FinOps -------------------------------------
    # Todo recurso criado sai marcado com estes valores. Sao eles que
    # permitem responder "quanto custou a aula?" no Cost Analysis.
    [string]$Projeto = "eva-agente",
    [string]$Ambiente = "aula",
    [string]$CentroDeCusto = "fiap-mba-ia",
    [string]$Responsavel = ""   # vazio = usa quem esta logado no az
)

# POR QUE "Continue" E NAO "Stop" — vale a aula inteira.
#
# 1) `$ErrorActionPreference = "Stop"` NAO para o script quando o `az` falha.
#    O `az` e um executavel externo: ele nao levanta excecao do PowerShell,
#    so devolve um codigo de saida em $LASTEXITCODE. Ou seja, para o que a
#    gente queria, "Stop" nao serve.
#
# 2) Pior: com "Stop", QUALQUER coisa que um comando nativo escreva em stderr
#    vira erro terminante (NativeCommandError). O `az` escreve aviso em stderr
#    o tempo todo — um pip desatualizado na maquina, por exemplo — e o script
#    morre no passo 0 por causa de um aviso inofensivo.
#
# A protecao de verdade e a funcao `Passo`, logo abaixo, que confere o
# $LASTEXITCODE depois de cada comando. Automacao que nao para no primeiro
# erro e pior que automacao nenhuma: ela esconde a causa no meio do ruido.
$ErrorActionPreference = "Continue"

function Passo {
    <#  Roda um bloco com `az` dentro e ABORTA se ele falhar. #>
    param([string]$Oque, [scriptblock]$Bloco)
    & $Bloco
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n-----------------------------------------" -ForegroundColor Red
        Write-Host " PAROU AQUI: $Oque" -ForegroundColor Red
        Write-Host " O erro do Azure CLI esta logo acima." -ForegroundColor Red
        Write-Host " Nada mais foi executado  -  corrija e rode de novo." -ForegroundColor Red
        Write-Host "-----------------------------------------`n" -ForegroundColor Red
        exit 1
    }
}

function Confirmar {
    <#  Roda um `show` e ABORTA se o recurso nao existir de verdade.

        Por que isto existe: codigo de saida 0 NAO e prova de que o recurso
        nasceu. Ja vimos nesta turma o passo 6 e o passo 7 "passarem" limpos,
        sem uma linha de erro, e o passo 8 morrer com "The containerapp
        'eva-app' does not exist". O `az` mentiu no codigo de saida, e o
        script acreditou.

        A regra que fica: depois de criar, PERGUNTE se existe. A verificacao
        custa um segundo e devolve o erro no lugar onde ele nasceu, em vez de
        dois passos adiante.  #>
    param([string]$Oque, [scriptblock]$Bloco)
    $valor = (& $Bloco | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($valor)) { return $null }
    return $valor.Trim()
}

# ATENCAO: variavel do PowerShell e CASE-INSENSITIVE. Se este nome fosse
# `$ambiente`, ele seria a MESMA variavel do parametro `-Ambiente` la de cima,
# e a tag do ambiente FinOps sairia valendo "eva-env" em vez de "aula" - sem
# erro nenhum, so o valor errado. Por isso o nome longo.
$nomeAmbienteACA = "${Prefixo}-env"

$appInsights = "${Prefixo}-appi"
$logAnalytics = "${Prefixo}-logs"
$app = "${Prefixo}-app"
$imagem = "eva:v1"

Write-Host "`n=== 0. Extensoes e provedores ===" -ForegroundColor Cyan
# Estas duas podem falhar por causa do pip da máquina e NÃO são fatais: o
# `containerapp` já vem embutido em versões recentes do Azure CLI. Por isso
# aqui não usamos `Passo` — só avisamos.
az extension add --name containerapp --upgrade --only-show-errors 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "  aviso: nao atualizei a extensao containerapp (seguindo)" -ForegroundColor DarkYellow }
az extension add --name application-insights --upgrade --only-show-errors 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "  aviso: nao atualizei a extensao application-insights (seguindo)" -ForegroundColor DarkYellow }

# O aviso acima e comum e quase sempre inofensivo - mas nem sempre. Se a
# extensao ficou MEIO instalada (um `pip` que falhou no meio), o comando
# `az containerapp` vira uma caixa preta: responde, sai com codigo 0, e nao
# faz nada. Por isso testamos o comando de verdade uma vez, AQUI, antes de o
# passo 6 depender dele.
az containerapp env list --only-show-errors -o none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nO comando 'az containerapp' nao esta funcionando nesta maquina." -ForegroundColor Red
    Write-Host "Conserte a extensao antes de seguir:" -ForegroundColor Red
    Write-Host "  az extension remove --name containerapp"
    Write-Host "  az extension add --name containerapp"
    Write-Host "Se o pip continuar falhando, atualize o Azure CLI:"
    Write-Host "  https://aka.ms/installazurecliwindows"
    exit 1
}
Write-Host "  az containerapp respondendo" -ForegroundColor DarkGray

Passo "registrar o provedor Microsoft.App" { az provider register --namespace Microsoft.App --wait | Out-Null }
Passo "registrar o provedor Microsoft.OperationalInsights" { az provider register --namespace Microsoft.OperationalInsights --wait | Out-Null }

$assinatura = az account show --query id -o tsv
if (-not $assinatura) {
    Write-Host "Voce nao esta logado. Rode: az login" -ForegroundColor Red
    exit 1
}
Write-Host "Assinatura: $assinatura"

# --------------------------------------------------------------------------
# QUEM SOU EU - e por que isso decide o nome do grupo de recursos
# --------------------------------------------------------------------------
# Numa turma rodando ao mesmo tempo, o que colide NAO sao os nomes globais
# (ACR e Key Vault ja levam sufixo aleatorio). O que colide e o GRUPO DE
# RECURSOS: com o mesmo nome para todo mundo, o `az group create` do segundo
# aluno nao falha - ele so passa a apontar para o grupo do primeiro. Dali em
# diante os dois compartilham ACR, Key Vault e Container App, e um sobrescreve
# o outro sem nenhum erro na tela.
#
# A saida e um sufixo POR ALUNO. Aleatorio nao serve: precisa ser estavel
# entre execucoes, senao cada `deploy.ps1` cria um grupo novo. Por isso ele sai
# da identidade de quem rodou - mesma pessoa, mesmo nome, sempre.

if (-not $Responsavel -or -not $Sufixo) {
    $upn = az ad signed-in-user show --query userPrincipalName -o tsv 2>$null
    if (-not $Responsavel) {
        $Responsavel = if ($upn) { ($upn -replace "\s", "").ToLower() } else { "desconhecido" }
    }
    if (-not $Sufixo -and $upn) {
        # so a parte antes do @, sem pontuacao: isaias.sb@x.com -> isaiassb
        $Sufixo = (($upn -split "@")[0].ToLower() -replace "[^a-z0-9]", "")
    }
}
if (-not $Sufixo) {
    $oid = az ad signed-in-user show --query id -o tsv 2>$null
    $Sufixo = if ($oid) { $oid.Substring(0, 8) } else { "aluno" }
}
if ($Sufixo.Length -gt 12) { $Sufixo = $Sufixo.Substring(0, 12) }

if (-not $ResourceGroup) { $ResourceGroup = "rg-eva-$Sufixo" }
Write-Host "Aluno: $Sufixo   ->   grupo de recursos: $ResourceGroup"

# Se o grupo ja existe e foi criado por OUTRA pessoa, para aqui. Sem esta
# checagem, a logica de "reaproveitar o que ja existe" vira "sequestrar o
# ambiente do colega" - e o erro so aparece quando o app do outro muda sozinho.
$donoDoGrupo = az group show --name $ResourceGroup --query "tags.responsavel" -o tsv 2>$null
if ($donoDoGrupo -and $donoDoGrupo -ne $Responsavel) {
    Write-Host "`nO grupo '$ResourceGroup' ja existe e pertence a OUTRA pessoa:" -ForegroundColor Red
    Write-Host "  dono atual: $donoDoGrupo"
    Write-Host "  voce......: $Responsavel"
    Write-Host "`nContinuar sobrescreveria o ambiente dessa pessoa." -ForegroundColor Red
    Write-Host "Rode com -Sufixo <algo-seu> ou -ResourceGroup <outro-nome>." -ForegroundColor Yellow
    exit 1
}

# --------------------------------------------------------------------------
Write-Host "`n=== 0.5 Conferindo o recurso do Foundry (ANTES de criar nada) ===" -ForegroundColor Cyan
# Validar a entrada antes de provisionar e o que separa um erro de 5 segundos
# de um grupo de recursos com metade das coisas criadas.

# Aceita o endpoint inteiro: pega so o primeiro rotulo do host.
# https://curso-agentes-resource.services.ai.azure.com/... -> curso-agentes-resource
if ($FoundryResourceName -match '^https?://') {
    $nomeDoHost = ([uri]$FoundryResourceName).Host
    $FoundryResourceName = $nomeDoHost.Split(".")[0]
    Write-Host "  recurso extraido do endpoint: $FoundryResourceName"
}

# Confusao mais comum: passar um GRUPO DE RECURSOS onde vai o nome do RECURSO.
if ($FoundryResourceName -eq $ResourceGroup -or $FoundryResourceName -like "rg-*") {
    Write-Host "`nATENCAO: '$FoundryResourceName' parece um GRUPO DE RECURSOS, nao um recurso." -ForegroundColor Yellow
    Write-Host "  -FoundryResourceName quer o RECURSO do Foundry (o primeiro pedaco do endpoint)." -ForegroundColor Yellow
    Write-Host "  O grupo da aplicacao ('$ResourceGroup') e outro parametro, e ja tem padrao." -ForegroundColor Yellow
    Write-Host ""
}

# Grupo do Foundry: se nao veio, descobre pelo nome do recurso.
if (-not $FoundryResourceGroup) {
    $FoundryResourceGroup = az cognitiveservices account list `
        --query "[?name=='$FoundryResourceName'] | [0].resourceGroup" -o tsv 2>$null
    if ($FoundryResourceGroup) {
        Write-Host "  grupo do Foundry descoberto: $FoundryResourceGroup"
    }
}

$foundryId = ""
if ($FoundryResourceGroup) {
    $foundryId = az cognitiveservices account show `
        --name $FoundryResourceName --resource-group $FoundryResourceGroup --query id -o tsv 2>$null
}

if (-not $foundryId) {
    Write-Host "`nNao encontrei o recurso '$FoundryResourceName' na sua assinatura." -ForegroundColor Red
    Write-Host "`nOs recursos de IA que EXISTEM:" -ForegroundColor Yellow
    az cognitiveservices account list --query "[].{recurso:name, grupo:resourceGroup, tipo:kind, regiao:location}" -o table
    Write-Host "`nUse a coluna 'recurso' em -FoundryResourceName. O grupo o script descobre sozinho." -ForegroundColor Yellow
    exit 1
}

# Deployment: se nao veio e so existe um, usa aquele.
$deploymentsExistentes = @(az cognitiveservices account deployment list `
    --name $FoundryResourceName --resource-group $FoundryResourceGroup --query "[].name" -o tsv)

if (-not $Deployment) {
    if ($deploymentsExistentes.Count -eq 1) {
        $Deployment = $deploymentsExistentes[0]
        Write-Host "  unico deployment do recurso: $Deployment"
    } else {
        Write-Host "`nEste recurso tem mais de um deployment. Escolha um com -Deployment:" -ForegroundColor Yellow
        $deploymentsExistentes | ForEach-Object { Write-Host "  - $_" }
        exit 1
    }
} elseif ($deploymentsExistentes -notcontains $Deployment) {
    Write-Host "`nO deployment '$Deployment' nao existe nesse recurso." -ForegroundColor Red
    Write-Host "Deployments disponiveis:" -ForegroundColor Yellow
    $deploymentsExistentes | ForEach-Object { Write-Host "  - $_" }
    Write-Host "`nLembre: aqui vai o nome do DEPLOYMENT que voce escolheu, nao o nome do modelo." -ForegroundColor Yellow
    exit 1
}

# O resumo abaixo existe para a confusao entre os tres nomes morrer aqui,
# e nao dez minutos depois, com meio ambiente provisionado.
Write-Host ""
Write-Host "  LE do Foundry (ja existe):" -ForegroundColor DarkGray
Write-Host "    recurso ......... $FoundryResourceName"
Write-Host "    grupo ........... $FoundryResourceGroup"
Write-Host "    deployment ...... $Deployment"
Write-Host "  CRIA para a Eva (novo):" -ForegroundColor DarkGray
Write-Host "    grupo ........... $ResourceGroup"
Write-Host "    regiao .......... $Local"

# --------------------------------------------------------------------------
# MARCACAO (TAGS) PARA FINOPS
# --------------------------------------------------------------------------
# No Azure, a fatura vem por recurso. Sem marcacao, "quanto custou a aula de
# agentes?" nao tem resposta: voce ve 6 recursos com nomes crus e adivinha.
#
# Detalhe que quase todo mundo erra: tag NAO e herdada. Marcar o grupo de
# recursos nao marca o que esta dentro dele. Existe Azure Policy para forcar a
# heranca, mas por padrao cada recurso precisa da sua.
#
# Limites: 50 tags por recurso, chave ate 512 e valor ate 256 caracteres.
# Evite espaco e acento no valor - simplifica o filtro e o CSV do Cost Analysis.

# O $Responsavel ja foi resolvido no bloco "quem sou eu", junto com o sufixo:
# os dois saem da mesma identidade e da mesma chamada ao az.
$tags = @(
    "projeto=$Projeto",              # a que iniciativa o gasto pertence
    "ambiente=$Ambiente",            # aula / dev / prod - separa o que e experimento
    "centro-custo=$CentroDeCusto",   # quem paga a conta
    "responsavel=$Responsavel",      # a quem perguntar antes de apagar
    "criado-por=deploy.ps1",         # distingue o que e IaC do que foi feito na mao
    "criado-em=$(Get-Date -Format 'yyyy-MM-dd')",
    "descartavel=sim",               # pode ser apagado sem consultar ninguem
    "aluno=$Sufixo"                  # separa a turma dentro do Cost Analysis
)

Write-Host "  MARCACAO (tags) em todos os recursos:" -ForegroundColor DarkGray
$tags | ForEach-Object { Write-Host "    $_" }

# --------------------------------------------------------------------------
Write-Host "`n=== 1. Grupo de recursos ===" -ForegroundColor Cyan
Passo "criar o grupo de recursos" {
    az group create --name $ResourceGroup --location $Local --tags $tags --only-show-errors | Out-Null
}

Write-Host "`n=== 2. Container Registry ===" -ForegroundColor Cyan
# Reaproveita o ACR se já houver um no grupo. Sem isto, cada execução criava um
# registry novo com sufixo aleatório — e a conta de estudante enche de lixo.
$acr = az acr list --resource-group $ResourceGroup --query "[0].name" -o tsv
if (-not $acr) {
    # ACR e Key Vault precisam de nome único no mundo inteiro.
    $sufixo = -join ((48..57) + (97..122) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
    $acr = "${Prefixo}acr${sufixo}"
    Passo "criar o Container Registry" {
        az acr create --resource-group $ResourceGroup --name $acr --sku Basic --tags $tags --only-show-errors | Out-Null
    }
    Write-Host "ACR criado: $acr"
} else {
    Write-Host "ACR reaproveitado: $acr"
}

Write-Host "`n=== 3. Build da imagem NA NUVEM (nao precisa de Docker local) ===" -ForegroundColor Cyan
# O `..` no fim é o contexto: a pasta do projeto, um nível acima de infra/.
Passo "buildar a imagem no ACR" {
    az acr build --registry $acr --image $imagem --file ../Dockerfile .. --only-show-errors
}

Write-Host "`n=== 4. Application Insights ===" -ForegroundColor Cyan
Passo "criar o workspace do Log Analytics" {
    az monitor log-analytics workspace create `
        --resource-group $ResourceGroup --workspace-name $logAnalytics --tags $tags --only-show-errors | Out-Null
}
$wsId = az monitor log-analytics workspace show `
    --resource-group $ResourceGroup --workspace-name $logAnalytics --query id -o tsv
Passo "criar o Application Insights" {
    az monitor app-insights component create `
        --app $appInsights --location $Local --resource-group $ResourceGroup `
        --workspace $wsId --tags $tags --only-show-errors | Out-Null
}
$appiConn = az monitor app-insights component show `
    --app $appInsights --resource-group $ResourceGroup --query connectionString -o tsv

Write-Host "`n=== 5. Key Vault + a chave do Foundry (fallback) ===" -ForegroundColor Cyan
$kv = az keyvault list --resource-group $ResourceGroup --query "[0].name" -o tsv
if (-not $kv) {
    $sufixoKv = -join ((48..57) + (97..122) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
    $kv = "${Prefixo}-kv-${sufixoKv}"
    Passo "criar o Key Vault" {
        az keyvault create --name $kv --resource-group $ResourceGroup --location $Local `
            --enable-rbac-authorization true --tags $tags --only-show-errors | Out-Null
    }
    Write-Host "Key Vault criado: $kv"
} else {
    Write-Host "Key Vault reaproveitado: $kv"
}

# Quem roda o script precisa de permissão para ESCREVER o segredo.
$meuId = az ad signed-in-user show --query id -o tsv
$kvId = az keyvault show --name $kv --resource-group $ResourceGroup --query id -o tsv
az role assignment create --role "Key Vault Secrets Officer" `
    --assignee-object-id $meuId --assignee-principal-type User --scope $kvId --only-show-errors | Out-Null
Write-Host "Aguardando a permissao propagar..." -ForegroundColor DarkGray
Start-Sleep -Seconds 30

$chaveFoundry = az cognitiveservices account keys list `
    --name $FoundryResourceName --resource-group $FoundryResourceGroup --query key1 -o tsv
if (-not $chaveFoundry) {
    Write-Host "Nao consegui ler a chave do Foundry. Voce tem permissao de leitura nesse recurso?" -ForegroundColor Red
    exit 1
}
Passo "gravar o segredo no Key Vault" {
    az keyvault secret set --vault-name $kv --name "foundry-api-key" `
        --value $chaveFoundry --only-show-errors | Out-Null
}
$segredoUri = az keyvault secret show --vault-name $kv --name "foundry-api-key" --query id -o tsv
# Tira a versão do URI: assim o Container Apps sempre pega a versão mais nova.
$segredoUri = $segredoUri -replace '/[^/]+$', ''
Write-Host "Segredo gravado: $segredoUri"

Write-Host "`n=== 6. Ambiente do Container Apps ===" -ForegroundColor Cyan
# A assinatura de estudante permite UM ambiente por região. Se já existe um,
# reaproveitamos — inclusive se estiver em outro grupo de recursos, porque o
# `--environment` aceita o ID completo.
#
# ATENCAO - o passo 6 e o 7 sao os unicos do script que NAO escondem a saida do
# `az` atras de `Out-Null`. E de proposito. Foi exatamente aqui que o script
# passou limpo, sem uma linha na tela, e o passo 8 morreu dizendo que o app nao
# existia. Criacao demorada e barulhenta e melhor do que silencio mentiroso.
$ambienteId = Confirmar "ambiente ja existente" {
    az containerapp env list --resource-group $ResourceGroup `
        --query "[?name=='$nomeAmbienteACA'] | [0].id" -o tsv 2>$null
}

if ($ambienteId) {
    Write-Host "Ambiente reaproveitado: $nomeAmbienteACA"
} else {
    # As duas leituras do workspace saem da linha do `create`. Antes elas eram
    # sub-expressoes `(...)` no meio dos argumentos: se uma falhasse, o
    # parametro chegava VAZIO no `az` e o erro aparecia longe da causa.
    $wsCliente = az monitor log-analytics workspace show `
        --resource-group $ResourceGroup --workspace-name $logAnalytics --query customerId -o tsv
    $wsChave = az monitor log-analytics workspace get-shared-keys `
        --resource-group $ResourceGroup --workspace-name $logAnalytics --query primarySharedKey -o tsv
    if (-not $wsCliente -or -not $wsChave) {
        Write-Host "`nNao consegui ler o workspace '$logAnalytics' do grupo '$ResourceGroup'." -ForegroundColor Red
        Write-Host "Sem ele o ambiente do Container Apps nao tem para onde mandar log." -ForegroundColor Red
        exit 1
    }

    Write-Host "Criando o ambiente '$nomeAmbienteACA' - leva de 2 a 5 minutos..." -ForegroundColor DarkGray
    az containerapp env create --name $nomeAmbienteACA --resource-group $ResourceGroup `
        --location $Local --logs-workspace-id $wsCliente --logs-workspace-key $wsChave `
        --tags $tags --only-show-errors
    $codigoAmbiente = $LASTEXITCODE

    # A prova nao e o codigo de saida: e o `show` responder com um ID.
    $ambienteId = Confirmar "ambiente recem-criado" {
        az containerapp env show --name $nomeAmbienteACA --resource-group $ResourceGroup --query id -o tsv 2>$null
    }

    if (-not $ambienteId) {
        Write-Host "O ambiente nao existe depois do create (codigo de saida do az: $codigoAmbiente)." -ForegroundColor DarkYellow
        Write-Host "Procurando um ambiente existente em '$Local'..." -ForegroundColor DarkYellow
        $regiao = $Local.Replace(" ", "").ToLower()
        # DOIS detalhes de PowerShell nesta linha, e os dois ja morderam:
        #
        # 1. O `-join` antes do ConvertFrom-Json e obrigatorio. A saida de um
        #    comando nativo chega como ARRAY DE LINHAS, e o ConvertFrom-Json
        #    tenta converter cada linha sozinha - o JSON do `az` vem sempre
        #    formatado em varias linhas, entao quebra com "Additional text
        #    encountered after finished reading JSON content".
        # 2. O @() forca lista: com UM resultado so, o ConvertFrom-Json devolve
        #    um objeto solto e o .Count vira 1 por acidente, nao por contagem.
        $jsonAmbientes = (az containerapp env list -o json 2>$null) -join "`n"
        $candidatos = @($jsonAmbientes | ConvertFrom-Json |
            Where-Object { $_.location.Replace(" ", "").ToLower() -eq $regiao })

        if ($candidatos.Count -eq 1) {
            $ambienteId = $candidatos[0].id
            Write-Host "Reaproveitando o ambiente '$($candidatos[0].name)' do grupo '$($candidatos[0].resourceGroup)'." -ForegroundColor Green
        } else {
            Write-Host "`nNao consegui criar nem escolher um ambiente do Container Apps." -ForegroundColor Red
            Write-Host "A assinatura permite 1 ambiente por regiao. Suas opcoes:" -ForegroundColor Red
            Write-Host "  a) rodar com -Local em outra regiao (ex.: -Local westus3)"
            Write-Host "  b) apagar o ambiente antigo e rodar de novo:"
            az containerapp env list --query "[].{nome:name, grupo:resourceGroup, regiao:location}" -o table
            Write-Host "     az containerapp env delete -n <nome> -g <grupo> --yes"
            exit 1
        }
    } else {
        Write-Host "Ambiente criado: $nomeAmbienteACA" -ForegroundColor Green
    }
}

# Ultima trava antes do passo 7: sem ID de ambiente, o `--environment` sairia
# vazio e o `az containerapp create` faria alguma coisa que nao e o que
# queremos - talvez ate saindo com codigo 0.
if ([string]::IsNullOrWhiteSpace($ambienteId)) {
    Write-Host "`nFiquei sem o ID do ambiente. Nao da para criar o app assim." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== 7. Container App (imagem publica primeiro) ===" -ForegroundColor Cyan
# Ordem obrigatória: o app precisa EXISTIR para ganhar identidade, e precisa de
# identidade para conseguir puxar a imagem privada do ACR. Por isso ele nasce
# com uma imagem pública descartável e só depois recebe a nossa.
$appExiste = Confirmar "app ja existente" {
    az containerapp show --name $app --resource-group $ResourceGroup --query id -o tsv 2>$null
}

if ($appExiste) {
    Write-Host "Container App ja existia: $app"
} else {
    Write-Host "Criando o Container App '$app' no ambiente:" -ForegroundColor DarkGray
    Write-Host "  $ambienteId" -ForegroundColor DarkGray
    az containerapp create --name $app --resource-group $ResourceGroup `
        --environment $ambienteId `
        --image "mcr.microsoft.com/k8se/quickstart:latest" `
        --target-port 80 --ingress external `
        --min-replicas 0 --max-replicas 2 `
        --tags $tags --only-show-errors
    $codigoApp = $LASTEXITCODE

    $appExiste = Confirmar "app recem-criado" {
        az containerapp show --name $app --resource-group $ResourceGroup --query id -o tsv 2>$null
    }
    if (-not $appExiste) {
        Write-Host "`n-----------------------------------------" -ForegroundColor Red
        Write-Host " PAROU AQUI: o Container App '$app' nao existe depois do create." -ForegroundColor Red
        Write-Host " codigo de saida do az: $codigoApp" -ForegroundColor Red
        Write-Host " ambiente usado: $ambienteId" -ForegroundColor Red
        Write-Host " Rode estes tres comandos e me mostre a saida:" -ForegroundColor Red
        Write-Host "   az containerapp env show -n $nomeAmbienteACA -g $ResourceGroup -o table"
        Write-Host "   az containerapp list -g $ResourceGroup -o table"
        Write-Host "   az extension list -o table"
        Write-Host "-----------------------------------------`n" -ForegroundColor Red
        exit 1
    }
    Write-Host "Container App criado: $app" -ForegroundColor Green
}

Write-Host "`n=== 8. Managed Identity ===" -ForegroundColor Cyan
Passo "atribuir a identidade gerenciada" {
    az containerapp identity assign --name $app --resource-group $ResourceGroup `
        --system-assigned --only-show-errors | Out-Null
}
$principalId = az containerapp show --name $app --resource-group $ResourceGroup `
    --query identity.principalId -o tsv
if (-not $principalId) {
    Write-Host "O app ficou sem identidade  -  sem ela nada adiante funciona." -ForegroundColor Red
    exit 1
}
Write-Host "Identidade do app: $principalId"

Write-Host "`n=== 9. Permissoes da identidade ===" -ForegroundColor Cyan
$acrId = az acr show --name $acr --resource-group $ResourceGroup --query id -o tsv

# Puxar a imagem do registry
Passo "dar AcrPull a identidade" {
    az role assignment create --role "AcrPull" `
        --assignee-object-id $principalId --assignee-principal-type ServicePrincipal `
        --scope $acrId --only-show-errors | Out-Null
}
# Ler o segredo no Key Vault
Passo "dar Key Vault Secrets User a identidade" {
    az role assignment create --role "Key Vault Secrets User" `
        --assignee-object-id $principalId --assignee-principal-type ServicePrincipal `
        --scope $kvId --only-show-errors | Out-Null
}
# Chamar o modelo no Foundry — esta é a que substitui a chave
Passo "dar Cognitive Services OpenAI User a identidade" {
    az role assignment create --role "Cognitive Services OpenAI User" `
        --assignee-object-id $principalId --assignee-principal-type ServicePrincipal `
        --scope $foundryId --only-show-errors | Out-Null
}

Write-Host "Aguardando as permissoes propagarem..." -ForegroundColor DarkGray
Start-Sleep -Seconds 45

Write-Host "`n=== 10. Registry via identidade ===" -ForegroundColor Cyan
Passo "apontar o registry pela identidade" {
    az containerapp registry set --name $app --resource-group $ResourceGroup `
        --server "$acr.azurecr.io" --identity system --only-show-errors | Out-Null
}

Write-Host "`n=== 11. Segredo do Key Vault + variaveis de ambiente ===" -ForegroundColor Cyan
Passo "referenciar o segredo do Key Vault" {
    az containerapp secret set --name $app --resource-group $ResourceGroup `
        --secrets "foundry-key=keyvaultref:$segredoUri,identityref:system" --only-show-errors | Out-Null
}

$endpointFoundry = az cognitiveservices account show `
    --name $FoundryResourceName --resource-group $FoundryResourceGroup `
    --query properties.endpoint -o tsv

Passo "publicar a nossa imagem e as variaveis" {
    az containerapp update --name $app --resource-group $ResourceGroup `
        --image "$acr.azurecr.io/$imagem" `
        --set-env-vars `
            "AZURE_FOUNDRY_ENDPOINT=$endpointFoundry" `
            "AZURE_FOUNDRY_DEPLOYMENT=$Deployment" `
            "AZURE_FOUNDRY_AUTH=entra" `
            "AZURE_FOUNDRY_API_KEY=secretref:foundry-key" `
            "APPLICATIONINSIGHTS_CONNECTION_STRING=$appiConn" `
        --only-show-errors | Out-Null
}

Write-Host "`n=== 12. Porta e ingress ===" -ForegroundColor Cyan
Passo "ajustar a porta para 8501" {
    az containerapp ingress update --name $app --resource-group $ResourceGroup `
        --target-port 8501 --transport auto --only-show-errors | Out-Null
}

$url = az containerapp show --name $app --resource-group $ResourceGroup `
    --query properties.configuration.ingress.fqdn -o tsv

if (-not $url) {
    Write-Host "`nO app foi criado, mas nao tem URL de ingress. Veja os logs:" -ForegroundColor Red
    Write-Host "  az containerapp logs show -n $app -g $ResourceGroup --follow"
    exit 1
}

Write-Host "`n=== 13. Marcacao: reconciliacao e conferencia ===" -ForegroundColor Cyan
# Por que existe este passo, se cada `create` ja levou --tags?
#
#   1. Recurso REAPROVEITADO nao passa pelo `create` - ficaria sem marcacao.
#   2. O Azure cria recursos IMPLICITOS que voce nunca pediu (o Container Apps
#      cria o seu proprio ambiente gerenciado, por exemplo). Eles aparecem na
#      fatura e nao na sua lista.
#
# `az tag update --operation merge` acrescenta sem apagar o que ja existe.
# Em FinOps a regra e essa: a cobertura de marcacao tem que ser verificada,
# nao presumida. Recurso sem tag e custo sem dono.
$semTag = 0
foreach ($id in (az resource list --resource-group $ResourceGroup --query "[].id" -o tsv)) {
    az tag update --resource-id $id --operation merge --tags $tags --only-show-errors 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { $semTag++ }
}
if ($semTag -gt 0) {
    Write-Host "  aviso: $semTag recurso(s) nao aceitaram marcacao (nem todo tipo aceita)" -ForegroundColor DarkYellow
}

# ATENCAO - por que a tabela abaixo NAO usa `--query`.
#
# A tag `centro-custo` tem hifen, e em JMESPath uma chave com hifen so pode ser
# referenciada entre ASPAS DUPLAS: tags."centro-custo". O problema e chegar com
# essa aspa inteira ate o `az`:
#
#   No PowerShell a barra invertida NAO escapa aspas - quem escapa e a crase.
#   Entao \" dentro de uma string com aspas duplas FECHA a string, e o resto da
#   linha (inclusive o `-o table`) vira parte do argumento --query. O erro que
#   aparece e enganoso, porque fala de JMESPath:
#
#     argument --query: invalid jmespath_type value:
#     '[].{...centro:tags." centro-custo\} -o table'
#
#   Da para consertar com \`" (crase + aspa), mas isso muda entre PowerShell
#   5.1 e 7 e quebra de novo no proximo copiar-e-colar.
#
# A saida robusta e nao mandar aspa nenhuma pela linha de comando: pedimos JSON
# ao `az` e formatamos no PowerShell, onde chave com hifen se escreve
# `$_.tags.'centro-custo'` sem drama nenhum.
$recursos = ((az resource list --resource-group $ResourceGroup -o json) -join "`n") | ConvertFrom-Json
if ($recursos) {
    $recursos |
        Select-Object @{ n = 'recurso';  e = { $_.name } },
                      @{ n = 'tipo';     e = { $_.type } },
                      @{ n = 'projeto';  e = { $_.tags.projeto } },
                      @{ n = 'ambiente'; e = { $_.tags.ambiente } },
                      @{ n = 'centro';   e = { $_.tags.'centro-custo' } },
                      @{ n = 'aluno';    e = { $_.tags.aluno } } |
        Format-Table | Out-String -Width 200 | Write-Host
        # `Format-Table -AutoSize` some quando nao ha console de verdade (saida
        # redirecionada para arquivo, execucao dentro de pipeline de CI). O
        # `Out-String -Width` desenha a tabela sempre igual, com ou sem console.

    $orfaos = @($recursos | Where-Object { -not $_.tags.projeto })
    if ($orfaos.Count -gt 0) {
        Write-Host "  ATENCAO: $($orfaos.Count) recurso(s) sem a tag 'projeto' - custo sem dono:" -ForegroundColor DarkYellow
        $orfaos | ForEach-Object { Write-Host "    $($_.name)  ($($_.type))" -ForegroundColor DarkYellow }
    } else {
        Write-Host "  cobertura de marcacao: 100% dos recursos com a tag 'projeto'" -ForegroundColor Green
    }
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " Eva publicada: https://$url" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host @"

Recursos no grupo '$ResourceGroup':
  ACR ................ $acr
  Key Vault .......... $kv
  App Insights ....... $appInsights
  Container App ...... $app

Ver os logs:
  az containerapp logs show -n $app -g $ResourceGroup --follow

FinOps - o custo desta aula, agrupado pela marcacao:

  1) No portal (caminho principal, sem instalar nada):
     Cost Management > Cost analysis > Group by > Tag > projeto
     Filtre por  centro-custo=$CentroDeCusto  para ver so o que e da turma.

  2) Por linha de comando, se voce quiser automatizar:
     cd infra
     .\custo.ps1                 # agrupado por projeto
     .\custo.ps1 -Tag aluno      # quanto cada pessoa da turma gastou

     O script chama a API de custo com `az rest`, manda o cabecalho ClientType
     (sem ele voce divide a cota com o mundo inteiro e toma 429 na primeira
     chamada) e tenta de novo com espera crescente se levar 429 mesmo assim.

  DOIS avisos que economizam tempo:
   - "az costmanagement query" foi REMOVIDO da extensao na versao 0.2.1.
     Instalar a extensao nao resolve, e a mensagem de erro nao explica isso.
   - O numero do Cost Management atrasa HORAS. Gastar e olhar em seguida nao
     funciona - para decidir agora, use o Application Insights.

  Conferir a cobertura da marcacao (recurso sem tag = custo sem dono):
  az resource list -g $ResourceGroup --query "[?tags.projeto==null].name" -o tsv

Apagar tudo quando terminar a aula:
  az group delete --name $ResourceGroup --yes --no-wait
"@
