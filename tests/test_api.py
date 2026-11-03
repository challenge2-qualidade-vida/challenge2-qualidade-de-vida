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


def test_proximos_traz_mercados_e_ranking(cliente):
    dados = cliente.get("/api/proximos", params={"lat": -15.7617, "lon": -47.8825, "raio_km": 8}).json()
    assert [m["id"] for m in dados["mercados"]] == ["A", "B"]
    assert dados["custo_segundo_mercado"] > 0
    assert dados["proteinas"]["alimentos"]


def test_proximos_sem_mercado_no_raio(cliente):
    dados = cliente.get("/api/proximos", params={"lat": -16.0190, "lon": -48.0660, "raio_km": 2}).json()
    assert dados["mercados"] == [] and dados["proteinas"] is None


def test_proximos_valida_coordenadas(cliente):
    assert cliente.get("/api/proximos", params={"lat": 100, "lon": 0}).status_code == 422


def test_cesta_so_com_mercados_escolhidos(cliente):
    dados = cliente.post("/api/cesta", json={"pessoas": 2, "mercados": ["A"]}).json()
    assert dados["cesta_recomendada"]["mercados"] == ["A"]
    assert cliente.post("/api/cesta", json={"pessoas": 2, "mercados": ["Z"]}).status_code == 422


def test_regioes(cliente):
    assert any(r["id"] == "taguatinga" for r in cliente.get("/api/regioes").json())


def test_osm_fora_do_ar_retorna_502(cliente, monkeypatch):
    import httpx

    from economia import geo

    def falha(*a, **k):
        raise httpx.ConnectError("sem rede")

    monkeypatch.setattr(geo.httpx, "post", falha)
    r = cliente.get("/api/osm", params={"lat": -15.76, "lon": -47.88})
    assert r.status_code == 502


def test_configuracoes_padrao(cliente):
    c = cliente.get("/api/configuracoes").json()
    assert c["raio_km"] == {"padrao": 10, "minimo": 1, "maximo": 100}


def test_proximos_aceita_raio_de_1_a_100(cliente):
    base = {"lat": -15.7617, "lon": -47.8825}
    assert cliente.get("/api/proximos", params={**base, "raio_km": 100}).status_code == 200
    assert cliente.get("/api/proximos", params={**base, "raio_km": 101}).status_code == 422
    assert cliente.get("/api/proximos", params={**base, "raio_km": 0.5}).status_code == 422


def test_proximos_informa_o_mais_proximo_fora_do_raio(cliente):
    d = cliente.get("/api/proximos", params={"lat": -15.7617, "lon": -47.8825, "raio_km": 1}).json()
    assert [m["id"] for m in d["mercados"]] == ["A"]
    assert d["mais_proximo_fora_do_raio_km"] == pytest.approx(6.4, abs=0.2)
    assert d["total_com_localizacao"] == 3


def test_proximos_usa_o_custo_por_km_do_usuario(cliente):
    params = {"lat": -15.7617, "lon": -47.8825, "raio_km": 10}
    barato = cliente.get("/api/proximos", params={**params, "custo_por_km": 0.2}).json()
    caro = cliente.get("/api/proximos", params={**params, "custo_por_km": 2.0}).json()
    b, c = barato["mercados"][1]["custo_ida_volta"], caro["mercados"][1]["custo_ida_volta"]
    assert c == pytest.approx(b * 10, rel=0.02)


def test_todo_alimento_tem_foto_e_credito(cliente):
    from pathlib import Path

    creditos = {c["alimento_id"]: c for c in cliente.get("/api/creditos").json()}
    opcoes = cliente.get("/api/precos").json()["produtos"]
    raiz = Path(__file__).resolve().parents[1] / "src" / "web"
    for p in opcoes:
        aid = p["alimento_id"]
        assert (raiz / "img" / "alimentos" / f"{aid}.webp").exists(), aid
        assert creditos[aid]["autor"] and creditos[aid]["licenca"] and creditos[aid]["pagina"], aid


def test_cesta_no_chat_traz_alimento_para_a_foto(cliente):
    dados = cliente.post("/api/chat", json={"mensagem": "Tenho R$ 800 para 4 pessoas no mês"}).json()
    detalhe = dados["dados"]["montar_cesta"]["itens_detalhe"]
    assert detalhe and all(i["alimento_id"] for i in detalhe)


def test_site_pede_revalidacao_para_nao_ficar_com_arquivo_antigo(cliente):
    assert cliente.get("/app.js").headers["cache-control"] == "no-cache"
    assert "cache-control" not in cliente.get("/api/saude").headers


def test_cesta_com_troca_e_em_casa(cliente):
    base_pedido = {"orcamento": None, "pessoas": 2, "periodo": "semana"}
    normal = cliente.post("/api/cesta", json=base_pedido).json()
    alvo = normal["cesta_recomendada"]["itens"][0]["alimento_id"]
    trocada = cliente.post("/api/cesta", json={**base_pedido, "sem_alimentos": [alvo]}).json()
    assert alvo not in {i["alimento_id"] for i in trocada["cesta_recomendada"]["itens"]}
    assert any("pediu para trocar" in f for f in trocada["explicacao"])
    casa = cliente.post("/api/cesta", json={**base_pedido, "em_casa": [{"alimento": "arroz", "gramas": 3000}]}).json()
    assert casa["cesta_recomendada"]["custo_total"] < normal["cesta_recomendada"]["custo_total"]
    assert any("3,0 kg de arroz" in f for f in casa["explicacao"])


def test_cesta_recusa_alimento_desconhecido(cliente):
    r = cliente.post("/api/cesta", json={"pessoas": 1, "sem_alimentos": ["pedra"]})
    assert r.status_code == 422
    r = cliente.post("/api/cesta", json={"pessoas": 1, "em_casa": [{"alimento": "pedra", "gramas": 10}]})
    assert r.status_code == 422


def test_opcoes_lista_alimentos(cliente):
    alimentos = cliente.get("/api/opcoes").json()["alimentos"]
    assert {"id": "arroz", "nome": "arroz"} in alimentos
