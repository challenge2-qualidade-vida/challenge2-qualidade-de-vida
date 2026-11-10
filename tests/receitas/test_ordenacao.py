import pytest

from economia.receitas.dominio.ordenacao import desempatar


def ordenar(itens, tolerancia):
    # item = (nome, score, faltando)
    return [
        nome
        for nome, _, _ in desempatar(
            itens, score=lambda i: i[1], faltando=lambda i: i[2], tolerancia=tolerancia
        )
    ]


def test_dentro_da_tolerancia_menos_faltando_primeiro():
    itens = [("torta", 0.905, 2), ("omelete", 0.900, 0)]
    assert ordenar(itens, 0.01) == ["omelete", "torta"]


def test_fora_da_tolerancia_vale_o_score():
    itens = [("torta", 0.95, 2), ("omelete", 0.90, 0)]
    assert ordenar(itens, 0.01) == ["torta", "omelete"]


def test_mesma_quantidade_faltando_vale_o_score():
    itens = [("b", 0.900, 1), ("a", 0.905, 1)]
    assert ordenar(itens, 0.01) == ["a", "b"]


def test_faixa_e_medida_a_partir_do_primeiro_do_grupo():
    # 0,905 → 0,897 → 0,889: os dois primeiros empatam; o terceiro fica a 0,016 do primeiro
    itens = [("a", 0.905, 3), ("b", 0.897, 0), ("c", 0.889, 0)]
    assert ordenar(itens, 0.01) == ["b", "a", "c"]


def test_tolerancia_zero_e_so_o_score():
    itens = [("a", 0.9, 5), ("b", 0.8, 0)]
    assert ordenar(itens, 0.0) == ["a", "b"]


def test_tolerancia_negativa_e_recusada():
    with pytest.raises(ValueError):
        desempatar([], score=lambda i: 0, faltando=lambda i: 0, tolerancia=-0.1)
