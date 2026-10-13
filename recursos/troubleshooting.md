# Troubleshooting — Problemas comuns

> Cada aula tem a sua tabela de troubleshooting no `guia-lab.md`. Aqui ficam os erros
> que aparecem em **qualquer** aula. Encontrou um novo? Avise o professor.

---

## AWS Academy Learner Lab

### A bolinha não fica verde / "Lab ended"

Clique em **Start Lab** de novo e espere 1–3 minutos. A sessão dura 4 horas; depois
disso tudo para (mas não é apagado).

### `ExpiredToken` / `The security token included in the request is expired`

A sessão do Learner Lab venceu. No **CloudShell**, feche e reabra a aba depois do
Start Lab. Na **sua máquina**, copie de novo as credenciais em **AWS Details → AWS
CLI: Show** (elas mudam a cada sessão).

### `AccessDenied` ao criar IAM role / policy

O Learner Lab não permite criar roles. Use a **`LabRole`** (Lambda, ECS, SageMaker)
e o **`LabInstanceProfile`** (EC2). Os Terraforms da disciplina já fazem isso com
`data "aws_iam_role" "lab"`.

### "Serviço não disponível" (Bedrock, Cost Explorer, Budgets)

Não é você: o Learner Lab não libera esses serviços. As aulas que os usam têm um
caminho alternativo (OpenAI na Eva, Tag Editor no FinOps) e a demonstração do professor.

---

## AWS CloudShell

### `No space left on device`

O `$HOME` tem 1 GB. Limpe: `pip3 cache purge`, `docker system prune -af`,
`rm -rf ~/aie-cloud/aulas/*/lab/**/.terraform` em aulas já destruídas. O cache de
plugins do Terraform (`~/.terraform.d/plugin-cache`) é compartilhado entre as aulas
justamente para economizar espaço.

### `terraform: command not found`

O Terraform fica no seu `$HOME/bin`. Rode `source ~/.bashrc` ou reinstale:
`bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh`.

### Python 3.9 no CloudShell × Python 3.12 na Lambda

Pacotes com binário (pydantic, pymongo...) instalados no CloudShell não servem na
Lambda. Use `pip install ... --platform manylinux2014_x86_64 --python-version 3.12
--only-binary=:all:` (a Aula 4 mostra).

---

## Terraform

### `Error: No valid credential sources found`

O Learner Lab está desligado, ou você está fora do CloudShell sem credenciais
exportadas. Ligue o lab e reabra o CloudShell.

### `Error: ... already exists`

Você está criando algo que já existe (de uma execução anterior cujo estado se perdeu).
Apague pelo console ou importe com `terraform import`.

### `BucketAlreadyExists`

Nome de bucket é único **no mundo**. Os Terraforms usam um sufixo aleatório
(`random_string`); se você fixou um nome, troque.

---

## Docker / imagens

### `toomanyrequests: You have reached your pull rate limit`

Limite anônimo do Docker Hub. Os Dockerfiles e Terraforms da disciplina usam o
espelho oficial do **ECR Public** (`public.ecr.aws/docker/library/...`), que não
tem esse limite. Se você escreveu `FROM python:3.12-slim`, troque por
`FROM public.ecr.aws/docker/library/python:3.12-slim`.

### `denied: Your authorization token has expired` no `docker push`

O login no ECR vale 12 h:
`aws ecr get-login-password | docker login --username AWS --password-stdin <conta>.dkr.ecr.us-east-1.amazonaws.com`.
