# Manual 2 — Provisionar por script (Terraform + Docker, no CloudShell)

> O laboratório inteiro em **três comandos**, de dentro do AWS CloudShell.
> Leia o [diagrama de arquitetura](imagens/02-arquitetura.png) ao lado: cada script
> corresponde a setas numeradas do desenho (1 · `terraform apply`, 2 · `docker push`,
> 3 · o ECS puxando as imagens).
>
> Tempo estimado: **10 a 15 minutos** (o build das imagens é a parte lenta).

---

## 0 · Preparar o ambiente

1. AWS Academy → **Learner Lab** → **Start Lab** → espere a bolinha **verde** → **AWS**.
2. No console, região **N. Virginia (us-east-1)**, ícone **CloudShell** na barra superior.
3. Terraform no `$HOME` (se ainda não fez na Aula 1):

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git ~/aie-cloud 2>/dev/null || git -C ~/aie-cloud pull
bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
source ~/.bashrc
terraform -version && docker --version && aws sts get-caller-identity
```

> O CloudShell já vem com AWS CLI, Docker e a **credencial da sua sessão**. Não há
> `login`, não há chave para copiar, não há provedor para registrar — o erro nº 1 da
> trilha Azure (`az provider register`) simplesmente não existe aqui.

---

## 1 · Os três comandos

```bash
cd ~/aie-cloud/aulas/05-bedrock-agents/Lab
export VERSAO=v1                     # etiqueta das imagens. Nunca 'latest'

bash infra/01-criar-recursos.sh      # bucket, ECR, cluster, logs, security group
bash infra/02-publicar-imagens.sh    # docker build + push das duas imagens
bash infra/03-implantar-apps.sh      # serviço ECS + IP público
```

Ao final, o terceiro script imprime:

```
 Interface ...... http://54.x.x.x:8501
 API (Swagger) .. http://54.x.x.x:8000/docs
 Saúde .......... http://54.x.x.x:8000/saude
```

---

## 2 · O que cada script faz

### `00-variaveis.sh` — carregado pelos outros

Define `AWS_REGION`, `VERSAO`, os caminhos e os utilitários (`tf`, `saida`,
`mostrar_alvo`). Não há `SUFIXO` para escolher: o Terraform sorteia um
(`random_string`) e guarda no estado. Nome de bucket é único **no mundo**, e o
sorteio evita a colisão entre colegas.

### `01-criar-recursos.sh` — `terraform apply` sem o serviço

| Recurso Terraform | O que é |
|---|---|
| `aws_s3_bucket.deteccoes` + bloqueio público + criptografia + **ciclo de vida** | onde ficam resultado e imagem (com consentimento). Expira em `retencao_dias` (7) |
| `aws_ecr_repository.app["api"]` / `["web"]` | os dois registros, com *scan on push* e lifecycle de 5 imagens |
| `aws_ecs_cluster.deva3` | o cluster (vazio até o passo 3) |
| `aws_cloudwatch_log_group.deva3` | logs dos dois containers, 7 dias |
| `aws_security_group.deva3` | portas 8000 e 8501 para `cidr_acesso` |
| `aws_ecs_task_definition.deva3` | a "receita" da tarefa: 2 containers, LabRole, variáveis |

O serviço (`aws_ecs_service`) fica de fora (`servico_ativo=false`): ele precisa de
imagens que só existem depois do passo 2.

### `02-publicar-imagens.sh` — build e push

```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <registro>
docker build -f api/Dockerfile -t <ecr_api>:v1 .
docker build -f web/Dockerfile -t <ecr_web>:v1 .
docker push ...
```

Repare no `-f api/Dockerfile .`: o contexto é a **raiz** do Lab, senão o pacote `api`
não entra na imagem (armadilha registrada no `MEMORY.md`). E repare no login: ele usa
a credencial da sessão — não existe usuário/senha de registro, ao contrário do
`az acr credential show` da versão Azure.

### `03-implantar-apps.sh` — o serviço

1. `terraform apply -var servico_ativo=true` cria o serviço `deva3` (1 tarefa).
2. `aws ecs update-service --force-new-deployment`: reenviar `v1` não muda a task
   definition, e sem isso o ECS não pegaria a imagem nova.
3. `aws ecs wait services-stable` espera a tarefa ficar saudável. A interface só sobe
   depois que a API responde `/saude` (`dependsOn: HEALTHY` na task definition).
4. ENI → IP público → as três URLs.

### `99-remover-tudo.sh` — fim da aula

Pede para digitar `apagar` e roda `terraform destroy`: serviço, cluster, imagens,
logs e o bucket **com tudo dentro**. É o "jeito de apagar" que a LGPD exige.

---

## 3 · Publicar uma nova versão

```bash
export VERSAO=v2
bash infra/02-publicar-imagens.sh
bash infra/03-implantar-apps.sh
```

Etiqueta nova a cada versão: é o que permite voltar atrás
(`VERSAO=v1 bash infra/03-implantar-apps.sh`). O **IP muda** a cada implantação — não
há load balancer.

---

## 4 · Rodar a API local gravando no bucket da nuvem

Útil para depurar sem rebuild. Na sua máquina (fora do CloudShell):

```bash
cp .env.exemplo .env
# ARMAZENAMENTO_BUCKET=<output bucket do Terraform>
# Learner Lab → AWS Details → AWS CLI: Show → cole as 3 variáveis no terminal
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_SESSION_TOKEN=...
make api      # http://localhost:8000/docs
```

---

## 5 · Quando dá errado

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `Error: reading IAM Role (LabRole)` | não está no Learner Lab | `-var role_name=<sua role>` (com Rekognition, S3 e ECS) |
| `no space left on device` no build | CloudShell com imagens antigas | `docker system prune -af` |
| `services-stable` não termina | a tarefa cai em loop | o script mostra o `stoppedReason`; veja também `aws logs tail /ecs/deva3-<sufixo> --since 10m` |
| `CannotPullContainerError` | etiqueta não publicada | rode o `02` com a mesma `VERSAO` |
| interface diz "A API não respondeu" | container `api` caiu | logs do stream `deva3/api/...` |
| `ExpiredTokenException` na API **local** | sessão do Learner Lab venceu (4 h) | copie as credenciais de novo |
| `AccessDeniedException` no Rekognition | sessão do Lab encerrada, ou role errada | confira a bolinha verde e o `taskRoleArn` |
| página não abre | IP mudou, ou `cidr_acesso` não inclui você | rode o `03` de novo; confira o SG |

> Regra de bolso: localize o problema **no diagrama** antes de abrir o log. Seta 3
> (pull), seta 5 (API_URL) ou seta 6 (credencial) — cada uma tem um sintoma
> diferente.
