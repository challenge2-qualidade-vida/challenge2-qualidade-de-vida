
"""Contratos da camada de aplicação da verificação."""

from typing import Protocol

from economia.verificacao.dominio.modelos import EvidenciaRecuperada


class PesquisadorDeEvidencias(Protocol):
    """Contrato para recuperação semântica de evidências científicas."""

    def pesquisar(
        self,
        pergunta: str,
        limite: int,
    ) -> list[EvidenciaRecuperada]:
        """Recupera evidências relevantes para uma pergunta ou alegação."""
        ...
