
import pytest

from economia.verificacao.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)


@pytest.fixture
def fonte():
    return FonteEvidencia(
        titulo="Insegurança alimentar no Brasil",
        instituicao="Instituto de Pesquisa",
        ano=2024,
        url="https://exemplo.org/estudo",
    )


@pytest.fixture
def documento(fonte):
    return DocumentoEvidencia(
        id="doc_001",
        fonte=fonte,
        arquivo="estudo.pdf",
        hash_sha256="a" * 64,
    )


@pytest.fixture
def trecho():
    return TrechoEvidencia(
        id="doc_001_p12_t01",
        documento_id="doc_001",
        texto="A insegurança alimentar está associada a fatores socioeconômicos.",
        pagina_inicial=12,
        pagina_final=12,
        secao="Resultados",
    )


def test_cria_fonte_valida(fonte):
    assert fonte.titulo == "Insegurança alimentar no Brasil"
    assert fonte.instituicao == "Instituto de Pesquisa"
    assert fonte.ano == 2024


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("titulo", " "), ("instituicao", "")],
)
def test_fonte_recusa_campos_obrigatorios_vazios(campo, valor):
    dados = {
        "titulo": "Estudo",
        "instituicao": "Instituição",
    }
    dados[campo] = valor

    with pytest.raises(ValueError):
        FonteEvidencia(**dados)


def test_fonte_recusa_ano_invalido():
    with pytest.raises(ValueError):
        FonteEvidencia(
            titulo="Estudo",
            instituicao="Instituição",
            ano=0,
        )


def test_cria_documento_valido(documento):
    assert documento.id == "doc_001"
    assert documento.fonte.titulo == "Insegurança alimentar no Brasil"


def test_documento_recusa_identificador_vazio(fonte):
    with pytest.raises(ValueError):
        DocumentoEvidencia(
            id=" ",
            fonte=fonte,
            arquivo="estudo.pdf",
            hash_sha256="a" * 64,
        )


def test_cria_trecho_valido(trecho):
    assert trecho.documento_id == "doc_001"
    assert trecho.pagina_inicial == 12
    assert trecho.secao == "Resultados"


def test_trecho_recusa_texto_vazio():
    with pytest.raises(ValueError):
        TrechoEvidencia(
            id="trecho_001",
            documento_id="doc_001",
            texto=" ",
        )


def test_trecho_recusa_pagina_inicial_invalida():
    with pytest.raises(ValueError):
        TrechoEvidencia(
            id="trecho_001",
            documento_id="doc_001",
            texto="Conteúdo",
            pagina_inicial=0,
        )


def test_trecho_recusa_pagina_final_anterior_a_inicial():
    with pytest.raises(ValueError):
        TrechoEvidencia(
            id="trecho_001",
            documento_id="doc_001",
            texto="Conteúdo",
            pagina_inicial=5,
            pagina_final=3,
        )


def test_cria_evidencia_recuperada(trecho, documento):
    evidencia = EvidenciaRecuperada(
        trecho=trecho,
        documento=documento,
        score=0.91,
    )

    assert evidencia.trecho == trecho
    assert evidencia.documento == documento
    assert evidencia.score == 0.91


@pytest.mark.parametrize("score", [-1.1, 1.1])
def test_evidencia_recusa_score_fora_do_intervalo(
    trecho,
    documento,
    score,
):
    with pytest.raises(ValueError):
        EvidenciaRecuperada(
            trecho=trecho,
            documento=documento,
            score=score,
        )


def test_evidencia_recusa_documento_incompativel(trecho, fonte):
    outro_documento = DocumentoEvidencia(
        id="doc_002",
        fonte=fonte,
        arquivo="outro_estudo.pdf",
        hash_sha256="b" * 64,
    )

    with pytest.raises(ValueError):
        EvidenciaRecuperada(
            trecho=trecho,
            documento=outro_documento,
            score=0.91,
        )


def test_modelos_sao_imutaveis(fonte):
    with pytest.raises(AttributeError):
        fonte.titulo = "Outro título"
