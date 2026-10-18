# Pré-Aula 1 — Checklist Antes do Início

**Tempo estimado:** 15-30 min
**Quando fazer:** pelo menos 1 dia antes da Aula 1

---

## Por que esta pré-aula existe

A Aula 1 tem 4 horas para teoria + 6 laboratórios. Se cada aluno gastar 20 min ativando a conta ao vivo, perdemos horas de tempo coletivo. Você chega na Aula 1 com:

- Convite do AWS Academy aceito
- Learner Lab iniciando sem erro
- CloudShell aberto e funcionando

Quem não fizer a pré-aula consegue acompanhar — a Atividade 1 cobre o acesso como fallback —, mas vai ficar corrido.

> **Política "no install":** tudo é via web — não precisa instalar nada no seu computador.

---

## Checklist

### ☐ 1. Aceitar o convite do AWS Academy (5-10 min)

1. Procure no e-mail FIAP a mensagem **"Course Invitation"** do AWS Academy
2. Clique em **Get Started** e crie a sua senha do AWS Academy (Canvas)
3. Entre em **https://awsacademy.instructure.com** e confirme que o curso **AWS Academy Learner Lab** aparece em **Courses**

**Se falhar:**

- Não recebeu o convite → confira o spam e avise o professor com o seu e-mail FIAP
- Convite expirado → peça um novo ao professor

### ☐ 2. Iniciar o Learner Lab (5 min)

1. No curso: **Modules → Launch AWS Academy Learner Lab**
2. Aceite os termos na primeira vez
3. Clique em **Start Lab** e aguarde a bolinha ao lado de **AWS** ficar **verde**
4. Clique em **AWS**: o console abre numa nova aba
5. Confira a região no canto superior direito: **N. Virginia (us-east-1)**

> O Learner Lab tem um crédito fixo para o semestre e sessões de ~4 h. O consumo aparece no topo da página do lab. **Recurso esquecido ligado consome crédito de todo mundo do seu grupo de estudo** — por isso o hábito de destruir tudo no fim de cada aula.

### ☐ 3. Abrir o AWS CloudShell (5 min)

O CloudShell é o ambiente de **TODOS os labs da disciplina**.

1. No console, clique no ícone **`>_`** na barra superior
2. Aguarde o prompt `[cloudshell-user@ip-... ~]$`

**Teste rápido:**

```bash
# Confirmar autenticação (deve mostrar a LabRole / voclabs)
aws sts get-caller-identity --output table

# Confirmar ferramentas
aws --version
python3 --version
git --version
```

Se todos respondem, **você está pronto para a Aula 1**.

### ☐ 4. (Opcional) Vídeo introdutório — 10 min

- [AWS Cloud Practitioner Essentials](https://explore.skillbuilder.aws/learn/course/external/view/elearning/134/aws-cloud-practitioner-essentials) (AWS Skill Builder, gratuito)

### ☐ 5. (Opcional) Trilha Cloud Practitioner — para quem quer ir além

A trilha gratuita do AWS Skill Builder prepara para a certificação **AWS Certified Cloud Practitioner (CLF-C02)**. Não é obrigatória, mas vale a pena ao longo da disciplina.

---

## O que NÃO fazer antes da aula

- Não instale Terraform, AWS CLI, Python ou VS Code no seu computador
- Não crie instâncias, buckets ou bancos antes da aula (vai bagunçar os exemplos e consumir crédito)
- Não compartilhe sua senha do AWS Academy com colegas

---

## Se a pré-aula travou em algum ponto

1. Tire um print da tela onde travou
2. Mande no canal da turma com: o passo, a mensagem de erro e o print
3. O professor ou um colega responde antes da aula

---

## Confirmação

- ✅ Convite do AWS Academy aceito
- ✅ Learner Lab iniciado (bolinha verde)
- ✅ CloudShell aberto, com `aws`, `python3` e `git` respondendo

**Nos vemos na Aula 1!**
