# Manual 1 — Provisionar pelo Azure Portal, tela a tela

> Caminho para quem está começando: **nenhum comando**, tudo clicando.
> Nomes dos campos conferidos no portal em **português do Brasil**, em **30/08/2026**.
> O caminho equivalente por script está no `02-manual-script.md`.
>
> **Antes de começar, veja os desenhos:** [`00-diagramas.md`](00-diagramas.md).
> O **diagrama de arquitetura** mostra cada recurso que você vai criar aqui e para que
> ele serve — criar as caixas sabendo o que elas fazem muda a aula inteira.
>
> Tempo estimado: **35 a 45 minutos**.
> Custo do laboratório inteiro, se você seguir o Módulo 0: **menos de US$ 2**.

---

## Módulo 0 — Antes de criar qualquer coisa: o orçamento

Um laboratório na nuvem sem teto de gasto é um cartão de crédito sem limite.
**Ninguém cria recurso antes de terminar este módulo.**

1. Vá para **portal.azure.com**.
2. Na busca do topo, digite **Gerenciamento de Custos** e abra o serviço.
3. No menu da esquerda, em **Monitoramento**, clique em **Orçamentos**.
4. **+ Adicionar**.
5. Na etapa **1 · Criar um orçamento**:

   | Campo | Valor |
   |---|---|
   | **Escopo** | sua assinatura (aparece o seu nome, ou "Azure for Students") |
   | **Filtros** | *(opcional)* **Adicionar filtro** → grupo de recursos → `rg-aula-05` |
   | **Nome** | `orc-aula-05` |
   | **Redefinir período** | Mensalmente |
   | **Valor** | 10 |

6. **Avançar >** e crie dois alertas sobre o **custo real**: em **50%** e em **90%**.
   Preencha o e-mail dos destinatários. **Criar**.

✅ **Confira:** o orçamento aparece na lista de **Orçamentos**.

---

## Módulo 1 — Grupo de recursos `rg-aula-05`

> 🗺️ No [diagrama de arquitetura](imagens/02-arquitetura.png), este é o **retângulo
> magenta** que envolve tudo.

Grupo de recursos é uma pasta. Tudo da aula vai para dentro dela — assim, no fim,
um único clique apaga o laboratório inteiro.

1. Busque **Grupos de recursos** → **+ Criar**.
2. Preencha:

   | Campo | Valor |
   |---|---|
   | **Assinatura** | Azure for Students |
   | **Grupo de recursos** | `rg-aula-05` |
   | **Região** | (US) East US 2 |

3. **Examinar + criar** → **Criar**.

💡 **Por que East US:** é a região com a maior disponibilidade de serviços e a que
menos causa surpresa em sala. Em projeto real com dado brasileiro, a escolha da região
é decisão de conformidade, não de conveniência.

---

## Módulo 2 — Conta de armazenamento e o container de blobs

É onde as fotos e os resultados vão ser guardados.

1. Busque **Contas de armazenamento** → **+ Criar**.
2. Aba **Básico**:

   | Campo | Valor |
   |---|---|
   | **Assinatura** | Azure for Students |
   | **Grupo de recursos** | `rg-aula-05` |
   | **Nome da conta de armazenamento** | `stdeva3` + seu sufixo (ex.: `stdeva3fiap01`) |
   | **Região** | (US) East US 2|
   | **Desempenho** | Standard |
   | **Redundância** | LRS (armazenamento com redundância local) |

   ⚠️ O nome da conta é **único no mundo inteiro**, só letras minúsculas e números,
   até 24 caracteres. Se der "já está em uso", troque o sufixo.

3. Aba **Avançado**: **desmarque** *Permitir acesso público a blob*.
   Container privado é o padrão certo para dado pessoal.
4. **Examinar + criar** → **Criar**.
5. Quando terminar, **Ir para o recurso** → menu **Armazenamento de dados** →
   **Contêineres** → **+ Contêiner**:

   | Campo | Valor |
   |---|---|
   | **Nome** | `deteccoes` |
   | **Nível de acesso público** | Privado (sem acesso anônimo) |

6. Guarde a chave: menu **Segurança + rede** → **Chaves de acesso** → **Mostrar** →
   copie a **Cadeia de conexão** da `key1`.

⚠️ Essa cadeia é uma senha completa da conta. Não vai para o Git, não vai para o slide,
não vai para o grupo do WhatsApp da turma.

---

## Módulo 3 — O recurso de visão

Este é o cérebro do Deva3.

