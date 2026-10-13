# Manual 1 — O Deva3 no console da AWS, tela a tela

> Duas metades. **Antes do código:** experimente o Rekognition direto no console e na
> CLI — você vê o JSON cru que a API do Deva3 vai traduzir. **Depois do
> `03-implantar-apps.sh`:** percorra no console cada peça que o Terraform criou, na
> ordem das setas do [diagrama de arquitetura](imagens/02-arquitetura.png).
>
> Por que não provisionar clicando? Dá, mas no ECS o caminho por clique tem dezenas de
> campos que não ensinam nada, e o push das imagens precisa da CLI de qualquer jeito.
> Provisione com o [Manual 2](02-manual-script.md) e use este para **entender** e para
> **investigar**.

---

## Passo zero — Learner Lab ligado

AWS Academy → **Learner Lab** → **Start Lab** → bolinha **verde** → **AWS**.
Região no canto superior direito: **N. Virginia (us-east-1)**.

> O crédito do Learner Lab é o orçamento — Budgets e Cost Explorer não são liberados.
> O que mais consome neste laboratório é a **tarefa Fargate ligada**. Apague no fim.

---

## Parte A · Antes do código: o Rekognition cru

### A.1 — No console

**Amazon Rekognition** → menu à esquerda → **Label detection** (demo).
Envie uma foto com pessoas. Observe:

- a lista de rótulos (`Person`, `Human`, `Face`, roupas, objetos...) com confiança;
- as **caixas** desenhadas só para rótulos com *instâncias* — `Person` é um deles;
- **Response** (embaixo): o JSON. Procure `"Name": "Person"` → `Instances` →
  `BoundingBox`. Os números estão entre **0 e 1** — é proporção da imagem, não pixel.

Agora **Facial analysis** com a mesma foto: uma caixa por rosto, `Confidence` perto de
99, e uma lista de atributos (idade estimada, emoções, óculos...).

> 💬 **Pare a aula aqui.** O console mostra idade e emoção. O Deva3 **não** pede esses
> atributos (`Attributes=["DEFAULT"]`) e o `AGENTS.md` proíbe inferir idade, gênero
> ou emoção. A API oferece; a decisão de não usar é de projeto — e é ela que a LGPD
> cobra.

### A.2 — Na CLI (CloudShell)

Faça upload de uma foto no CloudShell (**Actions → Upload file**) e:

```bash
aws rekognition detect-labels \
  --image-bytes fileb://foto.jpg \
  --features GENERAL_LABELS \
  --settings '{"GeneralLabels":{"LabelInclusionFilters":["Person"]}}' \
  --min-confidence 50 \
  --query 'Labels[].Instances[].{caixa: BoundingBox, confianca: Confidence}'

aws rekognition detect-faces --image-bytes fileb://foto.jpg \
  --query 'FaceDetails[].{caixa: BoundingBox, confianca: Confidence}'
```

É **exatamente** a chamada que `ServicoPessoasRekognition` e `ServicoRostosRekognition`
fazem — só que pelo boto3. Guarde a saída: no fim da aula, compare com o JSON do Deva3
para a mesma foto e confira as duas conversões (proporção → pixel, 0–100 → 0–1).

> A foto ficou no `$HOME` do CloudShell. Apague: `rm foto.jpg`.

---

## Parte B · Depois do deploy: o que o Terraform criou

### B.0 — As tags

**Resource Groups & Tag Editor** → **Tag Editor** → região `us-east-1`, *All supported
resource types*, tag `projeto` = `deva3` → **Search resources**.

Tudo do laboratório aparece aqui, com a tag `dado-pessoal = biometrico`. Essa tag é o
começo de um inventário de dados pessoais: quem audita LGPD pergunta "onde vocês
guardam biometria?", e a resposta é uma busca.

### B.1 — S3: o bucket (seta 7)

**S3** → `deva3-<sufixo>-deteccoes`:

