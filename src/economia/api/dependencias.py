"""Dependências da API EconoMIA."""

from functools import lru_cache

from economia.compartilhado.configuracao import obter_configuracao
from economia.compartilhado.infraestrutura.embeddings_e5 import GeradorE5
from economia.pesquisa_evidencias.aplicacao.pesquisar_evidencias import (
    PesquisarEvidencias,
)
from economia.pesquisa_evidencias.infraestrutura.pesquisador_qdrant import (
    PesquisadorQdrant,
)
from economia.pesquisa_evidencias.infraestrutura.repositorio_qdrant import (
    RepositorioQdrant,
)
from economia.verificacao.aplicacao.verificar_alegacao import VerificarAlegacao


@lru_cache(maxsize=1)
def obter_pesquisar_evidencias() -> PesquisarEvidencias:
    """Inicializa e disponibiliza o serviço de pesquisa de evidências."""
    configuracao = obter_configuracao()

    gerador = GeradorE5(
        dispositivo=configuracao.dispositivo_embeddings,
    )

    repositorio = RepositorioQdrant.conectar(
        url=configuracao.qdrant_url,
        colecao=configuracao.colecao_pesquisa_evidencias,
    )

    pesquisador = PesquisadorQdrant(
        gerador=gerador,
        repositorio=repositorio,
    )

    return PesquisarEvidencias(
        pesquisador=pesquisador,
        limiar_similaridade=configuracao.limiar_similaridade,
    )


@lru_cache(maxsize=1)
def obter_verificar_alegacao() -> VerificarAlegacao:
    """Orquestrador da verificação (#82): e5, Qdrant, Ollama e os prompts `production`.

    Usa as mesmas fábricas da CLI. Criado uma vez por processo.
    """
    from economia.api.app import obter_langfuse
    from economia.verificacao.cli import criar_verificar_alegacao

    return criar_verificar_alegacao(obter_configuracao(), obter_langfuse())
