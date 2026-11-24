"""Caso de uso de pesquisa de evidências científicas."""

from economia.pesquisa_evidencias.aplicacao.portas import PesquisadorDeEvidencias
from economia.pesquisa_evidencias.dominio.modelos import EvidenciaRecuperada


class PesquisarEvidencias:
    """Coordena a recuperação de evidências para uma pergunta ou alegação."""

    def __init__(self, pesquisador: PesquisadorDeEvidencias) -> None:
        self._pesquisador = pesquisador

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

        return self._pesquisador.pesquisar(
            pergunta=pergunta.strip(),
            limite=limite,
        )
