"""Contratos públicos da aplicação de leitura documental."""

from pathlib import Path
from typing import Protocol, TypedDict


class PaginaDocumental(TypedDict):
    pagina: int
    texto: str


class LeitorDocumental(Protocol):
    """Contrato para extração e normalização de documentos."""

    def extrair_paginas_pdf(self, caminho: Path) -> list[PaginaDocumental]:
        """Extrai o texto de cada página de um PDF."""

    def normalizar_texto(self, texto: str) -> str:
        """Normaliza o texto extraído."""
