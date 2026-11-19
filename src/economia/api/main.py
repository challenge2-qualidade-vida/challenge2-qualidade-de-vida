
"""Aplicação principal da API EconoMIA."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from economia.api.dependencias import obter_pesquisar_evidencias
from economia.api.modelos import (
    DocumentoEvidenciaResposta,
    EvidenciaResposta,
    FonteEvidenciaResposta,
    RequisicaoVerificacao,
    RespostaVerificacao,
    TrechoEvidenciaResposta,
)
from economia.verificacao.aplicacao.pesquisar_evidencias import (
    PesquisarEvidencias,
)

app = FastAPI(
    title="EconoMIA API",
    description="API do assistente EconoMIA.",
    version="0.1.0",
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Verifica se a aplicação está funcionando."""
    return {"status": "ok"}


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
