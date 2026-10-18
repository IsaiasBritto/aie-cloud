"""
Semeia reviews de exemplo no MongoDB da Aula 4.

Uso:  python3 scripts/semear_reviews.py
Variável de ambiente: MONGO_IP (IP público da EC2 do MongoDB)
  export MONGO_IP=$(cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform && terraform output -raw mongodb_public_ip)

⚠ EXERCÍCIO DE SEGURANÇA: este script tem uma falha de propósito. Você consegue
achá-la? Como consertar? (dica: compare com a Lambda, que lê a mesma conexão do
Secrets Manager.)
"""
import os
import sys
import time

MONGO_IP = os.environ.get("MONGO_IP")
if not MONGO_IP:
    print("Exporte MONGO_IP com o IP da EC2:")
    print("  export MONGO_IP=$(cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform && terraform output -raw mongodb_public_ip)")
    sys.exit(1)

try:
    from pymongo import MongoClient, errors
except ImportError:
    print("Instalando pymongo...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pymongo", "-q"])
    from pymongo import MongoClient, errors

URI = f"mongodb://admin:QCadmin2024!@{MONGO_IP}:27017/?authSource=admin"

print(f"Conectando ao MongoDB em {MONGO_IP}:27017...")
for tentativa in range(12):
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✓ MongoDB pronto!")
        break
    except errors.ServerSelectionTimeoutError:
        print(f"  Aguardando MongoDB... (tentativa {tentativa + 1}/12)")
        time.sleep(10)
else:
    print("✗ MongoDB não respondeu após 2 min — a EC2 ainda está subindo os containers?")
    sys.exit(1)

db = client["qc-db"]
reviews_col = db["reviews"]

# Limpar reviews existentes (idempotente)
reviews_col.delete_many({})

reviews = [
    {"id": "r001", "produto": "Notebook Pro X", "texto": "Excelente laptop, a bateria dura mais de 8 horas e o processador é muito rápido.", "estrelas": 5},
    {"id": "r002", "produto": "Fone Bluetooth QC-50", "texto": "Qualidade de som péssima, muito abaixo do esperado. Totalmente decepcionante.", "estrelas": 1},
    {"id": "r003", "produto": "Teclado Mecânico RGB", "texto": "Digitação muito boa mas o preço é elevado para o que oferece.", "estrelas": 3},
    {"id": "r004", "produto": "Mouse Gamer Quantum", "texto": "Perfeito para jogos, resposta imediata e design confortável. Recomendo!", "estrelas": 5},
    {"id": "r005", "produto": "Monitor 4K 27pol", "texto": "Imagem linda mas veio com um pixel morto. Atendimento resolveu rápido.", "estrelas": 4},
    {"id": "r006", "produto": "Cadeira Ergonômica", "texto": "Horrível, completamente desconfortável após 1 hora de uso. Não recomendo de jeito algum.", "estrelas": 1},
    {"id": "r007", "produto": "HD Externo 2TB", "texto": "Velocidade de transferência ótima, funciona perfeitamente no dia a dia.", "estrelas": 5},
    {"id": "r008", "produto": "Webcam Full HD", "texto": "Qualidade de imagem ok para videoconferências, nada excepcional pelo preço.", "estrelas": 3},
    {"id": "r009", "produto": "Impressora Laser", "texto": "Rápida e econômica em toner. Exatamente o que precisava para o escritório.", "estrelas": 4},
    {"id": "r010", "produto": "Caixa Bluetooth QC-Bass", "texto": "Som cheio e potente. Valeu cada centavo. Já é minha segunda compra.", "estrelas": 5},
]

result = reviews_col.insert_many(reviews)
print(f"✓ {len(result.inserted_ids)} reviews inseridas em qc-db.reviews")
print("\nDistribuição de estrelas:")
for stars in range(1, 6):
    count = sum(1 for r in reviews if r["estrelas"] == stars)
    bar = "★" * stars + "☆" * (5 - stars)
    print(f"  {bar}: {count} reviews")

client.close()
print("\n✅ MongoDB pronto para uso!")
print(f"   Mongo Express: http://{MONGO_IP}:8081 (usuário qcadmin, senha QCview2024!)")
