import pytest

from economia.receitas.aplicacao.metricas_de_texto import (
    cosseno,
    palavras,
    rouge_1_f1,
    rouge_l_f1,
    similaridade_com_a_referencia,
)


def test_palavras_ignora_acento_caixa_pontuacao_e_citacoes():
    assert palavras("Guarde a ALFACE seca [2], num pote fechado [1, 3].") == [
        "guarde",
        "a",
        "alface",
        "seca",
        "num",
        "pote",
        "fechado",
    ]
    assert palavras("Não é açúcar") == ["nao", "e", "acucar"]


def test_palavras_mantem_numero_com_virgula_inteiro():
    assert palavras("O ovo tem 13,3 g de proteína.") == [
        "o",
        "ovo",
        "tem",
        "13,3",
        "g",
        "de",
        "proteina",
    ]


@pytest.mark.parametrize("metrica", [rouge_1_f1, rouge_l_f1])
def test_textos_iguais_dao_1(metrica):
    assert metrica("Guarde a alface seca.", "guarde a alface seca") == 1.0


@pytest.mark.parametrize("metrica", [rouge_1_f1, rouge_l_f1])
def test_sem_palavra_em_comum_da_0(metrica):
    assert metrica("lave as folhas", "ferva o leite") == 0.0


@pytest.mark.parametrize("metrica", [rouge_1_f1, rouge_l_f1])
@pytest.mark.parametrize(("resposta", "referencia"), [("", "texto"), ("texto", "")])
def test_texto_vazio_da_0(metrica, resposta, referencia):
    assert metrica(resposta, referencia) == 0.0


def test_rouge_com_uma_palavra_trocada():
    # 4 das 5 palavras em comum e na mesma ordem: precisão 4/5, revocação 4/5, F1 0,8
    resposta = "o gato deitou no tapete"
    referencia = "o gato sentou no tapete"
    assert rouge_1_f1(resposta, referencia) == pytest.approx(0.8)
    assert rouge_l_f1(resposta, referencia) == pytest.approx(0.8)


def test_rouge_l_cai_quando_a_ordem_muda_e_o_rouge_1_nao():
    # mesmas palavras em ordem inversa: a maior subsequência comum tem 1 palavra
    resposta = "tapete no gato"
    referencia = "gato no tapete"
    assert rouge_1_f1(resposta, referencia) == 1.0
    assert rouge_l_f1(resposta, referencia) == pytest.approx(1 / 3)


def test_rouge_1_conta_palavra_repetida_so_ate_o_que_a_referencia_tem():
    # "arroz" aparece 3 vezes na resposta e 1 na referência: 1 em comum
    # precisão 1/3, revocação 1/2, F1 = 2 * (1/3 * 1/2) / (1/3 + 1/2) = 0,4
    assert rouge_1_f1("arroz arroz arroz", "arroz branco") == pytest.approx(0.4)


def test_rouge_com_resposta_mais_longa_que_a_referencia():
    # 2 em comum; precisão 2/4, revocação 2/2, F1 = 2/3
    resposta = "lave bem as folhas"
    referencia = "lave folhas"
    assert rouge_1_f1(resposta, referencia) == pytest.approx(2 / 3)
    assert rouge_l_f1(resposta, referencia) == pytest.approx(2 / 3)


def test_cosseno():
    assert cosseno([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosseno([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosseno([3.0, 4.0], [6.0, 8.0]) == pytest.approx(1.0)
    assert cosseno([0.0, 0.0], [1.0, 0.0]) == 0.0


class GeradorFalso:
    nome = "falso"
    dimensao = 2

    def __init__(self):
        self.textos = None

    def gerar_para_trechos(self, textos):
        self.textos = list(textos)
        return [[1.0, 0.0], [0.6, 0.8]]

    def gerar_para_pergunta(self, pergunta):
        raise AssertionError(
            "a comparação é simétrica: os dois textos usam o mesmo prefixo"
        )


def test_similaridade_com_a_referencia_usa_o_mesmo_prefixo_nos_dois_textos():
    gerador = GeradorFalso()
    valor = similaridade_com_a_referencia("resposta", "referência", gerador)
    assert valor == pytest.approx(0.6)
    assert gerador.textos == ["resposta", "referência"]
