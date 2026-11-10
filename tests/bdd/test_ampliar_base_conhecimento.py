"""Passos dos cenários da base ampliada e da avaliação (specs/16-ampliar-base-conhecimento)."""

from pytest_bdd import given, parsers, scenario, then, when

from economia.receitas.aplicacao.avaliacao import (
    AVISO_DE_PRECO,
    Esperado,
    PerguntaDeAvaliacao,
    avaliar,
    por_categoria,
)
from economia.receitas.aplicacao.avaliacao_respostas import avaliar_respostas
from economia.receitas.aplicacao.comparacao_de_avaliacoes import comparar_execucoes
from economia.receitas.aplicacao.indexar_base import indexar, montar_trechos
from economia.receitas.aplicacao.responder_pergunta import ResponderPergunta
from economia.receitas.dominio.modelos import Fonte, Ingrediente, Receita
from economia.receitas.infraestrutura.carregadores import catalogo_de_fontes

FEATURE = "16-ampliar-base-conhecimento/cenarios.feature"


@scenario(FEATURE, "A base de conhecimento tem pelo menos 20 documentos-fonte")
def test_base_com_20_fontes():
    pass


@scenario(FEATURE, "A avaliação da recuperação separa o resultado por categoria")
def test_recuperacao_por_categoria():
    pass


@scenario(FEATURE, "A avaliação das respostas confere o comportamento esperado")
def test_respostas_conferem_o_comportamento():
    pass


@scenario(FEATURE, "A comparação entre duas execuções mostra a diferença")
def test_comparacao_entre_execucoes():
    pass


# Catálogo


@given("o catálogo de documentos da base de conhecimento", target_fixture="catalogo")
def catalogo():
    return catalogo_de_fontes()


@then("o catálogo tem pelo menos 20 documentos-fonte")
def pelo_menos_20(catalogo):
    assert len(catalogo) >= 20, sorted(catalogo)


@then("cada documento tem título, instituição, link e licença")
def documentos_completos(catalogo):
    for documento_id, fonte in catalogo.items():
        assert fonte.titulo and fonte.instituicao, documento_id
        assert fonte.url and fonte.url.startswith("http"), documento_id
        assert fonte.licenca, documento_id


# Avaliação


@given(parsers.parse('que a base contém só a receita "{titulo}"'))
def base_com_uma_receita(contexto, titulo):
    receita = Receita(
        documento_id="teste:bolo",
        titulo=titulo,
        ingredientes=(
            Ingrediente("cenoura"),
            Ingrediente("ovo"),
            Ingrediente("farinha"),
        ),
        modo_de_preparo=("Bata tudo e asse.",),
        fonte=Fonte(
            titulo="Receitas de teste", instituicao="Equipe", url="https://exemplo.org"
        ),
    )
    trechos, _ = montar_trechos([receita], [])
    indexar(trechos, contexto["gerador"], contexto["repositorio"])
    contexto["perguntas"] = []


@given(
    parsers.parse(
        'um conjunto de avaliação com a pergunta "{pergunta}" na categoria "{categoria}" '
        "esperando essa receita"
    )
)
def pergunta_da_receita(contexto, pergunta, categoria):
    contexto["perguntas"].append(
        PerguntaDeAvaliacao("r1", pergunta, categoria, (Esperado("teste:bolo"),))
    )


@given(
    parsers.parse(
        'a pergunta "{pergunta}" na categoria "{categoria}" esperando o documento "{documento}"'
    )
)
def pergunta_de_outro_documento(contexto, pergunta, categoria, documento):
    contexto["perguntas"].append(
        PerguntaDeAvaliacao("n1", pergunta, categoria, (Esperado(documento),))
    )


@given(
    parsers.parse(
        'a pergunta "{pergunta}" na categoria "{categoria}" sem resposta na base'
    )
)
def pergunta_sem_resposta(contexto, pergunta, categoria):
    contexto["perguntas"].append(PerguntaDeAvaliacao("s1", pergunta, categoria))


@given(
    parsers.parse(
        'a pergunta "{pergunta}" na categoria "{categoria}" com aviso de preço'
    )
)
def pergunta_de_preco(contexto, pergunta, categoria):
    contexto["perguntas"].append(
        PerguntaDeAvaliacao("p1", pergunta, categoria, comportamento=AVISO_DE_PRECO)
    )


@when("eu avalio a recuperação")
def avaliar_recuperacao(contexto):
    resumo = avaliar(
        contexto["perguntas"], contexto["gerador"], contexto["repositorio"]
    )
    contexto["categorias"] = por_categoria(resumo.resultados)


@then(parsers.parse('o Recall@5 da categoria "{categoria}" é {valor:d}'))
def recall_da_categoria(contexto, categoria, valor):
    assert contexto["categorias"][categoria]["recall"] == valor


@when("eu avalio as respostas")
def avaliar_as_respostas(contexto):
    caso = ResponderPergunta(
        contexto["gerador"],
        contexto["repositorio"],
        contexto["llm"],
        prompt_do_sistema="sistema",
        limiar=contexto["limiar"],
    )
    contexto["resumo"] = avaliar_respostas(contexto["perguntas"], caso.responder)


@then(parsers.parse("a acurácia do comportamento é {valor:d}"))
def acuracia(contexto, valor):
    resumo = contexto["resumo"]
    assert resumo.acuracia == valor, [
        (r.id, r.esperado, r.obtido) for r in resumo.resultados
    ]


@then(parsers.parse('a resposta da categoria "{categoria}" cita a fonte esperada'))
def cita_fonte_esperada(contexto, categoria):
    assert contexto["resumo"].por_categoria[categoria]["fonte_esperada"] == 1


# Comparação


def _execucao(recall: float) -> dict:
    return {"modelos": [{"recall": recall, "por_categoria": {}}]}


@given(parsers.parse("uma execução com Recall@5 de {valor}"))
def execucao_anterior(contexto, valor):
    contexto["antes"] = _execucao(float(valor.replace(",", ".")))


@given(parsers.parse("uma execução seguinte com Recall@5 de {valor}"))
def execucao_seguinte(contexto, valor):
    contexto["depois"] = _execucao(float(valor.replace(",", ".")))


@when("eu comparo as duas execuções")
def comparar(contexto):
    contexto["diferencas"] = {
        d.metrica: d for d in comparar_execucoes(contexto["antes"], contexto["depois"])
    }


@then(parsers.parse("a diferença do Recall@5 é {valor}"))
def diferenca_do_recall(contexto, valor):
    assert contexto["diferencas"]["recall"].delta == float(valor.replace(",", "."))
