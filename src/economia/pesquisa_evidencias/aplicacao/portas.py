"""Contratos da camada de aplicação da pesquisa de evidências."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from economia.pesquisa_evidencias.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    TrechoEvidencia,
)


class PesquisadorDeEvidencias(Protocol):
    """Contrato para recuperação semântica de evidências científicas."""

    def pesquisar(
        self,
        pergunta: str,
        limite: int,
    ) -> list[EvidenciaRecuperada]:
        """Recupera evidências relevantes para uma pergunta ou alegação."""
        ...


class GeradorDeEmbeddings(Protocol):
    """Contrato para geração de embeddings de textos."""

    dimensao: int

    def gerar_para_trechos(
        self,
        textos: list[str],
    ) -> list[list[float]]:
        """Gera embeddings para trechos documentais."""
        ...

    def gerar_para_pergunta(
        self,
        pergunta: str,
    ) -> list[float]:
        """Gera embedding para uma pergunta."""
        ...


class RepositorioDeEvidencias(Protocol):
    """Contrato para persistência e recuperação de evidências."""

    def preparar(self, dimensao: int, recriar: bool = False) -> None:
        """Prepara a coleção vetorial."""

    def excluir_documento(self, documento_id: str) -> None:
        """Remove os trechos anteriores de um documento."""

    def excluir_documentos_fora_da_lista(
        self,
        documentos_ids: Sequence[str],
    ) -> None:
        """Remove documentos que não pertencem mais ao manifesto."""

    def gravar(
        self,
        trechos: Sequence[TrechoEvidencia],
        documentos: Sequence[DocumentoEvidencia],
        vetores: Sequence[Sequence[float]],
    ) -> None:
        """Persiste trechos, documentos e vetores."""

    def buscar(
        self,
        vetor: Sequence[float],
        limite: int,
    ) -> list[EvidenciaRecuperada]:
        """Recupera evidências por similaridade semântica."""


class PreparadorDeDocumentos(Protocol):
    """Contrato para preparação de documentos científicos."""

    def preparar(
        self,
        caminho: Path,
        metadados: Mapping[str, Any],
    ) -> tuple[DocumentoEvidencia, list[TrechoEvidencia]]:
        """Extrai e fragmenta um documento."""
