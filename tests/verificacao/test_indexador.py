
"""Testes do indexador de evidências científicas."""

from pathlib import Path
from typing import Any

import pytest

from economia.verificacao.dominio.modelos import (
    DocumentoEvidencia,
    FonteEvidencia,
    TrechoEvidencia,
)
from economia.verificacao.infraestrutura.indexador import (
    IndexadorEvidencias,
)


class PreparadorFalso:
    """Simula a preparação dos documentos científicos."""

    def preparar(
        self,
        caminho: Path,
        metadados: dict[str, Any],
    ) -> tuple[DocumentoEvidencia, list[TrechoEvidencia]]:
        documento = DocumentoEvidencia(
            id=f"id-{metadados['arquivo']}",
            fonte=FonteEvidencia(
                titulo=metadados["titulo"],
                instituicao=metadados["instituicao"],
                ano=metadados.get("ano"),
                url=metadados.get("url"),
            ),
            arquivo=metadados["arquivo"],
            hash_sha256="a" * 64,
        )

        quantidade = metadados.get("quantidade_trechos", 2)

        trechos = [
            TrechoEvidencia(
                id=f"{documento.id}-trecho-{indice}",
                documento_id=documento.id,
                texto=f"Texto científico {indice} de {documento.id}",
            )
            for indice in range(quantidade)
        ]

        return documento, trechos


class GeradorFalso:
    """Simula a geração de embeddings."""

    dimensao = 3

    def __init__(self) -> None:
        self.textos_recebidos: list[str] = []

    def gerar_para_trechos(
        self,
        textos: list[str],
    ) -> list[list[float]]:
        self.textos_recebidos.extend(textos)

        return [
            [float(indice), 0.1, 0.2]
            for indice, _ in enumerate(textos)
        ]


class RepositorioFalso:
    """Simula a persistência no Qdrant."""

    def __init__(self) -> None:
        self.dimensao_preparada: int | None = None
        self.recriar: bool | None = None
        self.lotes_gravados: list[
            tuple[
                list[TrechoEvidencia],
                list[DocumentoEvidencia],
                list[list[float]],
            ]
        ] = []

    def preparar(self, dimensao: int, recriar: bool = False) -> None:
        self.dimensao_preparada = dimensao
        self.recriar = recriar

    def gravar(
        self,
        trechos: list[TrechoEvidencia],
        documentos: list[DocumentoEvidencia],
        vetores: list[list[float]],
    ) -> None:
        self.lotes_gravados.append(
            (list(trechos), list(documentos), list(vetores))
        )


@pytest.fixture
def ambiente(tmp_path: Path) -> dict[str, Any]:
    """Monta os componentes falsos e um manifesto temporário."""
    pasta_base = tmp_path / "documentos"
    pasta_base.mkdir()

    fontes = [
        {
            "arquivo": "documento1.pdf",
            "titulo": "Documento 1",
            "instituicao": "Instituição 1",
            "ano": 2024,
            "quantidade_trechos": 3,
        },
        {
            "arquivo": "documento2.pdf",
            "titulo": "Documento 2",
            "instituicao": "Instituição 2",
            "ano": 2025,
            "quantidade_trechos": 2,
        },
    ]

    for fonte in fontes:
        (pasta_base / fonte["arquivo"]).touch()

    caminho_manifesto = tmp_path / "fontes.json"

    import json

    caminho_manifesto.write_text(
        json.dumps({"fontes": fontes}, ensure_ascii=False),
        encoding="utf-8",
    )

    preparador = PreparadorFalso()
    gerador = GeradorFalso()
    repositorio = RepositorioFalso()

    indexador = IndexadorEvidencias(
        preparador=preparador,
        gerador=gerador,
        repositorio=repositorio,
        pasta_base=pasta_base,
        caminho_manifesto=caminho_manifesto,
        tamanho_lote=2,
    )

    return {
        "indexador": indexador,
        "gerador": gerador,
        "repositorio": repositorio,
    }


def test_indexa_documentos_e_trechos(ambiente: dict[str, Any]) -> None:
    """Indexa todos os documentos e retorna os totais corretos."""
    resultado = ambiente["indexador"].executar()

    assert resultado == {
        "documentos": 2,
        "trechos": 5,
        "lotes": 3,
    }


def test_prepara_colecao_sem_recriar(
    ambiente: dict[str, Any],
) -> None:
    """Prepara a coleção sem solicitar a exclusão da existente."""
    ambiente["indexador"].executar()

    repositorio = ambiente["repositorio"]

    assert repositorio.dimensao_preparada == 3
    assert repositorio.recriar is False


def test_grava_lotes_com_embeddings_correspondentes(
    ambiente: dict[str, Any],
) -> None:
    """Gera e grava embeddings em lotes, inclusive o último incompleto."""
    ambiente["indexador"].executar()

    gerador = ambiente["gerador"]
    repositorio = ambiente["repositorio"]

    assert len(gerador.textos_recebidos) == 5
    assert [len(lote[0]) for lote in repositorio.lotes_gravados] == [
        2,
        2,
        1,
    ]

    for trechos, documentos, vetores in repositorio.lotes_gravados:
        assert len(trechos) == len(documentos) == len(vetores)

        for trecho, documento in zip(trechos, documentos, strict=True):
            assert trecho.documento_id == documento.id


def test_rejeita_tamanho_de_lote_invalido(tmp_path: Path) -> None:
    """Impede a criação do indexador com lote vazio ou negativo."""
    with pytest.raises(ValueError, match="tamanho do lote"):
        IndexadorEvidencias(
            preparador=PreparadorFalso(),
            gerador=GeradorFalso(),
            repositorio=RepositorioFalso(),
            pasta_base=tmp_path,
            caminho_manifesto=tmp_path / "fontes.json",
            tamanho_lote=0,
        )


def test_rejeita_documento_ausente(ambiente: dict[str, Any]) -> None:
    """Interrompe a indexação quando um PDF catalogado não existe."""
    indexador = ambiente["indexador"]
    pasta_base = indexador._pasta_base

    (pasta_base / "documento2.pdf").unlink()

    with pytest.raises(FileNotFoundError, match="Documento não encontrado"):
        indexador.executar()


def test_rejeita_quantidade_incorreta_de_embeddings(
    ambiente: dict[str, Any],
) -> None:
    """Impede a gravação quando o gerador retorna vetores insuficientes."""

    class GeradorIncorreto(GeradorFalso):
        def gerar_para_trechos(
            self,
            textos: list[str],
        ) -> list[list[float]]:
            return []

    indexador = ambiente["indexador"]

    indexador._gerador = GeradorIncorreto()

    with pytest.raises(ValueError, match="quantidade de embeddings"):
        indexador.executar()
