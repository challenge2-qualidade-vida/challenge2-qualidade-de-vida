import pytest

from economia.dados import carregar
from economia.rag import BaseConhecimento, contexto_para_llm, tokenizar


@pytest.fixture(scope="module")
def bc():
    return BaseConhecimento(carregar())


def test_base_tem_trechos_do_guia_dos_criterios_e_da_taco(bc):
    ids = {t.id.split("#")[0] for t in bc.trechos}
    assert {"guia-alimentar-principios", "guia-alimentar-grupos", "compras-e-economia", "aproveitamento-e-receitas", "taco"} <= ids
    assert all(t.fonte for t in bc.trechos)


@pytest.mark.parametrize(
    "pergunta, trecho_esperado",
    [
        ("Essa promoção vale a pena?", "promoção vale a pena"),
        ("o que são alimentos ultraprocessados", "ultraprocessados"),
        ("qual é a regra de ouro da alimentação", "Regra de ouro"),
        ("como comparar o preço de embalagens de tamanhos diferentes", "Preço por quilo"),
        ("quanta proteína tem o feijão carioca", "Feijão carioca"),
        ("o que fazer com banana muito madura", "Banana madura"),
        ("receita com lentilha", "lentilha"),
        ("vale a pena ir a dois mercados", "dois mercados"),
    ],
)
def test_busca_encontra_o_trecho_certo(bc, pergunta, trecho_esperado):
    resultados = bc.buscar(pergunta, k=3)
    assert resultados, pergunta
    titulos = " | ".join(r.trecho.titulo for r in resultados)
    assert trecho_esperado.lower() in titulos.lower(), titulos


def test_pergunta_fora_do_tema_nao_retorna_nada(bc):
    assert bc.buscar("quem ganhou a copa do mundo de futebol") == []


def test_resultados_vem_ordenados(bc):
    sims = [r.similaridade for r in bc.buscar("feijão arroz proteína", k=5)]
    assert sims == sorted(sims, reverse=True)


def test_tokenizar_remove_acentos_stopwords_e_plural():
    assert tokenizar("As frutas são ótimas") == ["fruta", "sao", "otima"]


def test_contexto_para_llm_numera_e_cita_fonte(bc):
    texto = contexto_para_llm(bc.buscar("regra de ouro"))
    assert texto.startswith("[1]")
    assert "Fonte:" in texto
    assert "Nenhum trecho" in contexto_para_llm([])
