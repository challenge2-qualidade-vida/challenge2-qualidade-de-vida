
"""Compatibilidade para o gerador E5 compartilhado."""

from economia.compartilhado.infraestrutura.embeddings_e5 import (
    GeradorE5,
    contador_de_tokens_e5,
    escolher_dispositivo,
)

__all__ = [
    "GeradorE5",
    "contador_de_tokens_e5",
    "escolher_dispositivo",
]
