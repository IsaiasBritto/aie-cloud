# Manual 1 — Provisionar pelo Azure Portal, tela a tela

> Caminho para quem está começando: o provisionamento é **todo clicando**, tela a tela.
> Só dois momentos pedem terminal: o **Passo zero** (clonar o repositório) e o **Módulo 5**
> (construir a imagem), que roda na **CLI da Azure** dentro do Cloud Shell. O Módulo 5 traz,
> como comentário, o caminho equivalente por telas do portal e por que não é o da aula.
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

## Passo zero — Clonar o repositório da disciplina

Faça isto **antes de tudo**, na sua máquina. É daqui que saem os manuais, os `Dockerfile`
e os scripts que você vai usar nos próximos módulos.

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/05-foundry-agents/Lab
```

No Windows, o mesmo comando funciona no **PowerShell** ou no **Git Bash** — só precisa ter o
[Git instalado](https://git-scm.com/download/win).

Confira que deu certo:

```bash
ls api/Dockerfile web/Dockerfile infra/00-variaveis.sh
```

Os três precisam existir. Se der "arquivo não encontrado", você está na pasta errada — repita
o `cd` acima.

> 💡 **Repositório grande?** Traga só a pasta da aula:
>
> ```bash
> git clone --depth 1 --filter=blob:none --sparse https://github.com/IsaiasBritto/aie-cloud.git
> cd aie-cloud
> git sparse-checkout set aulas/05-foundry-agents/Lab
> cd aulas/05-foundry-agents/Lab
> ```

> ⚠️ **Isto NÃO substitui o clone do Módulo 5.** O Azure Cloud Shell é **outra máquina**,
> na nuvem: o que você baixou no seu computador não está lá. No Módulo 5 você clona de novo,
> dentro do Cloud Shell. Parece redundante e não é — são dois ambientes diferentes.

**Já é o dia da aula e o repositório mudou?** `git pull` dentro da pasta atualiza tudo.

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

💡 **Por que East US 2:** é a região liberada na assinatura desta turma. Confira a sua
antes de começar — assinaturas *Azure for Students* liberam ~5 regiões e **elas variam por
aluno** (Portal → Política → Atribuições → *Allowed resource deployment regions*).
Em projeto real com dado brasileiro, a escolha da região é decisão de conformidade,
não de conveniência.

⚠️ **Exceção — o recurso de visão (Módulo 3).** A documentação da Microsoft **não lista
East US 2** entre as regiões do Image Analysis 4.0. Se o `features=people` responder 404
ou "not supported", crie **apenas o recurso de visão** numa região suportada — East US,
West US 2, Sweden Central, West Europe, entre outras. Os endpoints são independentes:
a API só precisa da URL e da chave, então o resto do lab continua em East US 2.

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
   | **Região** | (US) East US 2 |
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
   | **Região** | (US) East US 2 |
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
   | **Local** | (US) East US 2 |
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

> 🖥️ **Este é o único módulo que roda no terminal.** Todo o resto do manual é clicando; aqui
> usamos a **CLI da Azure**, dentro do **Cloud Shell** — que é o próprio portal, no ícone `>_`
> da barra superior. Nada para instalar na sua máquina, nem Docker.

### 5.1 Os quatro comandos

Você já está no Cloud Shell, na pasta do projeto (Módulo 5.2 explica como chegar lá).

```bash
# 1 · a imagem da API
az acr build --registry acrdeva3<sufixo> --image deva3-api:v1 --file api/Dockerfile .

# 2 · a imagem da interface
az acr build --registry acrdeva3<sufixo> --image deva3-web:v1 --file web/Dockerfile .

