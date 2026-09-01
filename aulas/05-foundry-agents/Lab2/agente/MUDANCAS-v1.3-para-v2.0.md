# O que mudou do `AGENTS.md` v1.3 para o v2.0

> Leia isto **antes** de comparar os dois arquivos. São seis mudanças, e cada uma responde
> a uma pergunta que a turma faz.

---

## 1. Nasceu a seção 0 — "antes de qualquer ação, sempre"

**Antes (v1.3):** a leitura da memória era o passo 1 do fluxo de trabalho, dentro da
seção 3. Ou seja: só quando havia um lote para processar.

**Agora (v2.0):** virou seção **0**, com duas chamadas — memória **e fila** — e uma regra
dura: se qualquer uma falhar, o agente para.

**Por quê:** um agente contínuo acorda sem ninguém dizer nada. Se ele não consulta a fila
logo de cara, não tem como saber o que fazer, e volta a depender de alguém digitar. A
seção 0 é o que transforma "esperar pergunta" em "procurar trabalho".

---

## 2. O fluxo de trabalho virou um ciclo de cinco passos

**Antes:** um procedimento linear, do primeiro ao último documento do lote.

**Agora:** `ler → olhar → avançar → parar → propor`, em laço.

**Por quê:** lote é evento; ciclo é processo. A diferença aparece na terceira semana de
uso, quando ninguém mais "roda o lote" — os documentos simplesmente chegam.

O passo que mais gente esquece de escrever é o **4 · parar**. Sem ele, o agente tenta
resolver de novo o que já falhou, e a conta cresce sozinha durante a madrugada.

---

## 3. A regra de memória inverteu: de escrita para proposta

**Antes (v1.3, §7):**

> *"Escreva em `MEMORY.md` **somente** quando o auditor humano corrigir você…"*

Parece seguro. Não é: quem decide se a condição foi satisfeita é o próprio agente.

**Agora (v2.0, §7):** o agente **não escreve**. Ele chama `POST /memoria/proposta`, e a
linha entra numa fila de revisão. Quem move de `memoria-pendente.md` para `MEMORY.md` é
uma pessoa, clicando.

**Por quê — com evidência do próprio laboratório:** na v1.3, uma nota fiscal chegou com
uma instrução escondida no rodapé mandando aprovar sem revisão. O Deva recusou e registrou
como incidente, exatamente como o `AGENTS.md` mandava. Mas repare no que teria acontecido
se ele tivesse errado **uma vez**: a frase viraria regra permanente, aprovada por ele
mesmo, aplicada a todos os documentos seguintes.

> **A frase para o quadro:** instrução no arquivo é promessa; permissão no serviço é
> garantia. A v2.0 troca uma pela outra.

---

## 4. Duas linhas novas na lista do "nunca sem confirmação humana"

- **Aprovar uma proposta de memória — inclusive a sua**
- **Tirar um documento do estado `excecao`**

**Por quê:** as duas são tentações naturais de um agente contínuo. Ele *quer* fechar a
fila. As duas linhas existem para que "fila zerada" nunca seja um objetivo que atropela a
revisão.

---

## 5. A seção 9 ganhou a Ferramenta OpenAPI — com um aviso

O Serviço de Continuidade entra como ferramenta, mas a especificação entregue ao agente
(`openapi-agente.json`) **declara só cinco operações** e **não declara** os cabeçalhos
`X-Auditor` e `X-Segredo`.

**Por quê:** não adianta escrever "não aprove" no `AGENTS.md` se o endpoint está ao
alcance. Instrução é a primeira camada; permissão é a que sobra quando a instrução falha.
Esta é a lição de arquitetura da aula: **o que você não quer que aconteça, você não expõe.**

---

## 6. O orçamento ganhou freio de laço (§10)

Duas linhas novas:

- no máximo **1 volta a cada 5 minutos** com a fila vazia;
- **duas voltas seguidas sem avançar nada = parar e avisar.**

**Por quê:** a v1.3 tinha teto por documento e por fechamento. Nenhum dos dois protege
contra o modo de falha típico do agente contínuo: girar em falso. Um laço que não progride
não gasta muito por volta — gasta por não parar nunca.

---

## Tabela de conferência rápida

| Tema | v1.3 | v2.0 |
|---|---|---|
| Quando lê a memória | no início do lote | antes de **qualquer** ação, junto com a fila |
| Como aprende | escreve em `MEMORY.md` | **propõe**; humano aprova |
| Origem da linha de memória | quem corrigiu | **quem aprovou** (auditor, com nome e data) |
| O que trava uma proposta ruim | uma regra escrita | uma regra escrita **e** o serviço recusando |
| Documento em exceção | volta para o lote | **espera pessoa**; o agente não retoma |
| Freio de custo | por documento e por fechamento | **+ freio de laço** |
| Como o aluno vê o aprendizado | abrindo o repositório | **tela + `MEMORY.md` no Blob**, mudando ao vivo |

---

## O exercício de 5 minutos que fecha o assunto

1. Abra `AGENTS.md` v1.3 na seção 7 e leia em voz alta: *"Escreva em `MEMORY.md` somente
   quando o auditor humano corrigir você."*
2. Pergunte à turma: **quem verifica que essa condição foi satisfeita?**
3. Espere o silêncio. A resposta é: o próprio agente.
4. Abra a v2.0 na mesma seção e mostre o `POST /memoria/proposta`.

É a demonstração mais direta de que, em agentes, **instrução não é controle**. Instrução é
intenção; controle é permissão.
