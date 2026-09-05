# Eva

Agente básico em Python, com duas caras: **terminal** e **interface web (Streamlit)**.
Feito para ser entendido inteiro em 10 minutos e crescer daí.

> 📘 **Primeira vez aqui?** Comece pelo [GUIA-DO-PROJETO.md](GUIA-DO-PROJETO.md) —
> objetivo, diagramas (contexto, arquitetura e sequência), o que é cada arquivo e
> exercícios. Este README é a referência rápida.

## Instalar (PowerShell)

### Passo 1 — baixar o projeto

```powershell
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud\aulas\05-foundry-agents\01-agente-Eva-local
```

### Passo 2 — criar o ambiente e instalar dependências

O PowerShell do Windows (5.1) **não aceita `&&`** — isso é sintaxe do `cmd` e do
PowerShell 7+. Use uma linha por comando:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env          # cole sua OPENAI_API_KEY e salve
```

Se o `Activate.ps1` reclamar de política de execução, libere só para esta janela:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Deu certo quando o prompt vira `(.venv) PS C:\...\Eva>`.

<details>
<summary>Linux / macOS</summary>

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
</details>

## Rodar

**Interface web:**

```powershell
streamlit run app.py
```

Abre no navegador em `http://localhost:8501`.

**Terminal:**

```powershell
python eva.py
```

```
Eva — gpt-4o-mini
Digite /ajuda para ver os comandos.

você> quantos dias faltam para o natal?

eva> Faltam 113 dias — hoje é 2 de setembro.
```

## A interface

| Onde | O que faz |
|---|---|
| Chat | Resposta em streaming, palavra a palavra |
| 🔧 acima da resposta | Rastro da ferramenta: o que foi pedido e o que voltou |
| Barra lateral · Modelo | Troca de modelo sem reiniciar |
| Barra lateral · Temperatura | 0 = objetiva · 1 = criativa |
| Barra lateral · Máx. de iterações | Quantas rodadas de ferramenta ela pode fazer |
| Barra lateral · `memory.md` | Edita a memória e reinjeta no prompt na hora |
| Barra lateral · `agent.md` | Edita a identidade dela pela própria tela |
| Nova conversa | Zera o histórico (a memória em arquivo continua) |

Editar o `memory.md` pela barra lateral e ver a Eva mudar de comportamento na
mensagem seguinte é o jeito mais rápido de sentir o que o prompt de sistema faz.

## Comandos do terminal

| Comando | O que faz |
|---|---|
| `/sair` | encerra |
| `/lembrar <fato>` | grava um fato em `memory.md` |
| `/memoria` | mostra o `memory.md` |
| `/limpar` | esquece a conversa atual |
| `/verboso` | mostra as chamadas de ferramenta |
| `/ajuda` | lista os comandos |

## Os arquivos

| Arquivo | Papel |
|---|---|
| `eva.py` | **O agente.** Configuração, ferramentas, loop e chat de terminal |
| `app.py` | **Só interface.** Streamlit; importa tudo do `eva.py` |
| `agent.md` | **É** o prompt de sistema. Identidade, tom e regras da Eva |
| `memory.md` | O que ela sabe sobre você. Lido a cada execução |

A separação que vale a pena manter conforme o projeto cresce:

```
eva.py  = o agente       (roda no terminal, num teste, num servidor)
app.py  = uma das caras  (Streamlit hoje; amanhã uma API, um bot)
```

Se você acrescentar uma ferramenta no `eva.py`, ela aparece na interface
sozinha — o `app.py` não sabe quais ferramentas existem, e é bom que não saiba.

## O que faz disso um agente

Uma chamada de API é: pergunta entra, resposta sai. Um agente tem um **loop**:

```
manda a conversa + as ferramentas para o modelo
   │
   ├─ modelo pediu ferramenta? → executa aqui na sua máquina,
   │                              devolve o resultado e repete
   │
   └─ modelo respondeu em texto? → acabou, essa é a resposta
```

Duas versões do mesmo loop, em `eva.py`:

- `responder()` — devolve a resposta pronta. Usada pelo terminal.
- `responder_stream()` — **gerador**: vai emitindo `("ferramenta", …)` e
  `("texto", …)` conforme acontecem. Usada pela interface.

O detalhe chato do streaming: a OpenAI manda a chamada de ferramenta **em
pedaços** — o nome vem numa hora, os argumentos chegam em fatias de texto que
você precisa concatenar antes de ter um JSON válido. É o dicionário `parciais`
dentro de `responder_stream()`.

E o ponto que costuma confundir: **o modelo nunca executa nada.** Ele só devolve
"quero chamar `que_horas_sao` com esses argumentos". Quem executa é o seu
Python. Isso é bom — você controla o que ele consegue fazer.

## Onde a OpenAI é instanciada

Uma função só, em `eva.py`:

```python
def get_cliente() -> OpenAI:
    ...
    _cliente = OpenAI(api_key=chave)
    return _cliente
```

É preguiçosa (só instancia na primeira chamada) para que `import eva` não
exploda sem chave configurada — é o que permite o `app.py` mostrar um erro
bonito na tela em vez de uma stack trace.

O modelo vem de `OPENAI_MODEL` no `.env`, e a interface pode sobrescrever pela
barra lateral.

## Adicionar uma ferramenta

Três passos, na seção 3 do `eva.py`:

```python
# 1. a função
def somar(a: float, b: float) -> dict:
    return {"resultado": a + b}

# 2. a declaração (é isso que o modelo lê para decidir se chama)
FERRAMENTAS.append({
    "type": "function",
    "function": {
        "name": "somar",
        "description": "Soma dois números. Use para qualquer conta de adição.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        },
    },
})

# 3. o registro
EXECUTORES["somar"] = somar
```

A `description` importa mais que o código: é por ela que o modelo decide quando
chamar. Descrição vaga = ferramenta ignorada ou usada na hora errada.

## Próximos passos sugeridos

Em ordem de esforço crescente — pegue um por vez:

1. **Memória automática.** Hoje quem grava é você (`/lembrar` ou a barra
   lateral). Vire isso numa ferramenta `salvar_memoria` e deixe a Eva decidir o
   que vale guardar. É o menor exercício possível de autonomia.
2. **Mais ferramentas.** Ler um arquivo, buscar na web, consultar sua agenda.
3. **Histórico entre sessões.** Salvar as mensagens em JSON e recarregar.
4. **Isolar a chamada do modelo** atrás de uma função `chamar_modelo()` — é o
   passo que depois permite apontar para Anthropic, Azure OpenAI ou modelo local.
5. **Publicar.** `streamlit run` é local; para colocar no ar, empacote em
   container e suba (Azure Container Apps, por exemplo).
