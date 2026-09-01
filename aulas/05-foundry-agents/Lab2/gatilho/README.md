# Deva contínuo — memória revisável e fila de documentos

**Aula 02 · módulo complementar** · MBA AI Engineering & Multi-Agents · Cloud & Cognitive
Environments · Prof. Isaias S. Britto · FIAP

Responde a duas perguntas feitas em sala:

> *"O Deva lê nota fiscal, mas não se mostra um agente interativo contínuo. Como
> incrementá-lo para ter esse comportamento?"*
>
> *"Como os alunos conseguem abrir o `MEMORY.md` para saber que ele está aprendendo?"*

A resposta é este projeto: um **Serviço de Continuidade** (FastAPI) com memória revisável e
fila de documentos, uma **tela** (Streamlit) onde a memória muda na frente da turma, e um
**gatilho** que faz o agente começar sozinho.

---

## A ideia em uma imagem

```
o agente:  POST /memoria/proposta   →  memoria-pendente.md   (não vale nada)
o humano:  clica em Aprovar         →  MEMORY.md             (o agente lê no início da sessão)
```

O agente **propõe**; ele não decide. A especificação OpenAPI que ele carrega tem cinco
operações, e nenhuma delas aprova coisa alguma — as rotas de aprovação existem e são
usadas pela tela, com o cabeçalho `X-Auditor` que o agente nunca recebe.

> Instrução é intenção; permissão é controle. Em agentes, o que você não quer que aconteça,
> você não expõe.

---

## Rodar em dois minutos, sem Azure

```bash
pip install -r api/requisitos.txt -r web/requisitos.txt

uvicorn api.principal:app --reload          # terminal 1
streamlit run web/aplicacao.py              # terminal 2

python gatilho/disparador.py --semear       # terminal 3
python gatilho/ciclo_do_agente.py --uma-volta --propor
python gatilho/ciclo_do_agente.py --uma-volta
python gatilho/ciclo_do_agente.py --uma-volta
```

Abra <http://localhost:8501>. Ou, com containers: `docker compose up --build`.

```bash
python -m pytest -q     # 22 testes, nenhum toca a rede
```

---

## Por onde começar a ler

| Ordem | Arquivo | Para quem |
|---|---|---|
| 1 | `docs/00-cinco-niveis.md` | todos — a escada da continuidade, degrau a degrau |
| 2 | `agente/MUDANCAS-v1.3-para-v2.0.md` | todos — as seis mudanças no `AGENTS.md`, com o porquê |
| 3 | `docs/03-roteiro-do-modulo.md` | professor — os 45 minutos, bloco a bloco |
| 4 | `docs/01-manual-portal.md` | aluno — tela a tela, sem digitar comando |
| 5 | `docs/02-manual-script.md` | aluno — o mesmo, em oito comandos |
| 6 | `api/servicos/memoria.py` | quem quiser ver a fronteira em código |

Apresentação: `deva-continuo-memoria-e-fila.pptx` — 32 slides, incluindo um **bloco de
laboratório** (objetivo, os oito módulos com o conceito de cada um, mapa conceito→código,
os trechos de código que importam, checkpoints e os erros que vão acontecer).

---

## Estrutura

```
deva-continuo/
├── api/                        Serviço de Continuidade (FastAPI)
│   ├── modelos.py              contratos: memória, propostas, fila, máquina de estados
│   ├── configuracao.py         toda variável de ambiente mora aqui
│   ├── erros.py                todo erro carrega `como_resolver`
│   ├── principal.py            as rotas — e a fronteira `exigir_auditor`
│   ├── servicos/
│   │   ├── armazenamento.py    Blob ou arquivo local, mesma interface
│   │   ├── memoria.py          propor · aprovar · descartar · renderizar
│   │   └── fila.py             estados e transições permitidas
│   └── testes/                 22 testes, sem rede
├── web/aplicacao.py            a tela: Painel · Memória · Propostas · Exceções
├── gatilho/
│   ├── disparador.py           sondagem (aula) — e `--semear`
│   ├── ciclo_do_agente.py      as cinco etapas do laço, para ver funcionando
│   └── logic-app-eventgrid.json  Event Grid → Logic App (produção)
├── agente/
│   ├── AGENTS.md               v2.0 — agente contínuo
│   ├── MUDANCAS-v1.3-para-v2.0.md
│   ├── openapi-agente.json     as CINCO operações que o agente recebe
│   └── skills/propor-memoria/SKILL.md
├── infra/                      scripts az numerados + remoção
├── docs/                       cinco níveis · manuais · roteiro · diagramas
└── figuras/                    telas capturadas e o script que as captura
```

---

## Os três diagramas

| Diagrama | O que mostra |
|---|---|
| `docs/imagens/01-fluxo-da-memoria.png` | proposta → validação → pendente → aprovação, com os dois caminhos de recusa |
| `docs/imagens/02-maquina-de-estados.png` | os sete estados do documento e por que exceção não volta ao agente |
| `docs/imagens/03-ciclo-continuo.png` | a sequência completa: gatilho, ciclo, recusa de aprovação, aprovação humana |

Os fontes `.mmd` ficam em `docs/diagramas/`. Diagrama é **código**: quando o projeto muda,
o `.mmd` muda no mesmo commit.

---

## O que este projeto deliberadamente NÃO faz

- **Não deixa o agente aprovar nada.** Nem com uma instrução dizendo que pode.
- **Não deixa o agente sair de uma exceção.** Ele para e chama gente.
- **Não guarda documento.** A fila guarda metadado e estado; o PDF fica onde estava.
- **Não chama modelo.** `ciclo_do_agente.py` decide por regra fixa, de propósito: o foco é
  o ciclo. Quando o agente do Foundry entra no lugar dele, as chamadas HTTP são as mesmas.
- **Não implementa esquecimento.** É o primeiro exercício sugerido — e a discussão de quem
  apaga uma memória errada vale mais do que o código.

---

## Custo

| Item | Valor |
|---|---|
| Rodar local (compose) | **US$ 0,00** |
| Laboratório completo na Azure | menos de **US$ 1,00** por aluno |
| Fora da aula | **≈ US$ 0,00** — `--min-replicas 0`, os containers dormem |
| Se esquecer o Aplicativo Lógico ativo | centavos por execução — mas ele fica tentando para sempre |

Encerramento: `bash infra/99-remover-tudo.sh` (exige digitar o nome do grupo).
