
"""Dependências da API EconoMIA."""

from functools import lru_cache

from economia.compartilhado.configuracao import obter_configuracao
from economia.compartilhado.infraestrutura.embeddings_e5 import GeradorE5
from economia.verificacao.aplicacao.pesquisar_evidencias import (
    PesquisarEvidencias,
)
from economia.verificacao.infraestrutura.pesquisador_qdrant import (
    PesquisadorQdrant,
)
from economia.verificacao.infraestrutura.repositorio_qdrant import (
    RepositorioQdrant,
)


@lru_cache(maxsize=1)
def obter_pesquisar_evidencias() -> PesquisarEvidencias:
    """Inicializa e disponibiliza o serviço de pesquisa de evidências."""
    configuracao = obter_configuracao()

    gerador = GeradorE5(
        dispositivo=configuracao.dispositivo_embeddings,
    )

    repositorio = RepositorioQdrant.conectar(
        url=configuracao.qdrant_url,
        colecao=configuracao.colecao_verificacao,
    )

    pesquisador = PesquisadorQdrant(
        gerador=gerador,
        repositorio=repositorio,
    )

    return PesquisarEvidencias(
        pesquisador=pesquisador,
    )
