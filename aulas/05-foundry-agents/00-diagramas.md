# Manual 0 — Os três diagramas do Deva3

> **Leia este documento antes dos outros.** Ele responde, em três desenhos, as três
> perguntas que todo aluno faz na primeira meia hora:
>
> 1. **Com quem esse sistema conversa?** → diagrama de contexto
> 2. **Onde cada pedaço roda?** → diagrama de arquitetura
> 3. **O que acontece quando eu clico em "Analisar"?** → diagrama de sequência
>
> As imagens estão em `docs/imagens/` e o **código-fonte** de cada uma está em
> `docs/diagramas/*.mmd` — é Mermaid, texto puro, versionado junto com o projeto.
> Se o desenho ficar errado, você corrige o `.mmd` e gera de novo. Diagrama que não
> pode ser corrigido apodrece.

---

## Como regerar os diagramas

```bash
npm install -g @mermaid-js/mermaid-cli      # uma vez por máquina

mmdc -i docs/diagramas/01-contexto.mmd   -o docs/imagens/01-contexto.png \
     -c docs/diagramas/tema-fiap.json -b "#15151A" -w 2200 --scale 2
mmdc -i docs/diagramas/02-arquitetura.mmd -o docs/imagens/02-arquitetura.png \
     -c docs/diagramas/tema-fiap.json -b "#15151A" -w 2200 --scale 2
mmdc -i docs/diagramas/03-sequencia.mmd  -o docs/imagens/03-sequencia.png \
     -c docs/diagramas/tema-fiap.json -b "#15151A" -w 2200 --scale 2
```

O arquivo `tema-fiap.json` traz a paleta da disciplina (fundo `#15151A`, magenta
`#EB0B4F`, ciano `#03E3FD`, âmbar `#FFD579`), então todo diagrama novo já nasce no
padrão do material.

⚠️ **Armadilha do Mermaid:** dentro de mensagens de diagrama de sequência, evite `&`,
`;`, `>` e entidades HTML como `&lt;`. O analisador quebra e a mensagem de erro não diz
que foi isso. Use `·`, `≥` e colchetes.

---

# 1 · Diagrama de contexto

**Pergunta que ele responde:** com quem o Deva3 conversa, e onde termina a nossa
responsabilidade.

É o **nível 1 do modelo C4**: só pessoas, o nosso sistema, e os sistemas externos.
Nenhum detalhe de tecnologia interna — de propósito.

![Diagrama de contexto do Deva3](imagens/01-contexto.png)

📄 Fonte: [`diagramas/01-contexto.mmd`](diagramas/01-contexto.mmd)

### Como ler

| Elemento | O que significa |
|---|---|
| **Caixas magenta** | Pessoas. O **aluno** envia a foto; o **professor** provisiona, publica e define o limiar |
| **Caixa ciano** | O nosso sistema. Tudo que está dentro do "limite do sistema" é responsabilidade nossa |
| **Caixas cinza** | Sistemas externos. Nós **usamos**, não controlamos |
| **Caixa âmbar tracejada** | O Azure AI Face é **opcional** e depende de aprovação de Acesso Limitado |
| **Seta tracejada** | Caminho que só existe se a chave estiver configurada |

### As três leituras que valem discussão em aula

1. **O limite do sistema é pequeno de propósito.** O Deva3 recebe, pergunta e devolve.
   Ele não treina modelo, não guarda template biométrico, não identifica pessoa.
2. **Três dependências externas, três formas de falhar.** Vision fora do ar, Face sem
   aprovação, Blob com cadeia de conexão errada — cada uma tem um erro diferente e um
   `como_resolver` diferente na API.
3. **A seta para o Blob tem uma condição escrita.** "SOMENTE com consentimento" está no
   desenho, não numa nota de rodapé. Se a regra é importante, ela aparece no diagrama.

---

# 2 · Diagrama de arquitetura

**Pergunta que ele responde:** onde cada pedaço roda, e por onde o código sai da sua
máquina e chega à nuvem.

![Diagrama de arquitetura do Deva3](imagens/02-arquitetura.png)

📄 Fonte: [`diagramas/02-arquitetura.mmd`](diagramas/02-arquitetura.mmd)

### Como ler

Os números nas setas são a **ordem em que as coisas acontecem no laboratório**:

| # | O que é | Comando ou ação |
|---|---|---|
| **1** | Da sua máquina para o registro | `az acr build` — constrói **na nuvem**, você não precisa de Docker |
| **2** | Do registro para os apps | `az containerapp create/update` |
| **3** | O aluno abre a interface | HTTPS, na URL pública do `ca-deva3-web` |
| **4** | A interface chama a API | `POST /detectar`, usando a variável `API_URL` |
| **5** | A API chama o serviço cognitivo | `imageanalysis:analyze?features=people` |
| **6** | A API grava o resultado | Upload no contêiner privado `deteccoes` |

