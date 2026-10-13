# Setup — Antes da Aula 1

Este guia leva ~15 minutos. Você **não precisa instalar nada** no seu computador.

---

## 1. Entrar no AWS Academy Learner Lab

A turma usa o **AWS Academy Learner Lab**: uma conta AWS de laboratório, com crédito
próprio e **sem cartão de crédito**.

1. Aceite o convite do **AWS Academy** que chegou no seu e-mail institucional (`@fiap.com.br`).
2. Crie a senha e entre em [awsacademy.instructure.com](https://awsacademy.instructure.com).
3. Abra o curso da disciplina → **Modules** → **Launch AWS Academy Learner Lab**.
4. Clique em **Start Lab** e espere a bolinha ao lado de **AWS** ficar **verde** (1–3 min).
5. Clique em **AWS**: o console abre numa aba nova, já autenticado.

> **Regras do Learner Lab que valem a disciplina inteira:**
>
> - A sessão dura **4 horas**. Ao fim, tudo **para** (instâncias desligam), mas **não é
>   apagado** — e volta a cobrar do crédito quando você religa. Por isso cada lab
>   termina com `terraform destroy`.
> - Use a região **us-east-1 (N. Virginia)**.
> - Não dá para criar IAM roles: usamos a **`LabRole`** e o **`LabInstanceProfile`** que já existem.
> - O crédito consumido aparece na página do Learner Lab — é o seu "budget".

**Não consegue entrar?** Anote o erro e traga para a Aula 1.

---

## 2. Abrir o AWS CloudShell

O CloudShell é o seu **ambiente de trabalho durante toda a disciplina**:

- no console da AWS, ícone **`>_`** na barra superior (ou busque "CloudShell");
- confira a região **us-east-1** no canto superior direito.

Ele já vem com `aws` (CLI v2, autenticada com a sua sessão), `python3`, `pip3`, `git` e
`docker`. O `$HOME` tem **1 GB persistente**: o que você salva lá sobrevive entre
sessões; o resto, não.

O **Terraform** não vem instalado — a Aula 1 instala no seu `$HOME` com um script:

```bash
bash ~/aie-cloud/aulas/01-fundamentos-iac/lab/install_terraform.sh
source ~/.bashrc
terraform -version
```

---

## 3. Clonar este repositório

Dentro do CloudShell:

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git ~/aie-cloud
cd ~/aie-cloud
```

Para editar arquivos: `nano` ou `vim` no próprio CloudShell, ou **Actions → Download
file / Upload file** para trabalhar na sua máquina.

---

## Pronto!

Se você conseguiu:

- [x] Iniciar o Learner Lab (bolinha verde)
- [x] Abrir o CloudShell em us-east-1
- [x] Clonar este repositório

Você está pronto para a **Aula 1**. Nos vemos lá.

---

## Ambientes complementares (usados em aulas específicas)

- **Sua máquina, com Python** — Aula 4 (app Streamlit com microfone) e Aula 5 (a Eva local). Opcional.
- **GitHub** — repositório privado do grupo para as entregas (Aula 1, `pos-aula-git.md`).
- **AWS Pricing Calculator** ([calculator.aws](https://calculator.aws)) — Aula 6, sem login.

Nada além disso precisa ser instalado.
