import json

import pytest

from economia.agentes import Orquestrador, RECUSA_FORA_DO_TEMA, verificar
from economia.dados import carregar
from economia.rag import BaseConhecimento


@pytest.fixture(scope="module")
def base():
    return carregar()


@pytest.fixture(scope="module")
def bc(base):
    return BaseConhecimento(base)


class LLMFalso:
    provedor, modelo = "falso", "falso"

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.recebido = []

    def conversar(self, mensagens, ferramentas=None):
        self.recebido.append({"mensagens": mensagens, "ferramentas": ferramentas})
        return self.respostas.pop(0)


def chamada(nome, **args):
    return {"content": "", "tool_calls": [{"id": "1", "function": {"name": nome, "arguments": json.dumps(args)}}]}


# ---------- Mia ----------

def test_mia_aceita_valores_das_ferramentas_e_da_pergunta():
    dados = {"avaliar_promocao": {"preco_kg_promocao": 4.98, "melhor_preco_kg_normal": 5.3, "fonte": "exemplo"}}
    resposta = "Com R$ 24,90 sai a R$ 4,98/kg, contra R$ 5,30. Preços de exemplo."
    assert verificar(resposta, dados, [], "Arroz 5 kg por R$ 24,90 vale a pena?") == []


def test_mia_pega_valor_inventado():
    dados = {"consultar_precos": {"produtos": [{"ofertas": [{"preco": 7.99, "fonte": "coleta"}]}]}}
    problemas = verificar("O feijão custa R$ 6,50.", dados, [])
    assert [p["tipo"] for p in problemas] == ["valor_nao_confere"]


def test_mia_cobra_aviso_de_preco_de_exemplo():
    dados = {"consultar_precos": {"produtos": [{"ofertas": [{"preco": 7.99, "fonte": "exemplo"}]}]}}
    assert [p["tipo"] for p in verificar("Custa R$ 7,99.", dados, [])] == ["faltou_aviso_exemplo"]


def test_mia_pega_restricao_violada():
    problemas = verificar("Almoço: arroz, feijão e frango assado.", {}, ["vegetariano"])
    assert problemas[0]["tipo"] == "restricao_violada"
    assert "frango" in problemas[0]["detalhe"]


# ---------- Orquestrador ----------

@pytest.mark.parametrize(
    "mensagem, rota",
    [
        ("Tenho R$ 600 para 4 pessoas", "cifrao"),
        ("Arroz 5 kg por R$ 24,90 é uma boa promoção?", "cifrao"),
        ("quanto custa o feijão preto?", "cifrao"),
        ("O que fazer com banana madura?", "miauricio"),
        ("Qual remédio tomar para pressão alta?", "saude"),
        ("Quem ganhou a Copa do Mundo de 2002?", "fora_do_tema"),
    ],
)
def test_roteamento(base, bc, mensagem, rota):
    assert Orquestrador(base, bc, None).rotear(mensagem) == rota


def test_fora_do_tema_nao_chama_llm(base, bc):
    llm = LLMFalso([])
    r = Orquestrador(base, bc, llm).responder("Quem ganhou a Copa do Mundo de 2002?")
    assert r.resposta == RECUSA_FORA_DO_TEMA
    assert llm.recebido == []


def test_cifrao_recebe_so_ferramentas_de_preco(base, bc):
    llm = LLMFalso([chamada("consultar_precos", produto="feijão preto"), {"content": "Custa R$ 7,99 no Mercado B (preço de exemplo)."}])
    r = Orquestrador(base, bc, llm).responder("quanto custa o feijão preto?")
    nomes = {f["function"]["name"] for f in llm.recebido[0]["ferramentas"]}
    assert nomes == {"montar_cesta", "consultar_precos", "avaliar_promocao"}
    assert [e["agente"] for e in r.etapas] == ["Orquestrador", "Cifrão", "Mia"]
    assert r.etapas[-1]["problemas"] == []


