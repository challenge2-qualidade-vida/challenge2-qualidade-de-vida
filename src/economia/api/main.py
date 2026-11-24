"""Aplicação principal da API EconoMIA."""

from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from economia.api.dependencias import obter_pesquisar_evidencias
from economia.api.modelos import (
    DocumentoEvidenciaResposta,
    EvidenciaResposta,
    FonteEvidenciaResposta,
    RequisicaoVerificacao,
    RespostaVerificacao,
    TrechoEvidenciaResposta,
)
from economia.pesquisa_evidencias.aplicacao.pesquisar_evidencias import (
    PesquisarEvidencias,
)

app = FastAPI(
    title="EconoMIA API",
    description="API do assistente EconoMIA.",
    version="0.1.0",
)


def criar_problema(
    request: Request,
    status: int,
    titulo: str,
    detalhe: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Monta uma resposta no formato Problem Details (RFC 9457)."""
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
        content={
            "type": "about:blank",
            "title": titulo,
            "status": status,
            "detail": detalhe,
            "instance": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(
    request: Request,
    erro: RequestValidationError,
) -> JSONResponse:
    """Converte erros de validação em Problem Details."""
    campos = {str(item["loc"][-1]) for item in erro.errors() if item.get("loc")}

    if "pergunta" in campos:
        detalhe = "A pergunta não pode ser vazia."
    elif "limite" in campos:
        detalhe = "O limite de evidências deve estar entre 1 e 20."
    else:
        detalhe = "Os dados enviados não atendem aos requisitos da solicitação."

    return criar_problema(
        request=request,
        status=422,
        titulo="Erro de validação",
        detalhe=detalhe,
    )


@app.exception_handler(StarletteHTTPException)
async def tratar_erro_http(
    request: Request,
    erro: StarletteHTTPException,
) -> JSONResponse:
    """Converte erros HTTP em Problem Details."""
    try:
        titulo = HTTPStatus(erro.status_code).phrase
    except ValueError:
        titulo = "Erro HTTP"

    return criar_problema(
        request=request,
        status=erro.status_code,
        titulo=titulo,
        detalhe=str(erro.detail),
        headers=erro.headers,
    )


@app.exception_handler(Exception)
async def tratar_erro_interno(
    request: Request,
    erro: Exception,
) -> JSONResponse:
    """Evita expor detalhes internos em erros inesperados."""
    return criar_problema(
        request=request,
        status=500,
        titulo="Erro interno do servidor",
        detalhe="Ocorreu uma falha inesperada ao processar a solicitação.",
    )


@app.get("/health", tags=["Health"])
def healthcheck() -> dict[str, str]:
    """Verifica se a aplicação está funcionando."""
    return {"status": "ok"}


@app.post(
    "/api/v1/verificar",
    response_model=RespostaVerificacao,
    tags=["Verificação"],
)
def verificar(
    requisicao: RequisicaoVerificacao,
    caso_de_uso: Annotated[
        PesquisarEvidencias,
        Depends(obter_pesquisar_evidencias),
    ],
) -> RespostaVerificacao:
    """Recupera evidências científicas relacionadas a uma pergunta."""
    evidencias = caso_de_uso.executar(
        pergunta=requisicao.pergunta,
        limite=requisicao.limite,
    )

    resposta = [
        EvidenciaResposta(
            trecho=TrechoEvidenciaResposta(
                id=evidencia.trecho.id,
                texto=evidencia.trecho.texto,
                pagina_inicial=evidencia.trecho.pagina_inicial,
                pagina_final=evidencia.trecho.pagina_final,
                secao=evidencia.trecho.secao,
            ),
            documento=DocumentoEvidenciaResposta(
                id=evidencia.documento.id,
                arquivo=evidencia.documento.arquivo,
                hash_sha256=evidencia.documento.hash_sha256,
                fonte=FonteEvidenciaResposta(
                    titulo=evidencia.documento.fonte.titulo,
                    instituicao=evidencia.documento.fonte.instituicao,
                    ano=evidencia.documento.fonte.ano,
                    url=evidencia.documento.fonte.url,
                ),
            ),
            score=evidencia.score,
        )
        for evidencia in evidencias
    ]

    return RespostaVerificacao(
        pergunta=requisicao.pergunta,
        total_evidencias=len(resposta),
        evidencias=resposta,
    )
