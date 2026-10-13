# Guia — a Eva pelo console da AWS

O `deploy.sh` cria tudo em poucos minutos — e esconde tudo também. Este guia
percorre **no console** cada peça que ele criou, na ordem em que uma depende
da outra. Serve para duas coisas: entender o que é cada recurso e saber onde
olhar quando algo quebrar.

> Por que não publicar clicando? Dá — e a primeira versão deste guia fazia
> isso. Mas no ECS o caminho por clique tem armadilhas que não ensinam nada
> (o push da imagem precisa da CLI de qualquer jeito, e a task definition
> tem dezenas de campos). O ganho didático está em **ler** o que foi criado.
> Publique com o [GUIA-DEPLOY-CLI.md](GUIA-DEPLOY-CLI.md) e venha para cá.

---

## Passo 0 — As tags, antes de tudo

Console → **Resource Groups & Tag Editor** → **Tag Editor**.

- Regions: `us-east-1` · Resource types: `All supported resource types`
- Tags: `projeto` = `eva` → **Search resources**

Tudo que o Terraform criou aparece aqui, com as mesmas sete tags
(`aula`, `disciplina`, `projeto`, `ambiente`, `responsavel`, `centro-custo`,
`provisionado`). Ninguém marcou recurso por recurso: foi o `default_tags` do
provider. Repare no que **não** aparece (a política IAM, a versão do segredo):
são peças que não aceitam tag e não aparecem na fatura.

## Passo 1 — ECR: a imagem

**Amazon ECR** → *Private registry* → *Repositories* → `eva-<sufixo>-app`.

- **Images:** uma por deploy, com a tag `v2026...`. A *lifecycle policy*
  (aba à esquerda) guarda só as 5 mais recentes — FinOps de registry.
- **Scan on push** está ligado: abra uma imagem → *Vulnerabilities*. É de
  graça no modo básico e é a primeira pergunta de qualquer revisão de
  segurança.

## Passo 2 — Secrets Manager: a chave (só provedor openai)

**Secrets Manager** → `eva-<sufixo>/openai-api-key`.

- **Não clique em *Retrieve secret value* na frente da turma.** Quem tem essa
  permissão lê a chave — é exatamente por isso que ela mora aqui e não no
  código.
- Repare em **Resource permissions** (vazio) e em quem pode ler: a
  `LabRole`, via IAM. Na conta comum, só a role criada pelo Terraform.

## Passo 3 — ECS: cluster, serviço, tarefa

**Amazon ECS** → *Clusters* → `eva-<sufixo>-cluster`.

### A task definition

*Task definitions* → `eva-<sufixo>-app` → a revisão mais alta → **JSON**.
Procure:

| Campo | O que dizer em aula |
|---|---|
| `taskRoleArn` | a identidade **do código** — é ela que assina a chamada ao Bedrock |
| `executionRoleArn` | a identidade **do agente do ECS** — puxa imagem, lê segredo, escreve log |
| `environment` | configuração em claro: provedor, modelo, preços, `EVA_TELEMETRIA` |
| `secrets` | só o **ARN** do segredo. O valor nunca aparece aqui |
| `logConfiguration` | driver `awslogs`: o stdout vira CloudWatch Logs, sem SDK |
| `cpu` / `memory` | 512 / 1024 — o que você paga por hora, ligado ou não |

### O serviço e a tarefa

*Services* → `eva` → aba **Tasks** → a tarefa em RUNNING:

- **Configuration → Public IP**: o endereço da Eva (porta 8501).
- **Logs**: o stdout do container — Streamlit e as linhas JSON da Eva.
- Se a tarefa morreu: *Tasks* → filtro **Stopped** → a tarefa → **Stopped
  reason**. É a primeira tela de qualquer incidente no ECS.

### Pausar pelo console

*Services* → `eva` → **Update service** → *Desired tasks* = `0`. A tarefa para
e para de cobrar; cluster, imagem e logs continuam.

## Passo 4 — VPC: o security group

**EC2** → *Security groups* → `eva-<sufixo>-web`.

Uma regra de entrada: TCP **8501** de `cidr_acesso` (padrão: o mundo todo).
Fora da aula, troque pelo seu IP (`/32`) no `terraform.tfvars` e rode o
deploy de novo — a Eva gasta o **seu** dinheiro a cada pergunta, de quem
quer que pergunte.

## Passo 5 — CloudWatch: logs e telemetria

**CloudWatch** → *Logs* → *Log groups* → `/ecs/eva/<sufixo>`.

- **Retention:** 7 days. O padrão do CloudWatch é *Never expire* — custo que
  cresce em silêncio.
- **Logs Insights** com este log group: as consultas do
  [LAB-OBSERVABILIDADE.md](LAB-OBSERVABILIDADE.md) e do
  [LAB-FINOPS.md](LAB-FINOPS.md).
- **Metric filters**: vazio até você fazer o 5.2 do LAB-FINOPS.

## Passo 6 — IAM: quem pode o quê

**IAM** → *Roles*.

- **Learner Lab:** `LabRole`. Abra e veja o tamanho das políticas — é uma
  role de laboratório, permissiva de propósito. Em produção, isto seria um
  achado de auditoria.
- **Conta comum:** `eva-<sufixo>-task`. Duas políticas: a gerenciada de
  execução do ECS e a `eva-minimo` — `bedrock:InvokeModel*` e, com openai,
  `secretsmanager:GetSecretValue` **naquele** segredo. Compare com a LabRole.

## Passo 7 — Bedrock (só conta comum)

**Amazon Bedrock** → *Playgrounds* → *Chat* → o mesmo modelo da Eva. Mande a
mesma pergunta. A diferença de resposta é o `agent.md` + `memory.md` +
ferramentas: o harness.

E em **CloudWatch** → *Metrics* → `AWS/Bedrock` → *By ModelId*: as chamadas
da Eva aparecem ali sem instrumentação nenhuma (Parte 1 do LAB-OBSERVABILIDADE).

---

## Apagar tudo

Pelo console seria recurso por recurso, na ordem inversa das dependências.
Não faça: `terraform destroy` (Passo 6 do [GUIA-DEPLOY-CLI.md](GUIA-DEPLOY-CLI.md)).
Depois, volte ao **Tag Editor** do Passo 0 e confirme que a busca por
`projeto = eva` voltou vazia.
