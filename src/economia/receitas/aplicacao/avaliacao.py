"""Avaliação da recuperação: Recall@k, MRR, separação dos scores e latência.

O conjunto de avaliação tem perguntas com gabarito (os documentos, e as seções, que deveriam
voltar) e perguntas sem resposta na base, usadas para calibrar o limiar da RN11.
"""

import json
import statistics
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from economia.receitas.aplicacao.portas import GeradorDeEmbeddings, RepositorioDeTrechos
from economia.receitas.dominio.modelos import Trecho, TrechoRecuperado


@dataclass(frozen=True)
class Esperado:
    """Um item do gabarito: o documento e, se for o caso, a seção dele."""

    documento_id: str
    secao: str | None = None

    def corresponde(self, trecho: Trecho) -> bool:
        if trecho.documento_id != self.documento_id:
            return False
        return (
            self.secao is None
            or (trecho.secao or "").casefold() == self.secao.casefold()
        )


@dataclass(frozen=True)
class PerguntaDeAvaliacao:
    id: str
    pergunta: str
    categoria: str
    esperados: tuple[Esperado, ...] = ()

    @property
    def tem_resposta(self) -> bool:
        return bool(self.esperados)


def carregar_perguntas(caminho: Path) -> list[PerguntaDeAvaliacao]:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return [
        PerguntaDeAvaliacao(
            id=item["id"],
            pergunta=item["pergunta"],
            categoria=item["categoria"],
            esperados=tuple(Esperado(**e) for e in item.get("esperados", [])),
        )
        for item in dados["perguntas"]
    ]


def posicao_do_primeiro_acerto(
    pergunta: PerguntaDeAvaliacao, recuperados: Sequence[TrechoRecuperado]
) -> int | None:
    """Posição (a partir de 1) do primeiro trecho que corresponde ao gabarito."""
    for posicao, recuperado in enumerate(recuperados, start=1):
        if any(e.corresponde(recuperado.trecho) for e in pergunta.esperados):
            return posicao
    return None


@dataclass(frozen=True)
class ResultadoDaPergunta:
    id: str
    categoria: str
    tem_resposta: bool
    posicao: int | None
    melhor_score: float
    segundos: float
    titulos: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResumoDaAvaliacao:
    modelo: str
    k: int
    recall: float
    mrr: float
    score_medio_com_resposta: float
    score_medio_sem_resposta: float
    menor_score_com_resposta: float
    maior_score_sem_resposta: float
    latencia_media: float
    resultados: tuple[ResultadoDaPergunta, ...] = field(default=())

    @property
    def separacao(self) -> float:
        """Diferença entre o menor score com resposta e o maior sem resposta.

        Positiva: existe um limiar que separa todas as perguntas. Negativa: os grupos se misturam.
        """
        return self.menor_score_com_resposta - self.maior_score_sem_resposta

    @property
    def limiar_sugerido(self) -> float:
        """Ponto médio entre os dois grupos (ponto de partida da calibração da RN11)."""
        return round(
            (self.menor_score_com_resposta + self.maior_score_sem_resposta) / 2, 3
        )


def resumir(
    modelo: str, k: int, resultados: Sequence[ResultadoDaPergunta]
) -> ResumoDaAvaliacao:
    com = [r for r in resultados if r.tem_resposta]
    sem = [r for r in resultados if not r.tem_resposta]
    if not com:
        raise ValueError("O conjunto de avaliação precisa de perguntas com resposta.")

    def media(valores: Sequence[float]) -> float:
        return statistics.fmean(valores) if valores else 0.0

    return ResumoDaAvaliacao(
        modelo=modelo,
        k=k,
        recall=sum(r.posicao is not None for r in com) / len(com),
        mrr=media([1 / r.posicao if r.posicao else 0.0 for r in com]),
        score_medio_com_resposta=media([r.melhor_score for r in com]),
        score_medio_sem_resposta=media([r.melhor_score for r in sem]),
        menor_score_com_resposta=min(r.melhor_score for r in com),
        maior_score_sem_resposta=max((r.melhor_score for r in sem), default=0.0),
        latencia_media=media([r.segundos for r in resultados]),
        resultados=tuple(resultados),
    )


def avaliar(
    perguntas: Sequence[PerguntaDeAvaliacao],
    gerador: GeradorDeEmbeddings,
    repositorio: RepositorioDeTrechos,
    k: int = 5,
) -> ResumoDaAvaliacao:
    """Busca o top-k de cada pergunta, sem limiar, e mede o resultado contra o gabarito."""
    resultados = []
    for pergunta in perguntas:
        inicio = time.perf_counter()
        vetor = gerador.gerar_para_pergunta(pergunta.pergunta)
        recuperados = repositorio.buscar(vetor, k)
        segundos = time.perf_counter() - inicio
        resultados.append(
            ResultadoDaPergunta(
                id=pergunta.id,
                categoria=pergunta.categoria,
                tem_resposta=pergunta.tem_resposta,
                posicao=posicao_do_primeiro_acerto(pergunta, recuperados)
                if pergunta.tem_resposta
                else None,
                melhor_score=recuperados[0].score if recuperados else 0.0,
                segundos=segundos,
                titulos=tuple(r.trecho.titulo for r in recuperados),
            )
        )
    return resumir(gerador.nome, k, resultados)
