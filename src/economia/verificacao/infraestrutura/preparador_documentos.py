
"""Preparação de documentos científicos para a Research Agent."""

import hashlib
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from economia.leitura_documentos.infraestrutura.ingestao.extratores import (
    extrair_paginas_pdf,
)
from economia.leitura_documentos.infraestrutura.ingestao.normalizadores import (
    normalizar_texto,
)
from economia.verificacao.aplicacao.fragmentacao import (
    LIMITE_TOKENS_TRECHO,
    fragmentar_documento,
)
from economia.verificacao.dominio.modelos import (
    DocumentoEvidencia,
    FonteEvidencia,
    TrechoEvidencia,
)


class PreparadorDocumentos:
    """Prepara PDFs científicos em documentos e trechos recuperáveis."""

    def __init__(
        self,
        contar_tokens: Callable[[str], int],
        limite_tokens: int = LIMITE_TOKENS_TRECHO,
        overlap_tokens: int | None = None,
    ) -> None:
        self._contar_tokens = contar_tokens
        self._limite_tokens = limite_tokens
        self._overlap_tokens = overlap_tokens

    def preparar(
        self,
        caminho: Path,
        metadados: Mapping[str, Any],
    ) -> tuple[DocumentoEvidencia, list[TrechoEvidencia]]:
        """Extrai, normaliza e fragmenta um PDF com sua proveniência."""
        caminho = Path(caminho)

        if caminho.suffix.lower() != ".pdf":
            raise ValueError(
                "A preparação da Research Agent aceita apenas arquivos PDF."
            )

        arquivo = metadados.get("arquivo")
        if not isinstance(arquivo, str) or not arquivo.strip():
            raise ValueError("O documento precisa de um caminho relativo.")

        titulo = metadados.get("titulo")
        instituicao = metadados.get("instituicao")
        ano = metadados.get("ano")
        url = metadados.get("url")

        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError("A fonte precisa de título.")

        if not isinstance(instituicao, str) or not instituicao.strip():
            raise ValueError("A fonte precisa da instituição.")

        if ano is not None and (
            not isinstance(ano, int)
            or isinstance(ano, bool)
            or ano <= 0
        ):
            raise ValueError("O ano da fonte precisa ser um inteiro positivo.")

        if url is not None and not isinstance(url, str):
            raise ValueError("A URL da fonte precisa ser textual.")

        paginas_extraidas = extrair_paginas_pdf(caminho)

        if not paginas_extraidas:
            raise ValueError(
                "O documento não possui texto extraível."
            )

        paginas_normalizadas = [
            {
                "pagina": pagina["pagina"],
                "texto": normalizar_texto(pagina["texto"]),
            }
            for pagina in paginas_extraidas
        ]

        paginas_normalizadas = [
            pagina
            for pagina in paginas_normalizadas
            if pagina["texto"]
        ]

        # Mantém o mesmo formato de reconstrução do pipeline original.
        texto_integral = "\n\n".join(
            f"[Página {pagina['pagina']}]\n{pagina['texto']}"
            for pagina in paginas_extraidas
        )

        texto_integral = normalizar_texto(texto_integral)

        hash_texto = hashlib.sha256(
            texto_integral.encode("utf-8")
        ).hexdigest()

        # Mantém o mesmo identificador estável do pipeline documental.
        identificador = hashlib.sha256(
            arquivo.encode("utf-8")
        ).hexdigest()[:16]

        fonte = FonteEvidencia(
            titulo=titulo,
            instituicao=instituicao,
            ano=ano,
            url=url,
        )

        documento = DocumentoEvidencia(
            id=identificador,
            fonte=fonte,
            arquivo=arquivo,
            hash_sha256=hash_texto,
        )

        trechos = fragmentar_documento(
            paginas=paginas_normalizadas,
            documento_id=documento.id,
            contar_tokens=self._contar_tokens,
            limite_tokens=self._limite_tokens,
            overlap_tokens=self._overlap_tokens,
        )

        return documento, trechos