1. Busque **Pesquisa Visual Computacional** → **Criar**.
   A tela se chama **"Criar a Pesquisa Visual Computacional"**, com as abas
   **Básico · Rede · Identity · Tags · Examinar + criar**.
2. Em **Detalhes do Projeto**:

   | Campo | Valor |
   |---|---|
   | **Assinatura** * | Azure for Students |
   | **Grupo de recursos** * | `rg-aula-05` |

3. Em **Detalhes da Instância**:

   | Campo | Valor |
   |---|---|
   | **Região** | (US) East US 2|
   | **Nome** * | `cv-deva3-` + seu sufixo |
   | **Faixa de preços** * | **Free F0 (20 Calls per minute, 5K Calls per month)** |

   💡 As duas opções que o portal oferece são exatamente estas:
   **Free F0 (20 chamadas por minuto, 5 mil por mês)** e
   **Standard S1 (10 chamadas por segundo)**.
   O F0 é **um por assinatura por região** — se já existir outro, o portal recusa.
   Numa turma de 40 pessoas clicando ao mesmo tempo, o F0 estoura: combine rodadas
   ou use S1 no dia da aula.

4. **Aviso de IA Responsável** — leia em voz alta com a turma. O texto do portal diz:

   > *"Este Serviço de IA do Azure foi projetado para processar Dados do Cliente que
   > incluem **Dados Biométricos** (conforme descrito na documentação do produto) que o
   > Cliente pode incorporar aos seus próprios sistemas usados para identificação pessoal
   > ou outras finalidades. O cliente reconhece e concorda que é responsável por cumprir
   > as obrigações de dados biométricos contidos no DPA de serviços online."*

   Marque **"Ao marcar esta caixa, declaro que li e aceito todos os termos acima."**

   🎓 **Momento da aula:** a Microsoft está transferindo a responsabilidade legal para
   quem clica. Quem clica é você. Em projeto real, essa tela é conversa com jurídico e
   com o encarregado de dados — não é um "próximo".

5. **Examinar + criar** → **Criar**.
6. **Ir para o recurso** → menu **Gerenciamento de recursos** →
   **Chaves e Ponto de Extremidade**. Copie a **Chave 1** e o **Ponto de extremidade**.

⚠️ O ponto de extremidade vem com **barra no final**. **Remova a barra** antes de colar
no `.env` — com barra, a URL final fica com `//` e a Azure devolve `404`, que todo aluno
confunde com chave errada.

---

## Módulo 4 — Registro de containers (ACR)

É o "armário" onde a imagem do nosso código fica guardada.

1. Busque **Registros de contêiner** → **+ Criar**.
2. Aba **Básico**:

   | Campo | Valor |
   |---|---|
   | **Assinatura** | Azure for Students |
   | **Grupo de recursos** | `rg-aula-05` |
   | **Nome do registro** | `acrdeva3` + seu sufixo (só letras e números) |
   | **Local** | (US) East US 2|
   | **SKU** | Basic |

   ⚠️ Também é nome **global**. E o Basic tem **custo fixo mensal** — é o único item do
   laboratório que cobra mesmo parado. Por isso o Módulo 8 existe.

3. **Examinar + criar** → **Criar**.
4. **Ir para o recurso** → menu **Configurações** → **Chaves de acesso** →
   ligue **Usuário administrador**. Copie **Nome de usuário** e **senha**.

💡 Usuário administrador é atalho didático. Em produção usa-se **identidade gerenciada**,
sem senha nenhuma.

---

## Módulo 5 — Enviar a imagem para o registro

O comando de referência é este:

```bash
az acr build --registry acrdeva3<sufixo> --image deva3-api:v1 --file api/Dockerfile .
```

### 5.1 O que cada pedaço faz (explique isto antes de clicar em qualquer coisa)

| Pedaço | O que significa |
|---|---|
| `az acr build` | **Quick task**: compacta o contexto, envia para a Azure, o ACR **constrói na nuvem** e já faz o *push*. O aluno **não precisa de Docker instalado** |
| `--registry acrdeva3<sufixo>` | em qual registro construir e guardar |
| `--image deva3-api:v1` | nome do repositório dentro do registro (`deva3-api`) e a marca (`v1`) |
| `--file api/Dockerfile` | onde está o Dockerfile — **caminho relativo ao contexto**, não à sua pasta atual |
| `.` (o ponto no fim) | **o contexto**: a pasta que sobe para a nuvem. Aqui é a **raiz do projeto** |

> 💡 **Por que o contexto é a raiz e não `api/`?** Porque o `api/Dockerfile` faz
> `COPY api/requirements.txt` e `COPY api ./api` — ele enxerga o projeto a partir de cima.
> Se você rodar com contexto `api/`, o build falha com *"file not found"*. O próprio
> Dockerfile avisa isso no comentário do topo.

