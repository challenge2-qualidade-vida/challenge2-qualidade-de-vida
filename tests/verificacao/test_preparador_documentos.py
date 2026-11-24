
"""Testes da preparação documental da Research Agent."""

import hashlib

import pymupdf
import pytest

from economia.leitura_documentos.infraestrutura.ingestao.extratores import (
    extrair_paginas_pdf,
)
from economia.leitura_documentos.infraestrutura.ingestao.normalizadores import (
    normalizar_texto,
)
from economia.verificacao.infraestrutura.preparador_documentos import (
    PreparadorDocumentos,
)


def contar_palavras(texto: str) -> int:
    """Contador simples para testes, sem carregar o modelo E5."""
    return len(texto.split())


def criar_pdf(caminho, paginas: list[str]) -> None:
    """Cria um PDF de teste com o conteúdo informado."""
    documento = pymupdf.open()

    for texto in paginas:
        pagina = documento.new_page()
        if texto:
            pagina.insert_text((72, 72), texto)

    documento.save(caminho)
    documento.close()


def criar_metadados() -> dict:
    """Retorna metadados válidos para os testes."""
    return {
        "arquivo": "orientacao-alimentar/documento_teste.pdf",
        "titulo": "Documento científico de teste",
        "instituicao": "Instituição de teste",
        "ano": 2026,
        "url": "https://exemplo.org/documento",
    }


def test_prepara_pdf_preservando_documento_e_paginas(tmp_path):
    caminho = tmp_path / "documento.pdf"

    criar_pdf(
        caminho,
        [
            "um dois tres",
            "quatro cinco seis",
        ],
    )

    preparador = PreparadorDocumentos(
        contar_tokens=contar_palavras,
        limite_tokens=5,
        overlap_tokens=0,
    )

    documento, trechos = preparador.preparar(
        caminho=caminho,
        metadados=criar_metadados(),
    )

    assert documento.id == hashlib.sha256(
        b"orientacao-alimentar/documento_teste.pdf"
    ).hexdigest()[:16]

    assert documento.fonte.titulo == "Documento científico de teste"
    assert documento.fonte.instituicao == "Instituição de teste"
    assert documento.fonte.ano == 2026
    assert documento.fonte.url == "https://exemplo.org/documento"

    assert len(trechos) == 2
    assert trechos[0].pagina_inicial == 1
    assert trechos[0].pagina_final == 1
    assert trechos[1].pagina_inicial == 2
    assert trechos[1].pagina_final == 2

    assert all(
        trecho.documento_id == documento.id
        for trecho in trechos
    )

    assert all(
        contar_palavras(trecho.texto) <= 5
        for trecho in trechos
    )


def test_preserva_hash_do_pipeline_original(tmp_path):
    caminho = tmp_path / "documento.pdf"

    criar_pdf(
        caminho,
        [
            "Primeira pagina do documento.",
            "Segunda pagina do documento.",
        ],
    )

    paginas = extrair_paginas_pdf(caminho)

    texto_integral = "\n\n".join(
        f"[Página {pagina['pagina']}]\n{pagina['texto']}"
        for pagina in paginas
    )

    texto_normalizado = normalizar_texto(texto_integral)

    hash_esperado = hashlib.sha256(
        texto_normalizado.encode("utf-8")
    ).hexdigest()

    preparador = PreparadorDocumentos(
        contar_tokens=contar_palavras,
    )

    documento, _ = preparador.preparar(
        caminho=caminho,
        metadados=criar_metadados(),
    )

    assert documento.hash_sha256 == hash_esperado


def test_rejeita_arquivo_que_nao_seja_pdf(tmp_path):
    caminho = tmp_path / "documento.txt"
    caminho.write_text("Texto de teste.", encoding="utf-8")

    preparador = PreparadorDocumentos(
        contar_tokens=contar_palavras,
    )

    with pytest.raises(ValueError, match="apenas arquivos PDF"):
        preparador.preparar(
            caminho=caminho,
            metadados=criar_metadados(),
        )


def test_rejeita_pdf_sem_texto_extraivel(tmp_path):
    caminho = tmp_path / "documento_vazio.pdf"

    criar_pdf(caminho, ["", ""])

    preparador = PreparadorDocumentos(
        contar_tokens=contar_palavras,
    )

    with pytest.raises(ValueError, match="não possui texto extraível"):
        preparador.preparar(
            caminho=caminho,
            metadados=criar_metadados(),
        )
