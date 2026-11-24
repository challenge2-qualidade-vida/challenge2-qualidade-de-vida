"""Caso de uso de pesquisa de evidências científicas."""

from economia.pesquisa_evidencias.aplicacao.portas import PesquisadorDeEvidencias
from economia.pesquisa_evidencias.dominio.modelos import EvidenciaRecuperada


class PesquisarEvidencias:
    """Coordena a recuperação de evidências para uma pergunta ou alegação."""

    def __init__(
        self,
        pesquisador: PesquisadorDeEvidencias,
        limiar_similaridade: float | None = None,
    ) -> None:
        if limiar_similaridade is not None and not 0.0 <= limiar_similaridade <= 1.0:
            raise ValueError("O limiar de similaridade deve estar entre 0 e 1.")

        self._pesquisador = pesquisador
        self._limiar_similaridade = limiar_similaridade

    def executar(
        self,
        pergunta: str,
        limite: int = 5,
    ) -> list[EvidenciaRecuperada]:
        """Valida a solicitação e recupera as evidências relevantes."""
        if not pergunta or not pergunta.strip():
            raise ValueError("A pergunta não pode ser vazia.")

        if limite < 1:
            raise ValueError("O limite de evidências deve ser positivo.")

        evidencias = self._pesquisador.pesquisar(
            pergunta=pergunta.strip(),
            limite=limite,
        )

        if self._limiar_similaridade is None:
            return evidencias

        return [
            evidencia
            for evidencia in evidencias
            if evidencia.score >= self._limiar_similaridade
        ]
