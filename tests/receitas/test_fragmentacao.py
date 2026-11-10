import pytest

from economia.receitas.aplicacao.fragmentacao import (
    contar_palavras,
    fragmentar_documento,
    fragmentar_receita,
    texto_da_receita,
)
from economia.receitas.dominio.modelos import (
    Documento,
    Fonte,
    Ingrediente,
    Receita,
    Secao,
    TipoDeTrecho,
)

FONTE_RECEITA = Fonte(titulo="RecipeNLG", instituicao="Poznań University of Technology")
FONTE_GUIA = Fonte(
    titulo="Guia Alimentar para a População Brasileira",
    instituicao="Ministério da Saúde",
    ano=2014,
)


def receita(preparo=("Bata os ovos.", "Frite."), idioma="pt") -> Receita:
    return Receita(
        documento_id="recipenlg:42",
        titulo=" Omelete de legumes ",
        ingredientes=(
            Ingrediente("2 ovos", nome="ovo"),
            Ingrediente("1 cenoura ralada"),
        ),
        modo_de_preparo=preparo,
        fonte=FONTE_RECEITA,
        idioma=idioma,
    )


def palavras(n: int, prefixo: str = "p") -> str:
    return " ".join(f"{prefixo}{i}" for i in range(n))


# Receitas


def test_texto_da_receita_traz_titulo_ingredientes_e_preparo_nessa_ordem():
    texto = texto_da_receita(receita())
    assert texto == (
        "Receita: Omelete de legumes. Ingredientes: 2 ovos; 1 cenoura ralada. "
        "Modo de preparo: Bata os ovos. Frite."
    )


def test_corte_da_receita_pega_o_fim_do_modo_de_preparo():
    longa = receita(preparo=(palavras(1000),))
    texto = texto_da_receita(longa, limite=20)
    assert contar_palavras(texto) == 20
    assert texto.startswith(
        "Receita: Omelete de legumes. Ingredientes: 2 ovos; 1 cenoura ralada."
    )


def test_corte_respeita_o_contador_injetado():
    def dois_por_palavra(texto: str) -> int:
        return 2 * len(texto.split())

    texto = texto_da_receita(
        receita(preparo=(palavras(100),)), limite=30, contar=dois_por_palavra
    )
    assert dois_por_palavra(texto) <= 30


def test_receita_vira_um_unico_trecho_com_payload():
    trecho = fragmentar_receita(receita(idioma="en"))
    assert trecho.id == "recipenlg:42"
    assert trecho.tipo is TipoDeTrecho.RECEITA
    assert trecho.titulo == "Omelete de legumes"
    assert trecho.fonte == FONTE_RECEITA
    assert trecho.idioma == "en"
    # usa o nome do alimento quando o dataset informa, senão a linha
    assert trecho.ingredientes == ("ovo", "1 cenoura ralada")
    assert "- 2 ovos" in trecho.conteudo
    assert "Frite." in trecho.conteudo


def test_conteudo_guarda_o_preparo_inteiro_mesmo_com_corte():
    trecho = fragmentar_receita(receita(preparo=(palavras(1000),)), limite=20)
    assert "p999" in trecho.conteudo
    assert "p999" not in trecho.texto


def test_receita_incompleta_nao_vira_trecho():
    with pytest.raises(ValueError):
        fragmentar_receita(receita(preparo=()))


# Documentos de orientação


def documento(*secoes: Secao) -> Documento:
    return Documento(
        documento_id="guia-alimentar",
        titulo=FONTE_GUIA.titulo,
        secoes=secoes,
        fonte=FONTE_GUIA,
    )


def test_secao_curta_vira_um_trecho_com_capitulo_secao_e_pagina():
    secao = Secao(
        titulo="Passo 1",
        paragrafos=("Faça de alimentos in natura a base da alimentação.",),
        capitulo="Dez passos",
        pagina=125,
    )
    [trecho] = fragmentar_documento(documento(secao))
    assert trecho.tipo is TipoDeTrecho.CONHECIMENTO
    assert trecho.id == "guia-alimentar:0:0"
    assert (trecho.capitulo, trecho.secao, trecho.pagina) == (
        "Dez passos",
        "Passo 1",
        125,
    )
    assert trecho.texto == "Faça de alimentos in natura a base da alimentação."
    assert trecho.ingredientes == ()


def test_trecho_nunca_junta_duas_secoes():
    # cada um dos Dez passos é uma seção, então vira um trecho próprio
    passos = [
        Secao(titulo=f"Passo {n}", paragrafos=(f"Texto do passo {n}.",))
        for n in range(1, 11)
    ]
    trechos = fragmentar_documento(documento(*passos))
    assert [t.secao for t in trechos] == [f"Passo {n}" for n in range(1, 11)]


def test_paragrafos_curtos_sao_juntados_ate_o_limite():
    secao = Secao(
        titulo="S", paragrafos=(palavras(4, "a"), palavras(4, "b"), palavras(4, "c"))
    )
    trechos = fragmentar_documento(documento(secao), limite=10, sobreposicao=2)
    assert trechos[0].texto == f"{palavras(4, 'a')}\n\n{palavras(4, 'b')}"
    # o trecho seguinte começa com a sobreposição do anterior
    assert trechos[1].texto == f"b2 b3\n\n{palavras(4, 'c')}"


def test_paragrafo_longo_e_dividido_com_sobreposicao():
    secao = Secao(titulo="S", paragrafos=(palavras(25),))
    trechos = fragmentar_documento(documento(secao), limite=10, sobreposicao=3)
    assert all(contar_palavras(t.texto) <= 10 for t in trechos)
    assert trechos[0].texto.split()[-3:] == trechos[1].texto.split()[:3]
    # nenhuma palavra se perde
    vistas = {p for t in trechos for p in t.texto.split()}
    assert vistas == set(palavras(25).split())


def test_todos_os_trechos_respeitam_o_limite():
    secao = Secao(
        titulo="S",
        paragrafos=tuple(palavras(n, f"x{n}_") for n in (3, 40, 7, 12, 1, 9)),
    )
    trechos = fragmentar_documento(documento(secao), limite=10, sobreposicao=3)
    assert all(contar_palavras(t.texto) <= 10 for t in trechos)
    assert len({t.id for t in trechos}) == len(trechos)


def test_palavra_maior_que_o_limite_nao_trava_a_divisao():
    def gigante(texto: str) -> int:
        return sum(100 if p == "GIGANTE" else 1 for p in texto.split())

    secao = Secao(titulo="S", paragrafos=(f"a b GIGANTE c d {palavras(20)}",))
    trechos = fragmentar_documento(
        documento(secao), limite=10, sobreposicao=2, contar=gigante
    )
    assert any("GIGANTE" in t.texto for t in trechos)


def test_paragrafos_vazios_sao_ignorados():
    secao = Secao(titulo="S", paragrafos=("", "  ", "texto"))
    [trecho] = fragmentar_documento(documento(secao))
    assert trecho.texto == "texto"


def test_sobreposicao_precisa_ser_menor_que_o_limite():
    with pytest.raises(ValueError):
        fragmentar_documento(documento(), limite=10, sobreposicao=10)
