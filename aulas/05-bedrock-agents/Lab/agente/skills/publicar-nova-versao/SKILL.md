---
name: publicar-nova-versao
description: Publica uma nova versão do Deva3 construindo as imagens da API e da interface, enviando ao Amazon ECR e atualizando a tarefa do serviço ECS Fargate deva3.
---

# Publicar nova versão do Deva3

## Quando usar

Quando o código já passou nos testes e precisa ir para o ambiente da aula. Não use
para experimentar: para experimentar existe `docker compose up`.

## Pré-requisitos

- Ambiente provisionado (skill `provisionar-ambiente-da-aula`).
- CloudShell com a credencial da sessão (`aws sts get-caller-identity`).
- `python -m pytest` verde.
- Uma etiqueta de versão decidida: `v1`, `v2`… nunca `latest`.

## Passos

1. **Confirmar que dá para publicar.**
   ```bash
   python -m pytest
   aws sts get-caller-identity --query Arn --output text
   ```
   Testes vermelhos ou conta errada → pare aqui.

2. **Pedir confirmação ao professor.** Publicar altera o ambiente da aula. O
   `AGENTS.md` §6 proíbe fazer isso sozinho. Diga qual etiqueta será publicada e espere
   o "pode ir".

3. **Construir e enviar as imagens** (o CloudShell tem Docker):
   ```bash
   export VERSAO=v2
   bash infra/02-publicar-imagens.sh
   ```

4. **Implantar** — atualiza a task definition, força o deploy e espera estabilizar:
   ```bash
   bash infra/03-implantar-apps.sh
   ```

5. **Verificar de fora**, como o aluno vai ver (o IP é o que o script imprimiu):
   ```bash
   curl -s http://$IP:8000/saude | jq
   ```

## Verificação antes de dizer que terminou

- [ ] `GET /saude` responde `200` e lista os modos `pessoas` e `rostos`
- [ ] A interface abre e o seletor de modo aparece preenchido
- [ ] Uma foto de teste retorna caixa e confiança
- [ ] Nenhuma credencial apareceu em log ou no terminal
- [ ] A etiqueta publicada foi anotada em `MEMORY.md` com a data

## Saída

Duas URLs públicas (interface e API) e a etiqueta publicada.

## Armadilhas

- Publicar `latest`: ninguém consegue voltar atrás depois. Sempre `vN`.
- Reenviar a mesma etiqueta e não forçar o deploy: o ECS segue com a imagem antiga.
  O `03-implantar-apps.sh` já força — não pule o script.
- O IP muda a cada implantação: atualize o slide.
