# Guia — Amazon Bedrock para a Eva

Do zero até `python verificar.py` dizer "Tudo certo". Leva uns 15 minutos.

> ⚠️ **Learner Lab:** o AWS Academy Learner Lab **não libera o Bedrock** — nem
> pelo console, nem pela API. Não é falta de permissão sua. Este guia é para
> uma **conta AWS comum** (a do professor, na demonstração, ou a sua, por
> conta própria). Custo da demonstração: centavos de dólar.

---

## 1. Escolher a região e o modelo

Use **us-east-1** (Norte da Virgínia): é onde o catálogo chega primeiro.

Abra o console → **Amazon Bedrock** → **Model catalog**. Para a Eva, qualquer
modelo com **tool use** na API Converse serve. Duas sugestões:

| Modelo | ID para o `.env` | Observação |
| --- | --- | --- |
| Amazon Nova Lite | `us.amazon.nova-lite-v1:0` | Barato; não pede formulário |
| Anthropic Claude Haiku | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 1º uso pede o formulário de caso de uso da Anthropic |

> Os IDs mudam com as versões. A fonte da verdade é a sua conta:
>
> ```bash
> aws bedrock list-inference-profiles --region us-east-1 \
>   --query "inferenceProfileSummaries[].inferenceProfileId" --output table
> ```

### Por que o prefixo `us.`?

É um **perfil de inferência** entre regiões: a AWS distribui a chamada entre
regiões dos EUA para ganhar vazão. Muitos modelos novos **só** aceitam
chamada por perfil — o ID nu (`amazon.nova-lite-v1:0`) devolve
`ValidationException`. Na dúvida, use o perfil.

## 2. Liberar o acesso ao modelo

Hoje os modelos serverless ficam disponíveis sem pedido prévio na maioria das
contas; o que pode aparecer é:

- **Anthropic:** um formulário curto de caso de uso no primeiro uso
  (console → *Model catalog* → o modelo → *Submit use case details*).
- **Modelos do Marketplace:** assinatura no AWS Marketplace — **evite** na
  aula: alguns cobram hospedagem **por hora**, mesmo parados.

Teste no próprio console: **Playgrounds → Chat**, escolha o modelo e mande
"olá". Se respondeu ali, a conta está liberada.

## 3. Credencial na sua máquina

Use um usuário IAM ou o IAM Identity Center — **nunca** a conta root.

```bash
aws configure                    # access key de um usuário IAM de laboratório
# ou
aws configure sso                # IAM Identity Center (recomendado)
aws sso login --profile aula-bedrock
```

Se usar perfil nomeado, descomente `AWS_PROFILE=aula-bedrock` no `.env`.

## 4. Política IAM mínima

A Eva só precisa disto (anexe ao usuário/role que você usa):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EvaInvocaModelos",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/*",
        "arn:aws:bedrock:*:*:inference-profile/*"
      ]
    },
    {
      "Sid": "VerificarListaModelos",
      "Effect": "Allow",
      "Action": ["bedrock:ListFoundationModels", "bedrock:ListInferenceProfiles"],
      "Resource": "*"
    }
  ]
}
```

> Repare: `Converse` e `ConverseStream` são autorizadas pelas ações
> `InvokeModel*`. E o perfil `us.` precisa de permissão no **perfil** e nos
> **modelos de cada região** para onde ele roteia — por isso o `*` na região.

## 5. Testar

```bash
pip install -r requirements.txt
cp .env.example .env
python verificar.py
```

Saída esperada (resumida):

```
=== Identidade ===
[ok]   conta          123456789012
=== Chamada de teste ===
[ok]   resposta       ok
       tokens         9 entrada / 2 saída
=== Ferramentas (tool use) ===
[ok]   tool use       o modelo pediu a ferramenta
```

## 6. Quanto custa e como não esquecer nada ligado

- O Bedrock **serverless** cobra **por token**. Sem chamada, sem cobrança —
  não há nada para desligar no fim da aula.
- A conversa de teste da Eva gasta centésimos de centavo.
- O que **cobra parado**: Provisioned Throughput e modelos do Marketplace com
  endpoint dedicado. Nenhum dos dois é usado aqui.
- O Bedrock **não tem limite rígido de gasto**. O freio imediato é a **cota**
  (tokens e requisições por minuto, em *Service Quotas*); o AWS Budgets avisa,
  mas com horas de atraso.

## 7. CLI pura, sem Python

A mesma chamada da Eva, direto da AWS CLI — bom para provar que o Python não
tem mágica:

```bash
aws bedrock-runtime converse \
  --region us-east-1 \
  --model-id us.amazon.nova-lite-v1:0 \
  --system '[{"text":"Você é a Eva. Responda em português, em uma frase."}]' \
  --messages '[{"role":"user","content":[{"text":"O que é um agente?"}]}]' \
  --inference-config '{"maxTokens":200,"temperature":0.3}' \
  --query '{texto: output.message.content[0].text, tokens: usage}'
```
