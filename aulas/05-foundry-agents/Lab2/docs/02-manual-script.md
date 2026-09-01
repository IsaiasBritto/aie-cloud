# Manual 2 — por script

> O mesmo resultado do [Manual 1](01-manual-portal.md), em oito comandos.
> Use este quando o objetivo for **repetir** — outra turma, outro aluno, outro ambiente.
> Use o do portal quando o objetivo for **entender**.

---

## Antes de tudo

```bash
az login
az account show --query "{assinatura:name, id:id}" -o table
az account set --subscription "<sua assinatura>"
```

E o orçamento — que não é opcional num módulo em que o agente acorda sozinho:

```bash
az consumption budget create \
  --budget-name orc-aula-02-continuo \
  --amount 10 --category cost --time-grain monthly \
  --start-date $(date +%Y-%m-01) --end-date $(date -d "+3 months" +%Y-%m-01)
```

---

## 1 · Rodar na sua máquina primeiro (2 min, sem gastar nada)

Antes de provisionar qualquer coisa, veja o ciclo inteiro funcionando local. É o melhor
uso possível de dois minutos.

```bash
git clone <seu-repositorio> && cd deva-continuo
python -m venv .venv && source .venv/bin/activate
pip install -r api/requisitos.txt -r web/requisitos.txt

# terminal 1 — o serviço
uvicorn api.principal:app --reload

# terminal 2 — a tela
streamlit run web/aplicacao.py

# terminal 3 — o gatilho e o agente
python gatilho/disparador.py --semear
python gatilho/ciclo_do_agente.py --uma-volta --propor
python gatilho/ciclo_do_agente.py --uma-volta
python gatilho/ciclo_do_agente.py --uma-volta
```

Abra <http://localhost:8501>. Ou, se preferir containers:

```bash
docker compose up --build
```

Rode os testes antes de subir qualquer coisa para a nuvem:

```bash
python -m pytest -q      # 22 testes, nenhum toca a rede
```

O teste que importa se chama `teste_agente_nao_consegue_aprovar_sozinho`. Se ele quebrar,
o projeto perdeu o sentido.

---

## 2 · Provisionar (5 min)

```bash
export SUFIXO=isb01          # suas iniciais + turma
source infra/00-variaveis.sh
bash infra/01-criar-recursos.sh      # pede confirmação digitada
```

Cria: grupo · conta de armazenamento · contêineres `memoria-do-deva` e `entrada` ·
registro de contêiner · ambiente de Container Apps.

O script imprime a cadeia de conexão no fim. Guarde:

```bash
export CONEXAO='<a cadeia impressa>'
```

---

## 3 · Publicar as imagens (4 min)

```bash
bash infra/02-publicar-imagens.sh
```

`az acr build` constrói **na nuvem**: o aluno não precisa de Docker instalado. É a linha
que economiza os 20 minutos de "na minha máquina não sobe".

⚠️ As duas imagens são construídas **a partir da raiz** (`docker build -f api/Dockerfile .`).
Construir de dentro de `api/` deixa o pacote de fora e o container sobe com
`ModuleNotFoundError`.

---

## 4 · Implantar (4 min)

```bash
bash infra/03-implantar-apps.sh
```

Três coisas para reparar na saída do script:

| Linha | Por que importa |
|---|---|
| `--min-replicas 0` | fora da aula, os containers dormem e não cobram |
| `--secrets "conexao=…" "segredo=…"` | a chave entra como segredo, e as variáveis apontam com `secretref:` — nunca em texto puro na linha de comando |
| o segredo do auditor impresso no fim | é ele que separa a tela do agente; guarde |

---

## 5 · Gerar a especificação do agente (1 min)

```bash
python gerar_openapi_do_agente.py
# edite agente/openapi-agente.json e troque https://SUA-URL/ pela URL impressa acima
```

O script imprime as **cinco** operações que o agente recebe. Ele também falha se alguma
rota de aprovação vazar para o arquivo — a verificação está no próprio código:

