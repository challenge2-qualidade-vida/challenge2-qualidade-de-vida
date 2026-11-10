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
    # a lista de fontes segue o ranking, não a ordem em que o LLM citou
    assert resposta.texto == "Use a receita [2] e depois a [1]. Ignore ."
    assert [r.trecho.id for r in resposta.trechos] == ["a", "c"]
    assert [f.titulo for f in resposta.fontes] == ["afrodite.json", "Guia"]


def test_citacoes_validas_ignora_numeros_inexistentes_e_repetidos():
    assert citacoes_validas("[2] [1] [2] [7] [0]", quantidade=3) == [2, 1]


def test_renumerar_segue_a_ordem_do_ranking():
    assert renumerar("[3] e [1]", [3, 1]) == "[2] e [1]"


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


# ---------------------------------------------------------------- desempate (fase 7b)


class LLMComExtracao(LLMFalso):
    def __init__(self, resposta, ingredientes):
        super().__init__(resposta)
        self.ingredientes = ingredientes
        self.extracoes = 0

    def gerar_json(self, sistema, mensagem, esquema):
        self.extracoes += 1
        return self.ingredientes


def criar_com_desempate(recuperados, ingredientes, resposta="[1] [2]", tolerancia=0.01):
    llm = LLMComExtracao(resposta, ingredientes)
    caso = ResponderPergunta(
        GeradorFalso(),
        RepositorioFalso(recuperados),
        llm,
        "sistema",
        limiar=0.5,
        prompt_de_extracao="extrair",
        ingredientes_basicos=("sal",),
        tolerancia=tolerancia,
    )
    return caso, llm


def test_empate_vem_primeiro_a_receita_com_menos_ingredientes_faltando(trecho):
    recuperados = [
        recuperado(
            trecho, "torta", 0.905, ingredientes=("ovo", "cenoura", "farinha", "leite")
        ),
        recuperado(
            trecho, "omelete", 0.900, ingredientes=("2 ovos", "1 cenoura", "sal")
        ),
    ]
    caso, _ = criar_com_desempate(
        recuperados, {"ingredientes_pt": ["ovo", "cenoura"], "ingredientes_en": []}
    )
    resposta = caso.responder("o que posso fazer com ovo e cenoura?")
    assert [r.trecho.id for r in resposta.trechos] == ["omelete", "torta"]
    assert resposta.faltando_na_receita("omelete") == ()
    assert resposta.faltando_na_receita("torta") == ("farinha", "leite")
    assert resposta.ingredientes_disponiveis == ("ovo", "cenoura")
    assert "Ingredientes que faltam:" in resposta.texto
    assert "- Título torta [2]: farinha, leite" in resposta.texto
    assert "- Título omelete [1]: nenhum" in resposta.texto


def test_fora_da_tolerancia_vale_o_score(trecho):
    recuperados = [
        recuperado(trecho, "torta", 0.95, ingredientes=("ovo", "farinha")),
        recuperado(trecho, "omelete", 0.90, ingredientes=("ovo",)),
    ]
    caso, _ = criar_com_desempate(recuperados, {"ingredientes_pt": ["ovo"]})
    resposta = caso.responder("o que faço com ovo?")
    assert [r.trecho.id for r in resposta.trechos] == ["torta", "omelete"]


def test_receita_em_ingles_usa_os_ingredientes_em_ingles(trecho):
    from dataclasses import replace

    em_ingles = replace(trecho("en", ingredientes=("eggs", "flour")), idioma="en")
    recuperados = [TrechoRecuperado(trecho=em_ingles, score=0.9)]
    caso, _ = criar_com_desempate(
        recuperados,
        {"ingredientes_pt": ["ovo"], "ingredientes_en": ["egg"]},
        resposta="[1]",
    )
    assert caso.responder("o que faço com ovo?").faltando_na_receita("en") == ("flour",)


def test_sem_receitas_recuperadas_nao_chama_a_extracao(trecho):
    recuperados = [recuperado(trecho, "guia", 0.9, tipo=TipoDeTrecho.CONHECIMENTO)]
    caso, llm = criar_com_desempate(
        recuperados, {"ingredientes_pt": ["ovo"]}, resposta="[1]"
    )
    resposta = caso.responder("como conservo alface?")
    assert llm.extracoes == 0
    assert "Ingredientes que faltam" not in resposta.texto


