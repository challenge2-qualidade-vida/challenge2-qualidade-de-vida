"""Passos BDD da Research Agent."""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

from economia.api.dependencias import obter_pesquisar_evidencias
from economia.api.main import app
from economia.pesquisa_evidencias.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)

FEATURE = "75-research-agent/cenarios.feature"
ROTA = "/api/v1/verificar"


class CasoDeUsoFalso:
    """Simula a recuperação de evidências sem conectar ao Qdrant."""

    def __init__(self, resultados):
        self.resultados = resultados
        self.pergunta_recebida = None
        self.limite_recebido = None

    def executar(self, pergunta, limite=5):
        self.pergunta_recebida = pergunta
        self.limite_recebido = limite
        return self.resultados[:limite]


def criar_evidencia():
    """Cria uma evidência de teste com proveniência completa."""
    fonte = FonteEvidencia(
        titulo="Alimentação adequada e direitos humanos",
        instituicao="Organização de Pesquisa",
        ano=2024,
        url="https://exemplo.org/estudo",
    )

    documento = DocumentoEvidencia(
        id="doc_bdd_001",
        fonte=fonte,
        arquivo="alimentacao.pdf",
        hash_sha256="a" * 64,
    )

    trecho = TrechoEvidencia(
        id="doc_bdd_001_p1_t01",
        documento_id="doc_bdd_001",
        texto="A alimentação adequada é um direito humano.",
        pagina_inicial=1,
        pagina_final=2,
        secao="Direitos humanos",
    )

    return EvidenciaRecuperada(
        trecho=trecho,
        documento=documento,
        score=0.92,
    )


@pytest.fixture
def contexto():
    """Armazena os dados e resultados de cada cenário."""
    return {
        "evidencias": [],
        "pergunta": "segurança alimentar",
        "limite": 5,
        "resposta": None,
    }


@pytest.fixture
def cliente():
    """Disponibiliza cliente HTTP e limpa as dependências ao final."""
    app.dependency_overrides.clear()

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def executar_consulta(contexto, cliente, rota=ROTA):
    """Executa a API com uma implementação falsa do caso de uso."""
    caso_de_uso = CasoDeUsoFalso(contexto["evidencias"])

    app.dependency_overrides[obter_pesquisar_evidencias] = lambda: caso_de_uso

    contexto["resposta"] = cliente.post(
        rota,
        json={
            "pergunta": contexto["pergunta"],
            "limite": contexto["limite"],
        },
    )

    contexto["caso_de_uso"] = caso_de_uso


# ---------------------------------------------------------------------
# Cenários
# ---------------------------------------------------------------------


@scenario(FEATURE, "Recuperar evidências relacionadas à pergunta")
def test_recuperar_evidencias():
    pass


@scenario(FEATURE, "Preservar a proveniência das evidências")
def test_preservar_proveniencia():
    pass


@scenario(FEATURE, "Rejeitar pergunta vazia")
def test_rejeitar_pergunta_vazia():
    pass


@scenario(FEATURE, "Rejeitar limite de evidências inválido")
def test_rejeitar_limite_invalido():
    pass


@scenario(FEATURE, "Retornar resposta sem evidências")
def test_retorno_sem_evidencias():
    pass


# ---------------------------------------------------------------------
# Dado
# ---------------------------------------------------------------------


@given("que a base de conhecimento possui documentos indexados")
def base_com_documentos(contexto):
    contexto["evidencias"] = [
        criar_evidencia(),
        criar_evidencia(),
    ]


@given("que a pergunta está preenchida")
def pergunta_preenchida(contexto):
    contexto["pergunta"] = "segurança alimentar"


@given("que uma evidência foi recuperada")
def evidencia_recuperada(contexto):
    contexto["evidencias"] = [criar_evidencia()]


@given("que a pergunta está vazia ou contém somente espaços")
def pergunta_vazia(contexto):
    contexto["pergunta"] = "   "


