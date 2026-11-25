"""Rota da pesquisa de evidências (#75), com erros em Problem Details (RFC 9457).

O formato de erro vale só para as rotas deste roteador: as rotas de receitas
continuam com `{"detail": ...}`, que o frontend já lê.
"""

import logging
from collections.abc import Callable, Coroutine
from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

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
from economia.pesquisa_evidencias.dominio.modelos import EvidenciaRecuperada

logger = logging.getLogger(__name__)


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


def _detalhe_da_validacao(erro: RequestValidationError) -> str:
    campos = {str(item["loc"][-1]) for item in erro.errors() if item.get("loc")}

    if "pergunta" in campos:
        return "A pergunta não pode ser vazia."
    if "limite" in campos:
        return "O limite de evidências deve estar entre 1 e 20."
    if "alegacao" in campos:
        return "A alegação precisa ter de 1 a 500 caracteres."
    if "perfil" in campos:
        return "O perfil de leitura deve ser consumidor_geral ou consumidor_rapido."
    return "Os dados enviados não atendem aos requisitos da solicitação."


class RotaComProblemDetails(APIRoute):
    """Converte os erros da rota em Problem Details, sem expor detalhes internos."""

    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        tratar = super().get_route_handler()

        async def tratar_com_problemas(request: Request) -> Response:
            try:
                return await tratar(request)
            except RequestValidationError as erro:
                return criar_problema(
                    request,
                    status=422,
                    titulo="Erro de validação",
                    detalhe=_detalhe_da_validacao(erro),
                )
            except HTTPException as erro:
                return criar_problema(
                    request,
                    status=erro.status_code,
                    titulo=HTTPStatus(erro.status_code).phrase,
                    detalhe=str(erro.detail),
                    headers=erro.headers,
                )
            except Exception:
                logger.exception("Falha inesperada em %s", request.url.path)
                return criar_problema(
                    request,
                    status=500,
                    titulo="Erro interno do servidor",
                    detalhe="Ocorreu uma falha inesperada ao processar a solicitação.",
                )

        return tratar_com_problemas


roteador = APIRouter(route_class=RotaComProblemDetails)


def para_a_resposta(evidencia: EvidenciaRecuperada) -> EvidenciaResposta:
    """Converte a evidência do domínio no formato da API."""
    trecho = evidencia.trecho
    documento = evidencia.documento
    fonte = documento.fonte
    return EvidenciaResposta(
        trecho=TrechoEvidenciaResposta(
            id=trecho.id,
            texto=trecho.texto,
            pagina_inicial=trecho.pagina_inicial,
            pagina_final=trecho.pagina_final,
            secao=trecho.secao,
        ),
        documento=DocumentoEvidenciaResposta(
            id=documento.id,
            arquivo=documento.arquivo,
            hash_sha256=documento.hash_sha256,
            fonte=FonteEvidenciaResposta(
                titulo=fonte.titulo,
                instituicao=fonte.instituicao,
                ano=fonte.ano,
                url=fonte.url,
            ),
        ),
        score=evidencia.score,
    )


@roteador.post(
    "/api/v1/verificar",
    response_model=RespostaVerificacao,
    tags=["pesquisa de evidências"],
    summary="Recupera evidências para uma pergunta",
)
def verificar(
    requisicao: RequisicaoVerificacao,
    caso_de_uso: Annotated[
        PesquisarEvidencias,
        Depends(obter_pesquisar_evidencias),
    ],
) -> RespostaVerificacao:
    """Recupera evidências científicas relacionadas a uma pergunta.

    O score é a similaridade semântica, não a probabilidade de a alegação ser verdadeira.
    """
    evidencias = caso_de_uso.executar(
        pergunta=requisicao.pergunta,
        limite=requisicao.limite,
    )
    resposta = [para_a_resposta(evidencia) for evidencia in evidencias]
    return RespostaVerificacao(
        pergunta=requisicao.pergunta,
        total_evidencias=len(resposta),
        evidencias=resposta,
    )
