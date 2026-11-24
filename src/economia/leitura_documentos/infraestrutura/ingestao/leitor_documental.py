"""Adaptador de leitura documental para consumidores do contexto."""

from pathlib import Path

from economia.leitura_documentos.aplicacao.portas import PaginaDocumental
from economia.leitura_documentos.infraestrutura.ingestao.extratores import (
    extrair_paginas_pdf,
)
from economia.leitura_documentos.infraestrutura.ingestao.normalizadores import (
    normalizar_texto,
)


class LeitorDocumentalPDF:
    """Implementa o contrato de leitura usando os componentes existentes."""

    def extrair_paginas_pdf(self, caminho: Path) -> list[PaginaDocumental]:
        return extrair_paginas_pdf(caminho)

    def normalizar_texto(self, texto: str) -> str:
        return normalizar_texto(texto)