# 3 · conferir
az acr repository show-tags --name acrdeva3<sufixo> --repository deva3-api -o table
az acr repository show-tags --name acrdeva3<sufixo> --repository deva3-web -o table
```

Cada build leva de **40 segundos a 2 minutos**. O log passa pela tela inteira; o que interessa
são as três últimas linhas:

```
Successfully tagged acrdeva3<sufixo>.azurecr.io/deva3-api:v1
2026/09/01 00:33:06 Successfully pushed image: acrdeva3<sufixo>.azurecr.io/deva3-api:v1
Run ID: ch1 was successful after 40s
```

Se aparecer `Run ID: ... was successful`, acabou. Pode ir para o Módulo 6.

### 5.2 Abrir o Cloud Shell e chegar na pasta

1. Em **`portal.azure.com`**, clique no ícone **`>_`** da barra superior.
2. Escolha **Bash** (não PowerShell — os comandos deste lab são Bash).
3. Na primeira vez ele pergunta onde guardar os arquivos:
   **"Sem conta de armazenamento"** é mais rápido e não gera custo; os arquivos somem quando a
   sessão fecha, o que é suficiente para a aula. **"Criar armazenamento"** cria uma Storage
   Account pequena (centavos por mês) e mantém os arquivos entre sessões.
4. Clone o projeto **aqui dentro**:

   ```bash
   git clone https://github.com/IsaiasBritto/aie-cloud.git
   cd aie-cloud/aulas/05-foundry-agents/Lab
   ls api/Dockerfile          # tem que existir; se não, você está na pasta errada
   ```

   > ⚠️ **Sim, é o segundo clone — e é necessário.** O Cloud Shell é um computador separado,
   > na Azure. O repositório que você baixou no [Passo zero](#passo-zero--clonar-o-repositório-da-disciplina),
   > no seu notebook, não existe aqui.

### 5.3 O que cada pedaço do comando faz

| Pedaço | O que significa |
|---|---|
| `az acr build` | **Quick task**: compacta o contexto, envia para a Azure, o ACR **constrói na nuvem** e já faz o *push*. Por isso ninguém precisa de Docker |
| `--registry acrdeva3<sufixo>` | em qual registro construir e guardar |
| `--image deva3-api:v1` | nome do repositório dentro do registro (`deva3-api`) e a marca (`v1`) |
| `--file api/Dockerfile` | onde está o Dockerfile — **caminho relativo ao contexto**, não à sua pasta atual |
| `.` (o ponto no fim) | **o contexto**: a pasta que sobe para a nuvem. Aqui é a **raiz do projeto** |

> 💡 **Por que o contexto é a raiz e não `api/`?** Porque o `api/Dockerfile` faz
> `COPY api/requirements.txt` e `COPY api ./api` — ele enxerga o projeto a partir de cima.
> Com o contexto em `api/`, o build falha em *"file not found"*. O próprio Dockerfile avisa
> disso no comentário do topo.

> 💡 **Repare nestas duas linhas do log:**
> ```
> Excluding '.gitignore' based on default ignore rules
> Sending context (47.033 KiB) to registry: acrdeva3<sufixo>...
> ```
> **47 KB.** É o `.dockerignore` funcionando: ele deixa de fora `.git`, `.venv`, `__pycache__`,
> `docs`, `infra` e os `*.md`. Sem esse arquivo, subiriam dezenas de MB a cada build. Vale abrir
> o `.dockerignore` com a turma neste momento.

### 5.4 Conferir no portal

1. Portal → **Registros de contêiner** → `acrdeva3<sufixo>`.
2. Menu esquerdo → **Serviços** → **Repositórios**: devem aparecer **`deva3-api`** e **`deva3-web`**.
3. Clique em `deva3-api` → a marca **`v1`** com o *digest*, o tamanho e a data.
4. **Serviços → Tarefas → Execuções**: o histórico de builds. Os `az acr build` do Cloud Shell
   aparecem aqui como execuções do tipo *QuickBuild*, com o log inteiro.

### 5.5 Erros comuns neste módulo

| Erro | Causa | Solução |
|---|---|---|
| `unable to prepare context: ... no such file or directory` | rodou de dentro de `api/`, ou esqueceu o `.` no fim | volte para a raiz do projeto; o contexto é `.` |
| `COPY failed: file not found in build context` | usou `api/` como contexto | o contexto tem que ser a **raiz** — o Dockerfile faz `COPY api/...` |
| `denied: requested access to the resource is denied` | sem permissão de push no ACR | peça a função **AcrPush** (ou Colaborador) no registro |
| `az: command not found` | não é o Cloud Shell, é um terminal local sem a CLI | volte para o `>_` do portal |
| A sessão do Cloud Shell caiu | ele encerra após ~20 min parado, e o modo efêmero apaga os arquivos | repita o `git clone` do 5.2 |
| `RequestDisallowedByAzure` ao criar o ACR | região fora das permitidas na assinatura | veja o Passo zero e o Módulo 0 |
| O nome do registro é recusado | nome de ACR é **global** e só aceita letras e números minúsculos | troque o sufixo |

---

### 📎 Comentário — e se fosse tudo pelo portal, sem terminal?

*Esta seção é referência, não passo do laboratório. Vale ler para entender o produto — e para
responder à pergunta que sempre aparece em sala: "não dá para fazer isso clicando?".*

**Dá, com uma condição: o código precisa estar num repositório Git.** O portal não tem nenhuma
tela que pegue uma pasta do seu computador e construa a imagem — ele constrói a partir do Git,
e só. Como o nosso projeto **está** no GitHub, o caminho existe e se chama **Tarefa do ACR**
(*ACR Task*). De brinde, ela reconstrói a imagem a cada `git push`.

1. Portal → **Registros de contêiner** → **`acrdeva3<sufixo>`**.
2. Menu esquerdo → **Serviços** → **Tarefas** → **+ Adicionar** → **Tarefa**.
3. Aba **Detalhes da tarefa**:

   | Campo | Valor |
   |---|---|
   | **Nome da tarefa** | `construir-deva3-api` |
   | **Localização de origem** / **Tipo de origem** | `GitHub` |
   | **URL do repositório** | `https://github.com/IsaiasBritto/aie-cloud.git` |
   | **Branch** | `main` |
   | **Caminho do arquivo Docker** | `aulas/05-foundry-agents/Lab/api/Dockerfile` |
   | **Imagem** | `deva3-api:v1` |
   | **Plataforma** | `Linux` · `amd64` |

   > ⚠️ **Atenção ao contexto.** Neste repositório o lab é uma **subpasta**, não a raiz. Se o
   > portal oferecer só um campo de URL, use a sintaxe de subpasta do próprio ACR:
   >
   > ```
   > https://github.com/IsaiasBritto/aie-cloud.git#main:aulas/05-foundry-agents/Lab
   > ```
   >
   > Com essa URL, o **Caminho do arquivo Docker** volta a ser só `api/Dockerfile`.