> 💡 **O que sobe junto?** Tudo que está na raiz, **menos** o que o `.dockerignore` exclui —
> neste projeto: `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `docs`, `infra`, `*.md`.
> Sem esse arquivo, o upload levaria centenas de MB inúteis. Vale mostrá-lo à turma.

### 5.2 A verdade sobre o portal

**Não existe, no portal da Azure, uma tela que pegue uma pasta do seu computador e construa
a imagem.** O portal só sabe construir a partir de um **repositório Git**. Isso não é
limitação do laboratório — é como o produto funciona.

Então há três caminhos, e cada um serve a uma situação diferente:

| Caminho | É "pelo portal"? | Precisa de Docker? | Precisa de Git? | Quando usar |
|---|---|---|---|---|
| **A · Cloud Shell** | sim — roda dentro do portal.azure.com | não | não | **o caminho da aula** |
| **B · Tarefa do ACR** | sim — 100% telas e cliques | não | **sim** | quando o código já está no GitHub |
| **C · Docker local** | não — só a conferência é no portal | **sim** | não | quem já tem Docker Desktop |

---

### Caminho A — Cloud Shell (recomendado para a aula)

O Cloud Shell **é** o portal: um terminal dentro de `portal.azure.com`, já autenticado, com o
`az` instalado. O aluno não instala nada e roda o comando original sem alterar uma vírgula.

1. Entre em **`portal.azure.com`**.
2. Na barra superior, clique no ícone **`>_`** (*Cloud Shell*).
3. Escolha **Bash** (não PowerShell — os comandos deste lab são Bash).
4. Na primeira vez, ele pergunta onde guardar os arquivos:
   - **"Sem conta de armazenamento"** / *ephemeral* → mais rápido e **não gera custo**, mas
     os arquivos somem quando a sessão fecha. **Suficiente para a aula.**
   - **"Criar armazenamento"** → cria uma Storage Account pequena (centavos/mês) e os arquivos
     ficam salvos entre sessões.
5. Suba o projeto. O botão fica no topo do terminal: **Gerenciar arquivos** → **Carregar**.
   > ⚠️ O upload é **um arquivo por vez**. Suba o **.zip** do projeto, não a pasta.
6. Descompacte e entre na raiz:

   ```bash
   unzip 05-foundry-agents.zip
   cd 05-foundry-agents/Lab
   ls api/Dockerfile          # tem que existir; se não, você está na pasta errada
   ```

7. Rode o comando — o mesmo, sem mudanças:

   ```bash
   az acr build --registry acrdeva3<sufixo> --image deva3-api:v1 --file api/Dockerfile .
   ```

8. Acompanhe o log de build ao vivo no próprio terminal. Ao final aparece
   `Run ID: ca1 was successful after Xm Ys`.

9. Repita para a interface:

   ```bash
   az acr build --registry acrdeva3<sufixo> --image deva3-web:v1 --file web/Dockerfile .
   ```

> 💡 **Alternativa sem upload:** se o projeto estiver no GitHub, troque o passo 5 por
> `git clone https://github.com/<usuario>/<repo>.git` dentro do Cloud Shell.

> ⚠️ O Cloud Shell **encerra a sessão após ~20 minutos de inatividade** e o modo *ephemeral*
> apaga os arquivos. Se a turma for parar para o intervalo, faça o build antes.

---

### Caminho B — Tarefa do ACR (100% cliques, mas exige o código no Git)

Este é o único caminho puramente clicável. Ele monta uma **Tarefa** (*ACR Task*) que aponta
para um repositório Git — e, de brinde, pode reconstruir a imagem a cada `git push`.

**Pré-requisito:** o projeto precisa estar num repositório **GitHub** ou **Azure Repos**.

1. Portal → busque **Registros de contêiner** → clique em **`acrdeva3<sufixo>`**.
2. Menu esquerdo → **Serviços** → **Tarefas**.
3. Clique em **+ Adicionar** → **Tarefa**.
4. Aba **Detalhes da tarefa**:

   | Campo | Valor |
   |---|---|
   | **Nome da tarefa** | `construir-deva3-api` |
   | **Localização de origem** / **Tipo de origem** | `GitHub` |
   | **URL do repositório** | `https://github.com/<usuario>/<repo>.git` |
   | **Branch** | `main` |
   | **Caminho do arquivo Docker** | `api/Dockerfile` |
   | **Imagem** | `deva3-api:v1` |
   | **Plataforma** | `Linux` · `amd64` |

   > O **contexto** é sempre a raiz do repositório — que é exatamente o que este Dockerfile
   > precisa. É o mesmo `.` do comando.

