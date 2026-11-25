"""Contratos da camada de aplicação da verificação.

As portas do Research (pesquisa de evidências) ficam em `economia.pesquisa_evidencias`.
"""

from typing import Protocol


class ModeloDeLinguagem(Protocol):
    """LLM que classifica, justifica e aponta contradições. Nunca calcula valores (RN01)."""

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        """Objeto JSON que segue o esquema."""
        ...
