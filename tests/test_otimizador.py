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
