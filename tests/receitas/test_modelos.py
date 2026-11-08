import pytest

from economia.receitas.dominio.modelos import (
    Fonte,
    Ingrediente,
    Receita,
    RespostaComFontes,
    TipoDeTrecho,
    Trecho,
    TrechoRecuperado,
)

FONTE = Fonte(titulo="afrodite.json", instituicao="afrodite.json (GitHub)")


def receita(ingredientes=("ovo",), preparo=("Bata os ovos.",)) -> Receita:
    return Receita(
        documento_id="afrodite:1",
        titulo="Omelete",
        ingredientes=tuple(Ingrediente(i) for i in ingredientes),
        modo_de_preparo=preparo,
        fonte=FONTE,
    )


def test_fonte_exige_titulo_e_instituicao():
    with pytest.raises(ValueError):
        Fonte(titulo=" ", instituicao="MS")
    with pytest.raises(ValueError):
        Fonte(titulo="Guia", instituicao="")


def test_ingrediente_exige_texto():
    with pytest.raises(ValueError):
        Ingrediente("  ")


@pytest.mark.parametrize(
    ("ingredientes", "preparo", "completa"),
    [
        (("ovo",), ("Bata os ovos.",), True),
        ((), ("Bata os ovos.",), False),
        (("ovo",), (), False),
        (("ovo",), ("  ",), False),
    ],
)
def test_receita_completa_tem_ingredientes_e_preparo(ingredientes, preparo, completa):
    assert receita(ingredientes, preparo).esta_completa is completa


def trecho_recuperado() -> TrechoRecuperado:
    trecho = Trecho(
        id="afrodite:1",
        tipo=TipoDeTrecho.RECEITA,
        documento_id="afrodite:1",
        titulo="Omelete",
        texto="Receita: Omelete.",
        conteudo="# Omelete",
        fonte=FONTE,
    )
    return TrechoRecuperado(trecho=trecho, score=0.9)


def test_resposta_que_encontrou_precisa_citar_fonte():
    with pytest.raises(ValueError, match="RN10"):
        RespostaComFontes(
            texto="Faça uma omelete.", encontrou=True, trechos=(trecho_recuperado(),)
        )


def test_resposta_sem_informacao_nao_tem_trechos_nem_fontes():
    with pytest.raises(ValueError):
        RespostaComFontes(texto="Não encontrei.", encontrou=False, fontes=(FONTE,))
    resposta = RespostaComFontes(texto="Não encontrei.", encontrou=False)
    assert resposta.fontes == ()


def test_resposta_com_fontes_valida():
    resposta = RespostaComFontes(
        texto="Faça uma omelete [1].",
        encontrou=True,
        trechos=(trecho_recuperado(),),
        fontes=(FONTE,),
    )
    assert resposta.fontes == (FONTE,)
