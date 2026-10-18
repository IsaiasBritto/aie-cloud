# QC Cognitive Studio — front-end da Aula 4

Aplicação Streamlit que consome os serviços de IA do lab (Polly, Transcribe e Rekognition) e explora texto → fala, fala → texto, análise de imagem e localização espacial.

O ponto da atividade não é a interface. É a comparação: **cada operação pode ser executada por dois caminhos**, e o app mostra os dois lado a lado.

| | Via Lambda | Direto na AWS |
|---|---|---|
| Credencial no cliente | não existe | access key na barra lateral |
| Quem se autentica | a função, com a LabRole | você, com a access key |
| Se o código vazar | só a URL da função | a credencial vai junto |
| Latência | um salto a mais | um salto a menos |

## Rodar

Na **sua máquina** — não no CloudShell. O navegador só libera o microfone em `localhost` ou HTTPS.

```bash
cd aulas/04-servicos-cognitivos/lab/app
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`.

## Preencher a barra lateral

No CloudShell, com o lab provisionado:

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab
source exportar-outputs.sh
echo "FUNC_URL    : $FUNC_URL"
echo "DATA_BUCKET : $DATA_BUCKET"
```

Só a **Function URL** é obrigatória. As credenciais (Learner Lab → **AWS Details** → **AWS CLI: Show**) e o `DATA_BUCKET` servem apenas ao caminho direto — deixá-los em branco é justamente a demonstração.

## As quatro abas

**🔊 Texto → Fala.** Sintetiza com vozes neurais do Polly (Camila, Vitória, Thiago...). O WAV pode ser baixado e serve de entrada para a próxima aba.

**🎤 Fala → Texto.** Grava do microfone ou aceita upload. O app converte para WAV 16 kHz mono antes de enviar. O Transcribe processa em **lote** (o áudio passa pelo S3): espere alguns segundos.

**🖼️ Visão + Espacial.** Rótulos, texto (OCR) e objetos com caixa, desenhados sobre a imagem original com Pillow. O Rekognition devolve as caixas em **proporção** (0–1); a Lambda e o app convertem para pixels.

**🏛️ Arquitetura.** A tabela comparativa e as perguntas de discussão.

## O que este app deliberadamente não faz

Não guarda credencial em disco, não usa `.env` e não tem "lembrar credenciais". Tudo vive na sessão do navegador e some quando a aba fecha.

## Rotas que ele consome

| Rota | Corpo | Devolve |
|---|---|---|
| `POST /tts` | `{"texto","voz"}` | `audio/wav` |
| `POST /stt?idioma=pt-BR&formato=wav` | bytes do áudio | `{"transcricao"}` |
| `POST /visao` | bytes da imagem | `{"tags","texto","objetos","largura","altura"}` |
