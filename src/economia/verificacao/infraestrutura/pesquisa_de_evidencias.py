"""Adaptador da Pesquisa de evidências (Research Agent, #75) para a verificação.

A verificação chama o caso de uso da camada `aplicacao` da Pesquisa de evidências e traduz
cada evidência para o modelo dela (`verificacao/dominio/evidencias.py`). Este é o único
ponto da verificação que conhece o formato do Research.
"""

from collections.abc import Callable, Sequence
from typing import Any

from economia.verificacao.dominio.evidencias import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)


def traduzir_evidencia(evidencia: Any) -> EvidenciaRecuperada:
    """Evidência do Research no modelo da verificação (só os campos usados aqui)."""
    trecho = evidencia.trecho
    documento = evidencia.documento
    fonte = documento.fonte
    return EvidenciaRecuperada(
        trecho=TrechoEvidencia(
            id=trecho.id,
            documento_id=trecho.documento_id,
            texto=trecho.texto,
            secao=trecho.secao,
        ),
        documento=DocumentoEvidencia(
            id=documento.id,
            fonte=FonteEvidencia(
                titulo=fonte.titulo,
                instituicao=fonte.instituicao,
                ano=fonte.ano,
                url=fonte.url,
            ),
        ),
        score=evidencia.score,
    )


class PesquisaDeEvidencias:
    """Recebe o `executar` do caso de uso do Research e devolve evidências da verificação."""

    def __init__(self, executar: Callable[[str, int], Sequence[Any]]):
        self._executar = executar

    def __call__(self, pergunta: str, limite: int) -> list[EvidenciaRecuperada]:
        return [traduzir_evidencia(e) for e in self._executar(pergunta, limite)]
