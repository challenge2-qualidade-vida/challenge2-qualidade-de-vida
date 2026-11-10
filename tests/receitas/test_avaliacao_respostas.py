import pytest

from economia.receitas.aplicacao.avaliacao import (
    AVISO_DE_PRECO,
    NAO_ENCONTRAR,
    RESPONDER,
    Esperado,
    PerguntaDeAvaliacao,
)
from economia.receitas.aplicacao.avaliacao_respostas import (
    ResultadoDaResposta,
    avaliar_respostas,
    citou_fonte_esperada,
    comportamento_obtido,
    resumir_respostas,
)
from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO as TEXTO_DO_AVISO,
)
from economia.receitas.aplicacao.responder_pergunta import NAO_ENCONTREI
from economia.receitas.dominio.modelos import RespostaComFontes, TrechoRecuperado


def respondida(*trechos):
    return RespostaComFontes(
        texto="Veja [1].",
        encontrou=True,
        trechos=tuple(TrechoRecuperado(t, 0.9) for t in trechos),
        fontes=tuple(t.fonte for t in trechos),
    )


NAO_ACHOU = RespostaComFontes(texto=NAO_ENCONTREI, encontrou=False)
AVISO = RespostaComFontes(texto=TEXTO_DO_AVISO, encontrou=False)


def resultado(id, esperado, obtido, fonte=None, categoria="x", segundos=1.0):
    return ResultadoDaResposta(id, categoria, esperado, obtido, fonte, segundos)


def test_comportamento_obtido(trecho):
    assert comportamento_obtido(respondida(trecho("a"))) == RESPONDER
    assert comportamento_obtido(NAO_ACHOU) == NAO_ENCONTRAR
    assert comportamento_obtido(AVISO) == AVISO_DE_PRECO


def test_comportamento_esperado_derivado_do_gabarito():
    assert (
        PerguntaDeAvaliacao("p", "?", "x", (Esperado("a"),)).comportamento_esperado
        == RESPONDER
    )
    assert PerguntaDeAvaliacao("p", "?", "x").comportamento_esperado == NAO_ENCONTRAR
    preco = PerguntaDeAvaliacao("p", "?", "preco", comportamento=AVISO_DE_PRECO)
    assert preco.comportamento_esperado == AVISO_DE_PRECO


def test_pergunta_rejeita_comportamento_invalido():
    with pytest.raises(ValueError):
        PerguntaDeAvaliacao("p", "?", "x", comportamento="inventar")
    with pytest.raises(ValueError):
        PerguntaDeAvaliacao("p", "?", "x", comportamento=RESPONDER)


def test_citou_fonte_esperada(trecho):
    pergunta = PerguntaDeAvaliacao("p", "?", "x", (Esperado("b"),))
    assert citou_fonte_esperada(pergunta, respondida(trecho("a"), trecho("b"))) is True
    assert citou_fonte_esperada(pergunta, respondida(trecho("a"))) is False
    assert citou_fonte_esperada(pergunta, NAO_ACHOU) is None
    sem_gabarito = PerguntaDeAvaliacao("p", "?", "x")
    assert citou_fonte_esperada(sem_gabarito, respondida(trecho("a"))) is None


def test_resumo_calcula_as_taxas_e_lista_os_erros():
    resumo = resumir_respostas(
        [
            resultado("r1", RESPONDER, RESPONDER, True, "receita", 2.0),
            resultado("r2", RESPONDER, RESPONDER, False, "receita", 4.0),
            resultado("r3", RESPONDER, NAO_ENCONTRAR, None, "receita", 1.0),
            resultado("s1", NAO_ENCONTRAR, NAO_ENCONTRAR, None, "sem", 1.0),
            resultado("s2", NAO_ENCONTRAR, RESPONDER, None, "sem", 1.0),
            resultado("$1", AVISO_DE_PRECO, AVISO_DE_PRECO, None, "preco", 0.0),
        ]
    )
    assert resumo.perguntas == 6
    assert resumo.acuracia == pytest.approx(4 / 6)
    assert resumo.taxa_de_resposta == pytest.approx(2 / 3)
    assert resumo.recusa_correta == pytest.approx(1 / 2)
    assert resumo.aviso_de_preco == 1.0
    assert resumo.fonte_esperada == pytest.approx(1 / 2)
    assert resumo.falsas_recusas == ("r3",)
    assert resumo.respostas_indevidas == ("s2",)
    assert resumo.latencia_media == pytest.approx(9 / 6)
    assert resumo.latencia_maxima == 4.0
    assert resumo.por_categoria["receita"]["acuracia"] == pytest.approx(2 / 3)
    assert resumo.por_categoria["sem"]["recusa_correta"] == pytest.approx(1 / 2)
    assert resumo.por_categoria["preco"]["taxa_de_resposta"] is None


def test_resumo_sem_perguntas_falha():
    with pytest.raises(ValueError):
        resumir_respostas([])


def test_avaliar_respostas_roda_o_caso_de_uso_em_cada_pergunta(trecho):
    perguntas = [
        PerguntaDeAvaliacao("r1", "bolo", "receita", (Esperado("bolo"),)),
        PerguntaDeAvaliacao("s1", "pneu", "sem_resposta"),
        PerguntaDeAvaliacao("$1", "preço", "preco", comportamento=AVISO_DE_PRECO),
    ]
    respostas = {
        "bolo": respondida(trecho("bolo"), trecho("bolo")),
        "pneu": NAO_ACHOU,
        "preço": AVISO,
    }
    tempos = iter([0.0, 3.0, 3.0, 4.0, 4.0, 4.5])
    vistos = []
    resumo = avaliar_respostas(
        perguntas,
        respostas.__getitem__,
        ao_progredir=lambda n, total, r: vistos.append((n, total, r.id)),
        relogio=lambda: next(tempos),
    )
    assert resumo.acuracia == 1.0
    assert resumo.fonte_esperada == 1.0
    assert [r.segundos for r in resumo.resultados] == [3.0, 1.0, 0.5]
    assert resumo.resultados[0].documentos_citados == ("bolo",)
    assert vistos == [(1, 3, "r1"), (2, 3, "s1"), (3, 3, "$1")]
