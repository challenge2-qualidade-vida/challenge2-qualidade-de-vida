"""Adaptador de pesquisa semântica usando embeddings e Qdrant."""

from economia.pesquisa_evidencias.aplicacao.portas import (
    GeradorDeEmbeddings,
    RepositorioDeEvidencias,
)
from economia.pesquisa_evidencias.dominio.modelos import EvidenciaRecuperada


class PesquisadorQdrant:
    """Recupera evidências científicas por similaridade semântica."""

    def __init__(
        self,
        gerador: GeradorDeEmbeddings,
        repositorio: RepositorioDeEvidencias,
    ) -> None:
        self._gerador = gerador
        self._repositorio = repositorio

    def pesquisar(
        self,
        pergunta: str,
        limite: int,
    ) -> list[EvidenciaRecuperada]:
        """Gera o vetor da pergunta e recupera as evidências mais semelhantes.

        A pergunta e o limite chegam validados pelo caso de uso `PesquisarEvidencias`.
        """
        vetor = self._gerador.gerar_para_pergunta(pergunta)

        return self._repositorio.buscar(
            vetor=vetor,
            limite=limite,
        )