5. Aba **Gatilhos**: para a aula, **desmarque "Habilitar gatilho de confirmação"** — senão
   cada `git push` dispara um build novo. Deixe **Gatilho de imagem base** desmarcado também.
6. Aba **Credenciais de origem**: para repositório **privado**, cole um **token de acesso
   pessoal (PAT)** do GitHub com escopo `repo`. Repositório público costuma dispensar.
7. **Criar**.
8. De volta em **Tarefas**, selecione `construir-deva3-api` e clique em **Executar agora**
   (*Run now*) → **Executar**.
9. Acompanhe em **Tarefas** → aba **Execuções** (*Runs*): a execução aparece com um ID
   (`ca1`, `ca2`…), o status e o **log completo** clicável.
10. Repita tudo para `construir-deva3-web`, trocando o Dockerfile para `web/Dockerfile` e a
    imagem para `deva3-web:v1`.

---

### Caminho C — Docker na máquina do aluno

Só faz sentido para quem já tem Docker Desktop rodando. Não é "pelo portal" — o portal entra
apenas na conferência do passo 5.4.

```bash
az acr login --name acrdeva3<sufixo>          # autentica o Docker no seu registro
docker build -f api/Dockerfile -t acrdeva3<sufixo>.azurecr.io/deva3-api:v1 .
docker push acrdeva3<sufixo>.azurecr.io/deva3-api:v1
```

> ⚠️ Repare que aqui a imagem precisa do **nome completo do registro** na tag
> (`acrdeva3<sufixo>.azurecr.io/…`). No `az acr build` isso é implícito, porque o
> `--registry` já diz o destino. É a confusão nº 1 de quem migra de um para o outro.

---

### 5.3 Conferir no portal que deu certo

Vale fazer isso em qualquer um dos três caminhos:

1. Portal → **Registros de contêiner** → `acrdeva3<sufixo>`.
2. Menu esquerdo → **Serviços** → **Repositórios**.
   Devem aparecer **`deva3-api`** e **`deva3-web`**.
3. Clique em `deva3-api` → deve existir a marca **`v1`**. Clicando nela você vê o *digest*,
   o tamanho, a data e o comando para puxar a imagem.
4. Para ver o histórico de builds: **Serviços** → **Tarefas** → aba **Execuções**.
   Cada execução traz status, duração e o log inteiro — inclusive os builds feitos por
   `az acr build` no Cloud Shell, que aparecem como execuções do tipo *QuickBuild*.

### 5.4 Erros comuns neste módulo

| Erro | Causa | Solução |
|---|---|---|
| `unable to prepare context: ... Dockerfile: no such file or directory` | rodou de dentro de `api/`, ou esqueceu o `.` no fim | volte para a raiz do projeto; o contexto é `.` |
| `COPY failed: file not found in build context` | usou `api/` como contexto | o contexto tem que ser a **raiz** — o Dockerfile faz `COPY api/...` |
| `denied: requested access to the resource is denied` | sem permissão de push no ACR | peça a função **AcrPush** (ou Colaborador) no registro |
| `az: command not found` | não é o Cloud Shell, é um terminal local sem CLI | use o Cloud Shell (Caminho A) |
| Upload da pasta não funciona no Cloud Shell | ele aceita **um arquivo por vez** | suba o `.zip` e descompacte lá dentro |
| `RequestDisallowedByAzure` ao criar o ACR | região fora das permitidas na assinatura | veja o Módulo 0 — escolha uma região liberada |
| O nome do registro é recusado | nome de ACR é **global** e só aceita letras e números minúsculos | troque o sufixo |

---

## Módulo 6 — Publicar a API como Aplicativo de Contêiner

1. Busque **Aplicativos de Contêiner** → **+ Criar**.
   A tela se chama **"Criar Aplicativo de contêiner"**, com as abas
   **Noções Básicas · Contêiner · Entrada · Tags · Examinar + criar**.

2. Aba **Noções Básicas** → **Detalhes do projeto**:

   | Campo | Valor |
   |---|---|
   | **Assinatura** * | Azure for Students |
   | **Grupo de recursos** * | `rg-aula-05` |
   | **Nome do aplicativo contêiner** * | `ca-deva3-api` |
   | **Otimizar para Azure Functions** | deixe **desmarcado** |
   | **Origem da implantação** | **Imagem de contêiner** |
   | **Ambiente do Aplicativo de Contêiner** | **Criar novo** → `cae-aula-05`, região East US |

