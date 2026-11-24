"""Testes do endpoint de pesquisa de evidências."""

import pytest
from fastapi.testclient import TestClient

from economia.api.dependencias import obter_pesquisar_evidencias
from economia.api.main import app
from economia.pesquisa_evidencias.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)

ROTA = "/api/v1/verificar"


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
def cliente():
    """Disponibiliza um cliente HTTP com limpeza das dependências."""
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


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


def registrar_caso_de_uso(caso_de_uso):
    """Substitui a dependência real por um caso de uso falso."""
    app.dependency_overrides[obter_pesquisar_evidencias] = lambda: caso_de_uso


def verificar_problem_details(response, status, detalhe):
    """Confere o formato de erro definido pela RFC 9457."""
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")

    problema = response.json()

    assert problema["type"] == "about:blank"
    assert problema["status"] == status
    assert problema["title"]
    assert problema["detail"] == detalhe
    assert problema["instance"] == ROTA


def test_verificar_retorna_evidencias_com_proveniencia(cliente, evidencia):
    caso_de_uso = CasoDeUsoFalso(resultados=[evidencia])
    registrar_caso_de_uso(caso_de_uso)

    response = cliente.post(
        ROTA,
        json={
            "pergunta": "segurança alimentar",
            "limite": 5,
        },
    )

    assert response.status_code == 200

    dados = response.json()

    assert dados["pergunta"] == "segurança alimentar"
    assert dados["total_evidencias"] == 1
    assert dados["evidencias"][0]["trecho"]["id"] == "doc_001_p1_t01"
    assert dados["evidencias"][0]["trecho"]["texto"] == (
        "A alimentação adequada é um direito humano."
    )
    assert dados["evidencias"][0]["trecho"]["pagina_inicial"] == 1
    assert dados["evidencias"][0]["trecho"]["pagina_final"] == 1
    assert dados["evidencias"][0]["documento"]["id"] == "doc_001"
    assert dados["evidencias"][0]["documento"]["arquivo"] == ("alimentacao.pdf")
    assert dados["evidencias"][0]["documento"]["hash_sha256"] == "a" * 64
    assert dados["evidencias"][0]["documento"]["fonte"]["titulo"] == (
        "Alimentação adequada e direitos humanos"
    )
    assert dados["evidencias"][0]["documento"]["fonte"]["instituicao"] == (
        "Organização de Pesquisa"
    )
    assert dados["evidencias"][0]["score"] == 0.92
    assert caso_de_uso.pergunta_recebida == "segurança alimentar"
    assert caso_de_uso.limite_recebido == 5


def test_verificar_normaliza_espacos_da_pergunta(cliente, evidencia):
    caso_de_uso = CasoDeUsoFalso(resultados=[evidencia])
    registrar_caso_de_uso(caso_de_uso)

    response = cliente.post(
        ROTA,
        json={"pergunta": "  segurança alimentar  "},
    )

    assert response.status_code == 200
    assert response.json()["pergunta"] == "segurança alimentar"
    assert caso_de_uso.pergunta_recebida == "segurança alimentar"


@pytest.mark.parametrize("pergunta", ["", " ", "   "])
def test_verificar_rejeita_pergunta_vazia(cliente, pergunta):
    caso_de_uso = CasoDeUsoFalso()
    registrar_caso_de_uso(caso_de_uso)

    response = cliente.post(
        ROTA,
        json={"pergunta": pergunta},
    )

    verificar_problem_details(
        response,
        422,
        "A pergunta não pode ser vazia.",
    )
    assert caso_de_uso.pergunta_recebida is None


@pytest.mark.parametrize("limite", [0, -1, 21])
def test_verificar_rejeita_limite_invalido(cliente, limite):
    caso_de_uso = CasoDeUsoFalso()
    registrar_caso_de_uso(caso_de_uso)

    response = cliente.post(
        ROTA,
        json={
            "pergunta": "segurança alimentar",
            "limite": limite,
        },
    )

    verificar_problem_details(
        response,
        422,
        "O limite de evidências deve estar entre 1 e 20.",
    )
    assert caso_de_uso.pergunta_recebida is None


def test_verificar_retorna_lista_vazia_sem_evidencias(cliente):
    caso_de_uso = CasoDeUsoFalso()
    registrar_caso_de_uso(caso_de_uso)

    response = cliente.post(
        ROTA,
        json={"pergunta": "tema sem evidências"},
    )

    assert response.status_code == 200
    assert response.json()["pergunta"] == "tema sem evidências"
    assert response.json()["total_evidencias"] == 0
    assert response.json()["evidencias"] == []
