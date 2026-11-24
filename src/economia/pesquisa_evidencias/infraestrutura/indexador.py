"""Indexação da base científica da Research Agent no Qdrant."""

import hashlib
from pathlib import Path

from economia.pesquisa_evidencias.aplicacao.portas import (
    GeradorDeEmbeddings,
    PreparadorDeDocumentos,
    RepositorioDeEvidencias,
)
from economia.pesquisa_evidencias.dominio.modelos import (
    DocumentoEvidencia,
    TrechoEvidencia,
)
from economia.pesquisa_evidencias.infraestrutura.manifesto import (
    carregar_manifesto,
)

TAMANHO_LOTE_INDEXACAO = 64


class IndexadorEvidencias:
    """Coordena preparação, vetorização e persistência da base científica."""

    def __init__(
        self,
        preparador: PreparadorDeDocumentos,
        gerador: GeradorDeEmbeddings,
        repositorio: RepositorioDeEvidencias,
        pasta_base: Path,
        caminho_manifesto: Path,
        tamanho_lote: int = TAMANHO_LOTE_INDEXACAO,
    ) -> None:
        if tamanho_lote <= 0:
            raise ValueError("O tamanho do lote precisa ser positivo.")

        self._preparador = preparador
        self._gerador = gerador
        self._repositorio = repositorio
        self._pasta_base = Path(pasta_base)
        self._caminho_manifesto = Path(caminho_manifesto)
        self._tamanho_lote = tamanho_lote

    def executar(self) -> dict[str, int]:
        """Indexa as fontes catalogadas no manifesto."""
        fontes = carregar_manifesto(self._caminho_manifesto)

        if not fontes:
            raise ValueError("O manifesto não possui fontes cadastradas.")

        self._repositorio.preparar(
            dimensao=self._gerador.dimensao,
            recriar=False,
        )

        documentos_ativos = [
            hashlib.sha256(arquivo.encode("utf-8")).hexdigest()[:16]
            for arquivo in fontes
        ]
        self._repositorio.excluir_documentos_fora_da_lista(documentos_ativos)

        total_documentos = 0
        total_trechos = 0
        total_lotes = 0

        trechos_lote: list[TrechoEvidencia] = []
        documentos_lote: list[DocumentoEvidencia] = []

        for arquivo, metadados in fontes.items():
            caminho = self._pasta_base / arquivo

            if not caminho.is_file():
                raise FileNotFoundError(f"Documento não encontrado: {caminho}")

            documento, trechos = self._preparador.preparar(
                caminho=caminho,
                metadados=metadados,
            )

            if not trechos:
                raise ValueError(f"O documento não gerou trechos: {arquivo}")

            self._repositorio.excluir_documento(documento.id)
            total_documentos += 1

            for trecho in trechos:
                trechos_lote.append(trecho)
                documentos_lote.append(documento)

                if len(trechos_lote) >= self._tamanho_lote:
                    self._gravar_lote(trechos_lote, documentos_lote)
                    total_trechos += len(trechos_lote)
                    total_lotes += 1
                    trechos_lote = []
                    documentos_lote = []

        if trechos_lote:
            self._gravar_lote(trechos_lote, documentos_lote)
            total_trechos += len(trechos_lote)
            total_lotes += 1

        return {
            "documentos": total_documentos,
            "trechos": total_trechos,
            "lotes": total_lotes,
        }

    def _gravar_lote(
        self,
        trechos: list[TrechoEvidencia],
        documentos: list[DocumentoEvidencia],
    ) -> None:
        """Gera embeddings e persiste um lote de trechos."""
        textos = [trecho.texto for trecho in trechos]
        vetores = self._gerador.gerar_para_trechos(textos)

        if len(vetores) != len(trechos):
            raise ValueError(
                "A quantidade de embeddings gerados não corresponde "
                "à quantidade de trechos."
            )

        self._repositorio.gravar(
            trechos=trechos,
            documentos=documentos,
            vetores=vetores,
        )
