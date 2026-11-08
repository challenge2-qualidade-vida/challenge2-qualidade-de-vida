"""Passos dos cenários da versão 1 do RAG de receitas (specs/15-rag-receitas/cenarios.feature).

Os cenários de restrições (RN27), notas recentes (RN21), lista de compras (RN29), substituições
(RN28) e busca sob demanda (RN26) ficam fora da versão 1 e ainda não têm passos.
"""

import re

from pytest_bdd import given, parsers, scenario, then, when

from economia.receitas.aplicacao.indexar_base import indexar, montar_trechos
from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO,
    NAO_ENCONTREI,
    ResponderPergunta,
    formatar_fonte,
)
from economia.receitas.dominio.modelos import (
    Documento,
    Fonte,
    Ingrediente,
    Receita,
    Secao,
)

FEATURE = "15-rag-receitas/cenarios.feature"

FONTE_DAS_RECEITAS = Fonte(
    titulo="RecipeNLG",
    instituicao="Poznań University of Technology",
    ano=2020,
    url="https://www.cookbooks.com/receita-de-teste",
)
FONTE_DA_ORIENTACAO = Fonte(
    titulo="Conservação de hortaliças", instituicao="Embrapa", ano=2020
)


@scenario(FEATURE, "Receita sugerida com os ingredientes informados cita a fonte")
def test_receita_sugerida_cita_a_fonte():
    pass


@scenario(FEATURE, "Pergunta sobre conservação é respondida com a fonte")
def test_pergunta_sobre_conservacao():
    pass


@scenario(FEATURE, "Pergunta sem informação na base de conhecimento")
def test_pergunta_sem_informacao():
    pass


@scenario(
    FEATURE, "Pergunta sobre preço atual não é respondida pela base de conhecimento"
)
def test_pergunta_sobre_preco_atual():
    pass


def aspas(texto: str) -> list[str]:
    return re.findall(r'"([^"]+)"', texto)


def adicionar_receita(contexto, titulo: str, ingredientes: list[str]) -> None:
    contexto["receitas"].append(
        Receita(
            documento_id=f"teste:{titulo}",
            titulo=titulo,
            ingredientes=tuple(Ingrediente(i) for i in ingredientes),
            modo_de_preparo=("Misture tudo e leve ao forno.",),
            fonte=FONTE_DAS_RECEITAS,
        )
    )


# ---------------------------------------------------------------- Dado


@given(parsers.parse('que a base de receitas contém a receita "{titulo}"'))
def base_com_receita(contexto, titulo):
    adicionar_receita(contexto, titulo, [])


@given(parsers.re(r"que essa receita usa (?P<lista>.+)"))
def receita_usa(contexto, lista):
    ultima = contexto["receitas"].pop()
    adicionar_receita(contexto, ultima.titulo, aspas(lista))


@given("que a base de conhecimento contém um trecho sobre conservação de folhas")
def base_com_trecho_de_conservacao(contexto):
    contexto["documentos"].append(
        Documento(
            documento_id="embrapa-folhas",
            titulo=FONTE_DA_ORIENTACAO.titulo,
            secoes=(
                Secao(
                    titulo="Folhas",
                    paragrafos=(
                        (
                            "Para conservar alface e outras folhas por mais tempo, lave, "
                            "seque bem e guarde na geladeira num pote fechado com papel toalha."
                        ),
                    ),
                ),
            ),
            fonte=FONTE_DA_ORIENTACAO,
        )
    )


@given(
    parsers.parse('que a base de conhecimento não contém informações sobre "{assunto}"')
)
def base_sem_o_assunto(contexto, assunto):
    base_com_trecho_de_conservacao(contexto)
    contexto["assunto_ausente"] = assunto


# ---------------------------------------------------------------- Quando


@when(parsers.parse('eu pergunto "{pergunta}"'))
def perguntar(contexto, pergunta):
    trechos, _ = montar_trechos(contexto["receitas"], contexto["documentos"])
    if trechos:
        indexar(trechos, contexto["gerador"], contexto["repositorio"])
    caso = ResponderPergunta(
        contexto["gerador"],
        contexto["repositorio"],
        contexto["llm"],
        prompt_do_sistema="",
        limiar=contexto["limiar"],
    )
    contexto["resposta"] = caso.responder(pergunta)


# ---------------------------------------------------------------- Então


def titulos_sugeridos(contexto) -> list[str]:
    return [r.trecho.titulo for r in contexto["resposta"].trechos]


@then(parsers.parse('a resposta sugere a receita "{titulo}"'))
def sugere(contexto, titulo):
    assert titulo in titulos_sugeridos(contexto)


@then("a resposta cita a fonte da receita com o link")
def cita_fonte_com_link(contexto):
    resposta = contexto["resposta"]
    assert resposta.encontrou
    assert FONTE_DAS_RECEITAS in resposta.fontes
    citacao = formatar_fonte(resposta.trechos[0])
    assert FONTE_DAS_RECEITAS.url in citacao


@then("a resposta se baseia nesse trecho")
def baseada_no_trecho(contexto):
    resposta = contexto["resposta"]
    assert resposta.encontrou
    assert [r.trecho.documento_id for r in resposta.trechos] == ["embrapa-folhas"]


@then("a resposta cita a fonte do trecho")
def cita_fonte_do_trecho(contexto):
    assert contexto["resposta"].fontes == (FONTE_DA_ORIENTACAO,)


@then("a resposta informa que não encontrou essa informação na base")
def nao_encontrou(contexto):
    resposta = contexto["resposta"]
    assert not resposta.encontrou
    assert resposta.texto == NAO_ENCONTREI


@then("a resposta informa que preços atuais não vêm da base de conhecimento")
def aviso_de_preco(contexto):
    resposta = contexto["resposta"]
    assert not resposta.encontrou
    assert resposta.texto == AVISO_DE_PRECO
