import pytest

from economia.cardapio import NOMES, RECEITAS, TERMOS_ALIMENTOS, montar_cardapio, problemas_cardapio, resolver_alimentos, texto_cardapio
from economia.dados import carregar
from economia.metas import DIAS_POR_PERIODO
from economia.otimizador import Pedido
from economia.planejador import planejar


@pytest.fixture(scope="module")
def base():
    return carregar()


def test_receitas_so_usam_alimentos_da_base(base):
    assert NOMES.keys() == base.alimentos.keys()
    assert TERMOS_ALIMENTOS.keys() == base.alimentos.keys()
    for r in RECEITAS:
        for a in [x for vaga in r["requer"] for x in vaga] + r["opcional"]:
            assert a in base.alimentos, f"{r['id']}: {a}"


def test_preparo_nao_cita_cru_nem_ingrediente_opcional(base):
    for r in RECEITAS:
        t = r["preparo"].lower()
        assert " cru" not in t
        for a in r["opcional"]:
            if a != "oleo_soja":
                assert NOMES[a] not in t, f"{r['id']} cita {a}"


def test_resolve_nomes_e_ids(base):
    assert resolver_alimentos(base, ["arroz", "Feijão carioca (cru)", "abóbora", "xyz"]) == ["arroz", "feijao_carioca", "abobora"]


def test_nao_usa_alimento_fora_da_cesta(base):
    cesta = ["arroz", "feijao_carioca", "ovo"]
    c = montar_cardapio(base, cesta, [], 3)
    assert {a for dia in c.dias for r in dia for a in r.alimentos} <= set(cesta)
    assert not c.vazio


def test_respeita_restricao_mesmo_se_o_alimento_vier_na_lista(base):
    c = montar_cardapio(base, ["arroz", "feijao_carioca", "frango_coxa", "ovo"], ["vegetariano"], 3)
    assert "frango_coxa" not in {a for dia in c.dias for r in dia for a in r.alimentos}


def test_usa_primeiro_o_que_estraga_rapido(base):
    c = montar_cardapio(base, ["arroz", "feijao_carioca", "repolho", "batata", "ovo"], [], 3)
    assert "repolho" in {a for r in c.dias[0] for a in r.alimentos}


def test_nao_repete_prato_no_mesmo_dia(base):
    c = montar_cardapio(base, ["arroz", "feijao_carioca", "repolho", "ovo", "macarrao", "banana"], [], 7)
    for dia in c.dias:
        assert len({r.receita for r in dia}) == len(dia)


@pytest.mark.parametrize("restricoes", [(), ("vegetariano",), ("sem_gluten",), ("sem_lactose",), ("sem_ovo",)])
@pytest.mark.parametrize("pessoas,periodo", [(1, "semana"), (4, "mes")])
def test_toda_cesta_do_otimizador_gera_almoco_e_jantar_todo_dia(base, pessoas, periodo, restricoes):
    pedido = Pedido(12 * pessoas * DIAS_POR_PERIODO[periodo], pessoas, periodo, restricoes)
    cesta = planejar(base, pedido).cesta_recomendada
    assert cesta is not None
    ids = sorted({i.alimento_id for i in cesta.itens})
    c = montar_cardapio(base, ids, list(restricoes), 7)
    for dia in c.dias:
        tipos = [r.tipo for r in dia]
        assert "almoco" in tipos and "jantar" in tipos
    assert set(a for dia in c.dias for r in dia for a in r.alimentos) <= set(ids)
    # A Mia não pode encontrar alimento cru ou fora da cesta no texto final.
    assert problemas_cardapio(texto_cardapio(c), ids) == []


def test_mia_detecta_problemas():
    assert problemas_cardapio("Jantar: feijão carioca cru", ["feijao_carioca"]) == ["cita alimento cru"]
    assert "fora da cesta: tomate" in problemas_cardapio("salada de tomate", ["arroz"])[0]
    assert "alface" in problemas_cardapio("salada de alface", ["arroz"])[0]
    assert problemas_cardapio("Arroz soltinho com feijão.", ["arroz", "feijao_preto"]) == []


@pytest.mark.parametrize("r", RECEITAS, ids=lambda r: r["id"])
def test_texto_de_cada_receita_so_cita_o_que_ela_usa(base, r):
    """Com a combinação mais simples de cada receita, o texto não pode citar outro alimento."""
    ids = [vaga[-1] for vaga in r["requer"]]
    c = montar_cardapio(base, ids, [], 1)
    for ref in (x for x in c.dias[0] if x.receita == r["id"]):
        assert problemas_cardapio(texto_cardapio(c), ids) == [], ref.receita
