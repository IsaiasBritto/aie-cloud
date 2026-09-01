"""Gera a especificação OpenAPI que o agente do Foundry recebe.

O ponto deste arquivo é uma frase: **o agente não vê o que ele não pode fazer.**

A API tem 14 operações. O agente recebe 5. As rotas de aprovação simplesmente não existem
na especificação que ele carrega — não estão escondidas, não estão bloqueadas por
mensagem: não estão lá. Um agente não consegue chamar uma operação que ele não conhece.

    python gerar_openapi_do_agente.py
    # escreve agente/openapi-agente.json
"""
from __future__ import annotations

import json
from pathlib import Path

from api.principal import app

#: As únicas cinco operações que o Deva pode executar.
PERMITIDAS = {
    ("/memoria", "get"),
    ("/fila", "get"),
    ("/fila/documentos/{identificador}", "get"),
    ("/fila/documentos/{identificador}/estado", "post"),
    ("/memoria/proposta", "post"),
}

#: Se qualquer uma destas aparecer no arquivo final, o projeto está quebrado.
PROIBIDAS = [
    "/memoria/propostas/{identificador}/aprovar",
    "/memoria/propostas/{identificador}/descartar",
    "/fila/documentos/{identificador}/liberar",
]

DESTINO = Path("agente/openapi-agente.json")


def gerar(url_do_servico: str = "https://SUA-URL/") -> dict:
    completa = app.openapi()

    caminhos: dict[str, dict] = {}
    for caminho, operacoes in completa["paths"].items():
        mantidas = {metodo: corpo for metodo, corpo in operacoes.items()
                    if (caminho, metodo) in PERMITIDAS}
        if mantidas:
            caminhos[caminho] = mantidas

    enxuta = {
        "openapi": completa.get("openapi", "3.1.0"),
        "info": {
            "title": "Serviço de Continuidade do Deva",
            "description": (
                "Memória e fila do agente Deva. O agente LÊ a memória, LÊ a fila, "
                "AVANÇA documentos e PROPÕE regras novas. Aprovar propostas e liberar "
                "exceções são operações de auditor humano e não fazem parte desta "
                "especificação de propósito."),
            "version": completa["info"]["version"],
        },
        "servers": [{"url": url_do_servico.rstrip("/")}],
        "paths": caminhos,
        "components": {"schemas": completa.get("components", {}).get("schemas", {})},
    }

    texto = json.dumps(enxuta, ensure_ascii=False, indent=2)
    for proibida in PROIBIDAS:
        assert proibida not in texto, f"rota proibida vazou para a especificação: {proibida}"
    assert "X-Auditor" not in texto, "o cabeçalho de auditor não pode aparecer aqui"
    return enxuta


def main() -> None:
    especificacao = gerar()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(especificacao, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    total = sum(len(v) for v in especificacao["paths"].values())
    print(f"{DESTINO} escrito com {total} operação(ões):")
    for caminho, operacoes in especificacao["paths"].items():
        for metodo in operacoes:
            print(f"  {metodo.upper():5} {caminho}")
    print("\nTroque 'https://SUA-URL/' pela URL do seu Container App antes de colar no "
          "portal do Foundry (Ferramentas → Personalizado → Ferramenta OpenAPI).")


if __name__ == "__main__":
    main()
