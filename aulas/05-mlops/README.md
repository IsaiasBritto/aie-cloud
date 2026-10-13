# Aula 5 — MLOps na Nuvem

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Provisionar via Terraform um **bucket S3 versionado** e um **Model Registry** (Model Package Group) do **Amazon SageMaker AI**.
- Treinar um modelo simples rastreando o experimento (**MLflow** local + métricas do Training Job).
- Submeter um **Training Job reproduzível** (mesmo código, container versionado, dado versionado) — a máquina nasce e morre com o job.
- Versionar e **aprovar** o modelo no **Model Registry**.
- Publicar a versão aprovada como **endpoint** (serverless, escala a zero) e consumi-lo.
- Identificar o **nível de maturidade MLOps** (0/1/2) e que automatizações faltam para subir de nível.

> **Importante (perfil dos alunos):** esta disciplina é uma das primeiras do MBA. **Você não precisa saber ML/Python avançado** para fazer os exercícios. O modelo de recomendação é apenas um **veículo didático** para o ciclo MLOps. Modelagem em profundidade é tema da disciplina **AI Foundation and Learning Models**.

---

## Por que esta aula importa para um AI Engineer

Sem MLOps, modelos viram **artefatos em notebooks** que ninguém consegue retreinar, versionar ou auditar. As mesmas ferramentas (Tracking, Registry, Endpoints, Drift Monitoring) seguem relevantes para **LLMOps** — com adaptações (prompt registry, eval framework, RAG quality).

---

## Conexão com o Quantum Commerce

Esta aula entrega o **5º recurso** consumido pelos agentes da QC: um **recomendador de produtos** treinado a partir do catálogo da Aula 2. O modelo é publicado como endpoint do SageMaker e poderia ganhar uma rota `/recomendar` na Lambda da Aula 3 (exercício N2.2).

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — 4 atividades + wrap-up com destroy crítico |
| [lab/terraform/](lab/terraform/) | Bucket versionado + dataset + Model Registry — L₁ |
| [lab/codigo/](lab/codigo/) | `train.py` (roda local **e** no job) + `inference.py` (contrato do endpoint) — L₂/L₃ |
| [lab/scripts/](lab/scripts/) | `submeter_job.py` · `registrar_modelo.py` · `implantar_endpoint.py` · `limpar.py` (boto3) — L₃/L₄ |
| [lab/endpoint/](lab/endpoint/) | Payload de teste e como chamar — L₄ |
| [exercicios.md](exercicios.md) | Após a aula — 3 níveis (N1/N2 conceituais; N3 avançado para perfil ML) |

## Entrega de grupo

Esta aula gera a **5ª e última entrega intermediária** (10% da nota): instruções em [entregas/entrega-05/](../../entregas/entrega-05/). Rubrica em [entregas/rubrica.md](../../entregas/rubrica.md).

A Aula 6 é dedicada ao **trabalho em grupo no projeto integrado final** (FinOps + entrega ZIP **1 semana após a Aula 6**, valendo 50%, **sem apresentação oral**) — ver [entregas/projeto-final/](../../entregas/projeto-final/).

---

## ⚠️ Alerta de custo

O **Training Job** cobra só os minutos em que a máquina existe (~2–4 min de ml.m5.large: centavos). O **endpoint serverless** escala a zero. Se você usar **endpoint de instância** (`--tipo instancia`), a ml.m5.large custa ~US$ 0,115/h **ligada** — apague com `python3 scripts/limpar.py --registro` **antes** do `terraform destroy`.

> O AWS Academy Learner Lab libera o SageMaker AI com a **LabRole** como role de execução e um conjunto limitado de tipos de instância (ml.m5.large funciona para treino e endpoint).

---

## Pré-requisitos

- ✅ Aulas 1-4 concluídas
- ✅ `produtos.csv` da Aula 2 acessível (já está commitado em [`aulas/02-storage-bancos/lab/data/produtos.csv`](../02-storage-bancos/lab/data/produtos.csv) — **não precisa ter a Aula 2 viva**)

> **Sem dependência de Aula 4:** esta aula é independente dos serviços cognitivos. Se você destruiu a Aula 4, segue normal.
