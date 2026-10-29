import pytest

from economia.dados import carregar
from economia.explicacao import data_br, explicar, reais
from economia.otimizador import Pedido
from economia.planejador import planejar


@pytest.fixture(scope="module")
def base():
    return carregar()


def test_um_mercado_e_o_mais_barato_entre_os_mercados(base):
    plano = planejar(base, Pedido(orcamento=None, pessoas=4))
    custos = [c.custo_total for c in plano.cestas_por_mercado.values() if c]
    assert plano.um_mercado.custo_total == min(custos)
    assert len(plano.um_mercado.mercados) == 1


def test_dois_mercados_nunca_e_mais_caro_que_um(base):
    plano = planejar(base, Pedido(orcamento=None, pessoas=4))
    assert len(plano.dois_mercados.mercados) == 2
    assert plano.dois_mercados.custo_total <= plano.um_mercado.custo_total


def test_deslocamento_alto_faz_recomendar_um_mercado(base):
    plano = planejar(base, Pedido(orcamento=None, pessoas=4), custo_deslocamento=1000)
    assert plano.recomendacao == "um"
    assert plano.cesta_recomendada is plano.um_mercado


def test_sem_deslocamento_recomenda_dois_se_for_mais_barato(base):
    plano = planejar(base, Pedido(orcamento=None, pessoas=4), custo_deslocamento=0)
    esperado = "dois" if plano.economia_bruta_dois > 0.005 else "um"
    assert plano.recomendacao == esperado


def test_orcamento_insuficiente_informa_minimo(base):
    plano = planejar(base, Pedido(orcamento=100, pessoas=4))
    assert plano.recomendacao is None
    assert plano.minimo_necessario > 100
    texto = " ".join(explicar(plano, base))
    assert "não dá para cumprir" in texto


def test_explicacao_cita_mercado_orcamento_e_aviso_de_exemplo(base):
    plano = planejar(base, Pedido(orcamento=900, pessoas=4), custo_deslocamento=15)
    texto = " ".join(explicar(plano, base))
    assert plano.um_mercado.itens[0].mercado in texto
    assert "Sobram" in texto
    assert "preços de exemplo" in texto
    assert "nutricionista" in texto


def test_formato_reais():
    assert reais(1234.5) == "R$ 1.234,50"
    assert reais(0) == "R$ 0,00"


def test_formato_data():
    assert data_br("2026-10-20") == "20/10/2026"


def test_dois_mercados_com_deslocamento_cabe_no_orcamento(base):
    sem_limite = planejar(base, Pedido(orcamento=None, pessoas=4), custo_deslocamento=10)
    orcamento = sem_limite.dois_mercados.custo_total + 5   # comida cabe, comida + deslocamento não
    plano = planejar(base, Pedido(orcamento=orcamento, pessoas=4), custo_deslocamento=10)
    if plano.recomendacao == "dois":
        assert plano.dois_mercados.custo_total + 10 <= orcamento
    assert plano.cesta_recomendada is None or plano.cesta_recomendada.custo_total <= orcamento


def test_minimo_necessario_e_maior_que_o_orcamento_e_suficiente(base):
    plano = planejar(base, Pedido(orcamento=150, pessoas=4, periodo="semana"), custo_deslocamento=10)
    assert plano.recomendacao is None
    assert plano.minimo_necessario > 150
    com_minimo = planejar(base, Pedido(orcamento=plano.minimo_necessario, pessoas=4, periodo="semana"), custo_deslocamento=10)
    assert com_minimo.recomendacao is not None