def test_mia_troca_resposta_com_valor_inventado(base, bc):
    llm = LLMFalso([chamada("consultar_precos", produto="feijão preto"), {"content": "Custa só R$ 3,00!"}])
    r = Orquestrador(base, bc, llm).responder("quanto custa o feijão preto?")
    assert "R$ 3,00" not in r.resposta
    assert "R$ 7,99" in r.resposta
    assert any("trocou a resposta" in e["acao"] for e in r.etapas)


def test_mia_acrescenta_aviso_de_exemplo(base, bc):
    llm = LLMFalso([chamada("consultar_precos", produto="feijão preto"), {"content": "Custa R$ 7,99 no Mercado B."}])
    r = Orquestrador(base, bc, llm).responder("quanto custa o feijão preto?")
    assert "são de exemplo" in r.resposta


def test_miauricio_recebe_trechos_e_nenhuma_ferramenta(base, bc):
    llm = LLMFalso([{"content": "Faça vitamina ou bolo [1]."}])
    r = Orquestrador(base, bc, llm).responder("O que fazer com banana madura?")
    assert llm.recebido[0]["ferramentas"] is None
    assert "Trechos da base" in llm.recebido[0]["mensagens"][-1]["content"]
    assert r.etapas[1]["agente"] == "Miau-ricio"


def test_sem_llm_usa_reserva_e_mia(base, bc):
    r = Orquestrador(base, bc, None).responder("Tenho R$ 800 para 4 pessoas no mês")
    assert r.modo == "sem_llm"
    assert r.etapas[-1]["agente"] == "Mia"


# ---------- Cardápio ----------

def test_cardapio_sem_llm_traz_receitas_da_base(base, bc):
    r = Orquestrador(base, bc, None).cardapio(["arroz", "feijão carioca", "lentilha", "cenoura", "abóbora"], [])
    assert "sopa de lentilha" in r.resposta.lower()
    assert r.fontes


def test_cardapio_com_llm_e_mia_alerta_restricao(base, bc):
    llm = LLMFalso([{"content": "Dia 1 almoço: arroz, feijão e frango."}])
    r = Orquestrador(base, bc, llm).cardapio(["arroz", "feijão carioca"], ["vegetariano"])
    assert "alimentos que você não come" in r.resposta
    assert "arroz, feijão carioca" in llm.recebido[0]["mensagens"][-1]["content"]


# ---------- Ajustes motivados pelo experimento (tópico 8) ----------

def test_saude_nao_chama_llm_e_indica_profissional(base, bc):
    llm = LLMFalso([])
    r = Orquestrador(base, bc, llm).responder("Qual remédio devo tomar para pressão alta?")
    assert "médico ou nutricionista" in r.resposta
    assert llm.recebido == []


def test_dois_mercados_sem_preco_nao_e_promocao(base, bc):
    assert Orquestrador(base, bc, None).rotear("Quando vale a pena fazer compras em dois mercados?") == "miauricio"


def test_mia_bloqueia_link_inventado(base, bc):
    resposta = "Acerola tem 238 mg de vitamina C [1]. Fonte: https://www.gov.br/economia/guia-falso.pdf"
    llm = LLMFalso([{"content": resposta}])
    r = Orquestrador(base, bc, llm).responder("Quanto de vitamina C tem a acerola?")
    assert "não tem uma fonte confiável" in r.resposta
    assert any(p["tipo"] == "fonte_inventada" for e in r.etapas for p in e.get("problemas", []))


def test_mia_bloqueia_numero_que_nao_esta_nos_trechos():
    fontes = [{"texto": "Lentilha (crua): por 100 g tem 339 kcal, 23.2 g de proteína."}]
    assert verificar("A lentilha tem 23,2 g de proteína [1].", {}, [], fontes=fontes) == []
    problemas = verificar("A lentilha tem 9 g de proteína [1].", {}, [], fontes=fontes)
    assert problemas[0]["tipo"] == "fonte_inventada"


def test_mia_nao_cobra_citacao_em_resposta_de_preco():
    dados = {"consultar_precos": {"produtos": [{"ofertas": [{"preco": 7.99, "fonte": "coleta"}]}]}}
    assert verificar("Custa R$ 7,99 [1].", dados, [], fontes=[]) == []
