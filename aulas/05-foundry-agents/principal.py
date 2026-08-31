"""Deva3 · API de Validação Biométrica Básica.

Um endpoint. Uma responsabilidade: receber uma imagem, perguntar ao serviço
cognitivo da Azure onde estão as pessoas (ou os rostos) e devolver as
coordenadas com a pontuação de confiança.

    POST /detectar?modo=pessoas   → Azure AI Vision (padrão, sempre funciona)
    POST /detectar?modo=rostos    → Azure AI Face (opcional, Acesso Limitado)

O que esta API NÃO faz, de propósito: não identifica ninguém, não compara
rostos, não guarda template biométrico. Ela detecta presença e devolve caixa.
"""

from __future__ import annotations

import io
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from api.configuracao import obter_configuracao
from api.erros import ErroDoDeva, ImagemGrandeDemais, ImagemInvalida, ServicoNaoConfigurado
from api.modelos import (
    CaixaDelimitadora,
    DimensoesImagem,
    Deteccao,
    EstadoSaude,
    Falha,
    ModoDeteccao,
    ResultadoDeteccao,
)
from api.servicos.armazenamento import ServicoArmazenamentoBlob
from api.servicos.detector_rostos import ServicoFaceAzure
from api.servicos.detector_visao import ServicoVisaoAzure

TIPOS_ACEITOS = {"image/jpeg", "image/jpg", "image/png", "image/bmp", "image/webp"}


@asynccontextmanager
async def ciclo_de_vida(aplicacao: FastAPI):
    """Roda uma vez na subida e uma vez na descida do container."""
    configuracao = obter_configuracao()
    print(f"[Deva3] Subindo em ambiente '{configuracao.ambiente}'")
    print(f"[Deva3] Modos disponíveis: {configuracao.modos_disponiveis or 'nenhum'}")
    print(f"[Deva3] Armazenamento configurado: {configuracao.armazenamento_configurado}")
    yield
    print("[Deva3] Encerrando.")


aplicacao = FastAPI(
    title="Deva3 · API de Validação Biométrica Básica",
    description=(
        "Recebe uma imagem e devolve as coordenadas das detecções com a pontuação "
        "de confiança do serviço cognitivo da Azure. Material didático da FIAP."
    ),
    version=obter_configuracao().versao,
    lifespan=ciclo_de_vida,
)

