# Os cinco níveis de continuidade

> **Aula 02 · módulo do agente contínuo** · MBA AI Engineering & Multi-Agents · FIAP
>
> A pergunta que abre este módulo: *"o Deva lê nota fiscal, mas não parece um agente
> interativo contínuo. Como incrementá-lo?"*
>
> A resposta curta: o problema não é o agente. É que **ninguém deu a ele um motivo para
> existir entre duas perguntas**. Este documento mostra os cinco degraus dessa escada e
> exatamente o que cada um exige.

---

## A escada

| Nível | O que muda para quem usa | O que é preciso construir |
|---|---|---|
| **0 · Pergunta e resposta** | nada persiste; toda conversa começa do zero | — |
| **1 · Sessão com contexto** | ele lembra **dentro** da conversa | nada: o *thread* do Foundry já faz |
| **2 · Memória entre sessões** | ele lembra **amanhã** | serviço de memória + Ferramenta OpenAPI |
| **3 · Iniciativa** | ele **começa sozinho** | gatilho por evento + fila de documentos |
| **4 · Fila de exceções** | ele trabalha e **chama gente só quando precisa** | máquina de estados + tela de revisão |

Cada degrau depende do anterior. Pular direto para o 3 produz um agente que acorda sozinho
e não sabe o que já fez — que é pior do que não acordar.

---

## Nível 0 — pergunta e resposta

É onde quase todo agente de curso para. O aluno digita, o agente responde, a janela
fecha, tudo evapora.

Não há nada de errado aqui: é o lugar certo para aprender instrução, ferramenta e
avaliação. Mas é um **assistente**, não um agente contínuo — e a diferença aparece na
primeira reunião em que alguém pergunta *"e o que ele fez ontem?"*.

---

## Nível 1 — sessão com contexto

O Foundry já entrega isso de graça: o **thread**. Dentro de uma conversa, o agente lembra
do que foi dito, das ferramentas que chamou e dos documentos que viu.

**O que isso não resolve:** amanhã é outro thread. O auditor que corrigiu o Deva na
terça-feira vai corrigir a mesma coisa na quarta.

**A demonstração de 30 segundos:** corrija o agente em uma conversa, abra outra e refaça a
mesma pergunta. Ele erra igual. A turma entende sozinha o que falta.

---

## Nível 2 — memória entre sessões

Aqui o agente passa a lembrar **entre** conversas. Duas formas, e a escolha é de projeto:

| Caminho | Vantagem | Custo |
|---|---|---|
| **Foundry Memory** (versão prévia) | nada para construir; perfil, resumo e procedural prontos | é caixa-preta: o aluno **não vê o texto**, e o texto é o conteúdo da aula |
| **`MEMORY.md` em serviço próprio** | legível, versionável, auditável, revisável | é preciso escrever a API — o que este módulo faz |

Nós fazemos o segundo **porque o objetivo é didático**: o valor está em o aluno abrir um
arquivo e ver uma linha nova. Numa empresa, a resposta madura costuma ser *os dois*:
Memory para o que é conveniência, `MEMORY.md` para o que precisa passar por revisão.

### E aqui aparece a decisão que define o projeto

Se o agente pode **escrever** na própria memória, ele pode aprender o próprio erro — e
passar a repeti-lo com confiança. Pior: vira vetor de ataque.

> No laboratório da Aula 02, uma nota fiscal chegou com uma instrução escondida no rodapé
> mandando aprovar sem revisão. O Deva recusou e registrou como incidente — correto. Mas
> se ele tivesse permissão de escrita direta, aquela frase teria virado **regra
> permanente, aprovada por ele mesmo**, aplicada a todos os documentos seguintes.

Por isso o desenho é **proposta + aprovação**:

```
o agente:  POST /memoria/proposta   →  memoria-pendente.md
o humano:  clica em Aprovar         →  MEMORY.md
```

