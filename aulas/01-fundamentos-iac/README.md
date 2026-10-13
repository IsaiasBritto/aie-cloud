# Aula 1 — Fundamentos & Estratégia de Cloud + IaC

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Explicar o que é cloud computing e os modelos de serviço (IaaS, PaaS, SaaS, FaaS).
- Comparar as três grandes nuvens (AWS, Azure, GCP) e suas equivalências.
- Discutir estratégia de cloud: escalabilidade horizontal vs vertical, balanceamento de carga, alta disponibilidade, os 6 Rs de migração.
- Provisionar recursos na AWS de três formas: console, CLI (`aws`) e IaC (Terraform/CloudFormation).
- Aplicar boas práticas iniciais de segurança (IAM e princípio do menor privilégio).
- Aplicar idempotência e ciclo `init → plan → apply → destroy` do Terraform.

---

## Conexão com o Quantum Commerce

Nesta aula você é apresentado ao **case Quantum Commerce** e propõe, em grupo, uma **arquitetura cloud de alto nível** que será construída ao longo das 6 aulas. O `main.tf` que você cria hoje é o embrião da infra QC — nas aulas seguintes ele ganha storage, bancos, funções, serviços cognitivos e MLOps.

Veja [quantum-commerce/](../../quantum-commerce/) para o briefing do case.

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [pre-aula.md](pre-aula.md) | **Antes da aula** — checklist de 15-30 min |
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — roteiro das 6 atividades de laboratório |
| [lab/terraform/](lab/terraform/) | Código Terraform pronto da Atividade 5 |
| [lab/cloudformation/](lab/cloudformation/) | A mesma VM em CloudFormation (comparativo) |
| [lab/install_terraform.sh](lab/install_terraform.sh) | Instala o Terraform no `$HOME` do CloudShell |
| [exercicios.md](exercicios.md) | Após a aula — exercícios em 3 níveis (🟢/🟡/🔴) que compõem a entrega de grupo |
| [pos-aula-git.md](pos-aula-git.md) | Após a aula — configuração do trabalho em grupo (repo privado + ZIP para o Portal FIAP) |

## Entrega de grupo

Esta aula gera a **1ª entrega de grupo** (10% da nota): instruções em [entregas/entrega-01/](../../entregas/entrega-01/). Rubrica única em [entregas/rubrica.md](../../entregas/rubrica.md).

---

## Pré-requisitos

Faça o [SETUP.md](../../SETUP.md) e o [pre-aula.md](pre-aula.md) antes da aula:

- [ ] Convite do AWS Academy aceito e Learner Lab iniciado (bolinha verde)
- [ ] AWS CloudShell aberto em `us-east-1`
- [ ] Repositório clonado no CloudShell
- [ ] `aws`, `python3`, `git` respondendo no CloudShell (o Terraform é instalado na Atividade 5)
