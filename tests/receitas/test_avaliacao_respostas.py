from dataclasses import replace

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
    avaliar_pergunta,
    avaliar_respostas,
    citou_fonte_esperada,
    comportamento_obtido,
    resumir_respostas,
)
from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO as TEXTO_DO_AVISO,
)
from economia.receitas.aplicacao.responder_pergunta import NAO_ENCONTREI
from economia.receitas.aplicacao.responder_sem_base import RespostaSemBase
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


REFERENCIA = "Guarde a alface seca num pote fechado."


def com_referencia(id="c1", referencia=REFERENCIA, esperados=("alface",)):
    return PerguntaDeAvaliacao(
        id,
        "como conservo alface?",
        "conservacao",
        tuple(Esperado(e) for e in esperados),
        resposta_referencia=referencia,
    )


def avaliar_uma(pergunta, resposta, gerador=None):
    return avaliar_respostas([pergunta], lambda _: resposta, gerador=gerador)


def test_resposta_igual_a_referencia_tem_rouge_1(trecho):
    resposta = respondida(trecho("alface"))
    resposta = replace(resposta, texto=f"{REFERENCIA} [1]")
    [r] = avaliar_uma(com_referencia(), resposta).resultados
    assert r.rouge_1 == 1.0
    assert r.rouge_l == 1.0
    # sem gerador de embeddings, o cosseno não é calculado
    assert r.cosseno is None


def test_cosseno_usa_o_gerador_de_embeddings():
    class Gerador:
        nome = "falso"
        dimensao = 2

        def gerar_para_trechos(self, textos):
            return [[1.0, 0.0], [0.6, 0.8]]

    resposta = RespostaSemBase(texto="Guarde seca.", encontrou=True)
    [r] = avaliar_uma(com_referencia(), resposta, Gerador()).resultados
    assert r.cosseno == pytest.approx(0.6)


def test_recusa_de_pergunta_com_referencia_zera_as_metricas_de_texto():
    class Gerador:
        nome = "falso"
        dimensao = 2

        def gerar_para_trechos(self, textos):
            raise AssertionError("recusa não passa pelo embedding")

    [r] = avaliar_uma(com_referencia(), NAO_ACHOU, Gerador()).resultados
    assert (r.rouge_1, r.rouge_l, r.cosseno) == (0.0, 0.0, 0.0)


def test_pergunta_sem_referencia_nao_tem_metricas_de_texto():
    resposta = RespostaSemBase(texto="Qualquer coisa.", encontrou=True)
    [r] = avaliar_uma(com_referencia(referencia=None), resposta).resultados
    assert (r.rouge_1, r.rouge_l, r.cosseno) == (None, None, None)


def test_hit_marca_o_gabarito_entre_os_recuperados(trecho):
    recuperados = tuple(TrechoRecuperado(trecho(i), 0.9) for i in ("x", "alface"))
    acertou = replace(respondida(trecho("x")), recuperados=recuperados)
    errou = replace(
        respondida(trecho("x")), recuperados=(TrechoRecuperado(trecho("x"), 0.9),)
    )
    assert avaliar_uma(com_referencia(), acertou).resultados[0].hit == 1
    assert avaliar_uma(com_referencia(), errou).resultados[0].hit == 0


def test_hit_so_olha_os_k_primeiros(trecho):
    recuperados = tuple(
        TrechoRecuperado(trecho(i), 0.9) for i in ("a", "b", "c", "d", "e", "alface")
    )
    resposta = replace(respondida(trecho("a")), recuperados=recuperados)
    resumo = avaliar_respostas([com_referencia()], lambda _: resposta, k=5)
    assert resumo.resultados[0].hit == 0


def test_sem_recuperados_nao_ha_hit():
    # modo puro: a resposta não passou pela busca
    resposta = RespostaSemBase(texto="Guarde seca.", encontrou=True)
    [r] = avaliar_uma(com_referencia(), resposta).resultados
    assert r.hit is None


def test_resumo_tira_a_media_das_metricas_de_texto_e_do_hit():
    def com_metricas(id, rouge_1, rouge_l, cosseno, hit):
        return ResultadoDaResposta(
            id,
            "x",
            RESPONDER,
            RESPONDER,
            None,
            1.0,
            rouge_1=rouge_1,
            rouge_l=rouge_l,
            cosseno=cosseno,
            hit=hit,
        )

    resumo = resumir_respostas(
        [
            com_metricas("a", 1.0, 0.5, 0.9, 1),
            com_metricas("b", 0.0, 0.0, 0.0, 0),
            com_metricas("c", None, None, None, None),
        ]
    )
    assert resumo.rouge_1 == pytest.approx(0.5)
    assert resumo.rouge_l == pytest.approx(0.25)
    assert resumo.cosseno == pytest.approx(0.45)
    assert resumo.hit == pytest.approx(0.5)
    assert resumo.por_categoria["x"]["rouge_1"] == pytest.approx(0.5)


def test_resumo_sem_metricas_de_texto_da_none():
    resumo = resumir_respostas([resultado("a", RESPONDER, RESPONDER)])
    assert (resumo.rouge_1, resumo.rouge_l, resumo.cosseno, resumo.hit) == (
        None,
        None,
        None,
        None,
    )


def test_avaliar_pergunta_avalia_uma_so(trecho):
    pergunta = PerguntaDeAvaliacao("r1", "bolo", "receita", (Esperado("bolo"),))
    tempos = iter([1.0, 3.5])
    r = avaliar_pergunta(
        pergunta, lambda _: respondida(trecho("bolo")), relogio=lambda: next(tempos)
    )
    assert (r.id, r.obtido, r.fonte_esperada, r.segundos) == (
        "r1",
        RESPONDER,
        True,
        2.5,
    )


def test_modo_puro_nao_tem_fonte_esperada():
    # sem busca não há fonte: a métrica não se aplica, em vez de contar como erro
    pergunta = PerguntaDeAvaliacao("c1", "?", "x", (Esperado("alface"),))
    resposta = RespostaSemBase(texto="Guarde na geladeira.", encontrou=True)
    assert citou_fonte_esperada(pergunta, resposta) is None
