# QC Cognitive Studio — front-end da Aula 4

Aplicação Streamlit que consome os serviços cognitivos provisionados no lab e
explora TTS, STT, análise de imagem e localização espacial.

O ponto da atividade não é a interface. É a comparação: **cada operação pode ser
executada por dois caminhos**, e o app mostra os dois lado a lado.

| | Via Function App | Direto no AI Services |
|---|---|---|
| Chave no cliente | não existe | `AI_KEY` na barra lateral |
| Quem se autentica | Managed Identity da Function | você, com a chave |
| Se o código vazar | só a URL da Function | a chave vai junto |
| Latência | um salto a mais | um salto a menos |

## Rodar

Na **sua máquina** — não no Cloud Shell. O navegador só libera o microfone em
`localhost` ou HTTPS, e o Cloud Shell não oferece nenhum dos dois.

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`.

## Preencher a barra lateral

No Cloud Shell, com o lab provisionado:

```bash
cd ~/qc-grupo-NN/aula04
source exportar-outputs.sh

echo "FUNC_HOSTNAME : $FUNC_HOSTNAME"
echo "AI_ENDPOINT   : $AI_ENDPOINT"
echo "AI_REGION     : $AI_REGION"
echo "AI_KEY        : $(az keyvault secret show --vault-name "$KEY_VAULT_NAME" \
                          --name ai-services-key --query value -o tsv)"
```

Só o **Function App** é obrigatório. `AI_ENDPOINT`, `AI_REGION` e `AI_KEY`
servem exclusivamente ao caminho direto — se você usar só o caminho via
Function, pode deixá-los em branco, e essa é justamente a demonstração.

## As quatro abas

**🔊 Texto → Fala.** Sintetiza com três vozes brasileiras. O áudio toca no
navegador e pode ser baixado — use o WAV gerado aqui para testar o STT, já que
ele sai no formato que o Speech espera.

**🎤 Fala → Texto.** Grava do microfone ou aceita upload.

> O Speech REST aceita **WAV PCM 16 kHz mono**. A gravação do navegador costuma
> sair em WebM/Opus, e o resultado é transcrição vazia com `200 OK` — falha
> silenciosa, não erro. Se acontecer, teste com o WAV da aba anterior para
> separar "meu áudio está no formato errado" de "o serviço não funciona".

**🖼️ Visão + Espacial.** Envia uma imagem e devolve tags, texto por OCR e os
objetos localizados. As bounding boxes são desenhadas sobre a imagem original com
Pillow, e a tabela ao lado mostra as coordenadas em pixels.

> As coordenadas vêm em pixels da imagem **original**. Redimensionar antes de
> desenhar desloca todas as caixas — por isso o desenho acontece no tamanho
> original e o Streamlit escala depois.

**🏛️ Arquitetura.** A tabela comparativa e as perguntas de discussão.

## O que este app deliberadamente não faz

Não guarda a chave em disco, não usa `.env` e não tem "lembrar credenciais".
Tudo vive na sessão do navegador e some quando a aba fecha. Num app de verdade
isso seria inconveniente; aqui é o conteúdo da aula.

## Rotas que ele consome

Adicionadas ao `function/function_app.py` para este app. Recebem o arquivo **no
corpo** da requisição, em vez de um nome de blob — assim o front-end não precisa
de credencial de Storage nenhuma.

| Rota | Corpo | Devolve |
|---|---|---|
| `POST /api/tts` | `{"texto","voz","idioma"}` | `audio/wav` |
| `POST /api/stt?idioma=pt-BR` | bytes do WAV | `{"transcricao"}` |
| `POST /api/visao` | bytes da imagem | `{"tags","texto","objetos","largura","altura"}` |

As rotas antigas (`/api/transcrever?blob=`, `/api/analisar-imagem?blob=`)
continuam existindo e são as usadas nas Atividades 2 e 4.
