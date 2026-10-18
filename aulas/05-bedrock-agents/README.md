# Aula 5 — Criando Agentes com Amazon Bedrock

O mesmo agente em degraus: do laço escrito à mão, na sua máquina, até o container
observado e custeado na AWS — e um laboratório de serviço cognitivo com LGPD no centro.

> ⚠️ **O AWS Academy Learner Lab não libera o Bedrock.** Por isso a aula tem dois
> trilhos: o **aluno** roda tudo com a OpenAI (local) e com o Rekognition (Lab), e a
> parte com Bedrock é **demonstração do professor**, numa conta comum.

| Pasta | O que é | Onde roda | Bedrock? |
|---|---|---|---|
| [agentebase/](agentebase/) | O esqueleto mínimo de um agente (~200 linhas) | sua máquina | não (OpenAI) |
| [01-agente-Eva-local/](01-agente-Eva-local/) | A Eva: laço, ferramentas, `agent.md` e `memory.md` | sua máquina | não (OpenAI) |
| [02-agente-Eva-local-to-bedrock/](02-agente-Eva-local-to-bedrock/) | A mesma Eva falando com a API **Converse** | sua máquina | **sim** — demo do professor |
| [03-agente-Eva-aws/](03-agente-Eva-aws/) | A Eva no **ECS Fargate**, com telemetria e FinOps no CloudWatch | AWS | opcional (`provedor = openai` no Learner Lab) |
| [Lab/](Lab/) | **Deva3** — validação biométrica básica com **Rekognition**, S3 e ECS | Learner Lab | não |

## Ordem sugerida

1. `agentebase` → `01-agente-Eva-local`: o que é um agente (o laço) e o que é harness.
2. `02-agente-Eva-local-to-bedrock` (professor): troca de provedor — cliente, credencial
   IAM e formato da conversa. O laço não muda.
3. `Lab/` (turma): serviço cognitivo, confiança × limiar, consentimento e retenção.
4. `03-agente-Eva-aws` (turma, com `provedor = openai`): container, ECR, ECS, segredo no
   Secrets Manager e o custo por turno no CloudWatch — que é a ponte para a Aula 6.

## Custos e limpeza

Tudo que roda no ECS cobra **enquanto está ligado**. Ao fim da aula:

```bash
bash Lab/infra/99-remover-tudo.sh
terraform -chdir=03-agente-Eva-aws/infra/terraform destroy -auto-approve
```
