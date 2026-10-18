---
name: provisionar-ambiente-da-aula
description: Provisiona do zero o ambiente do Deva3 na AWS (Learner Lab) — bucket S3 com retenção LGPD, repositórios ECR, cluster e serviço ECS Fargate — usando os scripts Terraform de infra/.
---

# Provisionar o ambiente da aula

## Quando usar

Antes da aula, ou quando o ambiente foi apagado e precisa voltar.

⚠️ Esta skill **cria recursos que geram custo** (a tarefa Fargate cobra enquanto está
de pé). O `AGENTS.md` §6 proíbe `terraform apply` sem confirmação humana explícita.
Peça, espere o "pode ir", e só então rode.

## Pré-requisitos

- Learner Lab ligado (bolinha verde) e CloudShell aberto em `us-east-1`.
- `aws sts get-caller-identity` responde (a credencial é a da sessão).
- Terraform no `$HOME`:
  ```bash
  bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh && source ~/.bashrc
  ```

## Passos

1. **Confirmar com o professor.** Diga o que será criado (bucket, 2 ECR, cluster,
   1 tarefa Fargate 0,5 vCPU / 1 GB) e que a tarefa custa ≈ US$ 0,03/h do crédito.

2. **Rodar os scripts na ordem**, que é a mesma da dependência entre recursos:
   ```bash
   cd ~/aie-cloud/aulas/05-bedrock-agents/Lab
   export VERSAO=v1
   bash infra/01-criar-recursos.sh     # terraform: bucket, ECR, cluster, logs, SG
   bash infra/02-publicar-imagens.sh   # docker build + push das duas imagens
   bash infra/03-implantar-apps.sh     # serviço ECS + IP público
   ```

3. **Guardar as URLs** que o script imprime no final. O IP muda a cada implantação.

4. **Testar como o aluno vai testar**, de fora:
   ```bash
   curl -s http://$IP:8000/saude | jq
   ```

5. **Anotar em `MEMORY.md`** a data e a etiqueta publicada.

## Verificação antes de dizer que terminou

- [ ] `terraform -chdir=infra/terraform state list` mostra bucket, 2 ECR, cluster, serviço
- [ ] `GET /saude` responde `200` com `modos_disponiveis` = `["pessoas", "rostos"]`
- [ ] A interface abre em `:8501` e conversa com a API
- [ ] O bucket tem a regra de ciclo de vida `lgpd-retencao`
- [ ] O Tag Editor acha tudo por `projeto = deva3`

## Saída

Ambiente provisionado e duas URLs públicas (interface e API).

## Armadilhas

- Rodar o `03` antes do `02`: a tarefa cai com `CannotPullContainerError`.
- `Error: reading IAM Role (LabRole)`: não é Learner Lab. Passe `-var role_name=...`.
- CloudShell sem espaço no build: `docker system prune -af`.
- Terminar a aula sem `infra/99-remover-tudo.sh`. A tarefa Fargate continua cobrando
  quando o Lab religar.
