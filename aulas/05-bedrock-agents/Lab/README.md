# Deva3 · API de Validação Biométrica Básica

> **FIAP · MBA AI Engineering & Multi-Agents · Cloud & Cognitive Environments · Aula 05**
> Prof. Isaias S. Britto · versão AWS, outubro de 2026

Um backend simples e isolado que recebe uma foto e devolve **as coordenadas das
detecções com a pontuação de confiança** do **Amazon Rekognition** — mais uma
interface web para o aluno enviar a própria foto e ver o resultado na hora.
Roda inteiro no **AWS Academy Learner Lab**.

```
   foto  →  [ Streamlit ]  →  [ FastAPI ]  →  [ Amazon Rekognition ]  →  JSON
                                    │
                                    └────────→  [ Amazon S3 ]  (imagem só com consentimento)
```

> 🗺️ **Comece pelos diagramas.** Contexto, arquitetura e sequência estão em
> [`docs/00-diagramas.md`](docs/00-diagramas.md), com o fonte Mermaid editável em
> `docs/diagramas/`. Eles respondem, em três desenhos, com quem o sistema conversa,
> onde cada pedaço roda e o que acontece quando o aluno clica em "Analisar".

![Diagrama de arquitetura do Deva3](docs/imagens/02-arquitetura.png)

---

## O que ele faz — e o que não faz

**Faz:** recebe a imagem, chama o **Rekognition · DetectLabels** (rótulo `Person`) ou o
**DetectFaces**, converte a caixa de proporção para pixels e a confiança de 0–100 para
0–1, desenha a caixa sobre a foto e guarda o resultado no S3 (a imagem, só com
consentimento).

**Não faz, e isso é decisão de projeto:** não identifica ninguém, não compara rostos,
não guarda template biométrico e não infere idade, gênero ou emoção.

---

## Começar em 3 minutos (local)

```bash
git clone https://github.com/IsaiasBritto/aie-cloud.git
cd aie-cloud/aulas/05-bedrock-agents/Lab
cp .env.exemplo .env
# credencial do Learner Lab: AWS Details → AWS CLI: Show → cole no terminal
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_SESSION_TOKEN=...
docker compose up --build
```

- Interface ......... http://localhost:8501
- API ............... http://localhost:8000
- Documentação ...... http://localhost:8000/docs
- Saúde ............. http://localhost:8000/saude

Sem Docker:

```bash
python -m venv .venv && source .venv/bin/activate
make instalar
make api      # em um terminal
make web      # em outro
```

---

## O endpoint

```http
POST /detectar?modo=pessoas&consentimento=true
Content-Type: multipart/form-data

imagem: <arquivo JPEG/PNG/BMP/WEBP, até 4 MB>
```

Resposta (recortada):

```json
{
  "identificador": "9f2c41ab77de",
  "modo": "pessoas",
  "servico": "Amazon Rekognition · DetectLabels (Person)",
  "dimensoes": { "largura": 1280, "altura": 960 },
  "limiar_confianca": 0.6,
  "total_detectado": 2,
  "total_acima_do_limiar": 1,
  "deteccoes": [
    {
      "indice": 1,
      "caixa": { "x": 412, "y": 96, "largura": 288, "altura": 640 },
      "confianca": 0.947,
      "acima_do_limiar": true,
      "proporcao_da_imagem": 0.15
    }
  ],
  "duracao_ms": 412,
  "imagem_persistida": true,
  "caminho_armazenamento": "s3://deva3-k3x9qa-deteccoes/deteccoes/2026/10/12/9f2c41ab77de",
  "avisos": []
}
```

Erros saem sempre no mesmo formato, com o campo que resolve a dúvida:

```json
{
  "erro": "falha_de_integracao",
  "mensagem": "Amazon Rekognition · DetectLabels (Person) devolveu ExpiredTokenException (HTTP 400).",
  "detalhe": "An error occurred (ExpiredTokenException) ...",
  "como_resolver": "A sessão do Learner Lab expirou (4 h). Copie as credenciais novas de AWS Details."
}
```

### Os dois modos

| | `modo=pessoas` (padrão) | `modo=rostos` |
|---|---|---|
| Chamada | `rekognition.detect_labels` filtrado em `Person` | `rekognition.detect_faces` |
| Precisa de aprovação? | **Não** | **Não** (detecção; *identificação* é outra API) |
| Devolve confiança? | **Sim**, 0–100 → a API divide por 100 | **Sim**, 0–100 → idem |
| Formato da caixa | proporção (0–1) → a API converte para pixels | idem |
| O que a caixa cerca | a pessoa | o rosto |

> Comparação que rende aula: no Azure AI Face, a detecção exigia Acesso Limitado e
> **não devolvia confiança**. No Rekognition, detectar rosto é livre e vem com
> confiança — o que é restrito (e o Deva3 não usa) é **comparar e buscar** rostos.

---

## Estrutura