4. Aba **Gatilhos**: desmarque **"Habilitar gatilho de confirmação"** — senão cada `git push`
   dispara um build. Deixe **Gatilho de imagem base** desmarcado também.
5. Aba **Credenciais de origem**: repositório privado exige um **token de acesso pessoal (PAT)**
   do GitHub com escopo `repo`. Público costuma dispensar.
6. **Criar** → selecione a tarefa → **Executar agora** → acompanhe em **Execuções**.

**Por que a aula não usa esse caminho:** ele leva de 5 a 8 minutos de configuração por imagem,
contra 40 segundos de um comando — e ainda assim depende do código estar publicado no Git. A
Tarefa do ACR brilha em outra situação: **automação**. Deixe o gatilho de confirmação ligado e
você tem um build automático a cada commit, sem pipeline nenhum. Vale mostrar a tela e explicar
essa diferença; é um bom gancho para CI/CD.

**E o terceiro caminho, Docker na própria máquina:**

```bash
az acr login --name acrdeva3<sufixo>
docker build -f api/Dockerfile -t acrdeva3<sufixo>.azurecr.io/deva3-api:v1 .
docker push acrdeva3<sufixo>.azurecr.io/deva3-api:v1
```

Só serve para quem já tem Docker Desktop. Repare que aqui a tag precisa do **nome completo do
registro** — no `az acr build` isso é implícito, porque o `--registry` já diz o destino. É a
confusão nº 1 de quem migra de um para o outro.

## Módulo 6 — Publicar a API como Aplicativo de Contêiner

### 6.1 Antes de criar: liberar o acesso ao registro

**Faça isto primeiro.** O Aplicativo de Contêiner precisa de credencial para **puxar** a imagem
do seu ACR. Se o registro estiver fechado, acontece uma de duas coisas — e as duas confundem:
o registro **não aparece** na lista da aba *Contêiner*, ou a implantação falha lá na frente com
**`UNAUTHORIZED`**.

**Pela CLI** (no Cloud Shell, dois comandos):

```bash
az acr update --name acrdeva3<sufixo> --admin-enabled true
az acr credential show -n acrdeva3<sufixo>
```

O segundo devolve o usuário e duas senhas:

```json
{
  "passwords": [ { "name": "password", "value": "..." },
                 { "name": "password2", "value": "..." } ],
  "username": "acrdeva3<sufixo>"
}
```

Guarde o **username** e **uma** das senhas — você só vai precisar deles se o portal pedir
(situação B do passo 6.2).

> ⚠️ **O `--name` desses dois comandos é o nome do REGISTRO, não o do aplicativo.** É um erro
> comum, porque quase todo comando `az containerapp` usa `--name` para o aplicativo — e aqui o
> comando é `az acr`. Passar `ca-deva3-api` ou `ca-deva3-web` devolve:
>
> ```
> Registry names may contain only alpha numeric characters and must be between 5 and 50 characters
> ```
>
> Não é problema de tamanho nem de caractere: é o nome errado. O valor certo é
> `acrdeva3<sufixo>` — o mesmo do Módulo 4. E este passo se faz **uma vez só**: o usuário
> administrador vale para o registro inteiro, ou seja, para as duas imagens
> (`deva3-api` e `deva3-web`).

**Pelo portal**, se preferir não usar terminal:

1. Portal → **Registros de contêiner** → **`acrdeva3<sufixo>`**.
2. Menu esquerdo → **Configurações** → **Chaves de acesso**.
3. Ligue a chave **Usuário administrador**.
4. A própria tela passa a mostrar **Servidor de logon**, **Nome de usuário** e duas senhas,
   com botão de copiar. É exatamente o que o `az acr credential show` imprime.

> ⚠️ **Isto é um atalho de sala, e vale dizer isso à turma.** O usuário administrador é uma
> senha compartilhada, igual para todo mundo que tem acesso ao registro, e não dá para rastrear
> quem puxou o quê. Em produção o caminho é **identidade gerenciada** com a função **AcrPull** —
> a documentação da Azure descreve a identidade gerenciada justamente como a forma de
> *"evitar o uso de credenciais administrativas"*.
>
> Se quiser mostrar o caminho correto depois de o lab funcionar:
>
> ```bash
> az containerapp registry set \
>   --name ca-deva3-api --resource-group rg-aula-05 \
>   --identity system --server acrdeva3<sufixo>.azurecr.io
> ```
>
> O portal tenta atribuir o papel `AcrPull` à identidade sozinho; quando não consegue —
> falta de permissão ou propagação —, é preciso atribuir na mão. É esse "às vezes funciona,
> às vezes não" que faz o usuário administrador ser o caminho previsível para uma turma.

