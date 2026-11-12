"""Avaliação das respostas: roda o caso de uso completo e confere o comportamento de cada pergunta.

A avaliação da recuperação (`avaliacao.py`) mede só a busca. Esta mede o que a pessoa recebe:
se o sistema respondeu quando devia, se disse que não encontrou quando a base não tem a
informação (RN11), se avisou nas perguntas de preço (RN04) e se a resposta citou o documento
esperado (RN10). Todas as contas são determinísticas (RN01).

Nas perguntas com resposta de referência, mede também o texto (ROUGE-1, ROUGE-L e cosseno,
em `metricas_de_texto.py`). Uma recusa vale 0 nas três: fora da média, um modelo que recusa as
perguntas difíceis teria médias maiores. O Hit@k olha os trechos que a busca entregou
(`recuperados`); no modo LLM puro não há busca, e ele fica vazio.
"""

import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from economia.receitas.aplicacao.avaliacao import (
    AVISO_DE_PRECO,
    NAO_ENCONTRAR,
    RESPONDER,
    PerguntaDeAvaliacao,
    posicao_do_primeiro_acerto,
)
from economia.receitas.aplicacao.metricas_de_texto import (
    rouge_1_f1,
    rouge_l_f1,
    similaridade_com_a_referencia,
)
from economia.receitas.aplicacao.portas import GeradorDeEmbeddings
from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO as TEXTO_DO_AVISO_DE_PRECO,
)
from economia.receitas.dominio.modelos import TrechoRecuperado


class RespostaAvaliada(Protocol):
    """O que a avaliação lê de uma resposta: a do RAG (`RespostaComFontes`) ou a do LLM puro."""

    @property
    def texto(self) -> str: ...

    @property
    def encontrou(self) -> bool: ...

    @property
    def trechos(self) -> tuple[TrechoRecuperado, ...]: ...

    @property
    def recuperados(self) -> tuple[TrechoRecuperado, ...]: ...


def comportamento_obtido(resposta: RespostaAvaliada) -> str:
    """Classifica a resposta em responder, não encontrar ou aviso de preço."""
    if resposta.encontrou:
        return RESPONDER
    if resposta.texto == TEXTO_DO_AVISO_DE_PRECO:
        return AVISO_DE_PRECO
    return NAO_ENCONTRAR


def citou_fonte_esperada(
    pergunta: PerguntaDeAvaliacao, resposta: RespostaAvaliada
) -> bool | None:
    """Se a resposta usou algum trecho do gabarito. `None` quando não se aplica."""
    if not pergunta.esperados or not resposta.encontrou:
        return None
    return any(
        esperado.corresponde(usado.trecho)
        for usado in resposta.trechos
        for esperado in pergunta.esperados
    )


@dataclass(frozen=True)
class MetricasDeTexto:
    rouge_1: float | None = None
    rouge_l: float | None = None
    cosseno: float | None = None


def metricas_de_texto(
    pergunta: PerguntaDeAvaliacao,
    resposta: RespostaAvaliada,
    gerador: GeradorDeEmbeddings | None = None,
) -> MetricasDeTexto:
    """ROUGE-1, ROUGE-L e cosseno contra a referência. Sem referência, nada; recusa, zero."""
    referencia = pergunta.resposta_referencia
    if not referencia:
        return MetricasDeTexto()
    if not resposta.encontrou:
        return MetricasDeTexto(0.0, 0.0, 0.0 if gerador else None)
    return MetricasDeTexto(
        rouge_1=rouge_1_f1(resposta.texto, referencia),
        rouge_l=rouge_l_f1(resposta.texto, referencia),
        cosseno=similaridade_com_a_referencia(resposta.texto, referencia, gerador)
        if gerador
        else None,
    )


def hit_em_k(
    pergunta: PerguntaDeAvaliacao, resposta: RespostaAvaliada, k: int
) -> int | None:
    """1 se um trecho do gabarito está entre os k primeiros recuperados. Sem busca, `None`."""
    if not pergunta.esperados or not resposta.recuperados:
        return None
    return int(
        posicao_do_primeiro_acerto(pergunta, resposta.recuperados[:k]) is not None
    )


@dataclass(frozen=True)
class ResultadoDaResposta:
    id: str
    categoria: str
    esperado: str
    obtido: str
    fonte_esperada: bool | None
    segundos: float
    documentos_citados: tuple[str, ...] = ()
    texto: str = ""
    rouge_1: float | None = None
    rouge_l: float | None = None
    cosseno: float | None = None
    hit: int | None = None

    @property
    def acertou(self) -> bool:
        return self.esperado == self.obtido


def _taxa(acertos: Sequence[bool]) -> float | None:
    return sum(acertos) / len(acertos) if acertos else None


def _media(valores: Sequence[float | None]) -> float | None:
    presentes = [v for v in valores if v is not None]
    return statistics.fmean(presentes) if presentes else None


