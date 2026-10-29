import json

import pytest

from economia.assistente import Assistente, interpretar
from economia.dados import carregar
from economia.llm import ErroLLM, cliente_do_ambiente
from economia.precos import avaliar_promocao, consultar_precos
from economia.rag import BaseConhecimento


@pytest.fixture(scope="module")
def base():
    return carregar()


@pytest.fixture(scope="module")
def bc(base):
    return BaseConhecimento(base)


class LLMFalso:
    """Devolve respostas pré-programadas e guarda o que recebeu."""

    provedor, modelo = "falso", "falso"

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.recebido = []

    def conversar(self, mensagens, ferramentas=None, temperatura=0.2):
        self.recebido.append({"mensagens": [dict(m) for m in mensagens], "ferramentas": ferramentas})
        return self.respostas.pop(0)


def chamada(nome, **args):
    return {"content": "", "tool_calls": [{"id": "1", "type": "function", "function": {"name": nome, "arguments": json.dumps(args)}}]}


# ---------- Ferramentas de preço ----------

def test_consultar_precos_ordena_por_preco_kg(base):
    r = consultar_precos(base, "feijão preto")
    assert r["encontrados"] == 1
    kgs = [o["preco_kg"] for o in r["produtos"][0]["ofertas"]]
    assert kgs == sorted(kgs)


@pytest.mark.parametrize("preco, esperado", [(24.90, "vale_a_pena"), (26.50, "empate"), (35.00, "nao_vale")])
def test_avaliar_promocao(base, preco, esperado):
    r = avaliar_promocao(base, "arroz", preco, 5000)
    assert r["conclusao"] == esperado
    assert r["melhor_preco_kg_normal"] == pytest.approx(5.30)


def test_avaliar_promocao_sem_dados(base):
    assert avaliar_promocao(base, "caviar", 10)["conclusao"] == "sem_dados"


# ---------- Interpretação do modo sem LLM ----------

@pytest.mark.parametrize(
    "mensagem, intencao, esperado",
    [
        ("Tenho R$ 600 para o mês, somos 4 pessoas e não como carne de porco", "cesta",
         {"orcamento": 600, "pessoas": 4, "periodo": "mes", "restricoes": ["sem_porco"]}),
        ("R$ 1.000 para 3 pessoas por uma semana, sou vegetariano", "cesta",
         {"orcamento": 1000, "pessoas": 3, "periodo": "semana", "restricoes": ["vegetariano"]}),
        ("Arroz 5 kg por R$ 24,90 é uma boa promoção?", "promocao", {"produto": "arroz", "preco": 24.9, "embalagem_g": 5000}),
        ("quanto custa o feijão preto?", "precos", {"produto": "feijao preto"}),
        ("o que fazer com banana madura?", "conhecimento", {}),
    ],
)
def test_interpretar(mensagem, intencao, esperado):
    achada, args = interpretar(mensagem)
    assert achada == intencao
    assert args == esperado


# ---------- Modo sem LLM ----------

def test_sem_llm_monta_cesta(base, bc):
    r = Assistente(base, bc, None).responder("Tenho R$ 800 para 4 pessoas no mês")
    assert r.modo == "sem_llm"
    assert r.ferramentas_usadas == ["montar_cesta"]
    assert "itens" in r.dados["montar_cesta"]
    assert r.aviso


def test_sem_llm_pede_numero_de_pessoas(base, bc):
    assert "quantas pessoas" in Assistente(base, bc, None).responder("monte uma cesta de R$ 500").resposta


def test_sem_llm_responde_com_a_base_e_cita_fonte(base, bc):
    r = Assistente(base, bc, None).responder("o que são alimentos ultraprocessados?")
    assert "ultraprocessados" in r.resposta.lower()
    assert r.fontes


def test_sem_llm_fora_do_tema(base, bc):
    assert "não tem informação" in Assistente(base, bc, None).responder("quem ganhou a copa do mundo").resposta


# ---------- Com LLM (falso) ----------

def test_llm_chama_ferramenta_e_responde(base, bc):
    llm = LLMFalso([chamada("montar_cesta", pessoas=4, orcamento=800, periodo="mes"), {"content": "Pronto, sua cesta custa R$ 602,66."}])
    r = Assistente(base, bc, llm).responder("Tenho R$ 800 para 4 pessoas")
    assert r.modo == "llm"
    assert r.ferramentas_usadas == ["montar_cesta"]
    assert r.resposta.startswith("Pronto")
    # A lista de itens vai para a tela, mas não para o LLM.
    assert "itens" in r.dados["montar_cesta"]
    resposta_ferramenta = json.loads(llm.recebido[1]["mensagens"][-1]["content"])
    assert "itens" not in resposta_ferramenta and "explicacao" in resposta_ferramenta


def test_llm_recebe_trechos_do_rag_junto_com_a_pergunta(base, bc):
    llm = LLMFalso([{"content": "Prefira alimentos in natura [1]."}])
    r = Assistente(base, bc, llm).responder("qual é a regra de ouro?")
    pergunta_enviada = llm.recebido[0]["mensagens"][-1]["content"]
    assert "Trechos da base de conhecimento" in pergunta_enviada
    assert "Regra de ouro" in pergunta_enviada
    assert r.fontes


def test_llm_sem_rag_nao_recebe_trechos_nem_ferramenta_de_busca(base, bc):
    llm = LLMFalso([{"content": "..."}])
    Assistente(base, bc, llm, usar_rag=False).responder("qual é a regra de ouro?")
    assert llm.recebido[0]["mensagens"][-1]["content"] == "qual é a regra de ouro?"
    nomes = {f["function"]["name"] for f in llm.recebido[0]["ferramentas"]}
    assert "buscar_conhecimento" not in nomes


def test_llm_fora_do_ar_cai_no_modo_sem_llm(base, bc):
    class LLMQuebrado:
        provedor, modelo = "quebrado", "x"

        def conversar(self, *a, **k):
            raise ErroLLM("conexão recusada")

    r = Assistente(base, bc, LLMQuebrado()).responder("Tenho R$ 800 para 4 pessoas")
    assert r.modo == "sem_llm"
    assert "conexão recusada" in r.aviso


def test_argumentos_invalidos_viram_erro_para_o_llm(base, bc):
    ruim = {"content": "", "tool_calls": [{"id": "1", "function": {"name": "montar_cesta", "arguments": "{nao e json"}}]}
    llm = LLMFalso([ruim, {"content": "Desculpe, pode repetir?"}])
    r = Assistente(base, bc, llm).responder("cesta")
    assert "Argumentos inválidos" in llm.recebido[1]["mensagens"][-1]["content"]
    assert r.resposta == "Desculpe, pode repetir?"


# ---------- Configuração ----------

def test_cliente_do_ambiente(monkeypatch):
    monkeypatch.setenv("LLM_PROVEDOR", "nenhum")
    assert cliente_do_ambiente() is None
    monkeypatch.setenv("LLM_PROVEDOR", "groq")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert cliente_do_ambiente() is None          # groq sem chave → modo sem LLM
    monkeypatch.setenv("LLM_PROVEDOR", "ollama")
    c = cliente_do_ambiente()
    assert c.provedor == "ollama" and c.modelo == "qwen2.5:7b"