### 6.2 Criar o Aplicativo de Contêiner

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
   | **Ambiente do Aplicativo de Contêiner** | **Criar novo** → `cae-aula-05`, região East US 2 |

3. Aba **Contêiner**. Aqui há **duas situações**, dependendo do que o portal te oferece:

   **Situação A — o registro aparece na lista** (o normal, depois do passo 6.1):

   | Campo | Valor |
   |---|---|
   | **Nome** | `api` |
   | **Origem da imagem** | Registro de Contêiner do Azure |
   | **Registro** | `acrdeva3<sufixo>.azurecr.io` |
   | **Imagem** | `deva3-api` |
   | **Marca da imagem** | `v1` |
   | **CPU e memória** | 0,5 CPU · 1 Gi |

   **Situação B — o registro não aparece**: escolha **Origem da imagem = Registro privado** e
   preencha à mão com o que você copiou no passo 6.1:

   | Campo | Valor |
   |---|---|
   | **Servidor de logon do registro** | `acrdeva3<sufixo>.azurecr.io` |
   | **Nome de usuário do registro** | o `username` do `az acr credential show` |
   | **Senha do registro** | uma das senhas — marque para guardar como **segredo** |
   | **Imagem e marca** | `deva3-api:v1` |

   Ainda na aba Contêiner, **role até o fim**: existe a seção **Variáveis de ambiente**.
   As sete variáveis do laboratório estão na tabela do passo **6.3** — preencha ali mesmo, se
   a seção aparecer. Se você não encontrar (o assistente muda de versão em versão), **siga em
   frente e crie o aplicativo**: o passo 6.3 mostra como adicioná-las depois.

4. Aba **Entrada**:

   | Campo | Valor |
   |---|---|
   | **Entrada** | Habilitada |
   | **Tráfego de entrada** | Aceitar tráfego de qualquer lugar |
   | **Tipo de transporte** | Automático |
   | **Porta de destino** | `8000` |

5. **Examinar + criar** → **Criar**. Leva de 2 a 4 minutos.

### 6.3 As variáveis de ambiente e os segredos

> ⚠️ **Depois que o aplicativo existe, variáveis de ambiente só mudam criando uma nova
> revisão.** Não há campo para editar na **Visão geral** — é assim por design: cada revisão é
> um instantâneo imutável. Muita gente procura na tela errada aqui.

**Primeiro os segredos.** Eles precisam existir antes de serem referenciados.

> ⚠️ **Só DOIS dos sete valores são segredos.** Os outros cinco são variáveis comuns e
> **não entram nesta tela** — se você tentar cadastrar `AMBIENTE` aqui, o portal recusa.

Menu esquerdo → **Segurança** → **Segredos** → **+ Adicionar**:

| Chave | Tipo | Valor |
|---|---|---|
| `visao-chave` | Segredo dos Aplicativos de Contêiner | a **CHAVE 1** do recurso de visão (Módulo 3) |
| `armazenamento-conexao` | Segredo dos Aplicativos de Contêiner | a cadeia de conexão da conta de armazenamento (Módulo 2) |

> ⚠️ **Nome de segredo e nome de variável seguem regras diferentes — e por isso são
> diferentes.** O portal exige que a chave do segredo tenha *"caracteres alfanuméricos
> minúsculos e `-`, começando e terminando com alfanumérico"*. Ou seja: `visao-chave` passa,
> `VISAO_CHAVE` é recusado.
>
> | | Nome do **segredo** | Nome da **variável de ambiente** |
> |---|---|---|
> | Regra | minúsculas, números e hífen | maiúsculas e `_` liberados |
> | Exemplo | `visao-chave` | `VISAO_CHAVE` |
>
> São dois cadastros distintos: **o segredo guarda o valor, a variável aponta para ele.** A
> aplicação continua lendo `VISAO_CHAVE` — o nome minúsculo é só o rótulo do cofre.

> 💡 **Leia o aviso da própria tela:** *"a alteração de segredos não criará uma nova revisão"*.
> Segredo vale para **todas** as revisões e pode ser trocado sem redeploy; variável de ambiente
> é presa à revisão e exige uma nova. É uma distinção que vale explicar à turma — troca de
> credencial vazada não deveria exigir implantação.

> 💡 **Não achou o "Segredos" no menu?** Use o campo **Pesquisar** no topo do menu do recurso e
> digite `segredo`. Ele filtra o menu inteiro e não depende da versão do portal — o layout desse
> menu muda com frequência.

