import pytest

from economia.pesquisa_evidencias.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)
from economia.pesquisa_evidencias.infraestrutura.pesquisador_qdrant import (
    PesquisadorQdrant,
)


class GeradorFalso:
    def __init__(self):
        self.perguntas_recebidas = []

    def gerar_para_pergunta(self, pergunta):
        self.perguntas_recebidas.append(pergunta)
        return [0.1, 0.2, 0.3]


class RepositorioFalso:
    def __init__(self, evidencias):
        self.evidencias = evidencias
        self.vetor_recebido = None
        self.limite_recebido = None

    def buscar(self, vetor, limite):
        self.vetor_recebido = vetor
        self.limite_recebido = limite
        return self.evidencias


@pytest.fixture
def evidencia():
    fonte = FonteEvidencia(
        titulo="Estudo sobre alimentação",
        instituicao="Instituto de Pesquisa",
        ano=2024,
        url="https://exemplo.org/estudo",
    )

    documento = DocumentoEvidencia(
        id="doc_001",
        fonte=fonte,
        arquivo="estudo.pdf",
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


def test_pesquisa_encaminha_pergunta_e_retorna_evidencias(evidencia):
    gerador = GeradorFalso()
    repositorio = RepositorioFalso([evidencia])

    pesquisador = PesquisadorQdrant(
        gerador=gerador,
        repositorio=repositorio,
    )

    resultado = pesquisador.pesquisar(
        pergunta="Qual a importância da alimentação adequada?",
        limite=5,
    )

    assert gerador.perguntas_recebidas == [
        "Qual a importância da alimentação adequada?"
    ]
    assert repositorio.vetor_recebido == [0.1, 0.2, 0.3]
    assert repositorio.limite_recebido == 5
    assert resultado == [evidencia]
