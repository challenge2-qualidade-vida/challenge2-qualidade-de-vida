"""Contratos da camada de aplicação da verificação.

A busca de evidências chega pelo `Pesquisar` de `verificar_alegacao.py`, já traduzida para o modelo
da verificação pelo adaptador de `infraestrutura/pesquisa_de_evidencias.py`.
"""

from typing import Protocol


class ModeloDeLinguagem(Protocol):
    """LLM que classifica, justifica e aponta contradições. Nunca calcula valores (RN01)."""

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        """Objeto JSON que segue o esquema."""
        ...
