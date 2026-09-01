"""Serviço de Continuidade do Deva.

Transforma o Deva de "pergunta e resposta" em agente que trabalha entre as conversas.

Três grupos de rota, com permissões diferentes de propósito:

| Grupo | Quem chama | O que pode |
|---|---|---|
| `/memoria`, `/fila` (leitura) | o agente e a tela | ler |
| `/memoria/proposta`, `/fila/{id}/estado` | o agente | propor e avançar |
| `/memoria/propostas/{id}/aprovar` e `/descartar`, `/fila/{id}/liberar` | **só a pessoa** | decidir |

A terceira linha é o projeto inteiro. O agente nunca recebe o cabeçalho `X-Auditor`, então
não consegue aprovar a própria memória nem liberar a própria exceção — não por educação,
por arquitetura.
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from .configuracao import VERSAO, obter_configuracao
from .erros import AutorizacaoDeAuditorAusente, ErroDoServico
from .modelos import (AtualizacaoDeDocumento, DecisaoSobreProposta, Documento,
                      EntradaDeDocumento, EntradaDeProposta, EstadoDeSaude,
                      EstadoDoDocumento, LinhaDeMemoria, Memoria, PropostaDeMemoria,
                      ResumoDaFila, SituacaoDaProposta)
from .servicos.armazenamento import montar_armazenamento
from .servicos.fila import ServicoDaFila
from .servicos.memoria import ServicoDeMemoria

app = FastAPI(
    title="Serviço de Continuidade do Deva",
    description=("Memória revisável e fila de documentos para o agente Deva. "
                 "O agente lê e propõe; o auditor humano decide."),
    version=VERSAO,
)


def _servicos():
    config = obter_configuracao()
    armazenamento = montar_armazenamento(config)
    return (config,
            ServicoDeMemoria(armazenamento, config.maximo_de_propostas_pendentes),
            ServicoDaFila(armazenamento))


def exigir_auditor(x_auditor: str | None = Header(default=None),
                   x_segredo: str | None = Header(default=None)) -> str:
    """A fronteira. Só passa quem é gente.

    O agente é configurado no Foundry com uma Ferramenta OpenAPI que **não declara**
    estes cabeçalhos. Ele não tem como enviá-los, então não tem como aprovar nada.
    """
    config = obter_configuracao()
    if not x_auditor or len(x_auditor.strip()) < 3:
        raise AutorizacaoDeAuditorAusente(
            "Esta operação exige o cabeçalho X-Auditor com o nome de quem decide.",
            como_resolver=("Use a tela do Deva, que preenche o cabeçalho. Se você chegou "
                           "aqui pelo agente, é exatamente o comportamento esperado: o "
                           "agente propõe, não aprova."),
        )
    if config.exige_segredo and x_segredo != config.segredo_do_auditor:
        raise AutorizacaoDeAuditorAusente(
            "Cabeçalho X-Segredo ausente ou incorreto.",
            como_resolver="Confira a variável DEVA_SEGREDO_AUDITOR do serviço e da tela.",
        )
    return x_auditor.strip()


@app.exception_handler(ErroDoServico)
async def tratar_erro(request: Request, erro: ErroDoServico):
    return JSONResponse(status_code=erro.situacao_http, content=erro.para_payload())


# ─────────────────────────────────────────────────────────────────────────────
# Saúde
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def raiz():
    return {"servico": "Serviço de Continuidade do Deva", "versao": VERSAO,
            "documentacao": "/docs", "saude": "/saude"}


@app.get("/saude", response_model=EstadoDeSaude, tags=["saúde"])
def saude() -> EstadoDeSaude:
    """Primeiro lugar onde se olha quando algo trava."""
    config, memoria, _ = _servicos()
    try:
        atual = memoria.obter_memoria()
        acessivel, total = True, atual.total_de_linhas
    except Exception:
        acessivel, total = False, 0
    return EstadoDeSaude(versao=VERSAO, armazenamento=config.armazenamento,
                         memoria_acessivel=acessivel, total_de_linhas_na_memoria=total,
                         propostas_pendentes=memoria.contar_pendentes())


# ─────────────────────────────────────────────────────────────────────────────
# Memória — o agente lê
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/memoria", response_model=Memoria, tags=["memória"],
         summary="Ler a memória aprovada",
         description="O agente chama isto no início de TODA sessão, antes de olhar "
                     "qualquer documento.")
def obter_memoria() -> Memoria:
    _, memoria, _ = _servicos()
    return memoria.obter_memoria()


@app.get("/memoria/markdown", response_class=PlainTextResponse, tags=["memória"],
         summary="Ler a memória como texto markdown")
def obter_memoria_markdown() -> str:
    """É este texto que o aluno vê na tela e no arquivo MEMORY.md do Blob."""
    _, memoria, _ = _servicos()
    return memoria.obter_memoria().markdown


@app.get("/memoria/hoje", response_model=list[LinhaDeMemoria], tags=["memória"],
         summary="O que foi aprendido hoje")
def memoria_de_hoje() -> list[LinhaDeMemoria]:
    """A tela destaca estas linhas em ciano. É a prova visual de que ele aprendeu."""
    _, memoria, _ = _servicos()
    return memoria.linhas_de_hoje()


# ─────────────────────────────────────────────────────────────────────────────
# Memória — o agente propõe
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/memoria/proposta", response_model=PropostaDeMemoria, status_code=201,
          tags=["memória"], summary="Propor uma regra nova",
          description="O agente chama isto quando o auditor o corrige. A regra NÃO passa "
                      "a valer: entra numa fila de revisão.")
def propor(entrada: EntradaDeProposta) -> PropostaDeMemoria:
    _, memoria, _ = _servicos()
    return memoria.propor(entrada)


@app.get("/memoria/propostas", response_model=list[PropostaDeMemoria], tags=["memória"])
def listar_propostas(
    situacao: SituacaoDaProposta | None = Query(default=None)
) -> list[PropostaDeMemoria]:
    _, memoria, _ = _servicos()
    return memoria.listar_propostas(situacao)


# ─────────────────────────────────────────────────────────────────────────────
# Memória — só a pessoa decide
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/memoria/propostas/{identificador}/aprovar", response_model=LinhaDeMemoria,
          tags=["auditor"], summary="Aprovar uma proposta (exige X-Auditor)")
def aprovar(identificador: str, decisao: DecisaoSobreProposta,
            auditor: str = Depends(exigir_auditor)) -> LinhaDeMemoria:
    _, memoria, _ = _servicos()
    return memoria.aprovar(identificador, decisao.auditor or auditor)


@app.post("/memoria/propostas/{identificador}/descartar", response_model=PropostaDeMemoria,
          tags=["auditor"], summary="Descartar uma proposta (exige X-Auditor)")
def descartar(identificador: str, decisao: DecisaoSobreProposta,
              auditor: str = Depends(exigir_auditor)) -> PropostaDeMemoria:
    _, memoria, _ = _servicos()
    return memoria.descartar(identificador, decisao.auditor or auditor, decisao.motivo)


# ─────────────────────────────────────────────────────────────────────────────
# Fila
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/fila", response_model=ResumoDaFila, tags=["fila"],
         summary="O que há para fazer agora",
         description="O agente chama isto para descobrir trabalho sem ninguém pedir. "
                     "Repare em 'aguardando_humano': isso NÃO é com ele.")
def resumo_da_fila() -> ResumoDaFila:
    _, memoria, fila = _servicos()
    return fila.resumir(memoria.contar_pendentes())


@app.get("/fila/documentos", response_model=list[Documento], tags=["fila"])
def listar_documentos(
    estado: EstadoDoDocumento | None = Query(default=None)
) -> list[Documento]:
    _, _, fila = _servicos()
    return fila.listar(estado)


@app.get("/fila/documentos/{identificador}", response_model=Documento, tags=["fila"])
def obter_documento(identificador: str) -> Documento:
    _, _, fila = _servicos()
    return fila.obter(identificador)


@app.post("/fila/documentos", response_model=Documento, status_code=201, tags=["fila"],
          summary="Registrar um documento que chegou",
          description="Chamado pelo GATILHO quando um arquivo cai no armazenamento. "
                      "É o ponto onde o agente deixa de esperar alguém digitar.")
def receber_documento(entrada: EntradaDeDocumento) -> Documento:
    _, _, fila = _servicos()
    return fila.receber(entrada)


@app.post("/fila/documentos/{identificador}/estado", response_model=Documento,
          tags=["fila"], summary="Avançar um documento na esteira")
def avancar_documento(identificador: str,
                      atualizacao: AtualizacaoDeDocumento) -> Documento:
    _, _, fila = _servicos()
    return fila.avancar(identificador, atualizacao, por="deva")


@app.post("/fila/documentos/{identificador}/liberar", response_model=Documento,
          tags=["auditor"], summary="Liberar uma exceção (exige X-Auditor)")
def liberar_excecao(identificador: str, atualizacao: AtualizacaoDeDocumento,
                    auditor: str = Depends(exigir_auditor)) -> Documento:
    _, _, fila = _servicos()
    return fila.avancar(identificador, atualizacao, por=auditor)
