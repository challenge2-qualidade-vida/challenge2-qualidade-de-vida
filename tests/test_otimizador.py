import pytest

from economia.dados import carregar
from economia.metas import RESTRICOES
from economia.otimizador import Pedido, montar_cesta


@pytest.fixture(scope="module")
def base():
    return carregar()


def test_cesta_cumpre_todas_as_metas_nutricionais(base):
    cesta = montar_cesta(base, Pedido(orcamento=None, pessoas=4, periodo="mes"), ("A",))
    assert cesta is not None
    for chave, meta in cesta.metas.items():
        assert cesta.obtido[chave] >= meta - 1e-6, chave


def test_cesta_respeita_orcamento(base):
    sem_limite = montar_cesta(base, Pedido(orcamento=None, pessoas=4), ("A",))
    orcamento = sem_limite.custo_total + 50
    cesta = montar_cesta(base, Pedido(orcamento=orcamento, pessoas=4), ("A",))
    assert cesta.custo_total <= orcamento
    assert cesta.dentro_do_orcamento


def test_orcamento_insuficiente_nao_tem_solucao(base):
    assert montar_cesta(base, Pedido(orcamento=50, pessoas=4), ("A",)) is None


def test_custo_total_e_soma_dos_itens(base):
    cesta = montar_cesta(base, Pedido(orcamento=None, pessoas=2, periodo="semana"), ("B",))
    assert cesta.custo_total == pytest.approx(sum(i.subtotal for i in cesta.itens), abs=0.01)


@pytest.mark.parametrize("restricao", sorted(RESTRICOES))
def test_restricao_remove_alimentos(base, restricao):
    cesta = montar_cesta(base, Pedido(orcamento=None, pessoas=2, restricoes=(restricao,)), ("A",))
    assert cesta is not None
    for item in cesta.itens:
        assert not RESTRICOES[restricao] & set(base.alimentos[item.alimento_id].tags), item.produto


def test_cesta_tem_variedade_de_frutas_e_hortalicas(base):
    cesta = montar_cesta(base, Pedido(orcamento=None, pessoas=4), ("A",))
    flv = {i.alimento_id for i in cesta.itens if i.grupo == "flv"}
    assert len(flv) >= 3


def test_cesta_pequena_e_viavel(base):
    assert montar_cesta(base, Pedido(orcamento=None, pessoas=1, periodo="semana"), ("C",)) is not None


def test_so_compra_nos_mercados_pedidos(base):
    cesta = montar_cesta(base, Pedido(orcamento=None, pessoas=3), ("B",))
    assert {i.mercado_id for i in cesta.itens} == {"B"}


def test_restricao_desconhecida_gera_erro(base):
    with pytest.raises(ValueError):
        montar_cesta(base, Pedido(orcamento=None, pessoas=1, restricoes=("dieta_x",)), ("A",))


def test_cesta_tem_pelo_menos_20_por_cento_de_proteina_animal(base):
    from economia.metas import GRUPOS_PROTEINA_ANIMAL

    cesta = montar_cesta(base, Pedido(orcamento=None, pessoas=4), ("A",))
    animal = sum(
        base.alimentos[i.alimento_id].proteina_g * base.produtos[i.produto_id].embalagem_g / 100 * i.quantidade
        for i in cesta.itens if i.grupo in GRUPOS_PROTEINA_ANIMAL
    )
    assert animal >= 0.20 * cesta.obtido["proteina_g"] - 1e-6


def test_sem_nenhuma_fonte_animal_a_cesta_continua_viavel(base):
    pedido = Pedido(orcamento=None, pessoas=2, restricoes=("vegetariano", "sem_lactose", "sem_ovo"))
    cesta = montar_cesta(base, pedido, ("A",))
    assert cesta is not None
    assert not any(i.grupo in ("proteina_animal", "laticinios") for i in cesta.itens)


# ---------- Trocar item e o que tenho em casa (tópico 19) ----------

def _ids(cesta):
    return {i.alimento_id for i in cesta.itens}


def test_trocar_alimento_tira_da_cesta_e_mantem_as_metas(base):
    original = montar_cesta(base, Pedido(None, 4), ("A",))
    alvo = next(i.alimento_id for i in original.itens if i.grupo == "leguminosas")
    nova = montar_cesta(base, Pedido(None, 4, sem_alimentos=(alvo,)), ("A",))
    assert alvo not in _ids(nova)
    assert nova.custo_total >= original.custo_total
    for chave, meta in nova.metas.items():
        assert nova.obtido[chave] >= meta - 1e-6, chave


def test_o_que_tem_em_casa_barateia_e_conta_para_as_metas(base):
    normal = montar_cesta(base, Pedido(None, 2), ("A",))
    casa = montar_cesta(base, Pedido(None, 2, em_casa=(("arroz", 5000.0), ("feijao_carioca", 3000.0))), ("A",))
    assert casa.custo_total < normal.custo_total
    for chave, meta in casa.metas.items():
        assert casa.obtido[chave] >= meta - 1e-6, chave
    assert casa.em_casa["kcal"] == pytest.approx(358 * 50 + 329 * 30)


def test_custo_por_kcal_nao_conta_o_que_estava_em_casa(base):
    casa = montar_cesta(base, Pedido(None, 2, em_casa=(("arroz", 5000.0),)), ("A",))
    comprado = casa.obtido["kcal"] - casa.em_casa["kcal"]
    assert casa.custo_por_1000_kcal == pytest.approx(casa.custo_total / comprado * 1000)


def test_alimento_em_casa_fora_da_restricao_nao_conta(base):
    casa = montar_cesta(base, Pedido(None, 1, "semana", ("vegetariano",), em_casa=(("frango_coxa", 3000.0),)), ("A",))
    assert casa.em_casa["proteina_g"] == 0


def test_com_tudo_em_casa_nao_precisa_comprar_nada(base):
    fartura = (("arroz", 50000.0), ("feijao_preto", 30000.0), ("ovo", 20000.0), ("banana", 10000.0), ("repolho", 10000.0))
    cesta = montar_cesta(base, Pedido(None, 1, "semana", em_casa=fartura), ("A",))
    assert cesta.itens == []
    assert cesta.custo_total == 0
    assert cesta.custo_por_1000_kcal == 0
