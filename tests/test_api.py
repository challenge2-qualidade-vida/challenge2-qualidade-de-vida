import pytest
from fastapi.testclient import TestClient

from economia.api import app


@pytest.fixture(scope="module")
def cliente():
    return TestClient(app)


def test_saude(cliente):
    assert cliente.get("/api/saude").json() == {"status": "ok"}


def test_opcoes_lista_mercados_e_restricoes(cliente):
    dados = cliente.get("/api/opcoes").json()
    assert {m["id"] for m in dados["mercados"]} == {"A", "B", "C"}
    assert any(r["id"] == "vegetariano" for r in dados["restricoes"])


def test_precos_trazem_preco_por_kg(cliente):
    produtos = cliente.get("/api/precos").json()["produtos"]
    arroz = next(p for p in produtos if p["produto_id"] == "arroz-5kg")
    assert arroz["precos"]["A"]["preco_kg"] == pytest.approx(5.58)


def test_cesta_devolve_plano_com_explicacao(cliente):
    r = cliente.post("/api/cesta", json={"orcamento": 800, "pessoas": 4, "periodo": "mes", "custo_deslocamento": 10})
    assert r.status_code == 200
    dados = r.json()
    assert dados["recomendacao"] in ("um", "dois")
    assert dados["cesta_recomendada"]["custo_total"] <= 800
    assert dados["cesta_recomendada"]["itens"]
    assert dados["explicacao"]


def test_cesta_com_orcamento_insuficiente(cliente):
    dados = cliente.post("/api/cesta", json={"orcamento": 50, "pessoas": 4}).json()
    assert dados["recomendacao"] is None
    assert dados["minimo_necessario"] > 50


def test_conhecimento_devolve_trechos_com_fonte(cliente):
    dados = cliente.get("/api/conhecimento", params={"pergunta": "essa promoção vale a pena?"}).json()
    assert dados["trechos"]
    assert all(t["fonte"] for t in dados["trechos"])


def test_chat_no_modo_sem_llm(cliente):
    assert cliente.get("/api/llm").json()["ativo"] is False
    dados = cliente.post("/api/chat", json={"mensagem": "Tenho R$ 800 para 4 pessoas no mês"}).json()
    assert dados["modo"] == "sem_llm"
    assert dados["ferramentas_usadas"] == ["montar_cesta"]


def test_chat_mostra_etapas_dos_agentes(cliente):
    dados = cliente.post("/api/chat", json={"mensagem": "quanto custa o feijão preto?"}).json()
    assert [e["agente"] for e in dados["etapas"]][0] == "Orquestrador"
    assert dados["etapas"][-1]["agente"] == "Mia"


def test_cardapio(cliente):
    dados = cliente.post("/api/cardapio", json={"alimentos": ["lentilha", "cenoura", "abóbora"]}).json()
    assert "lentilha" in dados["resposta"].lower()


def test_chat_rejeita_mensagem_vazia(cliente):
    assert cliente.post("/api/chat", json={"mensagem": ""}).status_code == 422


@pytest.mark.parametrize(
    "corpo",
    [
        {"pessoas": 0},
        {"pessoas": 2, "periodo": "ano"},
        {"pessoas": 2, "orcamento": -5},
        {"pessoas": 2, "restricoes": ["dieta_x"]},
    ],
)
def test_entrada_invalida_retorna_422(cliente, corpo):
    assert cliente.post("/api/cesta", json=corpo).status_code == 422


def test_nfce_recusa_imagem_sem_qrcode(cliente):
    r = cliente.post("/api/nfce/imagem", files={"arquivo": ("x.png", b"nao e imagem", "image/png")})
    assert r.status_code == 422


def test_nfce_recusa_url_de_outro_dominio(cliente):
    r = cliente.post("/api/nfce/url", json={"url": "http://169.254.169.254/latest/meta-data"})
    assert r.status_code == 422
    assert "SEFAZ-DF" in r.json()["detail"]


def test_nfce_processa_nota_e_confirma_precos(cliente, monkeypatch):
    from pathlib import Path

    from economia import nfce

    html = (Path(__file__).parent / "fixtures" / "nfce_exemplo.html").read_text(encoding="utf-8")
    monkeypatch.setattr(nfce, "baixar_pagina", lambda url: html)
    nota = cliente.post("/api/nfce/url", json={"url": "https://www.fazenda.df.gov.br/nfce/qrcode?p=1"}).json()
    assert nota["emitente"] == "SUPERMERCADO EXEMPLO LTDA"

    confirmados = [{"produto_id": i["produto_id"], "preco": i["preco_embalagem"]} for i in nota["itens"] if i["confianca"] == "alta"]
    try:
        r = cliente.post("/api/nfce/confirmar", json={"emitente": nota["emitente"], "cnpj": nota["cnpj"], "data": nota["data"], "itens": confirmados})
        assert r.json() == {"salvos": 3}
        precos = cliente.get("/api/precos").json()
        arroz = next(p for p in precos["produtos"] if p["produto_id"] == "arroz-5kg")
        assert arroz["precos"]["nfce-12345678000190"] == {"preco": 24.9, "preco_kg": 4.98, "data": "2026-10-27", "fonte": "nfce"}
    finally:
        # Não deixa os preços do teste valendo para os outros testes.
        from economia import api
        from economia.dados import ARQ_CONTRIBUICOES

        ARQ_CONTRIBUICOES.unlink(missing_ok=True)
        api.recarregar_base()


def test_nfce_confirmar_recusa_produto_desconhecido(cliente):
    r = cliente.post("/api/nfce/confirmar", json={"emitente": "X", "data": "2026-10-27", "itens": [{"produto_id": "caviar", "preco": 10}]})
    assert r.status_code == 422
