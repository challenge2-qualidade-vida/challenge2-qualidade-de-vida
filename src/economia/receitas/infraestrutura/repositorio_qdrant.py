"""Repositório de trechos no Qdrant: uma coleção por modelo de embeddings, distância cosseno."""

import uuid
from collections.abc import Sequence

from qdrant_client import QdrantClient, models

from economia.receitas.dominio.modelos import (
    Fonte,
    TipoDeTrecho,
    Trecho,
    TrechoRecuperado,
)

CAMPOS_INDEXADOS = ("tipo", "fonte", "idioma")


def id_do_ponto(trecho_id: str) -> str:
    """O Qdrant aceita só inteiro ou UUID. O UUID5 do id do trecho é estável entre indexações."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"economia/trecho/{trecho_id}"))


def para_payload(trecho: Trecho) -> dict:
    return {
        "trecho_id": trecho.id,
        "tipo": trecho.tipo.value,
        "documento_id": trecho.documento_id,
        "titulo": trecho.titulo,
        "texto": trecho.texto,
        "conteudo": trecho.conteudo,
        "idioma": trecho.idioma,
        "capitulo": trecho.capitulo,
        "secao": trecho.secao,
        "pagina": trecho.pagina,
        "ingredientes": list(trecho.ingredientes),
        "fonte": trecho.fonte.titulo,
        "instituicao": trecho.fonte.instituicao,
        "ano": trecho.fonte.ano,
        "url": trecho.fonte.url,
        "licenca": trecho.fonte.licenca,
    }


def de_payload(payload: dict) -> Trecho:
    return Trecho(
        id=payload["trecho_id"],
        tipo=TipoDeTrecho(payload["tipo"]),
        documento_id=payload["documento_id"],
        titulo=payload["titulo"],
        texto=payload["texto"],
        conteudo=payload["conteudo"],
        idioma=payload["idioma"],
        capitulo=payload.get("capitulo"),
        secao=payload.get("secao"),
        pagina=payload.get("pagina"),
        ingredientes=tuple(payload.get("ingredientes") or ()),
        fonte=Fonte(
            titulo=payload["fonte"],
            instituicao=payload["instituicao"],
            ano=payload.get("ano"),
            url=payload.get("url"),
            licenca=payload.get("licenca"),
        ),
    )


class RepositorioQdrant:
    def __init__(self, cliente: QdrantClient, colecao: str):
        self._cliente = cliente
        self.colecao = colecao

    @classmethod
    def conectar(cls, url: str, colecao: str) -> "RepositorioQdrant":
        return cls(QdrantClient(url=url, timeout=60), colecao)

    def preparar(self, dimensao: int, recriar: bool = False) -> None:
        existe = self._cliente.collection_exists(self.colecao)
        if existe and recriar:
            self._cliente.delete_collection(self.colecao)
            existe = False
        if not existe:
            self._cliente.create_collection(
                self.colecao,
                vectors_config=models.VectorParams(
                    size=dimensao, distance=models.Distance.COSINE
                ),
            )
            for campo in CAMPOS_INDEXADOS:
                self._cliente.create_payload_index(
                    self.colecao,
                    field_name=campo,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )

    def gravar(
        self, trechos: Sequence[Trecho], vetores: Sequence[Sequence[float]]
    ) -> None:
        self._cliente.upsert(
            self.colecao,
            points=[
                models.PointStruct(
                    id=id_do_ponto(t.id), vector=list(v), payload=para_payload(t)
                )
                for t, v in zip(trechos, vetores, strict=True)
            ],
        )

    def buscar(
        self, vetor: Sequence[float], limite: int, tipo: TipoDeTrecho | None = None
    ) -> list[TrechoRecuperado]:
        filtro = None
        if tipo is not None:
            filtro = models.Filter(
                must=[
                    models.FieldCondition(
                        key="tipo", match=models.MatchValue(value=tipo.value)
                    )
                ]
            )
        resposta = self._cliente.query_points(
            self.colecao,
            query=list(vetor),
            limit=limite,
            query_filter=filtro,
            with_payload=True,
        )
        return [
            TrechoRecuperado(trecho=de_payload(p.payload), score=p.score)
            for p in resposta.points
        ]

    def contar(self) -> int:
        if not self._cliente.collection_exists(self.colecao):
            return 0
        return self._cliente.count(self.colecao, exact=True).count
