"""
Gera um áudio MP3 em PT-BR com o Amazon Polly (voz neural Camila).

Uso:  python3 scripts/gerar_audio_tts.py
Saída: /tmp/audio-teste.mp3

Sem chave: o boto3 usa a credencial do CloudShell (LabRole). Compare com o
caminho "API key" de outras nuvens — aqui não existe chave para vazar.
"""
import sys

import boto3

TEXTO = (
    "A Quantum Commerce é uma plataforma de e-commerce que opera em doze países. "
    "Nossos agentes de inteligência artificial ajudam clientes a encontrar produtos, "
    "calcular fretes, processar pedidos e responder dúvidas em tempo real. "
    "A nossa missão é tornar o comércio mais humano, inteligente e acessível."
)

polly = boto3.client("polly")

print("Gerando áudio com o Amazon Polly (voz Camila, neural)...")
try:
    resp = polly.synthesize_speech(Text=TEXTO,
                                   VoiceId="Camila", Engine="neural",
                                   OutputFormat="mp3")
except Exception as e:  # noqa: BLE001
    print(f"✗ Erro: {e}")
    sys.exit(1)

output_path = "/tmp/audio-teste.mp3"
with open(output_path, "wb") as f:
    f.write(resp["AudioStream"].read())

print(f"✓ Áudio salvo em {output_path}")
print("Próximo passo: aws s3 cp /tmp/audio-teste.mp3 s3://$DATA_BUCKET/audios/audio-teste.mp3")