aplicacao.add_middleware(
    CORSMiddleware,
    allow_origins=obter_configuracao().lista_origens(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@aplicacao.exception_handler(ErroDoDeva)
async def tratar_erro_do_deva(requisicao: Request, erro: ErroDoDeva) -> JSONResponse:
    """Todo erro conhecido sai no mesmo formato, com 'como_resolver' preenchido."""
    return JSONResponse(status_code=erro.situacao_http, content=erro.como_dicionario())


# ─────────────────────────────── ENDPOINTS ────────────────────────────────

@aplicacao.get("/", tags=["Diagnóstico"])
async def raiz() -> dict:
    configuracao = obter_configuracao()
    return {
        "aplicacao": configuracao.nome_aplicacao,
        "versao": configuracao.versao,
        "documentacao": "/docs",
        "saude": "/saude",
        "detectar": "POST /detectar (campo 'imagem', multipart/form-data)",
    }


@aplicacao.get("/saude", response_model=EstadoSaude, tags=["Diagnóstico"])
async def saude() -> EstadoSaude:
    """Primeiro lugar onde se olha quando a aula trava."""
    configuracao = obter_configuracao()
    return EstadoSaude(
        situacao="saudavel" if configuracao.modos_disponiveis else "degradado",
        aplicacao=configuracao.nome_aplicacao,
        versao=configuracao.versao,
        ambiente=configuracao.ambiente,
        modos_disponiveis=configuracao.modos_disponiveis,
        armazenamento_configurado=configuracao.armazenamento_configurado,
        persistir_imagens=configuracao.persistir_imagens,
        limiar_confianca=configuracao.limiar_confianca,
    )


@aplicacao.post(
    "/detectar",
    response_model=ResultadoDeteccao,
    responses={400: {"model": Falha}, 413: {"model": Falha},
               502: {"model": Falha}, 503: {"model": Falha}},
    tags=["Detecção"],
)
async def detectar(
    imagem: UploadFile = File(..., description="Arquivo JPEG, PNG, BMP ou WEBP"),
    modo: ModoDeteccao = Query(
        ModoDeteccao.PESSOAS,
        description="'pessoas' usa o Image Analysis; 'rostos' usa o Face (Acesso Limitado)",
    ),
    consentimento: bool = Query(
        False,
        description="Marque como verdadeiro para autorizar a gravação da imagem no Blob",
    ),
) -> ResultadoDeteccao:
    """Recebe a imagem, chama o serviço da Azure e devolve as coordenadas."""
    configuracao = obter_configuracao()
    inicio = time.perf_counter()
    identificador = uuid.uuid4().hex[:12]
    momento = datetime.now(timezone.utc)
    avisos: list[str] = []

    conteudo = await imagem.read()
    largura, altura = _validar_imagem(conteudo, imagem.content_type,
                                      configuracao.tamanho_maximo_bytes)

    # ── chamada ao serviço cognitivo ─────────────────────────────────────
    if modo is ModoDeteccao.ROSTOS:
        if not configuracao.face_configurada:
            raise ServicoNaoConfigurado(
                servico="Azure AI Face",
                como_resolver=(
                    "Este modo é opcional e exige recurso Face aprovado no Acesso "
                    "Limitado. Use ?modo=pessoas, que funciona com qualquer chave de Vision."
                ),
            )
        servico = ServicoFaceAzure(
            endpoint=configuracao.endpoint_face,
            chave=configuracao.chave_face,
            modelo_deteccao=configuracao.modelo_deteccao_face,
            tempo_limite=configuracao.tempo_limite_segundos,
        )
        achados, _ = await servico.detectar(conteudo)
        avisos.append(
            "No modo 'rostos' a Azure não devolve confiança de detecção. "
            "A pontuação mostrada é derivada do atributo qualityForRecognition."
        )
    else:
        servico = ServicoVisaoAzure(
            endpoint=configuracao.endpoint_visao,
            chave=configuracao.chave_visao,
            versao_api=configuracao.versao_api_visao,
            tempo_limite=configuracao.tempo_limite_segundos,
        )
        achados, dimensoes_servico = await servico.detectar(conteudo)
        if dimensoes_servico[0] and dimensoes_servico[1]:
            largura, altura = dimensoes_servico

    # ── montagem do resultado ────────────────────────────────────────────
    area_imagem = max(largura * altura, 1)
    deteccoes = [
        Deteccao(
            indice=posicao,
            caixa=caixa,
            confianca=confianca,
            acima_do_limiar=bool(confianca is not None
                                 and confianca >= configuracao.limiar_confianca),
            proporcao_da_imagem=round(caixa.area / area_imagem, 4),
        )
        for posicao, (caixa, confianca) in enumerate(achados, start=1)
    ]

    if not deteccoes:
        avisos.append(
            "Nenhuma detecção. Isso não é erro: tente uma foto com a pessoa mais "
            "próxima, com o rosto visível e boa iluminação."
        )

    acima = sum(1 for d in deteccoes if d.acima_do_limiar)
    if deteccoes and acima == 0:
        avisos.append(
            f"Houve detecção, mas nenhuma acima do limiar de "
            f"{configuracao.limiar_confianca:.2f}. Limiar é decisão de risco, não verdade técnica."
        )

    resultado = ResultadoDeteccao(
        identificador=identificador,
        momento=momento,
        modo=modo,
        servico=servico.NOME,
        arquivo=imagem.filename or "sem-nome",
        tamanho_bytes=len(conteudo),
        dimensoes=DimensoesImagem(largura=largura, altura=altura),
        limiar_confianca=configuracao.limiar_confianca,
        total_detectado=len(deteccoes),
        total_acima_do_limiar=acima,
        deteccoes=deteccoes,
        duracao_ms=int((time.perf_counter() - inicio) * 1000),
        imagem_persistida=False,
        caminho_blob=None,
        avisos=avisos,
    )

    # ── persistência opcional ────────────────────────────────────────────
    if configuracao.armazenamento_configurado:
        guardar_imagem = configuracao.persistir_imagens and consentimento
        if configuracao.persistir_imagens and not consentimento:
            avisos.append(
                "A imagem NÃO foi guardada porque não houve consentimento. "
                "Só o resultado em JSON foi gravado."
            )
        armazenamento = ServicoArmazenamentoBlob(
            conexao=configuracao.conexao_armazenamento,
            container=configuracao.container_blob,
        )
        prefixo = await armazenamento.guardar(
            identificador=identificador,
            imagem=conteudo if guardar_imagem else None,
            tipo_conteudo=imagem.content_type or "application/octet-stream",
            resultado=resultado.model_dump(mode="json"),
            momento=momento,
        )
        resultado.imagem_persistida = guardar_imagem
        resultado.caminho_blob = f"{configuracao.container_blob}/{prefixo}"
        resultado.avisos = avisos

    return resultado


# ─────────────────────────────── AUXILIARES ───────────────────────────────

def _validar_imagem(conteudo: bytes, tipo: str | None,
                    tamanho_maximo: int) -> tuple[int, int]:
    """Valida tamanho, tipo e integridade; devolve (largura, altura) em pixels."""
    if not conteudo:
        raise ImagemInvalida(
            mensagem="O arquivo enviado está vazio.",
            como_resolver="Selecione uma foto antes de enviar.",
        )

    if len(conteudo) > tamanho_maximo:
        raise ImagemGrandeDemais(
            mensagem=(
                f"A imagem tem {len(conteudo) / 1_048_576:.1f} MB e o limite é "
                f"{tamanho_maximo / 1_048_576:.0f} MB."
            ),
            como_resolver="Reduza a resolução da foto ou ajuste TAMANHO_MAXIMO_MB.",
        )

    if tipo and tipo.lower() not in TIPOS_ACEITOS:
        raise ImagemInvalida(
            mensagem=f"O tipo '{tipo}' não é aceito.",
            como_resolver="Envie JPEG, PNG, BMP ou WEBP.",
        )

    try:
        with Image.open(io.BytesIO(conteudo)) as figura:
            figura.verify()
        with Image.open(io.BytesIO(conteudo)) as figura:
            return figura.size
    except (UnidentifiedImageError, OSError) as erro:
        raise ImagemInvalida(
            mensagem="O arquivo não é uma imagem válida ou está corrompido.",
            detalhe=str(erro),
            como_resolver="Abra a foto no seu computador para conferir e envie de novo.",
        ) from erro
