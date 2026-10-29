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
