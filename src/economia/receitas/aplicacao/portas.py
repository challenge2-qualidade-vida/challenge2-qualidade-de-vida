"""Portas do RAG de receitas: o que a aplicação precisa da infraestrutura.

Cada porta é um Protocol. Os adaptadores ficam em `infraestrutura/` e os testes usam dublês.
"""

from collections.abc import Sequence
from typing import Protocol

from economia.receitas.dominio.modelos import TipoDeTrecho, Trecho, TrechoRecuperado


class GeradorDeEmbeddings(Protocol):
    """Transforma textos em vetores normalizados."""

    nome: str
    dimensao: int

    def gerar_para_trechos(self, textos: Sequence[str]) -> list[list[float]]:
        """Vetores dos trechos que vão para a base."""
        ...

    def gerar_para_pergunta(self, pergunta: str) -> list[float]:
        """Vetor da pergunta. Cada modelo tem o seu prefixo de pergunta."""
        ...


class RepositorioDeTrechos(Protocol):
    """Guarda e busca trechos por similaridade de vetores."""

    def preparar(self, dimensao: int, recriar: bool = False) -> None:
        """Cria a coleção, se ainda não existir. Com `recriar`, apaga a anterior."""
        ...

    def gravar(
        self, trechos: Sequence[Trecho], vetores: Sequence[Sequence[float]]
    ) -> None:
        """Grava os trechos com os vetores. Gravar o mesmo trecho de novo substitui o anterior."""
        ...

    def buscar(
        self, vetor: Sequence[float], limite: int, tipo: TipoDeTrecho | None = None
    ) -> list[TrechoRecuperado]:
        """Trechos mais parecidos com o vetor, do maior score para o menor."""
        ...

    def contar(self) -> int:
        """Quantidade de trechos gravados."""
        ...


class ModeloDeLinguagem(Protocol):
    """LLM que interpreta a pergunta e redige a resposta. Nunca calcula valores (RN01)."""

    def gerar(self, sistema: str, mensagem: str) -> str:
        """Texto livre a partir das instruções (`sistema`) e da mensagem."""
        ...

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        """Objeto JSON que segue o esquema."""
        ...
