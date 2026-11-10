"""Embeddings com o qwen3-embedding:4b, servido pelo Ollama (`/api/embed`)."""

import math
from collections.abc import Sequence
from typing import Any

NOME_DO_MODELO = "qwen3-embedding:4b"
# O Qwen3-Embedding recomenda a instrução em inglês, mesmo com textos em outros idiomas.
TAREFA = (
    "Given a question about recipes, cooking or healthy eating, "
    "retrieve passages that answer the question"
)


def _normalizar(vetor: Sequence[float]) -> list[float]:
    norma = math.sqrt(sum(x * x for x in vetor))
    return [x / norma for x in vetor] if norma else list(vetor)


class GeradorOllama:
    """Gerador de embeddings pelo Ollama. A pergunta leva a instrução da tarefa; o trecho, não."""

    nome = NOME_DO_MODELO
    dimensao = 2560

    def __init__(
        self,
        url: str = "http://localhost:11434",
        modelo: str = NOME_DO_MODELO,
        cliente: Any = None,
    ):
        if cliente is None:
            import ollama

            cliente = ollama.Client(host=url)
        self._cliente = cliente
        self._modelo = modelo
        self.nome = modelo

    def _gerar(self, textos: list[str]) -> list[list[float]]:
        resposta = self._cliente.embed(model=self._modelo, input=textos, truncate=True)
        return [_normalizar(v) for v in resposta["embeddings"]]

    def gerar_para_trechos(self, textos: Sequence[str]) -> list[list[float]]:
        return self._gerar(list(textos))

    def gerar_para_pergunta(self, pergunta: str) -> list[float]:
        return self._gerar([f"Instruct: {TAREFA}\nQuery: {pergunta}"])[0]