3. Aba **Contêiner**:

   | Campo | Valor |
   |---|---|
   | **Nome** | `api` |
   | **Origem da imagem** | Registro de Contêiner do Azure |
   | **Registro** | `acrdeva3<sufixo>.azurecr.io` |
   | **Imagem** | `deva3-api` |
   | **Marca da imagem** | `v1` |
   | **CPU e memória** | 0,5 CPU · 1 Gi |

   Ainda na aba Contêiner, em **Variáveis de ambiente**, adicione:

   | Nome | Origem | Valor |
   |---|---|---|
   | `AMBIENTE` | Valor manual | `azure` |
   | `VISAO_ENDPOINT` | Valor manual | o endpoint **sem barra no final** |
   | `VISAO_CHAVE` | **Referência a um segredo** | a chave copiada no Módulo 3 |
   | `ARMAZENAMENTO_CONEXAO` | **Referência a um segredo** | a cadeia do Módulo 2 |
   | `ARMAZENAMENTO_CONTAINER` | Valor manual | `deteccoes` |
   | `PERSISTIR_IMAGENS` | Valor manual | `true` |
   | `LIMIAR_CONFIANCA` | Valor manual | `0.60` |

   💡 **Segredo é diferente de variável.** Chave e cadeia de conexão vão como **segredo**;
   o resto vai como valor comum. Segredo não aparece em log nem na tela de revisão.

4. Aba **Entrada**:

   | Campo | Valor |
   |---|---|
   | **Entrada** | Habilitada |
   | **Tráfego de entrada** | Aceitar tráfego de qualquer lugar |
   | **Tipo de transporte** | Automático |
   | **Porta de destino** | `8000` |

5. **Examinar + criar** → **Criar**. Leva de 2 a 4 minutos.
6. **Ir para o recurso** e copie a **URL do aplicativo**. Abra `.../saude` no navegador:
   deve responder um JSON com `"situacao": "saudavel"`.

---

## Módulo 7 — Publicar a interface

> 🗺️ A partir daqui vale abrir o [diagrama de sequência](imagens/03-sequencia.png):
> ele mostra exatamente o que vai acontecer quando o aluno clicar em "Analisar imagem".

Repita o Módulo 6 com estas diferenças:

| Campo | Valor |
|---|---|
| **Nome do aplicativo contêiner** | `ca-deva3-web` |
| **Ambiente** | `cae-aula-05` (o mesmo, não crie outro) |
| **Imagem** | `deva3-web` · marca `v1` |
| **Porta de destino** | `8501` |
| **Variável de ambiente** | `API_URL` = `https://<URL-da-api>` |

Abra a URL da interface. Suba uma foto. Veja a caixa aparecer.

✅ **Checkpoint do laboratório:** a foto sobe, a caixa é desenhada, a confiança aparece
e o JSON completo fica visível na tela.

---

## Módulo 8 — Apagar tudo

> O módulo que ninguém faz e todo mundo paga.

1. Busque **Grupos de recursos** → clique em `rg-aula-05`.
2. **Excluir grupo de recursos**.
3. Digite `rg-aula-05` para confirmar → **Excluir**.
4. No dia seguinte, confira em **Gerenciamento de Custos → Análise de custos** se o
   gasto parou. O custo do Azure aparece com algumas horas de atraso.

| Item | Continua cobrando parado? |
|---|---|
| **Registro de contêiner Basic** | **Sim** — custo fixo mensal |
| Container App com mínimo de réplicas 0 | Não, escala a zero |
| Conta de armazenamento | Só o que estiver guardado |
| Visão nível F0 | Não |

---

## Anexo — Erros mais comuns nesta trilha

| Sintoma | Causa | Correção |
|---|---|---|
| "O nome já está em uso" | Nome de Storage/ACR é global | Troque o sufixo |
| Não consigo criar o F0 | Já existe um F0 na assinatura/região | Use S1 ou outra região |
| `404` ao chamar a API | Endpoint com barra no final | Remova a barra |
| `401` | Chave de outro recurso | Recopie em Chaves e Ponto de Extremidade |
| `429` | Cota do F0 (20 chamadas/minuto) | Espere 1 minuto; combine rodadas |
| Container sobe e cai | Porta de destino errada | API é `8000`, interface é `8501` |
| Interface abre e não fala com a API | `API_URL` errada ou sem `https://` | Corrija a variável |
| `ModuleNotFoundError: api` | Imagem construída da pasta errada | Construa a partir da **raiz** do projeto |
