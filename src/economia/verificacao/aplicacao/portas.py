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


class ModeloDeLinguagem(Protocol):
    """LLM que classifica, justifica e aponta contradições. Nunca calcula valores (RN01)."""

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        """Objeto JSON que segue o esquema."""
        ...