@given("que solicito um limite menor que 1 ou maior que 20")
def limite_invalido(contexto):
    contexto["limite"] = 0


@given("que a pergunta não possui evidências correspondentes na base indexada")
def pergunta_sem_evidencias(contexto):
    contexto["pergunta"] = "assunto sem correspondência"
    contexto["evidencias"] = []


# ---------------------------------------------------------------------
# Quando
# ---------------------------------------------------------------------


@when(parsers.parse("solicito a recuperação de evidências com limite {limite:d}"))
def solicitar_com_limite(contexto, cliente, limite):
    contexto["limite"] = limite
    executar_consulta(contexto, cliente)


@when("o sistema monta a resposta")
def montar_resposta(contexto, cliente):
    executar_consulta(contexto, cliente)


@when(parsers.parse('envio uma solicitação para o endpoint "{rota}"'))
def enviar_solicitacao(contexto, cliente, rota):
    executar_consulta(contexto, cliente, rota)


@when("solicito a recuperação de evidências")
def solicitar_evidencias(contexto, cliente):
    executar_consulta(contexto, cliente)


# ---------------------------------------------------------------------
# Então
# ---------------------------------------------------------------------


@then(parsers.parse("o sistema deve retornar até {limite:d} evidências relevantes"))
def quantidade_de_evidencias(contexto, limite):
    resposta = contexto["resposta"]

    assert resposta.status_code == 200
    assert resposta.json()["total_evidencias"] <= limite


@then("cada evidência deve apresentar um score de similaridade")
def evidencias_com_score(contexto):
    evidencias = contexto["resposta"].json()["evidencias"]

    assert evidencias

    for evidencia in evidencias:
        assert isinstance(evidencia["score"], (int, float))
        assert -1 <= evidencia["score"] <= 1


@then("deve informar o texto do trecho recuperado")
def verificar_texto(contexto):
    dados = contexto["resposta"].json()

    assert dados["evidencias"][0]["trecho"]["texto"] == (
        "A alimentação adequada é um direito humano."
    )


@then("identificar o documento de origem")
def verificar_documento(contexto):
    dados = contexto["resposta"].json()

    assert dados["evidencias"][0]["documento"]["id"] == "doc_bdd_001"
    assert dados["evidencias"][0]["documento"]["arquivo"] == ("alimentacao.pdf")


@then("apresentar as informações bibliográficas disponíveis")
def verificar_fonte(contexto):
    fonte = contexto["resposta"].json()["evidencias"][0]["documento"]["fonte"]

    assert fonte["titulo"] == "Alimentação adequada e direitos humanos"
    assert fonte["instituicao"] == "Organização de Pesquisa"
    assert fonte["ano"] == 2024
    assert fonte["url"] == "https://exemplo.org/estudo"


@then("preservar a localização do trecho no documento")
def verificar_localizacao(contexto):
    trecho = contexto["resposta"].json()["evidencias"][0]["trecho"]

    assert trecho["pagina_inicial"] == 1
    assert trecho["pagina_final"] == 2
    assert trecho["secao"] == "Direitos humanos"


@then("a API deve retornar HTTP 422")
def verificar_http_422(contexto):
    assert contexto["resposta"].status_code == 422


@then("informar que a pergunta não pode ser vazia")
def verificar_erro_pergunta(contexto):
    problema = contexto["resposta"].json()

    assert problema["detail"] == "A pergunta não pode ser vazia."
    assert (
        contexto["resposta"]
        .headers["content-type"]
        .startswith("application/problem+json")
    )


@then("o sistema deve retornar uma lista vazia")
def verificar_lista_vazia(contexto):
    dados = contexto["resposta"].json()

    assert dados["evidencias"] == []


@then("informar total_evidencias igual a zero")
def verificar_total_zero(contexto):
    dados = contexto["resposta"].json()

    assert dados["total_evidencias"] == 0