def _metricas(resultados: Sequence[ResultadoDaResposta]) -> dict:
    deve_responder = [r for r in resultados if r.esperado == RESPONDER]
    deve_recusar = [r for r in resultados if r.esperado == NAO_ENCONTRAR]
    deve_avisar = [r for r in resultados if r.esperado == AVISO_DE_PRECO]
    com_fonte = [r.fonte_esperada for r in resultados if r.fonte_esperada is not None]
    return {
        "perguntas": len(resultados),
        "acuracia": _taxa([r.acertou for r in resultados]),
        "taxa_de_resposta": _taxa([r.obtido == RESPONDER for r in deve_responder]),
        "recusa_correta": _taxa([r.obtido == NAO_ENCONTRAR for r in deve_recusar]),
        "aviso_de_preco": _taxa([r.obtido == AVISO_DE_PRECO for r in deve_avisar]),
        "fonte_esperada": _taxa(com_fonte),
        "rouge_1": _media([r.rouge_1 for r in resultados]),
        "rouge_l": _media([r.rouge_l for r in resultados]),
        "cosseno": _media([r.cosseno for r in resultados]),
        "hit": _media([r.hit for r in resultados]),
    }


@dataclass(frozen=True)
class ResumoDasRespostas:
    """Resultado da avaliação das respostas.

    - `acuracia`: perguntas em que o comportamento foi o esperado.
    - `taxa_de_resposta`: entre as que deviam ser respondidas, quantas foram.
    - `recusa_correta`: entre as sem resposta na base, quantas disseram que não encontraram (RN11).
    - `aviso_de_preco`: entre as de preço, quantas receberam o aviso (RN04).
    - `fonte_esperada`: entre as respondidas que têm gabarito, quantas citaram um documento dele.
    - `rouge_1`, `rouge_l`, `cosseno`: médias nas perguntas com resposta de referência.
    - `hit`: Hit@k médio nas perguntas com gabarito que passaram pela busca.
    - `falsas_recusas`: deviam ser respondidas e o sistema disse que não encontrou.
    - `respostas_indevidas`: não deviam ser respondidas pela base e foram.
    """

    perguntas: int
    acuracia: float | None
    taxa_de_resposta: float | None
    recusa_correta: float | None
    aviso_de_preco: float | None
    fonte_esperada: float | None
    rouge_1: float | None
    rouge_l: float | None
    cosseno: float | None
    hit: float | None
    falsas_recusas: tuple[str, ...]
    respostas_indevidas: tuple[str, ...]
    latencia_media: float
    latencia_maxima: float
    por_categoria: dict = field(default_factory=dict)
    resultados: tuple[ResultadoDaResposta, ...] = ()


def resumir_respostas(resultados: Sequence[ResultadoDaResposta]) -> ResumoDasRespostas:
    if not resultados:
        raise ValueError(
            "A avaliação das respostas precisa de pelo menos uma pergunta."
        )
    categorias: dict[str, list[ResultadoDaResposta]] = {}
    for resultado in resultados:
        categorias.setdefault(resultado.categoria, []).append(resultado)
    tempos = [r.segundos for r in resultados]
    return ResumoDasRespostas(
        **_metricas(resultados),
        falsas_recusas=tuple(
            r.id
            for r in resultados
            if r.esperado == RESPONDER and r.obtido == NAO_ENCONTRAR
        ),
        respostas_indevidas=tuple(
            r.id
            for r in resultados
            if r.esperado != RESPONDER and r.obtido == RESPONDER
        ),
        latencia_media=statistics.fmean(tempos),
        latencia_maxima=max(tempos),
        por_categoria={c: _metricas(itens) for c, itens in sorted(categorias.items())},
        resultados=tuple(resultados),
    )


def avaliar_respostas(
    perguntas: Sequence[PerguntaDeAvaliacao],
    responder: Callable[[str], RespostaAvaliada],
    ao_progredir: Callable[[int, int, ResultadoDaResposta], None] | None = None,
    relogio: Callable[[], float] = time.perf_counter,
    gerador: GeradorDeEmbeddings | None = None,
    k: int = 5,
) -> ResumoDasRespostas:
    """Responde cada pergunta com o caso de uso e compara com o esperado.

    `gerador` calcula o cosseno com a referência; sem ele, o cosseno fica de fora.
    """
    resultados = []
    for n, pergunta in enumerate(perguntas, start=1):
        inicio = relogio()
        resposta = responder(pergunta.pergunta)
        segundos = relogio() - inicio
        texto = metricas_de_texto(pergunta, resposta, gerador)
        resultado = ResultadoDaResposta(
            id=pergunta.id,
            categoria=pergunta.categoria,
            esperado=pergunta.comportamento_esperado,
            obtido=comportamento_obtido(resposta),
            fonte_esperada=citou_fonte_esperada(pergunta, resposta),
            segundos=segundos,
            documentos_citados=tuple(
                dict.fromkeys(u.trecho.documento_id for u in resposta.trechos)
            ),
            texto=resposta.texto,
            rouge_1=texto.rouge_1,
            rouge_l=texto.rouge_l,
            cosseno=texto.cosseno,
            hit=hit_em_k(pergunta, resposta, k),
        )
        resultados.append(resultado)
        if ao_progredir:
            ao_progredir(n, len(perguntas), resultado)
    return resumir_respostas(resultados)