> ⚠️ **Cuidado com o vizinho de menu.** Dentro de **Segurança** existe também **Autenticação**,
> que abre uma tela convidativa: *"Adicionar um provedor de identidade"*, com Microsoft, Google,
> Facebook. **Não é isso, e não clique.** Essa tela configura o *Easy Auth* — quem pode **chamar**
> o seu aplicativo de fora. Se você adicionar um provedor com "Exigir autenticação", a Azure passa
> a interceptar **todas** as requisições: o Postman recebe `401` e o navegador é redirecionado
> (`302`) para uma tela de login antes de chegar na API. O laboratório para de funcionar.
>
> O recurso é **opcional e desligado por padrão** — deixe assim. Autenticação de verdade seria
> assunto de outra aula; aqui a API é pública de propósito, para a turma testar pelo Postman.


**Depois as variáveis.** Menu esquerdo → **Revisões e réplicas** → **Criar nova revisão**.

A tela *"Criar e implantar uma nova revisão"* tem três abas: **Contêiner · Escala · Volumes**.

> ⚠️ **Fique na aba `Contêiner`** — a primeira. **Volumes** e **Escala** não são usados neste
> laboratório; o "+ Adicionar" delas abre *"Adicionar volume"* e não tem nada a ver com
> variáveis de ambiente.

Na seção **Imagem do contêiner** há uma lista com o contêiner que já existe e, acima dela,
três botões: **✏️ Editar** · **🗑️ Excluir** · **+ Adicionar**.

> ⚠️ **NÃO use o "+ Adicionar".** Ele abre um menu com duas opções, e as duas **acrescentam**
> um contêiner novo ao aplicativo:
>
> | Opção | O que faz | Quando serviria |
> |---|---|---|
> | **Contêiner de aplicativo** | adiciona um *sidecar*, que roda em paralelo ao principal | agente de log, proxy, coletor de métricas |
> | **Contêiner de inicialização** | adiciona um *init*, que roda até terminar **antes** de o app subir | migração de banco, download de modelo |
>
> Os dois são recursos legítimos do Container Apps — só não é o que queremos aqui. Se você
> escolher qualquer um, o aplicativo passa a ter dois contêineres e não sobe direito.

**O caminho certo:** marque a caixa de seleção do contêiner na lista (o nome é o que foi
definido na criação — por exemplo `ca-deva3-api`) e clique em **✏️ Editar**.

Abre um painel lateral com **Imagem**, **Recursos** e, mais abaixo, a seção
**Variáveis de ambiente** → **Adicionar**:

| Nome | Origem | Valor |
|---|---|---|
| `AMBIENTE` | Valor manual | `azure` |
| `VISAO_ENDPOINT` | Valor manual | o endpoint **sem barra no final** |
| `VISAO_CHAVE` | **Referência a um segredo** | `visao-chave` |
| `ARMAZENAMENTO_CONEXAO` | **Referência a um segredo** | `armazenamento-conexao` |
| `ARMAZENAMENTO_CONTAINER` | Valor manual | `deteccoes` |
| `PERSISTIR_IMAGENS` | Valor manual | `true` |
| `LIMIAR_CONFIANCA` | Valor manual | `0.60` |

**Salvar** → **Criar**. Nasce uma revisão nova e a anterior é substituída. Leva ~1 minuto.

> 💡 O atalho **Contêineres → Editar e implantar** cai exatamente no mesmo editor.

> 💡 **Segredo é diferente de variável.** Chave e cadeia de conexão vão como **segredo**;
> o resto vai como valor comum. Segredo não aparece em log nem na tela de revisão — é um bom
> momento para mostrar à turma a diferença entre configuração e credencial.

**Pela CLI**, se preferir, o mesmo resultado em dois comandos:

```bash
az containerapp secret set -n ca-deva3-api -g rg-aula-05 \
  --secrets visao-chave="<CHAVE 1>" armazenamento-conexao="<cadeia de conexao>"

az containerapp update -n ca-deva3-api -g rg-aula-05 \
  --set-env-vars AMBIENTE=azure \
                 VISAO_ENDPOINT="https://<recurso>.cognitiveservices.azure.com" \
                 VISAO_CHAVE=secretref:visao-chave \
                 ARMAZENAMENTO_CONEXAO=secretref:armazenamento-conexao \
                 ARMAZENAMENTO_CONTAINER=deteccoes \
                 PERSISTIR_IMAGENS=true \
                 LIMIAR_CONFIANCA=0.60
```

### 6.4 A entrada (ingress)

Se a **Visão geral** mostrar **`URL do aplicativo: Entrada desabilitada`**, não existe endereço
para testar. Corrija em: menu esquerdo → **Rede** → **Entrada**.

| Campo | Valor |
|---|---|
| **Entrada** | Habilitada |
| **Tráfego de entrada** | Aceitar tráfego de qualquer lugar |
| **Tipo de transporte** | Automático |
| **Porta de destino** | `8000` |

Salve. Diferente das variáveis, a entrada é configuração **do aplicativo** e não exige revisão
nova. Pela CLI:

```bash
az containerapp ingress enable -n ca-deva3-api -g rg-aula-05 \
  --type external --target-port 8000 --transport auto
```

### 6.5 Testar

Na **Visão geral**, copie a **URL do aplicativo** e abra `.../saude` no navegador:
deve responder um JSON com `"situacao": "saudavel"`.

Se o `/saude` responder mas o `/detectar` falhar, o problema **não é o contêiner** — é o
serviço de visão. Volte ao Módulo 3 e teste o endpoint direto.

### 6.6 Erros comuns neste módulo

| Erro | Causa | Solução |
|---|---|---|
| O registro não aparece na lista da aba Contêiner | usuário administrador desligado | passo **6.1** |
| `UNAUTHORIZED` / `authentication required` na implantação | idem — o app não consegue puxar a imagem | passo **6.1**, e recrie o aplicativo |
| A revisão sobe e morre em seguida | a imagem subiu, mas o app quebra ao iniciar | **Monitoramento → Fluxo de logs**: quase sempre é variável de ambiente faltando |
| `URL do aplicativo: Entrada desabilitada` | ingress não foi habilitado na criação | passo **6.4** — Rede → Entrada, porta 8000 |
| Não acho "Variáveis de ambiente" na tela do app | depois de criado, elas vivem dentro da **revisão** | passo **6.3** — Revisões e réplicas → Criar nova revisão |
| O portal pede "Adicionar um provedor de identidade" | você abriu **Segurança → Autenticação** por engano | é o vizinho: **Segurança → Segredos**. Não configure provedor nenhum |
| "A chave deve consistir em caracteres alfanuméricos minúsculos e `-`" | tentou cadastrar `AMBIENTE` (ou outra variável comum) como **segredo** | só `visao-chave` e `armazenamento-conexao` são segredos; o resto vai em **Variáveis de ambiente** |
| Abriu "Adicionar volume" ao procurar as variáveis | está na aba **Volumes** da nova revisão | volte para a aba **Contêiner** — o lab não usa volume |
| O app passa a ter dois contêineres | escolheu "Contêiner de aplicativo" ou "de inicialização" no "+ Adicionar" | os dois **acrescentam**; para editar o existente é a caixa de seleção + **Editar** |
| `401` no Postman ou redirecionamento para tela de login | um provedor de identidade foi adicionado em Autenticação | **Segurança → Autenticação** → remova o provedor |
| `/saude` não responde | porta de destino errada | tem que ser **8000**, a mesma do `EXPOSE` do Dockerfile |
| `/saude` ok, `/detectar` com erro 5xx | endpoint ou chave de visão errados, ou região sem Image Analysis 4.0 | confira `VISAO_ENDPOINT` **sem barra no fim** e teste o serviço pelo Módulo 3 |

## Módulo 7 — Publicar a interface

> 🗺️ A partir daqui vale abrir o [diagrama de sequência](imagens/03-sequencia.png):
> ele mostra exatamente o que vai acontecer quando o aluno clicar em "Analisar imagem".

A interface é um segundo Aplicativo de Contêiner, publicado do **mesmo registro**, no **mesmo
ambiente**, a partir da imagem `deva3-web` que você construiu no Módulo 5. O caminho é o mesmo
do Módulo 6 — mas com três diferenças que quebram o lab se passarem batido: a **porta é 8501**,
a variável é **uma só** (`API_URL`) e ela precisa apontar para a **URL da API**, não para a
própria interface.

| | API (Módulo 6) | Interface (Módulo 7) |
|---|---|---|
| Aplicativo | `ca-deva3-api` | `ca-deva3-web` |
| Imagem | `deva3-api:v1` | `deva3-web:v1` |
| Porta de destino | `8000` | **`8501`** |
| Variáveis | sete (duas como segredo) | **uma**, sem segredo |
| Fala com | Azure AI Vision e Blob | **a API do Módulo 6** |

> ⚠️ **Só comece este módulo depois que o `/saude` da API responder.** A interface consulta a
> API assim que abre, para desenhar o painel lateral. Se a API não estiver de pé, a tela sobe
> com um erro vermelho — e você vai depurar a interface quando o problema está no outro
> aplicativo.

### 7.1 Antes de criar: copiar a URL da API

Portal → **Aplicativos de Contêiner** → **`ca-deva3-api`** → **Visão geral** → campo
**URL do aplicativo**. É algo assim:

```
https://ca-deva3-api.<identificador>.eastus2.azurecontainerapps.io
```

Copie e guarde. Esse é o único valor novo deste módulo.

> ⚠️ **Copie a URL limpa.** Sem `/saude` no fim, sem `/docs`, sem barra final. O que a interface
> espera é a **raiz** — ela mesma acrescenta `/saude` e `/detectar` na hora de chamar.

O acesso ao registro **já está liberado**: o passo 6.1 vale para o registro inteiro, e portanto
para as duas imagens. Não refaça.

### 7.2 Criar o Aplicativo de Contêiner

1. Busque **Aplicativos de Contêiner** → **+ Criar**.