```python
for proibida in PROIBIDAS:
    assert proibida not in texto, f"rota proibida vazou para a especificação: {proibida}"
```

Cole o arquivo em **ai.azure.com** → Deva → Ferramentas → Personalizado →
**Ferramenta OpenAPI**.

---

## 6 · Ligar o gatilho (3 min)

```bash
# assinatura do Event Grid apontando para a Logic App
az eventgrid event-subscription create \
  --name evt-deva-entrada \
  --source-resource-id $(az storage account show -n "$ARMAZENAMENTO" -g "$GRUPO" --query id -o tsv) \
  --endpoint-type webhook \
  --endpoint "<url-de-callback-da-logic-app>" \
  --included-event-types Microsoft.Storage.BlobCreated \
  --subject-begins-with "/blobServices/default/containers/entrada/"
```

⚠️ **O `--subject-begins-with` não é detalhe.** Sem ele, todo blob dispara o fluxo —
inclusive o `MEMORY.md` que o próprio serviço escreve. O agente acorda, escreve, e acorda
de novo. É o laço mais caro que existe, e ele se monta sozinho.

A definição da Logic App está em `gatilho/logic-app-eventgrid.json` (Modo de Exibição de
Código do designer).

**Sem Event Grid**, em sala, a sondagem resolve e é mais visível:

```bash
python gatilho/disparador.py --pasta entrada --intervalo 5
```

---

## 7 · Conferir de ponta a ponta (2 min)

```bash
API=https://<sua-url>

curl -s $API/saude | jq
curl -s -X POST $API/fila/documentos -H 'Content-Type: application/json' \
     -d '{"arquivo":"recibo_0412.pdf","fornecedor":"Trattoria","valor_total":412}'

# o agente propõe
curl -s -X POST $API/memoria/proposta -H 'Content-Type: application/json' \
     -d '{"secao":"classificacao","texto":"Estacionamento em aeroporto entra como viagem_aerea.","evidencia":"recibo_0412.pdf; correcao da Camila em 01/09"}'

# o agente tenta aprovar — deve falhar com 403
PROP=$(curl -s "$API/memoria/propostas?situacao=pendente" | jq -r '.[0].identificador')
curl -s -X POST $API/memoria/propostas/$PROP/aprovar \
     -H 'Content-Type: application/json' -d '{"auditor":"deva"}' | jq

# o auditor aprova — deve funcionar
curl -s -X POST $API/memoria/propostas/$PROP/aprovar \
     -H 'Content-Type: application/json' -H "X-Auditor: Camila Rocha" \
     -H "X-Segredo: $SEGREDO_AUDITOR" -d '{"auditor":"Camila Rocha"}' | jq

curl -s $API/memoria/markdown
```

A última linha imprime o `MEMORY.md`. É o mesmo arquivo que está no Blob — compare a hora
de modificação no portal.

---

## 8 · Apagar tudo (1 min)

```bash
bash infra/99-remover-tudo.sh     # exige digitar o nome do grupo
az group exists --name rg-aula-02-continuo    # deve responder false em alguns minutos
```

E, no Foundry, remova a Ferramenta OpenAPI do Deva — ela aponta para uma URL que deixou de
existir, e agente com ferramenta quebrada tenta, falha e gasta.

---

## Referência rápida das variáveis

| Variável | Onde vive | Para quê |
|---|---|---|
| `DEVA_BLOB_CONEXAO` | serviço | cadeia de conexão do armazenamento; vazia = arquivo local |
| `DEVA_BLOB_CONTAINER` | serviço | contêiner da memória (padrão `memoria-do-deva`) |
| `DEVA_PASTA_LOCAL` | serviço | pasta usada quando não há Blob (padrão `dados`) |
| `DEVA_SEGREDO_AUDITOR` | serviço **e** tela | separa a pessoa do agente; vazio = modo aula |
| `DEVA_MAX_PROPOSTAS` | serviço | teto da fila de propostas (padrão 50) |
| `DEVA_API` | tela e gatilho | URL do serviço |
