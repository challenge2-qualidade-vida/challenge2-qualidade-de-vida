from types import SimpleNamespace

from economia.api.observabilidade import (
    ObservadorDePerguntas,
    RegistroDaPergunta,
    scores_da_resposta,
)
from economia.receitas.aplicacao.responder_pergunta import AVISO_DE_PRECO


def resposta(texto="Guarde secas [1].", encontrou=True, fontes=("Embrapa",)):
    return SimpleNamespace(texto=texto, encontrou=encontrou, fontes=list(fontes))


def test_scores_de_uma_resposta_com_fonte():
    assert scores_da_resposta(resposta(), "como conservo alface?", 1.23456) == {
        "encontrou": 1.0,
        "fonte_citada": 1.0,
        "latencia_s": 1.235,
        "erro": 0.0,
    }


def test_pergunta_de_preco_tem_o_score_do_aviso():
    aviso = resposta(texto=AVISO_DE_PRECO, encontrou=False, fontes=())
    scores = scores_da_resposta(aviso, "quanto custa o arroz hoje?", 0.1)
    assert scores["aviso_de_preco"] == 1.0
    assert scores["fonte_citada"] == 0.0


def test_pergunta_que_nao_e_de_preco_nao_tem_o_score_do_aviso():
    assert "aviso_de_preco" not in scores_da_resposta(resposta(), "como conservo?", 0.1)


def test_sem_cliente_o_registro_nao_faz_nada():
    with ObservadorDePerguntas(None).registrar("pergunta") as registro:
        registro.concluir("pergunta", resposta(), 1.0)
        registro.falhar(RuntimeError("x"), 1.0)


def test_falha_ao_pontuar_nao_propaga():
    class ObservacaoQueFalha:
        def update(self, **_):
            raise ConnectionError("Langfuse fora do ar")

    RegistroDaPergunta(ObservacaoQueFalha()).falhar(RuntimeError("x"), 1.0)
