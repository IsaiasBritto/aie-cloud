# Eva (local → Azure)

A mesma Eva, agora falando com um modelo hospedado no **Microsoft Foundry**
(ex-Azure AI Foundry). A aplicação continua rodando na **sua máquina**; só o
modelo mudou de lugar.

> 📘 **Primeira vez?** Comece pelo [GUIA-AI-FOUNDRY.md](GUIA-AI-FOUNDRY.md) —
> como criar o recurso, implantar o modelo e pegar endpoint e chave.

---

### Passo 1 — baixar o projeto

```powershell
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud\aulas\05-foundry-agents\02-agente-Eva-local-to-azure
```

### Passo 2 — criar o ambiente e instalar dependências
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env          # preencha com os dados do seu Foundry
```

> PowerShell não aceita `&&` — um comando por linha.
> Se o `Activate.ps1` reclamar: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

**Sempre confira a conexão antes de rodar a Eva:**

```powershell
python verificar.py
```

Ele testa endpoint, autenticação, o deployment e o tool calling — um de cada
vez, dizendo exatamente onde parou.

## Rodar

```powershell
python eva.py              # terminal
streamlit run app.py       # interface web
```

---

## O que mudou em relação à Eva original

Uma função. Literalmente.

```diff
- cliente = OpenAI(api_key=chave)
+ cliente = OpenAI(base_url=f"{ENDPOINT}/openai/v1/", api_key=chave)
```

```diff
- model="gpt-5.4-mini"      # nome do modelo
+ model="eva-aula"         # nome do DEPLOYMENT
```

O loop do agente, as ferramentas, o `agent.md` e o `memory.md` estão
inalterados. Era esse o teste da arquitetura: se a troca de provedor não cabe
numa função, a separação estava errada.

**Arquivos novos:** `verificar.py` (diagnóstico) e `GUIA-AI-FOUNDRY.md`.

---

## Deployment ≠ modelo

A parte que mais confunde quem vem da OpenAI pública:

| | OpenAI pública | Foundry |
| --- | --- | --- |
| O que vai em `model=` | nome do modelo (`gpt-5.4-mini`) | **nome do deployment** (`eva-aula`) |
| Modelos disponíveis | todo o catálogo, na hora | só os que você implantou |
| Modelo não implantado | funciona | **404 DeploymentNotFound** |

O deployment é uma instância que você cria no portal, com nome e cota
escolhidos por você. Isso permite trocar o modelo por trás sem tocar no código
— e ter dois modelos no mesmo recurso, escolhendo por chamada.

Na interface web, o campo **Deployment** na barra lateral troca o destino ao
vivo, sem reiniciar.

---

## Configuração (`.env`)

| Variável | O que é |
| --- | --- |
| `AZURE_FOUNDRY_ENDPOINT` | Host do recurso, **sem** caminho: `https://seu-recurso.openai.azure.com` |
| `AZURE_FOUNDRY_DEPLOYMENT` | Nome do deployment que você criou |
| `AZURE_FOUNDRY_AUTH` | `chave` (aula) ou `entra` (produção) |
| `AZURE_FOUNDRY_API_KEY` | Só no modo `chave` |
| `EVA_TEMPERATURA` | 0 = objetiva · 1 = criativa |
| `EVA_MAX_ITERACOES` | Teto de voltas do loop |

### Modo `entra` (sem chave)

```powershell
pip install azure-identity
az login
```

E `AZURE_FOUNDRY_AUTH=entra` no `.env`. Precisa da role **Cognitive Services
OpenAI User** no recurso — ser Owner da assinatura não basta para o plano de
dados.

O código usa `AzureOpenAI` nesse modo (e não o `OpenAI` comum) porque o token
do Entra expira em ~1h e só o `AzureOpenAI` renova sozinho a cada requisição.

---

## Problemas comuns

| Erro | Causa provável |
| --- | --- |
| `401 Unauthorized` | Chave errada; ou no modo `entra`, faltou `az login` / a role |
| `404 DeploymentNotFound` | Nome do deployment errado, ou endpoint com caminho colado |
| `429` | TPM do deployment esgotado |
| Erro de api-version no modo `entra` | Troque `base_url=` por `azure_endpoint=` e use uma `api_version` datada em `get_cliente()` |
| O modelo ignora as ferramentas | O deployment não suporta tool calling |

`python verificar.py` traduz todos esses.

---

## Próximo passo

Hoje: modelo no Azure, aplicação local. Depois: aplicação também no Azure —
Dockerfile, Azure Container Apps, Managed Identity (o modo `entra`, sem
`az login`), Key Vault e Application Insights.

O modo `entra` já está aqui exatamente por causa disso: em Container Apps você
liga uma Managed Identity, dá a role no Foundry, e o mesmo código roda sem
nenhum segredo em lugar nenhum.