def test_extracao_invalida_vale_como_nenhum_ingrediente(trecho):
    recuperados = [recuperado(trecho, "a", 0.9, ingredientes=("ovo",))]
    caso, _ = criar_com_desempate(
        recuperados, {"ingredientes_pt": "não é lista"}, resposta="[1]"
    )
    resposta = caso.responder("o que faço?")
    assert resposta.encontrou
    assert resposta.faltando == ()


def test_formatar_fonte_nao_repete_o_nome_contido_na_instituicao(trecho):
    from dataclasses import replace

    receita = replace(
        trecho("a", titulo="Bolo"),
        fonte=Fonte(
            titulo="afrodite.json", instituicao="afrodite.json (dataset no GitHub)"
        ),
    )
    assert formatar_fonte(TrechoRecuperado(receita, 0.9)) == (
        "Bolo. afrodite.json (dataset no GitHub)."
    )


class LLMEmSequencia:
    """LLM falso que devolve uma resposta por chamada, em ordem, nos dois modos."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.mensagens = []

    def _proxima(self, mensagem):
        self.mensagens.append(mensagem)
        return self.respostas.pop(0)

    def gerar(self, sistema, mensagem):
        return self._proxima(mensagem)

    def gerar_json(self, sistema, mensagem, esquema):
        resposta = self._proxima(mensagem)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def criar_com(llm, recuperados, **kwargs):
    return ResponderPergunta(
        GeradorFalso(),
        RepositorioFalso(recuperados),
        llm,
        "sistema",
        limiar=0.8,
        **kwargs,
    )


def test_resposta_estruturada_usa_a_lista_de_trechos(trecho):
    recuperados = [recuperado(trecho, "a", 0.95), recuperado(trecho, "b", 0.90)]
    llm = LLMEmSequencia(
        {
            "encontrou": True,
            "resposta": "Guarde na geladeira.",
            "trechos_usados": [2, 7],
        }
    )
    resposta = criar_com(llm, recuperados, resposta_estruturada=True).responder("?")
    assert resposta.encontrou
    assert resposta.texto == "Guarde na geladeira."
    assert [r.trecho.id for r in resposta.trechos] == ["b"]


def test_resposta_estruturada_junta_citacoes_do_texto_e_da_lista(trecho):
    recuperados = [recuperado(trecho, "a", 0.95), recuperado(trecho, "b", 0.90)]
    llm = LLMEmSequencia(
        {"encontrou": True, "resposta": "Use a [2].", "trechos_usados": [1]}
    )
    resposta = criar_com(llm, recuperados, resposta_estruturada=True).responder("?")
    assert [r.trecho.id for r in resposta.trechos] == ["a", "b"]
    assert resposta.texto == "Use a [2]."


@pytest.mark.parametrize(
    "saida",
    [
        {"encontrou": False, "resposta": "", "trechos_usados": []},
        {"encontrou": True, "resposta": "   ", "trechos_usados": [1]},
        {"encontrou": True, "resposta": "Sem fonte.", "trechos_usados": []},
        {"resposta": "faltou o campo encontrou"},
        ValueError("JSON inválido"),
    ],
)
def test_resposta_estruturada_invalida_ou_sem_citacao_vira_nao_encontrei(trecho, saida):
    llm = LLMEmSequencia(saida)
    caso = criar_com(llm, [recuperado(trecho, "a", 0.9)], resposta_estruturada=True)
    resposta = caso.responder("?")
    assert not resposta.encontrou
    assert resposta.texto == NAO_ENCONTREI


def test_segunda_tentativa_pede_a_citacao_e_aceita_a_resposta_citada(trecho):
    llm = LLMEmSequencia("Faça um bolo.", "Faça um bolo [1].")
    caso = criar_com(
        llm,
        [recuperado(trecho, "a", 0.9)],
        pedido_de_citacao="Antes: {resposta}. Cite.",
    )
    resposta = caso.responder("?")
    assert resposta.encontrou
    assert resposta.texto == "Faça um bolo [1]."
    assert len(llm.mensagens) == 2
    assert llm.mensagens[1].endswith("Antes: Faça um bolo.. Cite.")
    assert llm.mensagens[1].startswith(llm.mensagens[0])


def test_segunda_tentativa_acontece_uma_vez_so(trecho):
    llm = LLMEmSequencia("Faça um bolo.", "Ainda sem citar.")
    caso = criar_com(
        llm, [recuperado(trecho, "a", 0.9)], pedido_de_citacao="{resposta}"
    )
    assert not caso.responder("?").encontrou
    assert len(llm.mensagens) == 2


def test_sem_segunda_tentativa_quando_o_llm_diz_que_nao_encontrou(trecho):
    llm = LLMEmSequencia("NAO_ENCONTRADO")
    caso = criar_com(
        llm, [recuperado(trecho, "a", 0.9)], pedido_de_citacao="{resposta}"
    )
    assert not caso.responder("?").encontrou
    assert len(llm.mensagens) == 1


def test_sem_pedido_de_citacao_vale_a_regra_da_versao_1(trecho):
    llm = LLMEmSequencia("Faça um bolo.")
    caso = criar_com(llm, [recuperado(trecho, "a", 0.9)])
    assert not caso.responder("?").encontrou
    assert len(llm.mensagens) == 1


def test_segunda_tentativa_no_modo_estruturado(trecho):
    llm = LLMEmSequencia(
        {"encontrou": True, "resposta": "Faça um bolo.", "trechos_usados": []},
        {"encontrou": True, "resposta": "Faça um bolo [1].", "trechos_usados": [1]},
    )
    caso = criar_com(
        llm,
        [recuperado(trecho, "a", 0.9)],
        resposta_estruturada=True,
        pedido_de_citacao="{resposta}",
    )
    assert caso.responder("?").encontrou
    assert len(llm.mensagens) == 2


def test_numeros_validos():
    from economia.receitas.aplicacao.responder_pergunta import numeros_validos

    assert numeros_validos([3, 1, 3, 0, 9, 2], 3) == [3, 1, 2]


def test_prompts_versionados_da_resposta_existem():
    from economia.compartilhado.infraestrutura.prompts import carregar_prompt

    assert "trechos_usados" in carregar_prompt("miau-ricio", "resposta_com_fontes_v2")
    assert "{resposta}" in carregar_prompt("miau-ricio", "pedido_de_citacao_v1")


# ---------------------------------------------------------------- busca por ingrediente


class GeradorQueGuardaOTexto:
    """O "vetor" é o próprio texto, para o repositório falso responder por pergunta."""

    nome, dimensao = "texto", 1

    def gerar_para_pergunta(self, pergunta):
        return pergunta


class RepositorioPorPergunta:
    def __init__(self, geral, por_texto):
        self.geral = geral
        self.por_texto = por_texto
        self.buscas = []

    def buscar(self, vetor, limite, tipo=None):
        self.buscas.append((vetor, tipo))
        if vetor in self.por_texto:
            assert tipo is TipoDeTrecho.RECEITA
            return self.por_texto[vetor][:limite]
        return self.geral[:limite]


def criar_por_ingrediente(trecho, geral, por_texto, ingredientes):
    repositorio = RepositorioPorPergunta(geral, por_texto)
    caso = ResponderPergunta(
        GeradorQueGuardaOTexto(),
        repositorio,
        LLMComExtracao("[1]", {"ingredientes_pt": ingredientes, "ingredientes_en": []}),
        "sistema",
        limiar=0.8,
        prompt_de_extracao="extrair",
    )
    return caso, repositorio


def test_com_varios_ingredientes_busca_uma_receita_para_cada(trecho):
    guia = TrechoRecuperado(trecho("guia", tipo=TipoDeTrecho.CONHECIMENTO), 0.86)
    tilapia = recuperado(trecho, "tilapia", 0.85)
    arroz = recuperado(trecho, "arroz-forno", 0.88)
    feijao = recuperado(trecho, "feijoada", 0.87)
    alface = recuperado(trecho, "salada", 0.70)  # abaixo do limiar: fica de fora
    caso, repositorio = criar_por_ingrediente(
        trecho,
        geral=[guia, tilapia],
        por_texto={
            "Receita com arroz": [arroz],
            "Receita com feijão": [feijao],
            "Receita com alface": [alface],
        },
        ingredientes=["arroz", "feijão", "alface"],
    )
    disponiveis = caso.extrair_ingredientes("almoço com arroz, feijão e alface")
    juntos = caso.somar_receitas_por_ingrediente([guia, tilapia], disponiveis)
    assert [r.trecho.id for r in juntos] == [
        "arroz-forno",
        "feijoada",
        "guia",
        "tilapia",
    ]
    assert [b[0] for b in repositorio.buscas] == [
        "Receita com arroz",
        "Receita com feijão",
        "Receita com alface",
    ]


def test_com_um_ingrediente_so_vale_a_busca_geral(trecho):
    geral = [recuperado(trecho, "a", 0.9)]
    caso, repositorio = criar_por_ingrediente(
        trecho, geral=geral, por_texto={}, ingredientes=["ovo"]
    )
    disponiveis = caso.extrair_ingredientes("o que faço com ovo?")
    assert caso.somar_receitas_por_ingrediente(geral, disponiveis) == geral
    assert repositorio.buscas == []


def test_busca_por_ingrediente_nao_repete_e_respeita_o_limite(trecho):
    mesma = recuperado(trecho, "bolo", 0.9)
    geral = [mesma] + [recuperado(trecho, f"g{i}", 0.85 - i / 100) for i in range(5)]
    caso, _ = criar_por_ingrediente(
        trecho,
        geral=geral,
        por_texto={"Receita com ovo": [mesma], "Receita com leite": [mesma]},
        ingredientes=["ovo", "leite"],
    )
    disponiveis = caso.extrair_ingredientes("bolo com ovo e leite")
    juntos = caso.somar_receitas_por_ingrediente(geral[:5], disponiveis)
    ids = [r.trecho.id for r in juntos]
    assert len(ids) == len(set(ids)) == 5  # limite: max(5 trechos, 2 ingredientes + 1)
    assert ids[0] == "bolo"


def test_responder_usa_as_receitas_de_cada_ingrediente(trecho):
    tilapia = recuperado(trecho, "tilapia", 0.85)
    arroz = recuperado(trecho, "arroz-forno", 0.88)
    caso, _ = criar_por_ingrediente(
        trecho,
        geral=[tilapia],
        por_texto={"Receita com arroz": [arroz], "Receita com carne": []},
        ingredientes=["arroz", "carne"],
    )
    resposta = caso.responder("almoço com arroz e carne")
    assert resposta.encontrou
    assert resposta.trechos[0].trecho.id == "arroz-forno"


# ---------------------------------------------------------------- evidência da busca


def test_resposta_traz_os_trechos_enviados_ao_llm(trecho):
    recuperados = [recuperado(trecho, "a", 0.95), recuperado(trecho, "b", 0.90)]
    caso, _ = criar(recuperados, resposta="Use a [2].")
    resposta = caso.responder("pergunta")
    assert [r.trecho.id for r in resposta.recuperados] == ["a", "b"]
    assert [r.trecho.id for r in resposta.trechos] == ["b"]
    assert caso.limiar == 0.8


def test_abaixo_do_limiar_traz_os_mais_proximos_como_evidencia(trecho):
    caso, _ = criar([recuperado(trecho, "a", 0.79), recuperado(trecho, "b", 0.70)])
    resposta = caso.responder("pergunta")
    assert not resposta.encontrou
    assert [r.score for r in resposta.recuperados] == [0.79, 0.70]
    assert resposta.trechos == () and resposta.fontes == ()


def test_llm_sem_citacao_mantem_os_trechos_recuperados(trecho):
    caso, _ = criar([recuperado(trecho, "a", 0.9)], resposta="NAO_ENCONTRADO")
    resposta = caso.responder("pergunta")
    assert not resposta.encontrou
    assert [r.trecho.id for r in resposta.recuperados] == ["a"]


def test_pergunta_de_preco_nao_busca_nada(trecho):
    caso, _ = criar([recuperado(trecho, "a", 0.9)])
    assert caso.responder("quanto custa o arroz hoje?").recuperados == ()


def test_desagrupar_citacoes():
    from economia.receitas.aplicacao.responder_pergunta import desagrupar_citacoes

    assert desagrupar_citacoes("Evite açúcar [1, 3].") == "Evite açúcar [1][3]."
    assert desagrupar_citacoes("Veja [2;4] e [5].") == "Veja [2][4] e [5]."
    assert desagrupar_citacoes("Sem grupo [1].") == "Sem grupo [1]."


def test_citacao_agrupada_e_renumerada_junto_com_as_fontes(trecho):
    recuperados = [recuperado(trecho, i, 0.9 - n / 100) for n, i in enumerate("abc")]
    llm = LLMEmSequencia(
        {
            "encontrou": True,
            "resposta": "Evite açúcar [1, 3].",
            "trechos_usados": [1, 3],
        }
    )
    resposta = criar_com(llm, recuperados, resposta_estruturada=True).responder("?")
    assert resposta.texto == "Evite açúcar [1][2]."
    assert [r.trecho.id for r in resposta.trechos] == ["a", "c"]
