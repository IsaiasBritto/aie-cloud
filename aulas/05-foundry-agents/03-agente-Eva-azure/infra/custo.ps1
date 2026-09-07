<#
    custo.ps1 - custo do mes corrente, agrupado por uma tag.

    POR QUE ESTE SCRIPT EXISTE, se a chamada e uma so:

    1. `az costmanagement query` NAO existe mais. Foi removido da extensao
       `costmanagement` na versao 0.2.1. Instalar a extensao nao resolve, e a
       mensagem do CLI ("is misspelled or not recognized") aponta para o lugar
       errado. O que continua funcionando e a API, via `az rest`.

    2. A API de Cost Management LIMITA agressivamente, e o limite e
       COMPARTILHADO. Se voce nao manda o cabecalho `ClientType`, cai num
       balde de cota dividido com todo mundo no mundo que tambem nao manda -
       e por isso da para tomar 429 na PRIMEIRA chamada, sem ter feito nada
       errado. Com `ClientType` proprio, a cota passa a ser sua.

    3. Mesmo com ClientType, uma turma inteira consultando ao mesmo tempo
       estoura o limite. Por isso o retry com espera crescente.

    Uso:
        .\custo.ps1
        .\custo.ps1 -Tag aluno
        .\custo.ps1 -Tag centro-custo -Tentativas 8
#>
[CmdletBinding()]
param(
    [string]$Tag = "projeto",
    [string]$Assinatura = "",
    [string]$ApiVersion = "2026-06-01",
    [int]$Tentativas = 5,
    # Identifica VOCE para o servico de cota. Troque pelo nome da sua turma se
    # quiser separar ainda mais - o valor e livre, so nao pode ficar vazio.
    [string]$ClientType = "FIAP-MBA-Eva-Lab",
    # Contrato EA usa "PreTaxCost" no lugar de "Cost". Azure for Students e
    # MCA, entao o padrao serve.
    [ValidateSet("Cost", "PreTaxCost")]
    [string]$CampoCusto = "Cost"
)

$ErrorActionPreference = "Continue"

if (-not $Assinatura) {
    $Assinatura = az account show --query id -o tsv
    if (-not $Assinatura) {
        Write-Host "Voce nao esta logado. Rode: az login" -ForegroundColor Red
        exit 1
    }
}

# O corpo vai em ARQUIVO, nunca inline. JSON com aspas na linha de comando
# esbarra no mesmo problema de escape que ja quebrou o passo 13 do deploy.ps1:
# no PowerShell a barra invertida nao escapa aspas.
$corpo = @{
    type      = "ActualCost"
    timeframe = "MonthToDate"
    dataset   = @{
        granularity = "None"
        aggregation = @{ totalCost = @{ name = $CampoCusto; function = "Sum" } }
        grouping    = @(@{ type = "TagKey"; name = $Tag })
    }
}
$arquivo = Join-Path ([System.IO.Path]::GetTempPath()) "eva-consulta-custo.json"
$corpo | ConvertTo-Json -Depth 8 | Set-Content -Path $arquivo -Encoding utf8

$url = "https://management.azure.com/subscriptions/$Assinatura" +
       "/providers/Microsoft.CostManagement/query?api-version=$ApiVersion"

Write-Host "Consultando o custo do mes, agrupado pela tag '$Tag'..." -ForegroundColor Cyan

$espera = 10
$resposta = $null

for ($i = 1; $i -le $Tentativas; $i++) {
    $saida = az rest --method post --url $url --body "@$arquivo" `
                --headers "ClientType=$ClientType" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $resposta = ($saida -join "`n") | ConvertFrom-Json
        break
    }

    if ("$saida" -match "429|Too many requests|TooManyRequests") {
        if ($i -eq $Tentativas) {
            Write-Host "`nAinda 429 depois de $Tentativas tentativas." -ForegroundColor Red
            Write-Host "O limite da API de custo e compartilhado e curto. Suas opcoes:" -ForegroundColor Red
            Write-Host "  a) esperar alguns minutos e rodar de novo"
            Write-Host "  b) usar o portal, que nao passa por esta cota:"
            Write-Host "     Cost Management > Cost analysis > Group by > Tag > $Tag"
            exit 1
        }
        Write-Host "  429 (limite da API). Tentativa $i de $Tentativas - esperando ${espera}s..." -ForegroundColor DarkYellow
        Start-Sleep -Seconds $espera
        $espera = [Math]::Min($espera * 2, 120)   # 10, 20, 40, 80, 120...
        continue
    }

    Write-Host "`nA consulta falhou por outro motivo:" -ForegroundColor Red
    Write-Host $saida
    exit 1
}

# --------------------------------------------------------------------------
# A resposta vem em `properties.columns` + `properties.rows`, sem nomes nas
# linhas. Descobrimos a posicao de cada coluna pelo nome antes de ler.
# --------------------------------------------------------------------------
$colunas = $resposta.properties.columns.name
$iCusto  = [Array]::IndexOf($colunas, $CampoCusto)
# Agrupando por TagKey a resposta traz DUAS colunas: `TagKey` (o nome da tag,
# igual em todas as linhas) e `TagValue` (o que interessa). Ler a errada faz a
# tabela sair com a mesma palavra repetida em todas as linhas.
$iTag    = [Array]::IndexOf($colunas, "TagValue")
if ($iTag -lt 0) { $iTag = [Array]::IndexOf($colunas, "TagKey") }
if ($iTag -lt 0) { $iTag = 1 }
$iMoeda  = [Array]::IndexOf($colunas, "Currency")

$linhas = @($resposta.properties.rows)
if ($linhas.Count -eq 0) {
    Write-Host "`nSem custo registrado ainda para esta janela." -ForegroundColor DarkYellow
    Write-Host "O Cost Management demora HORAS para consolidar - gastar e olhar em"
    Write-Host "seguida nao funciona. E a tag so vale a partir do momento em que existe:"
    Write-Host "custo gerado antes da marcacao nao e reclassificado."
    exit 0
}

$total = 0.0
$linhas |
    ForEach-Object {
        $valor = [double]$_[$iCusto]
        $total += $valor
        [pscustomobject]@{
            $Tag    = if ($_[$iTag]) { $_[$iTag] } else { "(sem a tag)" }
            custo   = [Math]::Round($valor, 4)
            moeda   = if ($iMoeda -ge 0) { $_[$iMoeda] } else { "" }
        }
    } |
    Sort-Object custo -Descending |
    Format-Table | Out-String -Width 120 | Write-Host

Write-Host ("Total no mes: {0:N4}" -f $total) -ForegroundColor Green
Write-Host "`nLembretes:" -ForegroundColor DarkGray
Write-Host "  - o numero atrasa horas; nao serve para conferir o que voce acabou de gastar" -ForegroundColor DarkGray
Write-Host "  - a linha '(sem a tag)' e custo sem dono: rode a conferencia de marcacao" -ForegroundColor DarkGray
