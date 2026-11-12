import json

import pytest

from economia.receitas.aplicacao.avaliacao import (
    Esperado,
    PerguntaDeAvaliacao,
    ResultadoDaPergunta,
    avaliar,
    carregar_perguntas,
    posicao_do_primeiro_acerto,
    resumir,
)
from economia.receitas.dominio.modelos import TipoDeTrecho, TrechoRecuperado


def resultado(id, tem_resposta, posicao, score, segundos=0.1):
    return ResultadoDaPergunta(id, "x", tem_resposta, posicao, score, segundos)


def test_esperado_por_documento_e_por_secao(trecho):
    from dataclasses import replace

    guia = replace(
        trecho("g", tipo=TipoDeTrecho.CONHECIMENTO),
        documento_id="guia",
        secao="Passo 1",
    )
    assert Esperado("guia").corresponde(guia)
    assert Esperado("guia", secao="passo 1").corresponde(guia)
    assert not Esperado("guia", secao="Passo 2").corresponde(guia)
    assert not Esperado("outro").corresponde(guia)


def test_posicao_do_primeiro_acerto(trecho):
    recuperados = [TrechoRecuperado(trecho(id), 0.9) for id in ("a", "b", "c")]
    pergunta = PerguntaDeAvaliacao("p", "?", "receita", (Esperado("c"), Esperado("b")))
    assert posicao_do_primeiro_acerto(pergunta, recuperados) == 2
    sem_acerto = PerguntaDeAvaliacao("p", "?", "receita", (Esperado("z"),))
    assert posicao_do_primeiro_acerto(sem_acerto, recuperados) is None


def test_resumo_calcula_recall_mrr_e_separacao():
    resumo = resumir(
        "modelo",
        5,
        [
            resultado("1", True, 1, 0.90),
            resultado("2", True, 2, 0.85),
            resultado("3", True, None, 0.84),
            resultado("4", False, None, 0.80),
            resultado("5", False, None, 0.70),
        ],
    )
    assert resumo.recall == pytest.approx(2 / 3)
    assert resumo.mrr == pytest.approx((1 + 0.5 + 0) / 3)
    assert resumo.menor_score_com_resposta == 0.84
    assert resumo.maior_score_sem_resposta == 0.80
    assert resumo.separacao == pytest.approx(0.04)
    assert resumo.limiar_sugerido == 0.82
    assert resumo.latencia_media == pytest.approx(0.1)


def test_resumo_exige_perguntas_com_resposta():
    with pytest.raises(ValueError):
        resumir("m", 5, [resultado("1", False, None, 0.5)])


def test_carregar_perguntas(tmp_path):
    arquivo = tmp_path / "perguntas.json"
    arquivo.write_text(
        json.dumps(
            {
                "perguntas": [
                    {
                        "id": "p1",
                        "pergunta": "Como guardar alface?",
                        "categoria": "conservacao",
                        "esperados": [{"documento_id": "embrapa-geladeira"}],
                    },
                    {"id": "p2", "pergunta": "Jiló?", "categoria": "sem_resposta"},
                ]
            }
        ),
        encoding="utf-8",
    )
    [p1, p2] = carregar_perguntas(arquivo)
    assert p1.esperados == (Esperado("embrapa-geladeira"),)
    assert p1.tem_resposta and not p2.tem_resposta
    assert p1.resposta_referencia is None


def test_carregar_perguntas_com_resposta_de_referencia(tmp_path):
    arquivo = tmp_path / "perguntas.json"
    arquivo.write_text(
        json.dumps(
            {
                "perguntas": [
                    {
                        "id": "p1",
                        "pergunta": "Como guardar alface?",
                        "categoria": "conservacao",
                        "esperados": [{"documento_id": "embrapa-geladeira"}],
                        "resposta_referencia": "Guarde a alface seca num pote fechado.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    [p1] = carregar_perguntas(arquivo)
    assert p1.resposta_referencia == "Guarde a alface seca num pote fechado."


def test_avaliar_busca_sem_limiar_e_mede(trecho):
    class Gerador:
        nome = "falso"

        def gerar_para_pergunta(self, pergunta):
            return [1.0]

    class Repositorio:
        def buscar(self, vetor, limite, tipo=None):
            return [
                TrechoRecuperado(trecho("a"), 0.6),
                TrechoRecuperado(trecho("b"), 0.5),
            ]

    perguntas = [
        PerguntaDeAvaliacao("p1", "?", "receita", (Esperado("b"),)),
        PerguntaDeAvaliacao("p2", "?", "sem_resposta"),
    ]
    resumo = avaliar(perguntas, Gerador(), Repositorio(), k=5)
    assert resumo.recall == 1.0
    assert resumo.mrr == 0.5
    assert resumo.resultados[0].titulos == ("Título a", "Título b")
    assert resumo.maior_score_sem_resposta == 0.6


def test_avaliacao_por_categoria():
    from economia.receitas.aplicacao.avaliacao import por_categoria

    resultados = [
        ResultadoDaPergunta("1", "receita", True, 1, 0.90, 0.1),
        ResultadoDaPergunta("2", "receita", True, None, 0.85, 0.1),
        ResultadoDaPergunta("3", "nutricao", True, 2, 0.88, 0.1),
        ResultadoDaPergunta("4", "sem_resposta", False, None, 0.83, 0.1),
    ]
    categorias = por_categoria(resultados)
    assert list(categorias) == ["nutricao", "receita", "sem_resposta"]
    assert categorias["receita"]["recall"] == 0.5
    assert categorias["receita"]["mrr"] == 0.5
    assert categorias["nutricao"]["mrr"] == 0.5
    assert categorias["sem_resposta"]["recall"] is None
    assert categorias["sem_resposta"]["maior_score"] == 0.83


def test_avaliacao_ignora_perguntas_de_preco(trecho):
    from economia.receitas.aplicacao.avaliacao import AVISO_DE_PRECO

    class Gerador:
        nome = "falso"

        def gerar_para_pergunta(self, pergunta):
            return [1.0]

    class Repositorio:
        def buscar(self, vetor, k):
            return [TrechoRecuperado(trecho("a"), 0.9)]

    perguntas = [
        PerguntaDeAvaliacao("r", "?", "receita", (Esperado("a"),)),
        PerguntaDeAvaliacao("$", "?", "preco", comportamento=AVISO_DE_PRECO),
    ]
    resumo = avaliar(perguntas, Gerador(), Repositorio())
    assert [r.id for r in resumo.resultados] == ["r"]


def test_conjunto_v2_e_valido():
    from pathlib import Path

    from economia.receitas.aplicacao.avaliacao import COMPORTAMENTOS

    perguntas = carregar_perguntas(Path("data/avaliacao/perguntas_rag_v2.json"))
    ids = [p.id for p in perguntas]
    assert len(ids) == len(set(ids))
    assert len(perguntas) >= 60
    assert {p.comportamento_esperado for p in perguntas} == set(COMPORTAMENTOS)
    # as 26 perguntas da v1 continuam, para comparar com os resultados antigos
    v1 = {
        p.id for p in carregar_perguntas(Path("data/avaliacao/perguntas_rag_v1.json"))
    }
    assert v1 <= set(ids)
