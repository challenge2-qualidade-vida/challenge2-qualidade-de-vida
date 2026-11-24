"""Repositório de evidências científicas no Qdrant."""

import uuid
from collections.abc import Sequence
from typing import Any

from qdrant_client import QdrantClient, models

from economia.pesquisa_evidencias.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)


def id_do_ponto(trecho_id: str) -> str:
    """Gera um UUID estável a partir do identificador do trecho."""
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"economia/verificacao/trecho/{trecho_id}",
        )
    )


def para_payload(
    trecho: TrechoEvidencia,
    documento: DocumentoEvidencia,
) -> dict[str, Any]:
    """Converte um trecho e seu documento de origem em payload do Qdrant."""
    if trecho.documento_id != documento.id:
        raise ValueError("O trecho e o documento precisam ter o mesmo identificador.")

    return {
        "trecho_id": trecho.id,
        "documento_id": documento.id,
        "texto": trecho.texto,
        "pagina_inicial": trecho.pagina_inicial,
        "pagina_final": trecho.pagina_final,
        "secao": trecho.secao,
        "arquivo": documento.arquivo,
        "hash_sha256": documento.hash_sha256,
        "fonte": {
            "titulo": documento.fonte.titulo,
            "instituicao": documento.fonte.instituicao,
            "ano": documento.fonte.ano,
            "url": documento.fonte.url,
        },
    }


def limitar_score(score: float) -> float:
    """Traz o cosseno para [-1, 1]: o Qdrant pode devolver 1.0000001 por arredondamento."""
    return max(-1.0, min(1.0, score))


def de_payload(
    payload: dict[str, Any],
) -> tuple[
    TrechoEvidencia,
    DocumentoEvidencia,
]:
    """Reconstrói o trecho e seu documento a partir do payload do Qdrant."""
    dados_fonte = payload["fonte"]

    fonte = FonteEvidencia(
        titulo=dados_fonte["titulo"],
        instituicao=dados_fonte["instituicao"],
        ano=dados_fonte.get("ano"),
        url=dados_fonte.get("url"),
    )

    documento = DocumentoEvidencia(
        id=payload["documento_id"],
        fonte=fonte,
        arquivo=payload["arquivo"],
        hash_sha256=payload["hash_sha256"],
    )

    trecho = TrechoEvidencia(
        id=payload["trecho_id"],
        documento_id=payload["documento_id"],
        texto=payload["texto"],
        pagina_inicial=payload.get("pagina_inicial"),
        pagina_final=payload.get("pagina_final"),
        secao=payload.get("secao"),
    )

    return trecho, documento


class RepositorioQdrant:
    """Persistência e recuperação de evidências científicas no Qdrant."""

    def __init__(self, cliente: QdrantClient, colecao: str):
        self._cliente = cliente
        self.colecao = colecao

    @classmethod
    def conectar(
        cls,
        url: str,
        colecao: str,
    ) -> "RepositorioQdrant":
        """Cria uma conexão com o servidor Qdrant."""
        return cls(
            cliente=QdrantClient(url=url, timeout=60),
            colecao=colecao,
        )

    def preparar(self, dimensao: int, recriar: bool = False) -> None:
        """Cria a coleção de evidências, se ela ainda não existir."""
        existe = self._cliente.collection_exists(self.colecao)

        if existe and recriar:
            self._cliente.delete_collection(self.colecao)
            existe = False

        if not existe:
            self._cliente.create_collection(
                collection_name=self.colecao,
                vectors_config=models.VectorParams(
                    size=dimensao,
                    distance=models.Distance.COSINE,
                ),
            )

    def excluir_documento(self, documento_id: str) -> None:
        """Remove todos os pontos associados a um documento."""
        self._cliente.delete(
            collection_name=self.colecao,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="documento_id",
                            match=models.MatchValue(value=documento_id),
                        )
                    ]
                )
            ),
        )

    def excluir_documentos_fora_da_lista(
        self,
        documentos_ids: Sequence[str],
    ) -> None:
        """Remove pontos de documentos ausentes no manifesto atual."""
        if not documentos_ids:
            raise ValueError("A lista de documentos ativos não pode ser vazia.")

        self._cliente.delete(
            collection_name=self.colecao,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must_not=[
                        models.FieldCondition(
                            key="documento_id",
                            match=models.MatchAny(any=list(documentos_ids)),
                        )
                    ]
                )
            ),
        )

    def gravar(
        self,
        trechos: Sequence[TrechoEvidencia],
        documentos: Sequence[DocumentoEvidencia],
        vetores: Sequence[Sequence[float]],
    ) -> None:
        """Grava trechos científicos, documentos e seus vetores."""
        if not (len(trechos) == len(documentos) == len(vetores)):
            raise ValueError(
                "A quantidade de trechos, documentos e vetores precisa ser igual."
            )

        self._cliente.upsert(
            collection_name=self.colecao,
            points=[
                models.PointStruct(
                    id=id_do_ponto(trecho.id),
                    vector=list(vetor),
                    payload=para_payload(trecho, documento),
                )
                for trecho, documento, vetor in zip(
                    trechos,
                    documentos,
                    vetores,
                    strict=True,
                )
            ],
        )

    def buscar(
        self,
        vetor: Sequence[float],
        limite: int,
    ) -> list[EvidenciaRecuperada]:
        """Recupera evidências ordenadas por similaridade com a consulta."""
        resposta = self._cliente.query_points(
            collection_name=self.colecao,
            query=list(vetor),
            limit=limite,
            with_payload=True,
        )

        evidencias = []

        for ponto in resposta.points:
            trecho, documento = de_payload(ponto.payload)

            evidencias.append(
                EvidenciaRecuperada(
                    trecho=trecho,
                    documento=documento,
                    score=limitar_score(ponto.score),
                )
            )

        return evidencias

    def contar(self) -> int:
        """Retorna a quantidade de pontos da coleção."""
        if not self._cliente.collection_exists(self.colecao):
            return 0

        return self._cliente.count(
            collection_name=self.colecao,
            exact=True,
        ).count
