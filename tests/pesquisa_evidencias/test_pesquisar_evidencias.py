"""Testes do caso de uso de pesquisa de evidências."""

import pytest

from economia.pesquisa_evidencias.aplicacao.pesquisar_evidencias import (
    PesquisarEvidencias,
)
from economia.pesquisa_evidencias.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)


class PesquisadorFalso:
    """Dublê da porta de pesquisa para testes isolados."""

    def __init__(self, resultados=None):
        self.resultados = resultados or []
        self.pergunta_recebida = None
        self.limite_recebido = None

    def pesquisar(self, pergunta, limite):
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


def test_executa_pesquisa_com_sucesso(evidencia):
    pesquisador = PesquisadorFalso(resultados=[evidencia])
    caso_de_uso = PesquisarEvidencias(pesquisador)

    resultado = caso_de_uso.executar("segurança alimentar")

    assert resultado == [evidencia]
    assert pesquisador.pergunta_recebida == "segurança alimentar"
    assert pesquisador.limite_recebido == 5


def test_remove_espacos_excedentes_da_pergunta():
    pesquisador = PesquisadorFalso()
    caso_de_uso = PesquisarEvidencias(pesquisador)

    caso_de_uso.executar("  segurança alimentar  ", limite=3)

    assert pesquisador.pergunta_recebida == "segurança alimentar"
    assert pesquisador.limite_recebido == 3


@pytest.mark.parametrize("pergunta", ["", " ", "   "])
def test_rejeita_pergunta_vazia(pergunta):
    pesquisador = PesquisadorFalso()
    caso_de_uso = PesquisarEvidencias(pesquisador)

    with pytest.raises(ValueError, match="pergunta não pode ser vazia"):
        caso_de_uso.executar(pergunta)

    assert pesquisador.pergunta_recebida is None


@pytest.mark.parametrize("limite", [0, -1, -5])
def test_rejeita_limite_invalido(limite):
    pesquisador = PesquisadorFalso()
    caso_de_uso = PesquisarEvidencias(pesquisador)

    with pytest.raises(ValueError, match="limite de evidências deve ser positivo"):
        caso_de_uso.executar("segurança alimentar", limite=limite)

    assert pesquisador.pergunta_recebida is None


def test_retorna_lista_vazia_quando_nao_encontra_evidencias():
    pesquisador = PesquisadorFalso()
    caso_de_uso = PesquisarEvidencias(pesquisador)

    resultado = caso_de_uso.executar("tema sem evidências")

    assert resultado == []