2. Aba **Noções Básicas**:

   | Campo | Valor |
   |---|---|
   | **Assinatura** * | Azure for Students |
   | **Grupo de recursos** * | `rg-aula-05` |
   | **Nome do aplicativo contêiner** * | `ca-deva3-web` |
   | **Otimizar para Azure Functions** | deixe **desmarcado** |
   | **Origem da implantação** | **Imagem de contêiner** |
   | **Ambiente do Aplicativo de Contêiner** | **`cae-aula-05`** — selecione o que já existe |

   > ⚠️ **Não crie um ambiente novo.** O campo oferece "Criar novo" de novo, e é tentador
   > clicar. Um segundo ambiente significa outra rede virtual gerenciada, outro workspace de
   > log e mais alguns minutos de espera — sem nenhum ganho. Os dois aplicativos convivem no
   > mesmo ambiente, que é justamente para isso que ele serve.

3. Aba **Contêiner**:

   | Campo | Valor |
   |---|---|
   | **Nome** | `web` |
   | **Origem da imagem** | Registro de Contêiner do Azure |
   | **Registro** | `acrdeva3<sufixo>.azurecr.io` |
   | **Imagem** | `deva3-web` |
   | **Marca da imagem** | `v1` |
   | **CPU e memória** | 0,5 CPU · 1 Gi |

   Se o registro não aparecer na lista, é a **situação B** do passo 6.2: escolha
   **Registro privado** e informe servidor, usuário e senha à mão.

   Role até o fim da aba: se a seção **Variáveis de ambiente** aparecer aqui, adicione já

   | Nome | Origem | Valor |
   |---|---|---|
   | `API_URL` | Valor manual | a URL que você copiou no 7.1 |

   Se não aparecer, siga em frente — o passo **7.3** mostra como adicionar depois.

4. Aba **Entrada**:

   | Campo | Valor |
   |---|---|
   | **Entrada** | Habilitada |
   | **Tráfego de entrada** | Aceitar tráfego de qualquer lugar |
   | **Tipo de transporte** | Automático |
   | **Porta de destino** | **`8501`** |

   > 💡 **De onde vem o 8501?** Do `EXPOSE 8501` do `web/Dockerfile` e do
   > `--server.port=8501` no comando do Streamlit. Porta de destino é a porta **em que o
   > contêiner escuta**, não a porta pela qual você acessa — de fora é sempre `443`, com o
   > certificado que a Azure emite. Errar isso é o motivo nº 1 de "a URL abre e fica em branco".

5. **Examinar + criar** → **Criar**. De 2 a 4 minutos.

**Pela CLI**, tudo de uma vez:

```bash
az containerapp create \
  --name ca-deva3-web --resource-group rg-aula-05 \
  --environment cae-aula-05 \
  --image acrdeva3<sufixo>.azurecr.io/deva3-web:v1 \
  --registry-server acrdeva3<sufixo>.azurecr.io \
  --target-port 8501 --ingress external \
  --cpu 0.5 --memory 1Gi \
  --env-vars API_URL="https://ca-deva3-api.<identificador>.eastus2.azurecontainerapps.io"
```

### 7.3 A variável de ambiente

Vale aqui a mesma regra do passo 6.3: **depois de criado, variável de ambiente só muda com uma
revisão nova.** O caminho é idêntico —

Menu esquerdo → **Revisões e réplicas** → **Criar nova revisão** → aba **Contêiner** →
marque a caixa do contêiner na lista → **✏️ Editar** → seção **Variáveis de ambiente** →
**Adicionar**:

| Nome | Origem | Valor | Obrigatória? |
|---|---|---|---|
| `API_URL` | Valor manual | `https://ca-deva3-api.<identificador>.eastus2.azurecontainerapps.io` | **sim** |
| `TEMPO_LIMITE_SEGUNDOS` | Valor manual | `60` | não — é o padrão do código |

**Salvar** → **Criar**.

> ⚠️ Continuam valendo os dois desvios do Módulo 6: **não** use o **+ Adicionar** (ele
> acrescenta um sidecar ou um init, não edita o contêiner que existe) e **não** vá para a aba
> **Volumes**. O caminho é caixa de seleção + **Editar**, na aba **Contêiner**.

> 💡 **Nenhuma variável aqui é segredo** — a URL da API é pública, é o mesmo endereço que a
> turma abre no Postman. Compare com os sete valores do Módulo 6: lá havia chave e cadeia de
> conexão. Vale dizer isso à turma: **segredo é o que não pode aparecer em log**; endereço não é.

> 💡 **`TEMPO_LIMITE_SEGUNDOS`** é quanto a interface espera a API responder antes de desistir.
> O padrão de 60 s cobre com folga a chamada ao serviço de visão. Se a sala estiver com internet
> ruim e aparecerem erros de *timeout*, suba para `120` — é o único ajuste fino deste módulo.

**Pela CLI:**