### O que o desenho mostra e o texto esconde

- **Tudo dentro da moldura magenta é `rg-aula-05`.** É por isso que um único
  `az group delete` encerra o laboratório inteiro — e por que o Módulo 8 existe.
- **Os dois Container Apps estão no mesmo ambiente `cae-aula-05`**, mas são apps
  separados. A fronteira entre backend e frontend é real, não conceitual.
- **A chave nunca aparece numa seta.** Ela está listada dentro do `ca-deva3-api` como
  *segredo* (`visao-chave`, `armazenamento-conexao`), porque é assim que ela vive:
  como `--secrets` do Container App, referenciada por `secretref:`.
- **`min 0 réplicas`** está escrito na caixa: fora da aula, os containers dormem e não
  cobram. O único recurso que cobra parado é o registro de contêiner.

### Exercício de 5 minutos

Peça à turma para apontar, no desenho, **onde estaria o problema** em cada caso:

| Sintoma | Onde olhar no diagrama |
|---|---|
| A interface abre mas dá erro ao analisar | seta 4 — variável `API_URL` |
| A API responde `404` na chamada à Azure | seta 5 — `VISAO_ENDPOINT` com barra no fim |
| O container sobe e cai | caixas dos apps — porta de destino errada |
| `ModuleNotFoundError: api` | seta 1 — imagem construída da pasta errada |

---

# 3 · Diagrama de sequência

**Pergunta que ele responde:** o que acontece, passo a passo, entre clicar em
"Analisar imagem" e ver a caixa desenhada na tela.

![Diagrama de sequência do POST /detectar](imagens/03-sequencia.png)

📄 Fonte: [`diagramas/03-sequencia.mmd`](diagramas/03-sequencia.mmd)

### Como ler

- **Linhas verticais** são participantes: pessoas, containers, classes do nosso código
  e serviços da Azure. Repare que `_validar_imagem`, `ServicoVisaoAzure` e
  `ServicoArmazenamentoBlob` aparecem como participantes — eles são objetos reais do
  projeto, não abstrações do desenho.
- **Setas cheias** são chamadas; **setas tracejadas** são respostas.
- **Blocos `alt`** são caminhos alternativos: ou um, ou outro.
- **Bloco `opt`** é um trecho que só acontece sob condição.
- **Os números** seguem a ordem real da execução — dá para acompanhar de ponta a ponta.

### Os quatro momentos que valem parar a aula

**Passos 3 a 7 · a validação vem antes de tudo.**
A imagem é checada em tamanho, tipo e integridade **antes** de qualquer chamada paga.
Arquivo ruim nunca vira custo na Azure. Repare que os erros já saem com
`como_resolver` preenchido.

**Passos 9 a 12 · o caminho de erro é tão desenhado quanto o de sucesso.**
`401`, `404`, `429` e `5xx` viram `FalhaDeIntegracao` e chegam ao aluno como `502` com
instrução. Diagrama que só mostra o caminho feliz esconde metade do sistema.

**Passo 14 · a tradução acontece num lugar só.**
`_interpretar` converte `boundingBox {x,y,w,h}` da Azure para a nossa
`CaixaDelimitadora` e ordena por confiança. No modo `rostos`, é o mesmo método que
traduz `left/top` para `x/y`. Conversão espalhada é como nasce bug de coordenada.

**Passo 16 · o limiar é aplicado pela API, não pela tela.**
`acima_do_limiar = confianca ≥ LIMIAR_CONFIANCA` acontece no backend. A interface só
pinta: ciano acima, âmbar abaixo. Quem decide a régua é a configuração, e ela vai
junto no payload.

**Passos 17 a 20 · o consentimento decide o que é gravado.**
A nota amarela no diagrama é a regra inteira: a imagem só sobe se
`PERSISTIR_IMAGENS=true` **e** o consentimento estiver marcado. Sem consentimento, vai
só o JSON. Essa condição é a implementação de uma decisão de privacidade, e ela está
desenhada.

---

## Onde cada diagrama entra na aula

| Momento | Diagrama | Por quê |
|---|---|---|
| Abertura, antes de qualquer comando | **Contexto** | Define o escopo e já abre a conversa de responsabilidade |
| Antes do Módulo 1 do provisionamento | **Arquitetura** | O aluno cria cada caixa sabendo para que ela serve |
| Depois do primeiro teste com foto | **Sequência** | Explica o que o aluno acabou de ver acontecer |
| Quando algo quebra | **Arquitetura + Sequência** | Localizar o problema no desenho é mais rápido que ler log |

---

## Para onde ir agora

- **Provisionar pelo portal, tela a tela** → [`01-manual-portal.md`](01-manual-portal.md)
- **Provisionar por script** → [`02-manual-script.md`](02-manual-script.md)
- **Como o projeto foi construído** → [`03-passo-a-passo-do-zero.md`](03-passo-a-passo-do-zero.md)
