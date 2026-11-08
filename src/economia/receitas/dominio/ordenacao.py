"""Desempate do top-k pelos ingredientes que faltam (regra proposta na fase 7b, ver RN13).

Os itens vêm ordenados pelo score de similaridade. Itens cujo score fica a até `tolerancia`
do primeiro item do grupo contam como empatados. Dentro de cada grupo, vem primeiro o que
tem menos ingredientes faltando; com a mesma quantidade, vale o score.
"""

from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")


def desempatar(
    itens: Sequence[T],
    score: Callable[[T], float],
    faltando: Callable[[T], int],
    tolerancia: float,
) -> list[T]:
    if tolerancia < 0:
        raise ValueError("A tolerância não pode ser negativa.")
    por_score = sorted(itens, key=score, reverse=True)
    grupos: list[list[T]] = []
    for item in por_score:
        if grupos and score(grupos[-1][0]) - score(item) <= tolerancia:
            grupos[-1].append(item)
        else:
            grupos.append([item])
    return [
        item
        for grupo in grupos
        for item in sorted(grupo, key=lambda i: (faltando(i), -score(i)))
    ]
