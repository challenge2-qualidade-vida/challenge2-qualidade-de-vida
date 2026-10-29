"""Valida a integridade das bases em data/. Rode depois de editar os JSON."""

import pytest

from economia.dados import carregar, preco_por_kg

GRUPOS = {"cereais", "tuberculos", "leguminosas", "proteina_animal", "laticinios", "flv", "oleos", "acucar"}


@pytest.fixture(scope="module")
def base():
    return carregar()


def test_alimentos_tem_grupo_valido_e_nutrientes_nao_negativos(base):
    for a in base.alimentos.values():
        assert a.grupo in GRUPOS, a.id
        assert a.kcal >= 0 and a.proteina_g >= 0 and a.fibra_g >= 0, a.id


def test_todo_produto_aponta_para_um_alimento(base):
    for p in base.produtos.values():
        assert p.alimento in base.alimentos, p.id
        assert p.embalagem_g > 0, p.id


def test_todo_preco_aponta_para_produto_e_mercado_existentes(base):
    for pr in base.precos:
        assert pr.produto in base.produtos, pr
        assert pr.mercado in base.mercados, pr
        assert pr.preco > 0, pr
        assert pr.data and pr.fonte, pr


def test_nao_ha_preco_duplicado_para_o_mesmo_produto_e_mercado(base):
    chaves = [(pr.produto, pr.mercado) for pr in base.precos]
    assert len(chaves) == len(set(chaves))


def test_todo_produto_tem_preco_em_pelo_menos_um_mercado(base):
    com_preco = {pr.produto for pr in base.precos}
    assert set(base.produtos) == com_preco


def test_preco_por_kg():
    from economia.dados import Preco, Produto

    produto = Produto("arroz-5kg", "arroz", "Arroz 5 kg", 5000)
    preco = Preco("arroz-5kg", "A", 27.90, "2026-10-20", "exemplo")
    assert preco_por_kg(produto, preco) == pytest.approx(5.58)