```
aulas/05-bedrock-agents/Lab/
├── AGENTS.md              A alma do agente (leia primeiro)
├── MEMORY.md              O que já foi aprendido — lido no início de toda sessão
├── api/                   Backend FastAPI
│   ├── principal.py       Rotas: / · /saude · /detectar
│   ├── configuracao.py    Variáveis de ambiente
│   ├── modelos.py         Contrato de dados
│   ├── erros.py           Erros com "como_resolver"
│   ├── servicos/          Uma classe por integração
│   └── testes/            20 testes, sem rede
├── web/aplicacao.py       Interface Streamlit
├── infra/                 Scripts bash + Terraform (S3, ECR, ECS Fargate)
├── agente/                Artefatos do agente
│   └── skills/            Três procedimentos salvos (SKILL.md)
└── docs/
    ├── 00-diagramas.md    Contexto · arquitetura · sequência
    ├── 01-manual-console.md
    ├── 02-manual-script.md
    ├── 03-passo-a-passo-do-zero.md
    ├── diagramas/         Fonte Mermaid (.mmd) + tema FIAP
    └── imagens/           Os PNG gerados
```

Todo identificador que **nós** criamos está em português. Ficam em inglês apenas as
bibliotecas, os campos que a AWS devolve (`BoundingBox`, `FaceDetails`) e os termos
de infra consagrados (Dockerfile, bucket, task definition).

---

## Publicar na AWS (Learner Lab)

Antes de abrir o console, veja os desenhos:

- **Os três diagramas** → [`docs/00-diagramas.md`](docs/00-diagramas.md)

Duas trilhas:

- **Por script (Terraform + Docker, no CloudShell)** → [`docs/02-manual-script.md`](docs/02-manual-script.md)
- **O que foi criado, tela a tela no console** → [`docs/01-manual-console.md`](docs/01-manual-console.md)

Como o projeto foi construído, passo a passo →
[`docs/03-passo-a-passo-do-zero.md`](docs/03-passo-a-passo-do-zero.md)

Resumo da trilha por script (no CloudShell):

```bash
bash infra/01-criar-recursos.sh     # terraform: bucket, ECR, cluster, logs, SG
bash infra/02-publicar-imagens.sh   # docker build + push das duas imagens
bash infra/03-implantar-apps.sh     # serviço ECS (1 tarefa, 2 containers) + IP público
# ... aula ...
bash infra/99-remover-tudo.sh       # terraform destroy
```

### Recursos criados

| Recurso | Nome | Para quê |
|---|---|---|
| Bucket S3 | `deva3-<sufixo>-deteccoes` | Privado, criptografado, expira em 7 dias |
| Repositórios ECR | `deva3-<sufixo>-api` / `-web` | Guardam as duas imagens |
| Cluster ECS | `deva3-<sufixo>-cluster` | Onde a tarefa roda |
| Serviço ECS | `deva3` | 1 tarefa Fargate: container `api` (8000) + `web` (8501) |
| Log group | `/ecs/deva3-<sufixo>` | stdout dos dois containers, 7 dias |
| Security group | `deva3-<sufixo>-web` | Portas 8000 e 8501 |
| Rekognition | — | Nada a criar: API pronta, paga por imagem |

O `<sufixo>` é sorteado pelo Terraform: nome de bucket é único no mundo.

---

## Privacidade — leia antes de subir foto de alguém

Imagem de rosto é **dado pessoal sensível** (LGPD, art. 5º, II — dado biométrico).
Este projeto foi desenhado para ensinar isso, não para contorná-lo:

- a interface pede **consentimento explícito** antes de gravar a imagem;
- sem consentimento, apenas o **JSON do resultado** é gravado;
- `PERSISTIR_IMAGENS=false` desliga a gravação por completo;
- o bucket é **privado** (Block Public Access) e **criptografado**;
- regra de **ciclo de vida** apaga tudo em `deteccoes/` em 7 dias, mesmo que ninguém
  lembre — e o laboratório termina com `terraform destroy`;
- nenhuma foto entra no repositório: o `.gitignore` bloqueia `*.jpg` e `*.png`.

Os termos de serviço do Rekognition deixam claro que, ao processar rosto, **o cliente
é responsável** por avisar e obter consentimento das pessoas na imagem. Quem chama a
API é você — e a responsabilidade vem junto.

---

## Testes

```bash
python -m pytest          # 20 testes, nenhum toca a rede
```

Eles usam payloads no formato da documentação do Rekognition e cobrem a conversão de
proporção para pixels, a escala da confiança, a conversão BMP → PNG, a validação da
imagem, a regra do limiar e o `POST /detectar` de ponta a ponta (com um boto3 falso).

---

## A ideia central da aula

> **Confiança não é acurácia.**

O serviço pode acertar com confiança baixa e errar com confiança alta. Onde colocar o
limiar é uma **decisão de risco** — e quem decide é quem responde pelo processo, não
quem escreve o código.

Por isso o limiar é configurável (`LIMIAR_CONFIANCA`), aparece no payload, aparece na
tela, e a interface pinta em cores diferentes o que está acima e abaixo dele.

---

*Uso exclusivo para fins acadêmicos.*
