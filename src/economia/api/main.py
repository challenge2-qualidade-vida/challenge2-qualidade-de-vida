"""Ponto de entrada da API EconoMIA (Dockerfile e README).

A aplicação fica em `app.py`. Aqui entra também a rota da verificação (Research Agent, #75),
registrada na mesma aplicação até a rota ir para `app.py` com o formato `/api/v1`.
"""

from typing import Annotated

from fastapi import Depends, HTTPException

from economia.api.app import app
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

__all__ = ["app"]


@app.post(
    "/verificar",
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
    if not requisicao.pergunta.strip():
        raise HTTPException(
            status_code=422,
            detail="A pergunta não pode ser vazia.",
        )

    try:
        evidencias = caso_de_uso.executar(
            pergunta=requisicao.pergunta,
            limite=requisicao.limite,
        )
    except ValueError as erro:
        raise HTTPException(
            status_code=422,
            detail=str(erro),
        ) from erro

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
        pergunta=requisicao.pergunta.strip(),
        total_evidencias=len(resposta),
        evidencias=resposta,
    )
