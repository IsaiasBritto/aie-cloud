# Aula 4 — Serviços de IA da AWS & APIs

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Consumir APIs de IA prontas da AWS: **Amazon Transcribe** (fala → texto em PT-BR), **Amazon Polly** (texto → fala), **Amazon Comprehend** (sentimento + entidades) e **Amazon Rekognition** (rótulos, objetos e texto em imagens).
- Explicar por que, na AWS, esses serviços **não precisam de recurso provisionado**: são APIs da conta, autorizadas por IAM.
- Autenticar uma Lambda nas APIs de IA pela **execution role** (sem chave no código) e ler segredos de terceiros do **Secrets Manager**.
- Decidir entre **API pronta**, **modelo customizado** (Custom Labels, Comprehend Custom) e **LLM** (Amazon Bedrock) para cada caso de uso.
- Construir um **pipeline de IA ponta a ponta**: a Lambda lê áudio/imagem do S3, transcreve/analisa e grava o resultado no MongoDB.

---

## Por que esta aula importa para um AI Engineer

Os agentes da QC precisam **ouvir**, **ler** e **ver** — não só processar texto. As APIs prontas dão essas capacidades em minutos, sem treinar nada. A escolha entre pronta, custom e LLM define **custo, latência e qualidade** da experiência.

---

## Conexão com o Quantum Commerce

Esta aula adiciona **novas tools** à API da QC:

| Tool | Serviço |
|------|---------|
| `/transcrever` | Transcribe — atendimento por voz |
| `/analisar-reviews` | Comprehend — sentimento + entidades das reviews do MongoDB |
| `/analisar-imagem` | Rekognition — rótulos + texto das imagens dos produtos |
| `/tts`, `/stt`, `/visao` | Polly, Transcribe e Rekognition para o front-end |

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — 5 atividades |
| [lab/terraform/](lab/terraform/) | Bucket + Lambda + Function URL + Secrets Manager + MongoDB na EC2 |
| [lab/function/](lab/function/) | Lambda com as rotas de IA (Powertools) |
| [lab/scripts/](lab/scripts/) | `semear_reviews.py` e `gerar_audio_tts.py` (Polly) |
| [lab/app/](lab/app/) | Front-end Streamlit: Lambda × chamada direta |
| [lab/exportar-outputs.sh](lab/exportar-outputs.sh) | `source` para recarregar os outputs num terminal novo |
| [exercicios.md](exercicios.md) | Após a aula — exercícios em 3 níveis |

## Entrega de grupo

Esta aula gera a **4ª entrega de grupo** (10% da nota): instruções em [entregas/entrega-04/](../../entregas/entrega-04/). Rubrica em [entregas/rubrica.md](../../entregas/rubrica.md).

---

## Pré-requisitos

- ✅ Learner Lab iniciado, CloudShell e Terraform no `$HOME`
- ✅ Nenhuma dependência das aulas anteriores — **esta aula é autossuficiente**

> **Amazon Bedrock:** o Learner Lab não libera o Bedrock. Ele aparece aqui como contexto (e nos exercícios de N3); a demonstração com LLM é do professor.
