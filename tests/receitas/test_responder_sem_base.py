import pytest

from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO,
    NAO_ENCONTREI,
)
from economia.receitas.aplicacao.responder_sem_base import (
    ResponderSemBase,
    RespostaSemBase,
)


class LLMFalso:
    def __init__(self, saida):
        self.saida = saida
        self.chamadas = []

    def gerar(self, sistema, mensagem):
        raise AssertionError("o modo puro usa a saída estruturada")

    def gerar_json(self, sistema, mensagem, esquema):
        self.chamadas.append((sistema, mensagem, esquema))
        if isinstance(self.saida, Exception):
            raise self.saida
        return self.saida


def test_resposta_do_modo_puro_nao_tem_fontes():
    llm = LLMFalso({"encontrou": True, "resposta": "Guarde a alface seca."})
    resposta = ResponderSemBase(llm, "prompt").responder("como conservo alface?")
    assert resposta == RespostaSemBase(texto="Guarde a alface seca.", encontrou=True)
    assert resposta.trechos == () and resposta.recuperados == ()


def test_manda_so_a_pergunta_com_o_prompt_e_o_esquema():
    llm = LLMFalso({"encontrou": True, "resposta": "ok"})
    ResponderSemBase(llm, "você é o Miau-ricio").responder("como conservo alface?")
    [(sistema, mensagem, esquema)] = llm.chamadas
    assert sistema == "você é o Miau-ricio"
    assert mensagem == "Pergunta: como conservo alface?"
    assert set(esquema["properties"]) == {"encontrou", "resposta"}


@pytest.mark.parametrize(
    "saida",
    [
        {"encontrou": False, "resposta": ""},
        {"encontrou": True, "resposta": "   "},
        {"resposta": "sem o campo encontrou"},
        ValueError("JSON inválido"),
    ],
)
def test_sem_resposta_valida_diz_que_nao_encontrou(saida):
    resposta = ResponderSemBase(LLMFalso(saida), "p").responder("fermento?")
    assert resposta == RespostaSemBase(texto=NAO_ENCONTREI, encontrou=False)


def test_pergunta_de_preco_recebe_o_aviso_sem_chamar_o_llm():
    # a RN04 é uma regra do código: vale igual nos dois modos, para a comparação ser justa
    llm = LLMFalso({"encontrou": True, "resposta": "R$ 5"})
    resposta = ResponderSemBase(llm, "p").responder("quanto está o arroz hoje?")
    assert resposta == RespostaSemBase(texto=AVISO_DE_PRECO, encontrou=False)
    assert llm.chamadas == []
