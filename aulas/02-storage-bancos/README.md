# Aula 2 — Armazenamento & Bancos de Dados na Nuvem

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Distinguir os 3 tipos de storage em cloud (Object, File, Block) e escolher o adequado para cada caso de uso.
- Provisionar e configurar um bucket Amazon S3 via Terraform com prefixos, classes de armazenamento e lifecycle.
- Diferenciar bancos de dados relacionais (SQL) e NoSQL (documentos), entendendo quando usar cada um.
- Provisionar um **Amazon RDS for PostgreSQL** via Terraform e popular tabelas via Python.
- Aplicar **AWS Secrets Manager** para eliminar segredos hardcoded (connection strings, senhas).
- Provisionar uma tabela **Amazon DynamoDB on-demand** (e um MongoDB alternativo) e popular via Python.
- Fazer **busca vetorial com pgvector** no RDS — base para o RAG dos agentes da QC.
- Reconhecer quando se usa um banco analítico (Athena/Redshift) — sem aprofundar no lab.
- Integrar os componentes provisionados à arquitetura cloud da Quantum Commerce.

---

## Por que esta aula importa para um AI Engineer

> *"Um agente sem dados é um chatbot genérico. Um agente com os dados certos, na estrutura certa, no banco certo — é uma experiência transformadora."*

Storage e banco **não são detalhes de implementação** — são decisões arquiteturais que definem o que um agente consegue (ou não) fazer.

---

## Conexão com o Quantum Commerce

Nesta aula você define **onde os dados dos agentes da Quantum Commerce vão viver**:

- **Catálogo de produtos** → Amazon RDS PostgreSQL (esquema fixo, joins, integridade)
- **Imagens e arquivos** → Amazon S3 (object storage)
- **Reviews dos clientes** → Amazon DynamoDB (NoSQL, texto livre)
- **Busca por significado** → pgvector no mesmo RDS (base de RAG)
- **Segredos (connection strings)** → AWS Secrets Manager (nunca hardcoded)

A camada de dados desta aula é consumida pelas funções da **Aula 3**, pelos serviços de IA da **Aula 4** e pelos agentes da **Aula 5**.

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — 3 atividades intercaladas |
| [lab/terraform/](lab/terraform/) | Código IaC pronto (8 arquivos `.tf`) |
| [lab/scripts/](lab/scripts/) | Scripts Python (popular RDS, popular DynamoDB/Mongo, indexar com pgvector) |
| [lab/data/produtos.csv](lab/data/produtos.csv) | 20 produtos de exemplo da QC |
| [exercicios.md](exercicios.md) | Após a aula — exercícios em 3 níveis (🟢/🟡/🔴) que compõem a entrega de grupo |

## Entrega de grupo

Esta aula gera a **2ª entrega de grupo** (10% da nota): instruções em [entregas/entrega-02/](../../entregas/entrega-02/). Rubrica única em [entregas/rubrica.md](../../entregas/rubrica.md).

---

## Pré-requisitos

- ✅ Aula 1 concluída — Learner Lab ativo, CloudShell, Terraform instalado no `$HOME`
- ✅ Tarefa pós-Aula 1 entregue — `respostas-aula01.md` no fork via github.dev (ver [pos-aula-git](../01-fundamentos-iac/pos-aula-git.md))
- ✅ Esboço da arquitetura QC do grupo commitado no fork (diagrama Excalidraw/draw.io/foto)

Quem perdeu a Aula 1: faça o [pre-aula](../01-fundamentos-iac/pre-aula.md) e o [pos-aula-git](../01-fundamentos-iac/pos-aula-git.md) da Aula 1 antes desta aula.