Dois arquivos, e o aluno vê os dois lado a lado. A linha atravessando de um para o outro
explica governança de IA melhor do que qualquer slide.

---

## Nível 3 — iniciativa

É o degrau que muda a **percepção** da turma. Enquanto alguém digita a pergunta, o agente
parece um chat com esteroides. Quando o aluno **larga um PDF numa pasta e o agente
acorda**, processa e volta dizendo *"3 notas aprovadas, 1 duvidosa, preciso de você"* —
aí ele virou processo.

Duas formas de disparar:

| Forma | Como | Quando usar |
|---|---|---|
| **Event Grid → Logic App** | `BlobCreated` no container `entrada` chama `POST /fila/documentos` | produção. Sem sondagem, custo por evento |
| **Sondagem** (`gatilho/disparador.py`) | um laço olha a pasta a cada N segundos | sala de aula: roda na máquina do aluno, sem provisionar nada, e deixa **ver** o mecanismo |

⚠️ **O gatilho é um evento, não um horário.** "Rodar às 8h" é agendamento — e agendamento
processa o que chegou até as 8h e ignora o resto do dia. O arquivo chegando é o que acorda
o processo.

E aqui nasce um risco novo: um agente que acorda sozinho pode **girar em falso**. Por isso
o `AGENTS.md` v2.0 ganhou freio de laço: no máximo uma volta a cada 5 minutos com a fila
vazia, e **duas voltas seguidas sem avançar nada = parar e avisar**. Laço que não progride
não gasta muito por volta; gasta por não parar nunca.

---

## Nível 4 — fila de exceções

Este é o degrau que separa automação de brinquedo.

**Um agente que devolve 40 itens para revisão não economizou nada.** Um que devolve 3
economizou 37. O número que interessa não é "quantos ele processou": é **quantos ele
devolveu**.

Para isso, o documento precisa de estado explícito:

```
recebido → extraido → auditado → conforme
                              ↘ excecao      (espera gente)
                    ↘ duplicado
         ↘ ilegivel
```

E de uma regra dura: **documento em `excecao` não volta para o agente**. Mesmo que ele
ache que sabe resolver. Sem isso, ele tenta de novo, falha de novo e gasta de novo — a
noite inteira, sem ninguém olhando.

No serviço, essa regra é código, não recomendação:

```python
if documento.estado is EstadoDoDocumento.EXCECAO and por == "deva":
    raise TransicaoProibida("Documento em exceção só é liberado por uma pessoa.")
```

---

## A lição de arquitetura que fecha o módulo

O `AGENTS.md` v1.3 dizia:

> *"Escreva em `MEMORY.md` **somente** quando o auditor humano corrigir você."*

Parece seguro. Não é. Pergunte à turma: **quem verifica que essa condição foi
satisfeita?** A resposta é: o próprio agente.

O v2.0 não confia nisso. A especificação OpenAPI entregue ao agente tem **cinco
operações**, e nenhuma delas aprova nada. Os endpoints de aprovação existem, funcionam e
são usados — pela tela, com o cabeçalho `X-Auditor`, que o agente nunca recebe.

> **A frase para o quadro:** instrução é intenção; permissão é controle. Em agentes, o que
> você não quer que aconteça, você não expõe.

---

## Onde cada nível aparece neste repositório

| Nível | Arquivos |
|---|---|
| 2 · memória | `api/servicos/memoria.py` · `agente/skills/propor-memoria/SKILL.md` · aba **Memória** e **Propostas** da tela |
| 3 · iniciativa | `gatilho/disparador.py` · `gatilho/logic-app-eventgrid.json` · `gatilho/ciclo_do_agente.py` |
| 4 · exceções | `api/modelos.py` (`TRANSICOES_PERMITIDAS`) · `api/servicos/fila.py` · aba **Exceções** |
| a fronteira | `api/principal.py` (`exigir_auditor`) · `gerar_openapi_do_agente.py` |
