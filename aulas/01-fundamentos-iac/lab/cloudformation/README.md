# CloudFormation — Aula 1 (comparativo)

A mesma VM do [Terraform](../terraform/) escrita em **CloudFormation**, o IaC nativo da AWS. Serve para o comparativo da Atividade 5 (Passo 6) e para o exercício 3.2.

| | Terraform | CloudFormation |
|---|---|---|
| Linguagem | HCL | YAML/JSON |
| Estado | arquivo `terraform.tfstate` (seu) | stack gerenciada pela AWS |
| Nuvens | multi-cloud | só AWS |
| Apagar | `terraform destroy` | `aws cloudformation delete-stack` |

## Como usar (AWS CloudShell)

```bash
cd ~/aie-cloud/aulas/01-fundamentos-iac/lab/cloudformation

# Validar a sintaxe
aws cloudformation validate-template --template-body file://ec2-lab.yaml

# Criar a stack (usa a key pair vockey do Learner Lab)
aws cloudformation deploy \
  --stack-name aula01-cfn \
  --template-file ec2-lab.yaml

# Ver os outputs (IP e comando SSH)
aws cloudformation describe-stacks --stack-name aula01-cfn \
  --query "Stacks[0].Outputs" --output table

# Apagar tudo ao final
aws cloudformation delete-stack --stack-name aula01-cfn
aws cloudformation wait stack-delete-complete --stack-name aula01-cfn
```

> Para conectar com a `vockey`, baixe o `labsuser.pem` em **AWS Details** na página do Learner Lab, envie ao CloudShell (**Actions → Upload file**) e rode `chmod 400 ~/labsuser.pem`.
