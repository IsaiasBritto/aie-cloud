---
name: diagnosticar-erro-de-deteccao
description: Diagnostica por que uma requisição ao endpoint de detecção do Deva3 falhou ou não retornou nenhuma caixa, seguindo a ordem que resolve mais rápido em sala de aula.
---

# Diagnosticar erro de detecção

## Quando usar

Quando alguém disser "não funcionou": erro HTTP, tela em branco, nenhuma caixa
desenhada ou confiança estranha.

## Pré-requisitos

- A URL da API.
- O corpo do erro (a API sempre devolve `erro`, `mensagem`, `detalhe` e `como_resolver`).
- Idealmente, a foto que causou o problema.

## Passos — nesta ordem, que é a que resolve mais rápido

1. **Olhe a saúde antes de olhar o código.**
   ```bash
   curl -s $URL_API/saude | jq
   ```
   - `modos_disponiveis` vazio → falta `VISAO_ENDPOINT`/`VISAO_CHAVE`.
   - `situacao: degradado` → a API subiu sem serviço configurado.

2. **Leia o campo `como_resolver` da resposta.** Ele existe justamente para isso e
   resolve a maioria dos casos sem abrir log.

3. **Classifique pelo código HTTP:**

   | Código | Quase sempre é | Ação |
   |---|---|---|
   | 400 | Arquivo não é imagem, ou tipo não aceito | Reenviar em JPEG/PNG |
   | 413 | Foto acima do limite | Reduzir resolução ou ajustar `TAMANHO_MAXIMO_MB` |
   | 401 | Chave de outro recurso | Recopiar em Chaves e Ponto de Extremidade |
   | 403 no modo `rostos` | Acesso Limitado do Face | Usar `?modo=pessoas` |
   | 404 | Endpoint com barra no fim ou host errado | Corrigir `VISAO_ENDPOINT` |
   | 429 | Cota do F0 estourada (20 req/min) | Esperar 1 minuto; combinar rodadas |
   | 502 | A API não conseguiu falar com a Azure | Ver `detalhe`; checar saída de rede |
   | 503 | Serviço não configurado | Ver passo 1 |

4. **Se o HTTP foi 200 mas veio zero detecção**, isso **não é erro**. Verifique, nesta
   ordem: a pessoa aparece inteira? o rosto está visível? a foto está muito escura ou
   muito pequena? Peça uma segunda foto antes de mexer em qualquer coisa.

5. **Se veio detecção mas todas abaixo do limiar**, o problema é a régua, não o modelo.
   Mostre o campo `limiar_confianca` no payload e discuta o valor — é conteúdo de aula,
   não defeito.

6. **Só agora abra o log do container:**
   ```bash
   az containerapp logs show -n ca-deva3-api -g rg-aula-05 --tail 100
   ```

7. **Reproduza fora da interface**, para separar frontend de backend:
   ```bash
   curl -s -X POST "$URL_API/detectar?modo=pessoas" \
        -F "imagem=@foto.jpg" | jq
   ```
   Funcionou no curl e não na tela → o problema é a interface (`API_URL`, CORS).

## Verificação antes de dizer que terminou

- [ ] A causa foi nomeada, não adivinhada
- [ ] A correção foi testada com a mesma foto que falhou
- [ ] Se for armadilha nova, foi registrada em `MEMORY.md` com origem e data

## Armadilhas

- Trocar a chave achando que é 401 quando na verdade é 404 por barra no endpoint.
- Mexer no código antes de olhar `/saude`.
- Tratar "nenhuma detecção" como defeito. Não é.
