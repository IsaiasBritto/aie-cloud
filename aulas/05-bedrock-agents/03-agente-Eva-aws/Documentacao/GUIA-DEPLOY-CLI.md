# Guia — publicar a Eva na AWS pela CLI (Terraform + Docker)

Do zero até a Eva respondendo num endereço público, em uns 10 minutos, de
dentro do **AWS CloudShell**. O script faz tudo; este guia explica cada passo
para você saber o que ele fez — e consertar quando não fizer.

> **Dois cenários, o mesmo código:**
>
> | | Learner Lab (aluno) | Conta comum (demo do professor) |
> |---|---|---|
> | Provedor | `openai` — o Lab não libera o Bedrock | `bedrock` |
> | Credencial do modelo | chave da OpenAI no **Secrets Manager** | **task role**, sem chave |
> | Role | `LabRole` (não se cria role) | `criar_role = true` |
> | Custo | sai do crédito do Lab | centavos + ~US$ 0,03/h da tarefa |

---

## Passo 0 — Ambiente

1. Learner Lab → **Start Lab** → bolinha verde → **AWS**.
2. No console, ícone **CloudShell** (barra superior). Região **us-east-1**.
3. Terraform no `$HOME` (se ainda não fez na Aula 1):

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git ~/aie-cloud 2>/dev/null || git -C ~/aie-cloud pull
bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
source ~/.bashrc
terraform -version
```

## Passo 1 — Configurar

```bash
cd ~/aie-cloud/aulas/05-bedrock-agents/03-agente-Eva-aws/infra
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
nano terraform/terraform.tfvars      # provedor, responsavel (seu RM) e preços
```

**Learner Lab — a chave da OpenAI** (a mesma da Eva local). Ela vai por
variável de ambiente, **nunca** em arquivo:

```bash
read -rsp "Chave da OpenAI: " TF_VAR_openai_api_key && export TF_VAR_openai_api_key && echo
```

> O `read -s` não mostra o que você digita nem grava no histórico do shell.
> `export TF_VAR_...=sk-...` direto funcionaria — e deixaria a chave no
> `~/.bash_history`.

**Conta comum (Bedrock):** no `terraform.tfvars`, `provedor = "bedrock"` e
`criar_role = true`. Nenhuma chave.

## Passo 2 — Publicar

```bash
bash deploy.sh
```

O que ele faz, em ordem:

| # | Comando | Por quê |
|---|---|---|
| 0 | `aws sts get-caller-identity` | confirma **quem** vai criar tudo — evita publicar na conta errada |
| 1 | `terraform apply -var ecs_enabled=false` | cria ECR, log group (retenção 7 dias), cluster, security group e — com `openai` — o segredo |
| 2 | `aws ecr get-login-password \| docker login` | login no registry com a credencial da sessão: nenhuma senha guardada |
| 2 | `docker build` + `docker push` | a imagem, com uma tag nova (`v2026...`) a cada deploy |
| 3 | `terraform apply -var ecs_enabled=true -var image_tag=...` | cria/atualiza o serviço ECS apontando para a imagem nova |
| 4 | `aws ecs list-tasks` → `describe-tasks` → `ec2 describe-network-interfaces` | descobre o IP público da tarefa (não há load balancer) |

No fim:

```
Eva no ar:   http://54.x.x.x:8501
Logs:        aws logs tail /ecs/eva/abc123 --follow
```

Abra o endereço. Na barra lateral, confira a linha 🔐 / 🔑:

- `bedrock · identidade (container-role)` — a task role funcionou, sem chave.
- `openai · chave de API (Secrets Manager)` — o caminho do Learner Lab. O
  aviso amarelo é de propósito: existe um segredo em jogo.

## Passo 3 — Conferir o que foi criado

```bash
cd terraform
terraform output
terraform state list
```

E o que a task definition entrega ao container (repare: o **ARN** do segredo,
nunca o valor):

```bash
FAMILIA=$(aws ecs list-task-definitions --family-prefix "$(terraform output -raw ecs_cluster_name | sed 's/-cluster$/-app/')" \
            --sort DESC --query 'taskDefinitionArns[0]' --output text)
aws ecs describe-task-definition --task-definition "$FAMILIA" \
  --query 'taskDefinition.containerDefinitions[0].{env: environment, segredos: secrets}'
```

## Passo 4 — Ver a telemetria

Converse com a Eva (inclua "que dia é hoje?", que usa ferramenta) e:

```bash
LOGS=$(terraform output -raw log_group_name)
aws logs tail "$LOGS" --since 10m --filter-pattern '{ $.evento = "eva.chamada_modelo" }'
bash ../custo.sh 1
```

Cada linha é uma chamada ao modelo; linhas com o mesmo `turno_id` são a mesma
pergunta. O resto está no [LAB-OBSERVABILIDADE.md](LAB-OBSERVABILIDADE.md).

## Passo 5 — Publicar uma alteração

Edite o `agent.md` (por exemplo, mude o tom da Eva) e rode de novo:

```bash
cd ~/aie-cloud/aulas/05-bedrock-agents/03-agente-Eva-aws/infra
bash deploy.sh
```

Tag nova → task definition nova → o ECS troca a tarefa. **O IP muda** (não há
load balancer); o script imprime o novo.

## Passo 6 — Desligar

```bash
# pausa (a tarefa para de cobrar; o resto continua):
aws ecs update-service --cluster "$(terraform -chdir=terraform output -raw ecs_cluster_name)" \
  --service eva --desired-count 0

# apagar tudo:
terraform -chdir=terraform destroy -auto-approve
```

> No Learner Lab, a sessão acabar **não** apaga nada: a tarefa Fargate volta a
> cobrar do seu crédito quando o Lab religa. `destroy` ao fim da aula.

---

## Problemas comuns

| Sintoma | Causa provável | Conserto |
|---|---|---|
| `provedor = openai exige a chave` | faltou o `TF_VAR_openai_api_key` | Passo 1, de novo, na mesma aba |
| `Error: reading IAM Role (LabRole)` | conta comum sem LabRole | `criar_role = true` |
| `AccessDeniedException ... bedrock` na tela | Learner Lab com `provedor = bedrock` | `provedor = "openai"` |
| `denied: Your authorization token has expired` no push | o login do ECR vale 12 h | rode o `deploy.sh` de novo |
| a tarefa fica PENDING → STOPPED | imagem não encontrada, ou segredo ilegível | `aws ecs describe-tasks ... --query 'tasks[0].stoppedReason'` |
| `CannotPullContainerError` | tag inexistente no ECR | rode o `deploy.sh` inteiro, não só o apply |
| a página não abre | IP mudou, ou `cidr_acesso` não inclui você | rode o passo 4 do script; confira o SG |
| `no space left on device` no CloudShell | imagens antigas do Docker | `docker system prune -af` |
| `ResourceInitializationError: unable to pull secrets` | execution role sem `secretsmanager:GetSecretValue` | na conta comum, `criar_role = true` resolve |

---

## Depois: o mesmo pelo console

O [GUIA-DEPLOY-CONSOLE.md](GUIA-DEPLOY-CONSOLE.md) percorre no console tudo o
que o script criou — para entender cada peça e investigar incidente.
