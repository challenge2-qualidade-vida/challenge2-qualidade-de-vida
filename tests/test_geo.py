import pytest

from economia.dados import carregar
from economia.geo import (
    custo_ida_volta,
    custo_segundo_mercado,
    distancia_km,
    ler_overpass,
    mercados_proximos,
    ranking_proteinas,
)
from economia.otimizador import Pedido
from economia.planejador import planejar

ASA_NORTE = (-15.7617, -47.8825)
GUARA = (-15.8230, -47.9790)


@pytest.fixture(scope="module")
def base():
    return carregar()


def test_distancia_entre_asa_norte_e_guara():
    # ~12,4 km em linha reta
    assert distancia_km(*ASA_NORTE, *GUARA) == pytest.approx(12.4, abs=0.3)
    assert distancia_km(*ASA_NORTE, *ASA_NORTE) == 0


def test_custo_ida_volta():
    # 10 km × 1,3 (ruas) × 2 (ida e volta) × R$ 0,65
    assert custo_ida_volta(10) == pytest.approx(16.90)


def test_mercados_proximos_filtra_pelo_raio_e_ordena(base):
    perto = mercados_proximos(base, *ASA_NORTE, raio_km=8)
    assert [m.id for m in perto] == ["A", "B"]
    assert perto[0].distancia_km == 0
    longe = mercados_proximos(base, *ASA_NORTE, raio_km=50)
    assert [m.id for m in longe] == ["A", "B", "C"]


def test_custo_do_segundo_mercado(base):
    perto = mercados_proximos(base, *ASA_NORTE, raio_km=50)
    assert custo_segundo_mercado(perto) == perto[1].custo_ida_volta
    assert custo_segundo_mercado(perto[:1]) == 0


def test_coordenadas_invalidas(base):
    with pytest.raises(ValueError):
        mercados_proximos(base, 200, 0, 10)


def test_ranking_proteinas(base):
    r = ranking_proteinas(base, ["A", "B", "C"])
    por_id = {a["alimento_id"]: a for a in r["alimentos"]}
    # Coxa de frango: A 13,90 · B 12,99 · C 14,49
    assert por_id["frango_coxa"]["melhor_mercado"] == "B"
    assert por_id["frango_coxa"]["precos"]["B"]["preco_kg"] == 12.99
    # Patinho: 42,90/kg com 21,7 g de proteína por 100 g → R$ 19,77 por 100 g de proteína
    assert por_id["patinho"]["precos"]["B"]["custo_100g_proteina"] == pytest.approx(19.77, abs=0.01)
    # Ordenado da proteína mais barata para a mais cara
    custos = [a["precos"][a["melhor_mercado"]]["custo_100g_proteina"] for a in r["alimentos"]]
    assert custos == sorted(custos)
    # Feijão preto não existe no C, então fica fora do carrinho comum
    assert "Feijão preto" not in r["carrinho"]["itens"]
    assert r["carrinho"]["melhor_mercado"] in ("A", "B", "C")


def test_ranking_so_com_mercados_pedidos(base):
    r = ranking_proteinas(base, ["A"])
    assert all(set(a["precos"]) == {"A"} for a in r["alimentos"])


def test_planejar_so_com_mercados_proximos(base):
    plano = planejar(base, Pedido(orcamento=None, pessoas=2), mercados=["A", "B"])
    assert set(plano.cestas_por_mercado) == {"A", "B"}
    assert set(plano.cesta_recomendada.mercados) <= {"A", "B"}


def test_ler_overpass():
    dados = {"elements": [
        {"type": "node", "lat": -15.762, "lon": -47.883, "tags": {"name": "Mercado A", "shop": "supermarket"}},
        {"type": "way", "center": {"lat": -15.770, "lon": -47.890}, "tags": {"name": "Supermercado Novo", "shop": "supermarket"}},
        {"type": "node", "lat": -15.770, "lon": -47.890, "tags": {"name": "Supermercado Novo"}},
        {"type": "node", "lat": -15.700, "lon": -47.800, "tags": {"shop": "supermarket"}},
    ]}
    from economia.dados import Mercado

    r = ler_overpass(dados, *ASA_NORTE, [Mercado("A", "Mercado A", "x")])
    assert [m["nome"] for m in r] == ["Mercado A", "Supermercado Novo"]   # sem nome e duplicado saem
    assert r[0]["tem_precos"] and not r[1]["tem_precos"]
