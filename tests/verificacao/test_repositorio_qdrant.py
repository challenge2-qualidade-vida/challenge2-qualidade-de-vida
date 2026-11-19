
from economia.verificacao.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)
from economia.verificacao.infraestrutura.repositorio_qdrant import (
    de_payload,
    id_do_ponto,
    para_payload,
)


def criar_evidencia():
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
        id="doc_001_p12_t01",
        documento_id="doc_001",
        texto="A alimentação adequada é um direito humano.",
        pagina_inicial=12,
        pagina_final=12,
        secao="Resultados",
    )

    return EvidenciaRecuperada(
        trecho=trecho,
        documento=documento,
        score=0.92,
    )


def test_id_do_ponto_e_estavel():
    primeiro = id_do_ponto("doc_001_p12_t01")
    segundo = id_do_ponto("doc_001_p12_t01")

    assert primeiro == segundo


def test_id_do_ponto_diferencia_trechos():
    primeiro = id_do_ponto("doc_001_p12_t01")
    segundo = id_do_ponto("doc_001_p13_t01")

    assert primeiro != segundo


def test_para_payload_preserva_dados():
    evidencia = criar_evidencia()

    payload = para_payload(
        evidencia.trecho,
        evidencia.documento,
    )

    assert payload["trecho_id"] == "doc_001_p12_t01"
    assert payload["documento_id"] == "doc_001"
    assert payload["texto"] == "A alimentação adequada é um direito humano."
    assert payload["pagina_inicial"] == 12
    assert payload["pagina_final"] == 12
    assert payload["secao"] == "Resultados"
    assert payload["arquivo"] == "estudo.pdf"
    assert payload["hash_sha256"] == "a" * 64
    assert payload["fonte"]["titulo"] == "Estudo sobre alimentação"
    assert payload["fonte"]["instituicao"] == "Instituto de Pesquisa"
    assert payload["fonte"]["ano"] == 2024


def test_de_payload_reconstroi_documento_e_trecho():
    evidencia_original = criar_evidencia()

    payload = para_payload(
        evidencia_original.trecho,
        evidencia_original.documento,
    )

    trecho, documento = de_payload(payload)

    assert trecho == evidencia_original.trecho
    assert documento == evidencia_original.documento


def test_para_payload_rejeita_documento_incompativel():
    evidencia = criar_evidencia()

    outro_documento = DocumentoEvidencia(
        id="doc_002",
        fonte=evidencia.documento.fonte,
        arquivo="outro.pdf",
        hash_sha256="b" * 64,
    )

    try:
        para_payload(evidencia.trecho, outro_documento)
    except ValueError:
        pass
    else:
        raise AssertionError("Era esperado ValueError para documentos incompatíveis.")
