# Agente base — template

Esse projeto tem a finalidade de ser um esqueletobase para nossos agentes de IA em Python.

---

## 1. Rodar em 5 minutos

### Passo 1 — baixar o projeto

```powershell
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud\aulas\05-foundry-agents\agentebase
```

### Passo 2 — criar o ambiente e instalar dependências

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env          # cole sua OPENAI_API_KEY e salve
```

> **PowerShell não aceita `&&`** — um comando por linha.
> Se o `Activate.ps1` reclamar de política de execução:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

<details>
<summary>Linux / macOS</summary>

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
</details>

**Versão terminal:**

```powershell
python agent.py
```

**Versão web:**

```powershell
streamlit run app.py
```

Teste com *"quanto é 1234 mais 5678?"* — você vai ver a linha
`[ferramenta] somar(...)` no terminal. Esse é o loop do agente acontecendo.

---

## 2. Os arquivos

```
agentebase/
├── agent.py            ← o agente (a lógica)
├── app.py              ← a interface web (Streamlit)
├── agent.md            ← o prompt de sistema: quem o agente é
├── memory.md           ← o que ele sabe, entre execuções
├── dados/              ← o que o agente pode ler (usado pelos exercícios)
├── .env.example        ← modelo de configuração (vai para o Git)
├── .env                ← sua chave (NÃO vai para o Git)
├── .gitignore
├── requirements.txt
├── README.md
```

| Arquivo | O que é | Você mexe? |
|---|---|---|
| `agent.py` | Configuração, ferramentas, loop e terminal | Sim — seção 3 (ferramentas) |
| `app.py` | Só interface. Importa tudo do `agent.py` | Só se quiser mudar a tela |
| `exercicios_tools.py` | Ferramentas de exercício, **desligadas** | Quando fizer o roteiro de aula |
| `agent.md` | **É** o prompt de sistema, não documentação | **Sim — comece por aqui** |
| `memory.md` | Injetado no prompt a cada execução | Sim, conforme precisar |
| `.env` | Chave e parâmetros | Uma vez, no começo |

O `agent.py` está dividido em 5 seções numeradas: configuração, contexto,
ferramentas, loop e terminal. Leia nessa ordem.

---

## 3. O que faz disso um agente

Uma chamada de API é: pergunta entra, resposta sai. Um agente tem um **loop**:

```
manda a conversa + as ferramentas para o modelo
   │
   ├─ pediu ferramenta?  → executa aqui na sua máquina,
   │                        devolve o resultado e repete
   │
   └─ respondeu em texto? → acabou, essa é a resposta
```

Está na função `responder()`, ~35 linhas. É o padrão inteiro.

**O ponto que mais confunde:** o modelo **nunca executa nada**. Ele devolve um
texto dizendo *"quero chamar `somar` com estes argumentos"*. Quem executa é o
seu Python, na sua máquina, com as suas permissões. Isso é bom — você controla
exatamente o que ele consegue fazer.

---

## 4. Como personalizar

### Passo 1 — reescreva o `agent.md`

Alterar o arquivo agent.md é o que principalmente  muda o comportamento do agente e não exige uma linha de código. Os `TODO`
dentro do arquivo indicam o que trocar.

# 3. o registro
## Exercício

Em ordem de dificuldade:

1. **Mudar a personalidade** — só `agent.md`.
2. **Sabotar a `description`** — troque a da `somar` por *"faz uma coisa"* e
   veja o modelo parar de chamá-la. É a forma mais rápida de entender que a
   descrição é a interface entre o modelo e o seu código.
3. **Criar uma ferramenta** do seu domínio.
4. **Ferramenta que lê um arquivo** — cuidado: valide o caminho, senão o agente
   lê qualquer coisa do disco. O `exercicios_tools.py` já traz uma pronta, com
   o roteiro de aula sobre sandbox.
5. **Memória automática** — hoje o `memory.md` você edita à mão. Crie uma
   ferramenta `salvar_memoria(nota)` e deixe o agente decidir o que guardar.
   É o menor exercício possível de autonomia.
6. **Histórico entre sessões** — salvar as mensagens em JSON e recarregar.
7. **Streaming na interface** — resposta palavra a palavra em vez do spinner.

---

## 6. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `O token '&&' não é um separador válido` | PowerShell não aceita `&&`. Um comando por linha. |
| `Activate.ps1 não pode ser carregado` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `ModuleNotFoundError` | Instalou fora do venv. Ative o venv e repita o `pip install`. |
| `OPENAI_API_KEY não encontrada` | Falta o `.env`, ou você está rodando de outra pasta. |
| Erro 401 | Chave inválida — confira se não sobrou a linha de exemplo no `.env`. |
| Erro 429 | Limite de cota da sua conta OpenAI. Não é bug do código. |
| O agente não chama a ferramenta | A `description` está vaga. Diga **quando** usar. |
| Ele "esqueceu" o combinado | Foi para o histórico da conversa, não para o `memory.md`. Só o arquivo persiste. |
| Parede de `missing ScriptRunContext` | Rodou `python app.py`. Use `streamlit run app.py`. |

---

## 7. O que este template deliberadamente NÃO tem

Para você saber o que falta quando precisar:

- **Streaming** — a resposta aparece de uma vez
- **Troca de provedor** — está preso à OpenAI; isolar em `chamar_modelo()` é o primeiro passo para mudar isso
- **Persistência** — nada é salvo entre execuções, exceto o `memory.md`
- **Testes** — nenhum
- **Autenticação, logs, custos, deploy** — nada disso

Tudo isso é infraestrutura em volta das ~35 linhas do `responder()`. O loop não
muda.
