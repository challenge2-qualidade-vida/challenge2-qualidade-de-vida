"""Avaliação das respostas: roda o caso de uso completo e confere o comportamento de cada pergunta.

A avaliação da recuperação (`avaliacao.py`) mede só a busca. Esta mede o que a pessoa recebe:
se o sistema respondeu quando devia, se disse que não encontrou quando a base não tem a
informação (RN11), se avisou nas perguntas de preço (RN04) e se a resposta citou o documento
esperado (RN10). Todas as contas são determinísticas (RN01).
"""

import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from economia.receitas.aplicacao.avaliacao import (
    AVISO_DE_PRECO,
    NAO_ENCONTRAR,
    RESPONDER,
    PerguntaDeAvaliacao,
)
from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO as TEXTO_DO_AVISO_DE_PRECO,
)
from economia.receitas.dominio.modelos import RespostaComFontes


def comportamento_obtido(resposta: RespostaComFontes) -> str:
    """Classifica a resposta em responder, não encontrar ou aviso de preço."""
    if resposta.encontrou:
        return RESPONDER
    if resposta.texto == TEXTO_DO_AVISO_DE_PRECO:
        return AVISO_DE_PRECO
    return NAO_ENCONTRAR


def citou_fonte_esperada(
    pergunta: PerguntaDeAvaliacao, resposta: RespostaComFontes
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
class ResultadoDaResposta:
    id: str
    categoria: str
    esperado: str
    obtido: str
    fonte_esperada: bool | None
    segundos: float
    documentos_citados: tuple[str, ...] = ()
    texto: str = ""

    @property
    def acertou(self) -> bool:
        return self.esperado == self.obtido


def _taxa(acertos: Sequence[bool]) -> float | None:
    return sum(acertos) / len(acertos) if acertos else None


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
    }


@dataclass(frozen=True)
class ResumoDasRespostas:
    """Resultado da avaliação das respostas.

    - `acuracia`: perguntas em que o comportamento foi o esperado.
    - `taxa_de_resposta`: entre as que deviam ser respondidas, quantas foram.
    - `recusa_correta`: entre as sem resposta na base, quantas disseram que não encontraram (RN11).
    - `aviso_de_preco`: entre as de preço, quantas receberam o aviso (RN04).
    - `fonte_esperada`: entre as respondidas que têm gabarito, quantas citaram um documento dele.
    - `falsas_recusas`: deviam ser respondidas e o sistema disse que não encontrou.
    - `respostas_indevidas`: não deviam ser respondidas pela base e foram.
    """

    perguntas: int
    acuracia: float | None
    taxa_de_resposta: float | None
    recusa_correta: float | None
    aviso_de_preco: float | None
    fonte_esperada: float | None
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
    responder: Callable[[str], RespostaComFontes],
    ao_progredir: Callable[[int, int, ResultadoDaResposta], None] | None = None,
    relogio: Callable[[], float] = time.perf_counter,
) -> ResumoDasRespostas:
    """Responde cada pergunta com o caso de uso completo e compara com o esperado."""
    resultados = []
    for n, pergunta in enumerate(perguntas, start=1):
        inicio = relogio()
        resposta = responder(pergunta.pergunta)
        segundos = relogio() - inicio
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
        )
        resultados.append(resultado)
        if ao_progredir:
            ao_progredir(n, len(perguntas), resultado)
    return resumir_respostas(resultados)
