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
        """Gera o vetor da pergunta e recupera as evidências mais semelhantes."""
        if not pergunta or not pergunta.strip():
            raise ValueError("A pergunta não pode ser vazia.")

        if limite < 1:
            raise ValueError("O limite de evidências deve ser positivo.")

        vetor = self._gerador.gerar_para_pergunta(pergunta.strip())

        return self._repositorio.buscar(
            vetor=vetor,
            limite=limite,
        )
