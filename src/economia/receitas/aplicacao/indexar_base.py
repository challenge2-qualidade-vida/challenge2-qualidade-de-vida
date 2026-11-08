"""Caso de uso: indexar a base de conhecimento (carregar → fragmentar → embedar → gravar)."""

import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from economia.receitas.aplicacao.fragmentacao import (
    ContadorDeTokens,
    contar_palavras,
    fragmentar_documento,
    fragmentar_receita,
)
from economia.receitas.aplicacao.portas import GeradorDeEmbeddings, RepositorioDeTrechos
from economia.receitas.dominio.modelos import Documento, Receita, TipoDeTrecho, Trecho


@dataclass(frozen=True)
class ResultadoDaIndexacao:
    trechos: int
    receitas_descartadas: int
    segundos: float


def montar_trechos(
    receitas: Iterable[Receita],
    documentos: Iterable[Documento],
    contar: ContadorDeTokens = contar_palavras,
) -> tuple[list[Trecho], int]:
    """Aplica a curadoria e o chunking. Devolve os trechos e quantas receitas saíram."""
    trechos: list[Trecho] = []
    descartadas = 0
    for receita in receitas:
        if receita.esta_completa:
            trechos.append(fragmentar_receita(receita, contar=contar))
        else:
            descartadas += 1
    for documento in documentos:
        trechos += fragmentar_documento(documento, contar=contar)
    return trechos, descartadas


def amostra_fixa(trechos: Sequence[Trecho], receitas: int) -> list[Trecho]:
    """Todos os trechos de orientação e até `receitas` receitas, divididas igualmente entre as fontes.

    A amostra é sempre a mesma para a mesma lista, para comparar os modelos nos mesmos trechos
    quando a base inteira demora demais (ex.: qwen3 numa máquina só com CPU).
    """
    por_fonte: dict[str, list[Trecho]] = {}
    for trecho in trechos:
        if trecho.tipo is TipoDeTrecho.RECEITA:
            por_fonte.setdefault(trecho.fonte.titulo, []).append(trecho)
    cota = receitas // len(por_fonte) if por_fonte else 0
    escolhidas = {t.id for lista in por_fonte.values() for t in lista[:cota]}
    return [
        t for t in trechos if t.tipo is TipoDeTrecho.CONHECIMENTO or t.id in escolhidas
    ]


def indexar(
    trechos: Sequence[Trecho],
    gerador: GeradorDeEmbeddings,
    repositorio: RepositorioDeTrechos,
    tamanho_do_lote: int = 32,
    recriar: bool = False,
    ao_progredir: Callable[[int, int], None] | None = None,
    receitas_descartadas: int = 0,
) -> ResultadoDaIndexacao:
    """Gera os vetores em lotes e grava no repositório. Lotes pequenos poupam memória.

    Os trechos são processados do mais curto para o mais longo: cada lote é preenchido até o
    tamanho do maior texto dele, e lotes com textos de tamanho parecido desperdiçam menos.
    A ordem não muda o resultado, porque cada trecho é gravado com o próprio id.
    """
    if tamanho_do_lote < 1:
        raise ValueError("O lote precisa ter pelo menos 1 trecho.")
    inicio = time.perf_counter()
    repositorio.preparar(gerador.dimensao, recriar=recriar)
    trechos = sorted(trechos, key=lambda t: len(t.texto))
    for n in range(0, len(trechos), tamanho_do_lote):
        lote = trechos[n : n + tamanho_do_lote]
        vetores = gerador.gerar_para_trechos([t.texto for t in lote])
        if len(vetores) != len(lote):
            raise RuntimeError(
                "O gerador devolveu uma quantidade de vetores diferente da de trechos."
            )
        repositorio.gravar(lote, vetores)
        if ao_progredir:
            ao_progredir(n + len(lote), len(trechos))
    return ResultadoDaIndexacao(
        trechos=len(trechos),
        receitas_descartadas=receitas_descartadas,
        segundos=time.perf_counter() - inicio,
    )
