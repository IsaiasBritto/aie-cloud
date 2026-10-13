# Pós-Aula 1 — Git, GitHub e Entrega via ZIP no Portal FIAP

**Tempo estimado:** ~30 min (após concluir o curso pré-requisito)
**Quando fazer:** Entre a Aula 1 e a Aula 2 (até 1 dia antes da Aula 2)

---

## Pré-requisito obrigatório — Curso Alura

Antes desta apostila, **conclua o curso gratuito da Alura**:

📚 **[Git e GitHub: compartilhando e colaborando em projetos](https://www.alura.com.br/curso-online-git-github-compartilhando-colaborando-projetos)**

- Curso gravado, gratuito para alunos do MBA
- ~8 horas de conteúdo, mas você pode acelerar (1.5x ou 2x se já conhece o básico)
- Cobre: conceitos de Git, GitHub, branches, pull requests, colaboração em equipe
- **Você só precisa fazer esta apostila depois de concluir o curso** — caso contrário vai patinar nas seções de comandos

---

## Por que esta apostila existe

O curso da Alura cobre os fundamentos. Esta apostila cobre **o que é específico da disciplina:**

1. Como o **grupo organiza** o repositório do projeto Quantum Commerce
2. Como **gerar o ZIP de entrega** que vai para o Portal FIAP em cada aula
3. Por que **não fazemos fork público** do repositório oficial da disciplina

---

## A estrutura no fluxo da disciplina

```
┌─────────────────────────────────────────────────────────────┐
│  github.com/IsaiasBritto/aie-cloud   (PÚBLICO — só leitura)      │
│  Material oficial: planos, labs, exercícios                  │
│  Você faz "git clone" para baixar o material                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ git clone (leitura)
                            ▼
        ┌──────────────────────────────────────┐
        │  Seu grupo (PRIVADO)                 │
        │  Cada grupo cria UM repo PRIVADO     │
        │  com os 4-5 membros como collaborators│
        │  Aqui vocês trabalham juntos          │
        └──────────────────────────────────────┘
                            │
                            │ git archive (gera ZIP)
                            ▼
        ┌──────────────────────────────────────┐
        │  Portal FIAP                         │
        │  Upload do ZIP em cada entrega       │
        │  (5 entregas durante a disciplina)    │
        └──────────────────────────────────────┘
```

> **Por que não fazer fork público?** Como há vários grupos por turma e várias turmas, fork público permitiria que grupos copiassem as entregas uns dos outros. O Portal FIAP isola as entregas.

---

## Parte 1 — Clonar o material oficial (5 min)

O repositório `aie-cloud` é **público**. Você não precisa fazer fork — só clonar para ter o material localmente no CloudShell.

```bash
# No CloudShell
cd ~
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud
ls
```

Para atualizar quando o professor publicar novos materiais (Aulas 2-6):

```bash
cd ~/aie-cloud
git pull origin main
```

**Não tente commitar no aie-cloud.** Você não tem permissão e nem é o objetivo. Use só para ler.

---

## Parte 2 — Criar o repositório PRIVADO do grupo (10 min)

### Passo 1 — Definir quem cria o repo

Um membro do grupo (geralmente quem tem mais experiência com Git) cria. Pode ser feito direto pelo browser, **sem instalar nada**.

### Passo 2 — Criar no GitHub

1. Acesse https://github.com/new
2. Preencha:
   - **Owner:** sua conta GitHub
   - **Repository name:** `qc-grupo-NN-<turma>` (substitua NN pelo número do grupo e `<turma>` pelo código da sua turma)
   - **Visibility:** ⚠️ **PRIVATE** (importantíssimo!)
   - Marque "Add a README file"
   - Marque "Add .gitignore" → Python
3. Clique em **"Create repository"**

### Passo 3 — Adicionar os outros membros

No repo recém-criado:

1. **Settings** (engrenagem no topo do repo)
2. Menu lateral → **Collaborators**
3. **Add people** → digite o username GitHub de cada colega → Role: **Write** (Maintain se quiser que ajudem na admin)
4. Cada membro recebe e-mail de convite — precisa aceitar

### Passo 4 — Confirmar acesso

Cada membro deve conseguir:

1. Acessar `https://github.com/<criador>/qc-grupo-NN-<turma>`
2. Abrir o editor pelo `github.dev` (apertar `.` no teclado)
3. Fazer um commit de teste editando o README

---

## Parte 3 — Estrutura sugerida do repo do grupo (5 min)

Recomendamos esta estrutura no repo privado:

```
qc-grupo-NN/
├── README.md                          # Apresentação do grupo + arquitetura QC
├── .gitignore                         # Não commitar segredos
├── aula01/
│   ├── entrega-grupo-aula01.md        # Documento principal da entrega
│   ├── terraform/                     # main.tf, variables.tf, outputs.tf
│   └── diagramas/                     # PNG/SVG da arquitetura
├── aula02/
│   ├── entrega-grupo-aula02.md
│   ├── terraform/
│   ├── scripts/
│   └── diagramas/
├── aula03/
│   └── ...
└── docs/
    └── decisoes-tecnicas.md           # Bitácora do grupo (opcional, recomendado)
```

> **Princípio:** **uma pasta por aula**, cada uma fechada em si. Permite zipar a pasta direto na hora da entrega.

---

## Parte 4 — Como gerar o ZIP de entrega (5 min)

### Opção A — Via `git archive` no CloudShell (recomendado)

```bash
# Ir para o repo clonado do grupo
cd ~/qc-grupo-NN

# Atualizar com o que os colegas committaram
git pull origin main

# Gerar ZIP só com a pasta da aula que você está entregando
git archive --format=zip --prefix=qc-grupo-NN-aula01/ -o ~/entrega-grupo-NN-aula01.zip HEAD:aula01

# Confirmar
unzip -l ~/entrega-grupo-NN-aula01.zip
```

Vantagens:

- Inclui só o que está versionado (não vaza segredos do `.gitignore`)
- Inclui só a pasta da aula específica
- Pasta dentro do ZIP tem prefixo claro

### Opção B — `zip` direto no CloudShell

```bash
cd ~/qc-grupo-NN
zip -r ~/entrega-grupo-NN-aula01.zip aula01/ -x "*.tfstate*" "*.pyc" "__pycache__/*"
```

> **Cuidado:** `zip -r aula01/` SEM o `-x` pode incluir `terraform.tfstate` (que tem segredos!) e `__pycache__/`. Por isso preferimos `git archive` ou `zip -x`.

### Baixar o ZIP do CloudShell para o seu computador

No CloudShell: **Actions → Download file** → informe o caminho completo, por exemplo `/home/cloudshell-user/entrega-grupo-NN-aula01.zip`. O arquivo vai para a pasta de downloads do navegador, pronto para o upload no Portal FIAP.

---

## Parte 5 — O que vai dentro do ZIP

Cada `entrega-grupo-NN-aulaXX.zip` deve conter:

```
qc-grupo-NN-aulaXX/
├── entrega-grupo-aulaXX.md       # ⭐ documento principal (cabeçalho + N1 + N2 + N3 + reflexão)
├── README.md                     # Como rodar o que está dentro
├── terraform/                    # Código IaC (se houver na aula)
├── scripts/                      # Python (se houver)
└── diagramas/                    # Imagens (PNG/SVG)
```

**Não inclua:**

- `terraform.tfstate*` (tem segredos)
- `__pycache__/`, `.venv/`, `node_modules/`
- Arquivos `.env` com credenciais
- Imagens binárias gigantes (>5 MB)

Tamanho ideal do ZIP: < 5 MB. Se passar, revise o que está incluindo.

Use o **[template obrigatório](../../entregas/template-entrega-grupo.md)** para o `entrega-grupo-aulaXX.md`. A **[rubrica](../../entregas/rubrica.md)** descreve como cada entrega é avaliada.

---

## Parte 6 — Upload no Portal FIAP

(O processo exato do Portal FIAP será comunicado pelo professor antes da primeira entrega.)

Esperado:

1. Acessar o Portal FIAP → disciplina Cloud & Cognitive Environments
2. Localizar a tarefa "Entrega Aula 01"
3. Upload do `entrega-grupo-NN-aula01.zip`
4. Submeter
5. **Apenas um membro do grupo** faz o upload (combine antes para evitar duplicação)

> **Confira o tamanho do ZIP antes** — Portal FIAP costuma ter limite de ~20 MB por arquivo.

---

## Boas práticas para o trabalho em grupo

### Trabalhar em paralelo sem pisar no pé um do outro

Use **branches** (curso da Alura cobre):

```bash
# Você está fazendo o N1 da Aula 1
git checkout -b feat/aula01-n1
# faz suas mudanças, commita, push
git push origin feat/aula01-n1
# Abre Pull Request no GitHub para revisar antes do merge na main
```

### Identificar autoria nos commits

Cada membro deve ter sua identidade Git configurada (curso Alura):

```bash
git config user.name "Seu Nome Completo"
git config user.email "seu.email@gmail.com"
```

> A rubrica usa principalmente o cabeçalho `Distribuição do trabalho` do `entrega-grupo-aulaXX.md`, mas commits autênticos ajudam o professor a confirmar a divisão real.

### Evitar conflito de merge

- Combine quem mexe em qual arquivo antes da semana
- Faça `git pull` antes de cada sessão de trabalho
- Evite editar o mesmo arquivo simultaneamente — use branches

### O que NÃO commitar

Seu `.gitignore` deve excluir, no mínimo:

```gitignore
# Terraform
*.tfstate
*.tfstate.*
*.tfvars
.terraform/
.terraform.lock.hcl

# Python
__pycache__/
*.pyc
.venv/

# Segredos
.env
*.pem
credentials.json

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
```

---

## Cheat-sheet — Comandos Git mais usados na disciplina

```bash
# Clonar repo do grupo
git clone https://github.com/<criador>/qc-grupo-NN.git

# Ver o que mudou
git status
git diff

# Salvar mudanças
git add aula01/entrega-grupo-aula01.md
git commit -m "feat(aula01): respostas N1 do João"

# Sincronizar com o grupo
git pull origin main
git push origin main

# Trabalhar em branch separada
git checkout -b feat/aula01-arquitetura
# (faz alterações)
git push origin feat/aula01-arquitetura
# Abre Pull Request no GitHub

# Gerar ZIP de entrega
git archive --format=zip --prefix=qc-grupo-NN-aula01/ -o ~/entrega.zip HEAD:aula01

# Ver histórico
git log --oneline --all --graph
```

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| "Permission denied" ao clonar o repo privado | Verifique se o criador adicionou você como collaborator e se você aceitou o convite |
| Conflitos de merge complicados | Curso Alura aborda; em último caso, peça ajuda do professor no chat |
| ZIP ficou > 20 MB | Você incluiu `terraform.tfstate` ou imagens binárias. Limpe com `git rm --cached <arquivo>` |
| GitHub pede 2FA e você não configurou | Use Personal Access Token ou ative 2FA (recomendado em qualquer caso) |
| Esqueci de criar branch e fiz tudo na `main` | Funciona mesmo assim, mas dificulta paralelizar. Da próxima vez, branch |

---

## Confirmação

Ao final, você deve ter:

- ✅ Concluído o curso Alura de Git (pré-requisito)
- ✅ Clone local do `aie-cloud` no CloudShell para consultar o material
- ✅ Repositório **privado** do seu grupo criado no GitHub com todos os membros como collaborators
- ✅ Saber gerar o ZIP da entrega via `git archive`
- ✅ Estrutura de pastas iniciada (`aula01/`)

**Próxima parada:** Resolver os exercícios da Aula 1 ([exercicios.md](exercicios.md)), gerar o ZIP seguindo o [template](../../entregas/template-entrega-grupo.md) e fazer upload no Portal FIAP até 1 dia antes da Aula 2.
