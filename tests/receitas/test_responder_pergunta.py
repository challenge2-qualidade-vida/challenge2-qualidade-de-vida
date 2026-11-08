import pytest

from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO,
    NAO_ENCONTREI,
    ResponderPergunta,
    citacoes_validas,
    e_pergunta_de_preco,
    formatar_fonte,
    montar_mensagem,
    renumerar,
)
from economia.receitas.dominio.modelos import (
    Fonte,
    TipoDeTrecho,
    Trecho,
    TrechoRecuperado,
)


class GeradorFalso:
    nome, dimensao = "falso", 2

    def gerar_para_pergunta(self, pergunta):
        return [1.0, 0.0]

    def gerar_para_trechos(self, textos):
        return [[1.0, 0.0] for _ in textos]


class RepositorioFalso:
    def __init__(self, recuperados):
        self.recuperados = recuperados

    def buscar(self, vetor, limite, tipo=None):
        return self.recuperados[:limite]


class LLMFalso:
    def __init__(self, resposta):
        self.resposta = resposta
        self.mensagens = []

    def gerar(self, sistema, mensagem):
        self.mensagens.append(mensagem)
        return self.resposta


def recuperado(trecho, id: str, score: float, **kwargs) -> TrechoRecuperado:
    return TrechoRecuperado(trecho=trecho(id, **kwargs), score=score)


def criar(recuperados, resposta="Faça assim [1].", limiar=0.8):
    llm = LLMFalso(resposta)
    caso = ResponderPergunta(
        GeradorFalso(), RepositorioFalso(recuperados), llm, "sistema", limiar=limiar
    )
    return caso, llm


@pytest.mark.parametrize(
    "pergunta",
    [
        "quanto está o arroz no mercado hoje?",
        "Quanto custa o feijão?",
        "qual o preço atual do leite?",
        "onde o café está mais barato?",
    ],
)
def test_pergunta_de_preco_atual(pergunta):
    assert e_pergunta_de_preco(pergunta)


@pytest.mark.parametrize(
    "pergunta",
    [
        "como avaliar se uma promoção vale a pena?",
        "o que é preço por unidade?",
        "o que posso fazer com arroz, ovo e cenoura?",
        "como conservo alface?",
    ],
)
def test_pergunta_que_nao_e_de_preco_atual(pergunta):
    assert not e_pergunta_de_preco(pergunta)


def test_preco_atual_responde_com_o_aviso_sem_buscar(trecho):
    caso, llm = criar([recuperado(trecho, "a", 0.99)])
    resposta = caso.responder("quanto está o arroz no mercado hoje?")
    assert resposta.texto == AVISO_DE_PRECO
    assert not resposta.encontrou
    assert llm.mensagens == []


def test_abaixo_do_limiar_diz_que_nao_encontrou_sem_chamar_o_llm(trecho):
    caso, llm = criar([recuperado(trecho, "a", 0.79)], limiar=0.8)
    resposta = caso.responder("quanto tempo dura o fermento biológico?")
    assert resposta.texto == NAO_ENCONTREI
    assert not resposta.encontrou
    assert llm.mensagens == []


def test_so_os_trechos_acima_do_limiar_vao_para_o_llm(trecho):
    caso, llm = criar([recuperado(trecho, "a", 0.9), recuperado(trecho, "b", 0.5)])
    caso.responder("pergunta")
    assert "[1]" in llm.mensagens[0]
    assert "[2]" not in llm.mensagens[0]


def test_llm_sem_resposta_nos_trechos_vira_nao_encontrei(trecho):
    caso, _ = criar([recuperado(trecho, "a", 0.9)], resposta="NAO_ENCONTRADO")
    resposta = caso.responder("pergunta")
    assert resposta.texto == NAO_ENCONTREI
    assert not resposta.encontrou


def test_resposta_sem_citacao_nao_e_aceita(trecho):
    # sem citar o trecho, não há como dizer de onde veio a resposta (RN10)
    caso, _ = criar([recuperado(trecho, "a", 0.9)], resposta="Faça um bolo.")
    assert not caso.responder("pergunta").encontrou


def test_fontes_sao_as_dos_trechos_citados_renumeradas(trecho):
    recuperados = [
        recuperado(trecho, "a", 0.95, fonte="afrodite.json"),
        recuperado(trecho, "b", 0.90, fonte="RecipeNLG"),
        recuperado(trecho, "c", 0.85, fonte="Guia"),
    ]
    caso, _ = criar(
        recuperados, resposta="Use a receita [3] e depois a [1]. Ignore [9]."
    )
    resposta = caso.responder("pergunta")
    assert resposta.encontrou
    assert resposta.texto == "Use a receita [1] e depois a [2]. Ignore ."
    assert [r.trecho.id for r in resposta.trechos] == ["c", "a"]
    assert [f.titulo for f in resposta.fontes] == ["Guia", "afrodite.json"]


def test_citacoes_validas_ignora_numeros_inexistentes_e_repetidos():
    assert citacoes_validas("[2] [1] [2] [7] [0]", quantidade=3) == [2, 1]


def test_renumerar_segue_a_ordem_das_citacoes():
    assert renumerar("[3] e [1]", [3, 1]) == "[1] e [2]"


def test_mensagem_numera_os_trechos_com_titulo_e_conteudo(trecho):
    mensagem = montar_mensagem(
        "o que faço?", [recuperado(trecho, "a", 0.9, titulo="Omelete")]
    )
    assert mensagem.startswith("Pergunta: o que faço?")
    assert "[1] Receita: Omelete\nconteúdo a" in mensagem


def test_formatar_fonte_de_receita_e_de_orientacao():
    receita = Trecho(
        id="r",
        tipo=TipoDeTrecho.RECEITA,
        documento_id="r",
        titulo="Lemon Chicken",
        texto="",
        conteudo="",
        fonte=Fonte(
            titulo="RecipeNLG",
            instituicao="Poznań University of Technology",
            ano=2020,
            url="https://www.cookbooks.com/1",
            licenca="Uso não comercial",
        ),
    )
    guia = Trecho(
        id="g",
        tipo=TipoDeTrecho.CONHECIMENTO,
        documento_id="g",
        titulo="Guia Alimentar",
        texto="",
        conteudo="",
        fonte=Fonte(
            titulo="Guia Alimentar", instituicao="Ministério da Saúde", ano=2014
        ),
        capitulo="Dez passos",
        secao="Evitar o consumo de alimentos ultraprocessados",
        pagina=126,
    )
    assert formatar_fonte(TrechoRecuperado(receita, 0.9)) == (
        "Lemon Chicken. RecipeNLG (Poznań University of Technology), 2020. "
        "https://www.cookbooks.com/1 Licença: Uso não comercial."
    )
    assert formatar_fonte(TrechoRecuperado(guia, 0.9)) == (
        "Guia Alimentar (Ministério da Saúde), 2014. Dez passos. "
        "Evitar o consumo de alimentos ultraprocessados. p. 126."
    )
