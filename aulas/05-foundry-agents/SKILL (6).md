---
name: publicar-nova-versao
description: Publica uma nova versão do Deva3 construindo as imagens da API e da interface no Azure Container Registry e atualizando os dois Container Apps do grupo rg-aula-05.
---

# Publicar nova versão do Deva3

## Quando usar

Quando o código já passou nos testes e precisa ir para o ambiente da aula. Não use
para experimentar: para experimentar existe `docker compose up`.

## Pré-requisitos

- `az login` feito e a assinatura certa selecionada (`az account show`).
- Grupo `rg-aula-05` já provisionado (skill `provisionar-ambiente-da-aula`).
- `python -m pytest` verde.
- Uma etiqueta de versão decidida: `v1`, `v2`… nunca `latest`.

## Passos

1. **Confirmar que dá para publicar.**
   ```bash
   python -m pytest
   az account show --query "{assinatura:name, id:id}" -o table
   ```
   Testes vermelhos ou assinatura errada → pare aqui.

2. **Pedir confirmação ao professor.** Publicar altera o ambiente da aula. O
   `AGENTS.md` §6 proíbe fazer isso sozinho. Diga qual etiqueta será publicada e espere
   o "pode ir".

3. **Construir as imagens no próprio ACR** (não precisa de Docker na sua máquina):
   ```bash
   az acr build --registry $ACR --image deva3-api:$VERSAO --file api/Dockerfile .
   az acr build --registry $ACR --image deva3-web:$VERSAO --file web/Dockerfile .
   ```

4. **Atualizar a API** e esperar a revisão ficar saudável:
   ```bash
   az containerapp update -n ca-deva3-api -g rg-aula-05 \
      --image $ACR.azurecr.io/deva3-api:$VERSAO
   ```

5. **Atualizar a interface**, apontando para a URL pública da API:
   ```bash
   URL_API=$(az containerapp show -n ca-deva3-api -g rg-aula-05 \
             --query properties.configuration.ingress.fqdn -o tsv)
   az containerapp update -n ca-deva3-web -g rg-aula-05 \
      --image $ACR.azurecr.io/deva3-web:$VERSAO \
      --set-env-vars API_URL=https://$URL_API
   ```

6. **Verificar de fora**, como o aluno vai ver:
   ```bash
   curl -s https://$URL_API/saude | jq
   ```

## Verificação antes de dizer que terminou

- [ ] `GET /saude` responde `200` e lista pelo menos o modo `pessoas`
- [ ] A interface abre e o seletor de modo aparece preenchido
- [ ] Uma foto de teste retorna caixa e confiança
- [ ] Nenhuma variável de ambiente com segredo apareceu em log ou no terminal
- [ ] A etiqueta publicada foi anotada em `MEMORY.md` com a data

## Saída

Duas URLs públicas (API e interface) e a etiqueta publicada.

## Armadilhas

- Publicar `latest`: ninguém consegue voltar atrás depois. Sempre `vN`.
- Esquecer de atualizar `API_URL` na interface: a tela sobe e não fala com a API.
- Trocar a imagem sem checar `/saude`: o container pode subir e falhar só na primeira
  requisição, e você descobre em sala.