```bash
az containerapp update -n ca-deva3-web -g rg-aula-05 \
  --set-env-vars API_URL="https://ca-deva3-api.<identificador>.eastus2.azurecontainerapps.io"
```

### 7.4 A entrada (ingress)

Se a **Visão geral** mostrar **`URL do aplicativo: Entrada desabilitada`**, repita o passo 6.4
com a porta desta imagem: menu esquerdo → **Rede** → **Entrada**.

| Campo | Valor |
|---|---|
| **Entrada** | Habilitada |
| **Tráfego de entrada** | Aceitar tráfego de qualquer lugar |
| **Tipo de transporte** | Automático |
| **Porta de destino** | **`8501`** |

```bash
az containerapp ingress enable -n ca-deva3-web -g rg-aula-05 \
  --type external --target-port 8501 --transport auto
```

> 💡 **Por que "Automático" e não HTTP/1.1?** O Streamlit conversa com o navegador por
> **WebSocket** depois que a página carrega — é assim que o resultado aparece sem recarregar a
> tela. O transporte automático negocia HTTP/2 e WebSocket sozinho. Se você forçar um tipo e a
> página abrir mas nunca reagir aos cliques, é aqui que se olha.

### 7.5 Testar — o checkpoint da aula

Na **Visão geral** de `ca-deva3-web`, copie a **URL do aplicativo** e abra no navegador.
A primeira carga leva alguns segundos (o Streamlit sobe sob demanda).

Confira nesta ordem:

1. **O painel lateral, à esquerda.** Deve mostrar `API: <a URL da sua API>` e uma faixa
   **verde** de saudável, com o **limiar de confiança** e o **blob configurado**. Faixa vermelha
   dizendo que não foi possível falar com a API significa `API_URL` errada — volte ao 7.3.
2. **Modo de detecção**: deixe em **Pessoas · Image Analysis 4.0**.
3. **Consentimento**: marque, se quiser ver a imagem gravada no Blob do Módulo 2. Desmarcado,
   só o JSON é guardado — e essa é a diferença que vale discutir com a turma.
4. **Envie uma foto** e clique em **Analisar imagem**.

✅ **Checkpoint do laboratório:** a foto sobe, a caixa é desenhada em volta da pessoa, a
confiança aparece nos cartões do topo, a tabela de coordenadas é preenchida e o **payload JSON**
completo fica visível no fim da coluna da direita.

> 💡 **É o mesmo JSON do Postman.** Vale abrir os dois lado a lado: a interface não tem
> inteligência nenhuma, ela desenha o que a API respondeu. Isso torna concreta a separação
> entre serviço e apresentação — e é o gancho para a próxima aula, em que o **Deva** entra no
> lugar da tela e transforma esse número em decisão.

### 7.6 Erros comuns neste módulo

| Erro | Causa | Solução |
|---|---|---|
| A URL abre e fica **em branco** ou dá erro 502 | porta de destino errada | tem que ser **8501**, não 8000 — passo **7.4** |
| Painel lateral vermelho: "Não foi possível falar com a API" | `API_URL` ausente, errada ou com `/saude` no fim | passo **7.3** — a URL é a **raiz** da API, sem barra final |
| A tela abre mas não reage aos cliques | transporte forçado, WebSocket bloqueado | **Rede → Entrada → Tipo de transporte = Automático** |
| A revisão sobe e morre | quase sempre imagem errada (`deva3-api` no lugar de `deva3-web`) | **Monitoramento → Fluxo de logs** e confira a imagem na revisão |
| Criou um ambiente novo por engano | o campo oferece "Criar novo" na aba Noções Básicas | apague o ambiente extra; os dois apps devem ficar em `cae-aula-05` |
| `Registry names may contain only alpha numeric characters...` | passou `ca-deva3-web` para um comando `az acr` | o `--name` do `az acr` é o **registro**: `acrdeva3<sufixo>` — passo **6.1** |
| Timeout ao analisar a foto | rede da sala lenta, ou API demorando no serviço de visão | suba `TEMPO_LIMITE_SEGUNDOS` para `120` e teste o `/detectar` direto no Postman |
| A caixa não é desenhada, mas o JSON aparece | a resposta não trouxe detecção | não é erro da interface: a foto não tem pessoa reconhecível, ou a confiança ficou abaixo do limiar |

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
| O registro não aparece ao criar o Container App | Usuário administrador do ACR desligado | `az acr update --name <acr> --admin-enabled true` (Módulo 6.1) |
| `UNAUTHORIZED` ao implantar o Container App | O app não tem credencial para puxar do ACR | Módulo 6.1 — habilite o administrador ou use identidade gerenciada |
| Interface abre e não fala com a API | `API_URL` errada ou sem `https://` | Corrija a variável |
| `Registry names may contain only alpha numeric characters` | Passou o nome do **aplicativo** a um comando `az acr` | O `--name` do `az acr` é o registro: `acrdeva3<sufixo>` |
| `ModuleNotFoundError: api` | Imagem construída da pasta errada | Construa a partir da **raiz** do projeto |
