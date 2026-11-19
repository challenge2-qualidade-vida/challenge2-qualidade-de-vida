
"""Testes do endpoint de pesquisa de evidências."""

import pytest
from fastapi.testclient import TestClient

from economia.api.dependencias import obter_pesquisar_evidencias
from economia.api.main import app
from economia.verificacao.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)


class CasoDeUsoFalso:
    """Simula o caso de uso sem conectar ao Qdrant."""

    def __init__(self, resultados=None):
        self.resultados = resultados if resultados is not None else []
        self.pergunta_recebida = None
        self.limite_recebido = None

    def executar(self, pergunta, limite=5):
        self.pergunta_recebida = pergunta
        self.limite_recebido = limite
        return self.resultados


@pytest.fixture
def evidencia():
    fonte = FonteEvidencia(
        titulo="Alimentação adequada e direitos humanos",
        instituicao="Organização de Pesquisa",
        ano=2024,
        url="https://exemplo.org/estudo",
    )

    documento = DocumentoEvidencia(
        id="doc_001",
        fonte=fonte,
        arquivo="alimentacao.pdf",
        hash_sha256="a" * 64,
    )

    trecho = TrechoEvidencia(
        id="doc_001_p1_t01",
        documento_id="doc_001",
        texto="A alimentação adequada é um direito humano.",
        pagina_inicial=1,
        pagina_final=1,
    )

    return EvidenciaRecuperada(
        trecho=trecho,
        documento=documento,
        score=0.92,
    )


def test_verificar_retorna_evidencias_com_proveniencia(evidencia):
    caso_de_uso = CasoDeUsoFalso(resultados=[evidencia])
    app.dependency_overrides[obter_pesquisar_evidencias] = (
        lambda: caso_de_uso
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/verificar",
            json={
                "pergunta": "segurança alimentar",
                "limite": 5,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    dados = response.json()

    assert dados["pergunta"] == "segurança alimentar"
    assert dados["total_evidencias"] == 1
    assert dados["evidencias"][0]["trecho"]["texto"] == (
        "A alimentação adequada é um direito humano."
    )
    assert dados["evidencias"][0]["trecho"]["pagina_inicial"] == 1
    assert dados["evidencias"][0]["documento"]["fonte"]["titulo"] == (
        "Alimentação adequada e direitos humanos"
    )
    assert dados["evidencias"][0]["score"] == 0.92
    assert caso_de_uso.pergunta_recebida == "segurança alimentar"
    assert caso_de_uso.limite_recebido == 5


@pytest.mark.parametrize("pergunta", ["", " ", "   "])
def test_verificar_rejeita_pergunta_vazia(pergunta):
    caso_de_uso = CasoDeUsoFalso()
    app.dependency_overrides[obter_pesquisar_evidencias] = (
        lambda: caso_de_uso
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/verificar",
            json={"pergunta": pergunta},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert caso_de_uso.pergunta_recebida is None


@pytest.mark.parametrize("limite", [0, -1, 21])
def test_verificar_rejeita_limite_invalido(limite):
    caso_de_uso = CasoDeUsoFalso()
    app.dependency_overrides[obter_pesquisar_evidencias] = (
        lambda: caso_de_uso
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/verificar",
            json={
                "pergunta": "segurança alimentar",
                "limite": limite,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert caso_de_uso.pergunta_recebida is None


def test_verificar_retorna_lista_vazia_sem_evidencias():
    caso_de_uso = CasoDeUsoFalso()
    app.dependency_overrides[obter_pesquisar_evidencias] = (
        lambda: caso_de_uso
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/verificar",
            json={"pergunta": "tema sem evidências"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total_evidencias"] == 0
    assert response.json()["evidencias"] == []