| Aba | O que conferir | Por quê |
|---|---|---|
| **Permissions → Block public access** | tudo *On* | imagem de rosto não pode ter link público |
| **Properties → Default encryption** | SSE-S3 | criptografia em repouso |
| **Management → Lifecycle rules** | `lgpd-retencao`: expira `deteccoes/` em 7 dias | retenção que se cumpre sozinha |
| **Objects** | `deteccoes/AAAA/MM/DD/<id>/` | analise uma foto **sem** e outra **com** consentimento e compare as pastas |

### B.2 — ECR: as imagens (setas 2 e 3)

**ECR** → *Repositories* → `deva3-<sufixo>-api` e `-web` → etiqueta `v1`.
Clique na imagem → **Vulnerabilities**: o *scan on push* já rodou.

### B.3 — ECS: a tarefa (setas 4 e 5)

**ECS** → *Clusters* → `deva3-<sufixo>-cluster` → *Services* → `deva3` → *Tasks* → a
tarefa RUNNING.

- **Containers:** `api` (HEALTHY) e `web`. A `web` só subiu depois que a `api` ficou
  saudável — `dependsOn` na task definition.
- **Configuration → Public IP:** o endereço do laboratório.
- **Logs:** filtre por container. Os `print` do `ciclo_de_vida` da API aparecem aqui:
  `[Deva3] Região: us-east-1`, `Modos disponíveis: ['pessoas', 'rostos']`.

*Task definitions* → `deva3-<sufixo>-app` → **JSON**. Procure:

| Campo | O que dizer em aula |
|---|---|
| `taskRoleArn` | a identidade do **código**: é ela que assina o `detect_labels` e o `put_object` |
| `executionRoleArn` | a identidade do **ECS**: puxa a imagem e escreve log |
| `environment` da `api` | bucket, limiar, região — **nenhuma chave** |
| `environment` da `web` | `API_URL=http://localhost:8000`: mesma tarefa, mesma placa de rede |
| `healthCheck` da `api` | o `GET /saude` que libera a `web` |

### B.4 — Security group (seta 4)

**EC2** → *Security groups* → `deva3-<sufixo>-web`: 8501 (interface) e 8000 (API).
Fora da aula, restrinja `cidr_acesso` ao seu IP — qualquer um com o endereço manda foto
e gasta o seu crédito.

### B.5 — IAM: a LabRole (seta 6)

**IAM** → *Roles* → `LabRole`. É uma role de laboratório, permissiva de propósito. Numa
conta de verdade, a task role do Deva3 teria só `rekognition:DetectLabels`,
`rekognition:DetectFaces` e `s3:PutObject` no prefixo `deteccoes/` do bucket. Escreva
essa política como exercício.

### B.6 — O checkpoint da aula

Abra `http://<IP>:8501`, envie a mesma foto da Parte A e compare:

1. a caixa em pixels do Deva3 × a `BoundingBox` em proporção da CLI;
2. a confiança 0–1 × a `Confidence` 0–100;
3. o que mudou ao subir o `LIMIAR_CONFIANCA` (no `terraform apply -var limiar_confianca=0.95`).

---

## Apagar tudo

```bash
bash ~/aie-cloud/aulas/05-bedrock-agents/Lab/infra/99-remover-tudo.sh
```

Depois, repita a busca do **Tag Editor** (B.0): ela tem que voltar vazia.

---

## Anexo — Erros mais comuns nesta trilha

| Sintoma | Onde | Causa |
|---|---|---|
| a demo do Rekognition não carrega a foto | console | formato não é JPEG/PNG, ou passa de 5 MB |
| `InvalidImageFormatException` na CLI | A.2 | idem — o Rekognition só lê JPEG e PNG |
| tarefa em `PENDING` → `STOPPED` | B.3 | abra a tarefa parada → *Stopped reason* |
| `web` nunca sobe | B.3 | a `api` não ficou HEALTHY — logs do container `api` |
| bucket não apaga no console | B.1 | tem objetos; use o script (o Terraform tem `force_destroy`) |
