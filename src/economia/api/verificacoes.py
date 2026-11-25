"""Rota da verificação de alegações (#82), com erros em Problem Details (RFC 9457).

Roda o orquestrador na requisição: Research → Analysis → Validation → Communication, com os
retornos do Validation. A resposta traz o veredito e o histórico das etapas.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from economia.api.dependencias import obter_verificar_alegacao
from economia.api.evidencias import RotaComProblemDetails
from economia.api.modelos import (
    EtapaResposta,
    FonteDoVeredito,
    RequisicaoDaAlegacao,
    RespostaDaAlegacao,
    VereditoResposta,
)
from economia.compartilhado.infraestrutura.prompts_langfuse import PromptIndisponivel
from economia.verificacao.aplicacao.verificar_alegacao import (
    ResultadoDaVerificacao,
    VerificarAlegacao,
)

logger = logging.getLogger(__name__)

INDISPONIVEL = "A verificação está indisponível agora. Tente de novo em instantes."


def _erros_de_indisponibilidade() -> tuple[type[BaseException], ...]:
    """Falhas do LLM, do Qdrant ou do Langfuse de prompts: o serviço está fora (regra 8)."""
    erros: list[type[BaseException]] = [
        ConnectionError,
        TimeoutError,
        PromptIndisponivel,
    ]
    try:
        import httpx

        erros.append(httpx.HTTPError)
    except ImportError:  # pragma: no cover - o httpx vem com o ollama e o qdrant-client
        pass
    try:
        from ollama import ResponseError

        erros.append(ResponseError)
    except ImportError:  # pragma: no cover
        pass
    try:
        from qdrant_client.http.exceptions import (
            ResponseHandlingException,
            UnexpectedResponse,
        )

        erros += [ResponseHandlingException, UnexpectedResponse]
    except ImportError:  # pragma: no cover
        pass
    return tuple(erros)


ERROS_DE_INDISPONIBILIDADE = _erros_de_indisponibilidade()

roteador = APIRouter(route_class=RotaComProblemDetails)


def para_a_resposta(resultado: ResultadoDaVerificacao) -> RespostaDaAlegacao:
    veredito = resultado.veredito
    return RespostaDaAlegacao(
        veredito=VereditoResposta(
            classificacao=(
                veredito.classificacao.value if veredito.classificacao else None
            ),
            mensagem=veredito.mensagem,
            fontes=[
                FonteDoVeredito(
                    titulo=f.titulo, instituicao=f.instituicao, ano=f.ano, url=f.url
                )
                for f in veredito.fontes
            ],
            aprovado_pela_validacao=veredito.aprovado_pela_validacao,
        ),
        retornos=resultado.retornos,
        historico=[
            EtapaResposta(
                agente=e.agente.value,
                entrada=e.entrada,
                saida=e.saida,
                segundos=e.segundos,
            )
            for e in resultado.historico
        ],
    )


@roteador.post(
    "/api/v1/verificacoes",
    response_model=RespostaDaAlegacao,
    tags=["verificação de alegações"],
    summary="Verifica uma alegação sobre alimentação",
    responses={503: {"description": INDISPONIVEL}},
)
def verificar_alegacao(
    requisicao: RequisicaoDaAlegacao,
    caso_de_uso: Annotated[VerificarAlegacao, Depends(obter_verificar_alegacao)],
) -> RespostaDaAlegacao:
    """Veredito da alegação no perfil de leitura pedido, com as etapas de cada agente.

    A classificação diz o quanto a base de evidências cobre a alegação, não se ela é
    verdadeira. Sem análise aprovada, o veredito diz que não foi possível concluir (RN11).
    """
    try:
        resultado = caso_de_uso.executar(requisicao.alegacao, requisicao.perfil)
    except ERROS_DE_INDISPONIBILIDADE as erro:
        logger.exception("Serviço indisponível na verificação")
        raise HTTPException(status_code=503, detail=INDISPONIVEL) from erro
    return para_a_resposta(resultado)
