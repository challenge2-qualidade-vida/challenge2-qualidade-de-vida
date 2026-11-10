"""API HTTP do EconoMIA. Por enquanto, a rota de saúde e a pergunta ao Miau-ricio (RAG, #24).

Rodar: poetry run uvicorn economia.api.app:app --port 8000
Documentação interativa: http://localhost:8000/docs
"""

import logging
import time
from functools import lru_cache
from typing import Annotated, Literal, Protocol

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from economia.receitas.dominio.modelos import RespostaComFontes

logger = logging.getLogger(__name__)

INDISPONIVEL = "O Miau-ricio está indisponível agora. Tente de novo em instantes."


class CasoDeUsoDeResposta(Protocol):
    def responder(self, pergunta: str) -> RespostaComFontes: ...


class PerguntaDeConhecimento(BaseModel):
    pergunta: str = Field(
        min_length=1,
        max_length=500,
        examples=["Como guardar folhas verdes na geladeira?"],
    )

    @field_validator("pergunta", mode="before")
    @classmethod
    def sem_espacos_nas_pontas(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor


class FonteDaResposta(BaseModel):
    numero: int = Field(description="Número usado no texto: [1], [2]...")
    titulo: str
    descricao: str = Field(description="Citação completa, montada pelo código (RN10)")
    url: str | None
    licenca: str | None
    tipo: Literal["receita", "conhecimento"]


class TrechoDaBusca(BaseModel):
    posicao: int = Field(description="Posição na lista enviada ao LLM (1 = primeiro)")
    titulo: str
    tipo: Literal["receita", "conhecimento"]
    origem: str = Field(description="Documento-fonte do trecho")
    score: float = Field(description="Similaridade de cosseno com a pergunta (0 a 1)")
    acima_do_limiar: bool
    fonte: int | None = Field(
        description="Número da fonte na resposta, se o trecho foi citado"
    )
    resumo: str = Field(description="Começo do conteúdo do trecho")


class IngredientesQueFaltam(BaseModel):
    receita: str
    ingredientes: list[str]


class RespostaDaPergunta(BaseModel):
    texto: str
    encontrou: bool
    fontes: list[FonteDaResposta]
    ingredientes_disponiveis: list[str]
    faltando: list[IngredientesQueFaltam]
    trechos_recuperados: list[TrechoDaBusca] = Field(
        description="Evidência da busca: trechos com o score, citados ou não"
    )
    limiar: float | None = Field(description="Score mínimo para um trecho ser usado")
    segundos: float


TAMANHO_DO_RESUMO = 280


def _resumo(texto: str) -> str:
    texto = " ".join(texto.split())
    if len(texto) <= TAMANHO_DO_RESUMO:
        return texto
    return texto[:TAMANHO_DO_RESUMO].rsplit(" ", 1)[0] + "…"


def para_a_api(
    resposta: RespostaComFontes, segundos: float, limiar: float | None = None
) -> RespostaDaPergunta:
    """Converte a resposta do caso de uso no formato da API, com as fontes numeradas."""
    from economia.receitas.aplicacao.responder_pergunta import formatar_fonte

    titulos = {r.trecho.id: r.trecho.titulo for r in resposta.trechos}
    numero_da_fonte = {r.trecho.id: n for n, r in enumerate(resposta.trechos, start=1)}
    return RespostaDaPergunta(
        texto=resposta.texto,
        encontrou=resposta.encontrou,
        fontes=[
            FonteDaResposta(
                numero=n,
                titulo=r.trecho.titulo,
                descricao=formatar_fonte(r),
                url=r.trecho.fonte.url,
                licenca=r.trecho.fonte.licenca,
                tipo=r.trecho.tipo.value,
            )
            for n, r in enumerate(resposta.trechos, start=1)
        ],
        ingredientes_disponiveis=list(resposta.ingredientes_disponiveis),
        faltando=[
            IngredientesQueFaltam(receita=titulos.get(id, id), ingredientes=list(itens))
            for id, itens in resposta.faltando
        ],
        trechos_recuperados=[
            TrechoDaBusca(
                posicao=n,
                titulo=r.trecho.titulo,
                tipo=r.trecho.tipo.value,
                origem=r.trecho.fonte.titulo,
                score=round(r.score, 4),
                acima_do_limiar=limiar is None or r.score >= limiar,
                fonte=numero_da_fonte.get(r.trecho.id),
                resumo=_resumo(r.trecho.conteudo),
            )
            for n, r in enumerate(resposta.recuperados, start=1)
        ],
        limiar=limiar,
        segundos=round(segundos, 1),
    )


@lru_cache
def obter_caso_de_uso() -> CasoDeUsoDeResposta:
    """Caso de uso com a configuração do .env, criado uma vez por processo (carrega o modelo e5)."""
    from economia.compartilhado.configuracao import obter_configuracao
    from economia.receitas.cli import criar_responder

    return criar_responder(obter_configuracao())


app = FastAPI(
    title="EconoMIA",
    description="API do EconoMIA. Nesta versão, só a pergunta ao Miau-ricio (RAG de receitas e alimentação).",
    version="0.1.0",
)


@app.get("/saude", tags=["saúde"])
def saude() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/receitas/perguntas",
    tags=["receitas"],
    summary="Pergunta ao Miau-ricio",
    responses={503: {"description": INDISPONIVEL}},
)
def perguntar(
    entrada: PerguntaDeConhecimento,
    caso: Annotated[CasoDeUsoDeResposta, Depends(obter_caso_de_uso)],
) -> RespostaDaPergunta:
    """Responde com os trechos da base de conhecimento e as fontes (RN10).

    Sem informação na base, `encontrou` é falso e o texto diz que não encontrou (RN11).
    Pergunta sobre preço atual recebe o aviso da RN04.
    """
    inicio = time.perf_counter()
    try:
        resposta = caso.responder(entrada.pergunta)
    except Exception as erro:  # Qdrant ou Ollama fora do ar, tempo esgotado
        logger.exception("Falha ao responder a pergunta")
        raise HTTPException(status_code=503, detail=INDISPONIVEL) from erro
    return para_a_api(
        resposta, time.perf_counter() - inicio, getattr(caso, "limiar", None)
    )
