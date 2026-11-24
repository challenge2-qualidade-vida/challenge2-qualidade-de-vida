"""Extração de texto de documentos da base de conhecimento."""

from pathlib import Path
from typing import TypedDict

import pymupdf


class PaginaExtraida(TypedDict):
    """Representa o texto extraído de uma página de PDF."""

    pagina: int
    texto: str


def extrair_paginas_pdf(caminho: Path) -> list[PaginaExtraida]:
    """Extrai texto de PDF, preservando o número de cada página."""
    paginas = []

    with pymupdf.open(caminho) as documento:
        for numero, pagina in enumerate(documento, start=1):
            texto = pagina.get_text("text")

            if texto.strip():
                paginas.append(
                    {
                        "pagina": numero,
                        "texto": texto,
                    }
                )

    return paginas


def extrair_pdf(caminho: Path) -> str:
    """Extrai texto de PDF textual, preservando separação entre páginas."""
    paginas = extrair_paginas_pdf(caminho)

    return "\n\n".join(
        f"[Página {pagina['pagina']}]\n{pagina['texto']}" for pagina in paginas
    )


def extrair_texto(caminho: Path) -> str:
    """Extrai texto dos formatos suportados."""
    extensao = caminho.suffix.lower()

    if extensao == ".pdf":
        return extrair_pdf(caminho)

    if extensao in {".txt", ".md"}:
        return caminho.read_text(encoding="utf-8")

    raise ValueError(f"Formato não suportado: {extensao}")
