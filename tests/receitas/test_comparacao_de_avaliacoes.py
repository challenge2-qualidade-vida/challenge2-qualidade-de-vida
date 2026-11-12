import pytest

from economia.receitas.aplicacao.comparacao_de_avaliacoes import (
    Diferenca,
    comparar_categorias,
    comparar_execucoes,
    formatar_delta,
    resumo_da_execucao,
    tipo_da_execucao,
)


def recuperacao(recall, mrr=0.5, categorias=None):
    return {
        "k": 5,
        "modelos": [
            {
                "recall": recall,
                "mrr": mrr,
                "score_medio_com_resposta": 0.87,
                "score_medio_sem_resposta": 0.82,
                "separacao": -0.01,
                "latencia_media": 0.1,
                "por_categoria": categorias or {},
            }
        ],
    }


def respostas(acuracia, categorias=None):
    return {
        "acuracia": acuracia,
        "taxa_de_resposta": 0.5,
        "recusa_correta": 1.0,
        "aviso_de_preco": 1.0,
        "fonte_esperada": None,
        "latencia_media": 20.0,
        "por_categoria": categorias or {},
    }


def test_tipo_e_resumo_da_execucao():
    assert tipo_da_execucao(recuperacao(0.5)) == "recuperacao"
    assert tipo_da_execucao(respostas(0.5)) == "respostas"
    assert resumo_da_execucao(recuperacao(0.5))["recall"] == 0.5
    with pytest.raises(ValueError):
        resumo_da_execucao({"modelos": []})


def test_diferenca_das_metricas_gerais():
    diferencas = {
        d.metrica: d
        for d in comparar_execucoes(recuperacao(0.5), recuperacao(0.75, 0.6))
    }
    assert diferencas["recall"].delta == 0.25
    assert diferencas["mrr"].delta == pytest.approx(0.1)
    assert diferencas["separacao"].delta == 0


def test_metrica_ausente_nao_tem_diferenca():
    diferencas = {
        d.metrica: d for d in comparar_execucoes(respostas(0.5), respostas(0.75))
    }
    assert diferencas["acuracia"].delta == 0.25
    assert diferencas["fonte_esperada"].delta is None
    # execuções antigas não têm as métricas de texto: aparecem sem diferença
    assert diferencas["rouge_1"].delta is None


def test_compara_as_metricas_de_texto_e_o_hit():
    antes = {
        **respostas(0.5),
        "rouge_1": 0.2,
        "rouge_l": 0.1,
        "cosseno": 0.8,
        "hit": 0.5,
    }
    depois = {
        **respostas(0.5),
        "rouge_1": 0.3,
        "rouge_l": 0.2,
        "cosseno": 0.85,
        "hit": None,
    }
    diferencas = {d.metrica: d for d in comparar_execucoes(antes, depois)}
    assert diferencas["rouge_1"].delta == 0.1
    assert diferencas["rouge_l"].delta == 0.1
    assert diferencas["cosseno"].delta == 0.05
    # o modo puro não tem busca: o Hit@k aparece só de um lado
    assert diferencas["hit"].delta is None


def test_tipos_diferentes_nao_se_comparam():
    with pytest.raises(ValueError):
        comparar_execucoes(recuperacao(0.5), respostas(0.5))


def test_categoria_nova_aparece_sem_valor_anterior():
    antes = recuperacao(0.5, categorias={"receita_pt": {"recall": 1.0, "mrr": 1.0}})
    depois = recuperacao(
        0.6,
        categorias={
            "receita_pt": {"recall": 0.875, "mrr": 0.8},
            "nutricao": {"recall": 0.8, "mrr": 0.7},
        },
    )
    categorias = comparar_categorias(antes, depois)
    assert list(categorias) == ["nutricao", "receita_pt"]
    assert categorias["nutricao"][0] == Diferenca("recall", None, 0.8)
    assert categorias["receita_pt"][0].delta == -0.125


def test_formatar_delta():
    assert formatar_delta(0.25) == "+0.250"
    assert formatar_delta(-0.1) == "-0.100"
    assert formatar_delta(None) == "—"
