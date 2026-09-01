"""O gatilho — o que faz o agente deixar de esperar alguém digitar.

Duas formas de disparar, e a aula mostra as duas:

**A · Event Grid (produção).** O container `entrada` do Blob emite `BlobCreated`; o Event
Grid entrega numa Logic App; a Logic App chama `POST /fila/documentos`. Zero código, zero
sondagem, custo por evento. A definição está em `gatilho/logic-app-eventgrid.json`.

**B · Sondagem (este arquivo).** Um laço que olha a pasta a cada N segundos. É pior em
produção e é **melhor em sala**: roda na máquina do aluno, sem provisionar nada, e deixa
ver o mecanismo. Use `--intervalo 5` e largue um PDF na pasta durante a aula.

    python gatilho/disparador.py --semear          # cria 4 documentos de exemplo
    python gatilho/disparador.py --pasta entrada   # vigia uma pasta de verdade
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests

API = os.getenv("DEVA_API", "http://localhost:8000").rstrip("/")

EXTENSOES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

EXEMPLOS = [
    ("recibo_0412_trattoria.pdf", "Restaurante Trattoria Ltda", 412.00),
    ("nota_1180_hotel_ibis.pdf", "Hotel Íbis Paulista", 389.90),
    ("recibo_0771_transporte.pdf", "Mobilidade Urbana SA", 47.30),
    ("nota_1180_hotel_ibis_copia.pdf", "Hotel Íbis Paulista", 389.90),  # duplicata
]


def registrar(arquivo: str, fornecedor: str | None = None,
              valor: float | None = None) -> str | None:
    """Chama a mesma rota que a Logic App chamaria. O contrato é um só."""
    corpo = {"arquivo": arquivo}
    if fornecedor:
        corpo["fornecedor"] = fornecedor
    if valor is not None:
        corpo["valor_total"] = valor
    try:
        resposta = requests.post(f"{API}/fila/documentos", json=corpo, timeout=15)
    except requests.RequestException as erro:
        print(f"  ✗ não consegui falar com {API}: {erro}")
        print("    Como resolver: suba a API com "
              "'uvicorn api.principal:app --reload' e tente de novo.")
        return None
    if resposta.status_code != 201:
        print(f"  ✗ {arquivo}: HTTP {resposta.status_code} — {resposta.text[:160]}")
        return None
    identificador = resposta.json()["identificador"]
    print(f"  ✓ {arquivo} → {identificador}")
    return identificador


def semear() -> None:
    print(f"Semeando 4 documentos de exemplo em {API} …")
    for arquivo, fornecedor, valor in EXEMPLOS:
        registrar(arquivo, fornecedor, valor)
    print("\nPronto. Abra a tela: a fila tem 4 documentos em 'recebido'.")
    print("O quarto é uma duplicata do segundo — de propósito.")


def vigiar(pasta: Path, intervalo: int) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    print(f"Vigiando {pasta.resolve()} a cada {intervalo}s. Ctrl+C para parar.")
    print("Largue um PDF aí dentro e olhe a tela.\n")
    ja_vistos: set[str] = {p.name for p in pasta.iterdir() if p.is_file()}
    print(f"({len(ja_vistos)} arquivo(s) já existiam e foram ignorados)")
    try:
        while True:
            atuais = {p.name for p in pasta.iterdir()
                      if p.is_file() and p.suffix.lower() in EXTENSOES}
            for novo in sorted(atuais - ja_vistos):
                print(f"[{time.strftime('%H:%M:%S')}] chegou {novo}")
                registrar(novo)
            ja_vistos = atuais
            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("\nParei.")


def principal() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--semear", action="store_true",
                            help="cria 4 documentos de exemplo e sai")
    analisador.add_argument("--pasta", default="entrada",
                            help="pasta a vigiar (padrão: entrada)")
    analisador.add_argument("--intervalo", type=int, default=5,
                            help="segundos entre uma olhada e outra")
    argumentos = analisador.parse_args()

    if argumentos.semear:
        semear()
        return 0
    vigiar(Path(argumentos.pasta), argumentos.intervalo)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
