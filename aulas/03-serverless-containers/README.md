# Aula 3 — Processamento Serverless & Containers

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Explicar o modelo serverless (FaaS) e quando ele vence um servidor ligado.
- Provisionar uma **AWS Lambda** com **Function URL** via Terraform e publicar código com a AWS CLI.
- Ler dados do **S3** a partir da Lambda **sem credenciais no código** (execution role).
- Empacotar o mesmo código num **container Docker**, publicar no **Amazon ECR** e rodar no **Amazon ECS (Fargate)**.
- Comparar Lambda × Fargate × App Runner em custo parado, cold start, escala e operação.
- Descrever a API como **tool** consumível por um agente de IA.

---

## Conexão com o Quantum Commerce

A API de catálogo desta aula é a **primeira ferramenta** dos agentes da QC: o agente pergunta "tem cadeira para home office?" e a Lambda responde com os produtos do catálogo. A mesma lógica sai em dois sabores — a Lambda, que vai para produção, e o container no ECR, como alternativa.

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — 3 atividades + wrap-up |
| [lab/terraform/](lab/terraform/) | Bucket + Lambda + Function URL + ECR + ECS Fargate |
| [lab/function/](lab/function/) | Código da Lambda: `v1-mock` e `v2-s3` |
| [lab/docker/](lab/docker/) | A mesma API em FastAPI + Dockerfile |
| [lab/scripts/task_ip.sh](lab/scripts/task_ip.sh) | Descobre o IP público da tarefa Fargate |
| [lab/data/produtos.csv](lab/data/produtos.csv) | 20 produtos de exemplo (sobe no apply) |
| [exercicios.md](exercicios.md) | Após a aula — exercícios em 3 níveis (🟢/🟡/🔴) |

## Entrega de grupo

Esta aula gera a **3ª entrega de grupo** (10% da nota): instruções em [entregas/entrega-03/](../../entregas/entrega-03/). Rubrica em [entregas/rubrica.md](../../entregas/rubrica.md).

---

## Pré-requisitos

- ✅ Aula 1 concluída — Learner Lab, CloudShell e Terraform no `$HOME`
- ✅ **Não depende da Aula 2:** esta aula cria o próprio bucket com o catálogo

## Por que build no CloudShell (e não numa máquina do professor)

O AWS CloudShell tem Docker e a credencial da sua sessão. Isso fecha o ciclo inteiro dentro da conta: `docker build` → `docker push` para o ECR (login com a LabRole, sem token pessoal) → tarefa Fargate puxando a imagem com a mesma role. Nenhuma senha em lugar nenhum.
