"""O laço do agente — o que o Deva faria sozinho, aqui simulado passo a passo.

Este arquivo existe por um motivo pedagógico: em sala, **antes** de conectar o agente
real do Foundry, a turma precisa ver o ciclo rodando e entender que ele é simples.
Cinco passos, em laço:

    1. ler a memória aprovada
    2. perguntar à fila o que há para fazer
    3. avançar cada documento que é dele
    4. parar no que não é dele (exceção fica esperando gente)
    5. propor memória quando aprender algo — e NÃO aprovar nada

O que este arquivo **não** faz: chamar modelo. A decisão aqui é uma regra fixa, para o
foco ficar no ciclo. Quando o agente do Foundry entra no lugar dele, as chamadas HTTP
são exatamente as mesmas — muda só quem decide.

    python gatilho/ciclo_do_agente.py --uma-volta
    python gatilho/ciclo_do_agente.py --intervalo 10
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import requests

API = os.getenv("DEVA_API", "http://localhost:8000").rstrip("/")

LIMITE_DE_REFEICAO = 90.00     # POL-REF-004
LIMITE_DE_REVISAO = 5000.00    # AGENTS.md §6


def _get(caminho: str):
    return requests.get(f"{API}{caminho}", timeout=15).json()


def _post(caminho: str, corpo: dict):
    return requests.post(f"{API}{caminho}", json=corpo, timeout=20)


def passo_1_ler_memoria() -> list[str]:
    memoria = _get("/memoria")
    regras = [linha["texto"] for linha in memoria["linhas"]]
    print(f"  memória: {len(regras)} regra(s) aprovada(s)")
    return regras


def passo_2_olhar_a_fila() -> dict:
    resumo = _get("/fila")
    print(f"  fila: {len(resumo['aguardando_o_agente'])} comigo, "
          f"{len(resumo['aguardando_humano'])} com gente, "
          f"{resumo['propostas_pendentes']} proposta(s) pendente(s)")
    return resumo


def passo_3_avancar(identificador: str, regras: list[str]) -> None:
    documento = _get(f"/fila/documentos/{identificador}")
    estado = documento["estado"]

    if estado == "recebido":
        # Aqui, no agente real, entra o analisador de documentos.
        _mover(identificador, {"estado": "extraido", "confianca": "alta"})

    elif estado == "extraido":
        if _e_duplicado(documento):
            _mover(identificador, {
                "estado": "duplicado",
                "justificativa": "Mesmo fornecedor, mesmo valor e mesmo mês de um "
                                 "documento já processado neste lote."})
        else:
            _mover(identificador, {"estado": "auditado", "regra_aplicada": "POL-REF-004"})

    elif estado == "auditado":
        valor = documento.get("valor_total") or 0.0
        if valor > LIMITE_DE_REVISAO:
            _mover(identificador, {
                "estado": "excecao", "confianca": "alta",
                "justificativa": f"Valor de R$ {valor:,.2f} acima do teto de revisão "
                                 f"obrigatória de R$ {LIMITE_DE_REVISAO:,.2f}."})
        elif valor > LIMITE_DE_REFEICAO and _parece_refeicao(documento, regras):
            _mover(identificador, {
                "estado": "excecao", "categoria": "refeicao", "confianca": "alta",
                "justificativa": f"Refeição de R$ {valor:,.2f} excede o limite diário de "
                                 f"R$ {LIMITE_DE_REFEICAO:,.2f} (POL-REF-004). Se houve "
                                 f"jantar de equipe, informe os participantes."})
        else:
            _mover(identificador, {"estado": "conforme", "confianca": "alta",
                                   "justificativa": "Dentro dos limites da política."})


def _mover(identificador: str, corpo: dict) -> None:
    resposta = _post(f"/fila/documentos/{identificador}/estado", corpo)
    if resposta.status_code == 200:
        print(f"    {identificador} → {corpo['estado']}")
    else:
        dados = resposta.json()
        print(f"    ✗ {identificador}: {dados.get('mensagem')}")
        if dados.get("como_resolver"):
            print(f"      {dados['como_resolver']}")


def _e_duplicado(documento: dict) -> bool:
    if not documento.get("valor_total") or not documento.get("fornecedor"):
        return False
    for outro in _get("/fila/documentos"):
        if outro["identificador"] == documento["identificador"]:
            continue
        if outro["estado"] in {"duplicado", "ilegivel"}:
            continue
        if (outro.get("fornecedor") == documento["fornecedor"]
                and outro.get("valor_total") == documento["valor_total"]
                and outro["recebido_em"] < documento["recebido_em"]):
            return True
    return False


def _parece_refeicao(documento: dict, regras: list[str]) -> bool:
    nome = (documento.get("arquivo") or "").lower()
    fornecedor = (documento.get("fornecedor") or "").lower()
    pistas = ("restaurante", "trattoria", "refeic", "lanche", "padaria", "bar ")
    return any(p in nome or p in fornecedor for p in pistas)


def passo_5_propor(texto: str, evidencia: str, secao: str = "classificacao") -> None:
    """O agente propõe. Repare no que ele NÃO chama: /aprovar."""
    resposta = _post("/memoria/proposta",
                     {"secao": secao, "texto": texto, "evidencia": evidencia})
    if resposta.status_code == 201:
        print(f"  proposta registrada: {resposta.json()['identificador']} "
              f"(aguardando auditor)")
    else:
        dados = resposta.json()
        print(f"  proposta recusada: {dados.get('mensagem')}")
        if dados.get("como_resolver"):
            print(f"    {dados['como_resolver']}")


def uma_volta(propor_exemplo: bool = False) -> int:
    print(f"[{time.strftime('%H:%M:%S')}] volta do agente")
    regras = passo_1_ler_memoria()
    resumo = passo_2_olhar_a_fila()

    for identificador in resumo["aguardando_o_agente"]:
        passo_3_avancar(identificador, regras)

    if resumo["aguardando_humano"]:
        print(f"  parei em {len(resumo['aguardando_humano'])} documento(s): "
              f"não é comigo. Quem decide é o auditor, na tela.")

    if propor_exemplo:
        passo_5_propor(
            texto="Estacionamento em aeroporto entra como viagem aérea, não como "
                  "estacionamento e pedágio — a XPTO consolida custo de viagem por evento.",
            evidencia="recibo_0412_trattoria.pdf; correção do auditor na conversa de hoje")

    return len(resumo["aguardando_o_agente"])


def principal() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--uma-volta", action="store_true")
    analisador.add_argument("--intervalo", type=int, default=8)
    analisador.add_argument("--propor", action="store_true",
                            help="registra uma proposta de memória de exemplo")
    argumentos = analisador.parse_args()

    try:
        if argumentos.uma_volta:
            uma_volta(argumentos.propor)
            return 0
        print("Laço do agente. Ctrl+C para parar.\n")
        primeira = True
        while True:
            uma_volta(argumentos.propor and primeira)
            primeira = False
            time.sleep(argumentos.intervalo)
    except KeyboardInterrupt:
        print("\nParei.")
    except requests.RequestException as erro:
        print(f"Não consegui falar com {API}: {erro}")
        print("Como resolver: suba a API com 'uvicorn api.principal:app --reload'.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(principal())
