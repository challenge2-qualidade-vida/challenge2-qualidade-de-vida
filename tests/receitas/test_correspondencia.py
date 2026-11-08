import pytest

from economia.receitas.dominio.correspondencia import (
    ingredientes_que_faltam,
    normalizar,
)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("2 Cenouras raladas", ("2", "cenoura", "ralada")),
        ("Limões", ("limao",)),
        ("pães", ("pao",)),
        ("3 colheres de açúcar", ("3", "colher", "de", "acucar")),
        ("nozes", ("noz",)),
        ("feijões", ("feijao",)),
        ("arroz", ("arroz",)),
        ("ovos", ("ovo",)),
    ],
)
def test_normalizar_em_portugues(texto, esperado):
    # números saem: só letras viram palavras
    assert normalizar(texto) == tuple(p for p in esperado if not p.isdigit())


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("tomatoes", ("tomato",)),
        ("berries", ("berry",)),
        ("2 eggs", ("egg",)),
        ("molasses", ("molass",)),
        ("glass", ("glass",)),
    ],
)
def test_normalizar_em_ingles(texto, esperado):
    assert normalizar(texto, idioma="en") == esperado


def test_ingrediente_disponivel_quando_o_nome_aparece_na_linha():
    faltam = ingredientes_que_faltam(
        ["2 xícaras de farinha de trigo", "3 ovos", "1 copo de leite"],
        disponiveis=["farinha", "ovo"],
    )
    assert faltam == ["1 copo de leite"]


def test_nome_com_varias_palavras_precisa_aparecer_em_sequencia():
    assert ingredientes_que_faltam(["leite condensado"], ["leite condensado"]) == []
    assert ingredientes_que_faltam(["leite de coco"], ["leite condensado"]) == [
        "leite de coco"
    ]


def test_basicos_contam_como_disponiveis():
    faltam = ingredientes_que_faltam(
        ["sal a gosto", "água", "óleo para fritar", "ovo"],
        disponiveis=[],
        basicos=["sal", "agua", "oleo"],
    )
    assert faltam == ["ovo"]


def test_sem_ingredientes_disponiveis_falta_tudo():
    assert ingredientes_que_faltam(["ovo", "leite"], disponiveis=[]) == ["ovo", "leite"]


def test_palavra_parecida_nao_conta():
    # "ovo" não está em "ovomaltine"
    assert ingredientes_que_faltam(["ovomaltine"], ["ovo"]) == ["ovomaltine"]
