
from pathlib import Path

import pytest

from economia.leitura_documentos.infraestrutura.ingestao.extratores import (
    extrair_pdf,
    extrair_texto,
)


def test_extrair_texto_txt(tmp_path: Path):
    arquivo = tmp_path / "guia.txt"
    arquivo.write_text("Conteúdo do documento.", encoding="utf-8")

    assert extrair_texto(arquivo) == "Conteúdo do documento."


def test_extrair_texto_markdown(tmp_path: Path):
    arquivo = tmp_path / "guia.md"
    arquivo.write_text("# Título\n\nConteúdo.", encoding="utf-8")

    assert extrair_texto(arquivo) == "# Título\n\nConteúdo."


def test_extrair_pdf_preserva_separacao_entre_paginas(monkeypatch):
    class Pagina:
        def __init__(self, texto):
            self.texto = texto

        def get_text(self, formato):
            return self.texto

    class Documento:
        def __init__(self):
            self.paginas = [
                Pagina("Conteúdo da primeira página."),
                Pagina("Conteúdo da segunda página."),
            ]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __iter__(self):
            return iter(self.paginas)

    monkeypatch.setattr(
        "economia.leitura_documentos.infraestrutura.ingestao.extratores.pymupdf.open",
        lambda caminho: Documento(),
    )

    resultado = extrair_pdf(Path("guia.pdf"))

    assert resultado == (
        "[Página 1]\nConteúdo da primeira página."
        "\n\n"
        "[Página 2]\nConteúdo da segunda página."
    )


def test_extrair_pdf_ignora_paginas_sem_texto(monkeypatch):
    class Pagina:
        def __init__(self, texto):
            self.texto = texto

        def get_text(self, formato):
            return self.texto

    class Documento:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __iter__(self):
            return iter([
                Pagina("Conteúdo disponível."),
                Pagina("   "),
            ])

    monkeypatch.setattr(
        "economia.leitura_documentos.infraestrutura.ingestao.extratores.pymupdf.open",
        lambda caminho: Documento(),
    )

    resultado = extrair_pdf(Path("guia.pdf"))

    assert resultado == "[Página 1]\nConteúdo disponível."


def test_extrair_texto_rejeita_formato_nao_suportado(tmp_path: Path):
    arquivo = tmp_path / "guia.docx"
    arquivo.write_text("Conteúdo.", encoding="utf-8")

    with pytest.raises(ValueError, match="Formato não suportado"):
        extrair_texto(arquivo)
