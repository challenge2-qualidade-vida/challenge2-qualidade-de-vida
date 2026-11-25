"""Dublês da análise e da validação: evidências fictícias e um LLM com respostas prontas."""

import json

import pytest

from economia.verificacao.dominio.evidencias import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)

FONTE = FonteEvidencia(
    titulo="Guia Alimentar para a População Brasileira",
    instituicao="Ministério da Saúde",
    ano=2014,
)
DOCUMENTO = DocumentoEvidencia(
    id="guia-alimentar", fonte=FONTE
)


def evidencia(
    numero: int, score: float, texto: str | None = None
) -> EvidenciaRecuperada:
    return EvidenciaRecuperada(
        trecho=TrechoEvidencia(
            id=f"guia-alimentar-{numero:04d}",
            documento_id=DOCUMENTO.id,
            texto=texto or f"Trecho {numero} sobre alimentação.",
            secao="Capítulo 2",
        ),
        documento=DOCUMENTO,
        score=score,
    )


def evidencias(*scores: float) -> list[EvidenciaRecuperada]:
    return [evidencia(n, s) for n, s in enumerate(scores, start=1)]


class LLMRoteirizado:
    """Devolve as respostas na ordem, uma por chamada, separadas por prompt do sistema.

    Uma resposta `str` simula uma saída que não é JSON: o `gerar_json` real levanta
    `ValueError` nesse caso. Depois da última resposta, repete a última.
    """

    def __init__(self, **respostas_por_prompt: list):
        self._respostas = {k: list(v) for k, v in respostas_por_prompt.items()}
        self.chamadas: list[tuple[str, str]] = []

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        self.chamadas.append((sistema, mensagem))
        fila = self._respostas[sistema]
        resposta = fila.pop(0) if len(fila) > 1 else fila[0]
        if isinstance(resposta, str):
            try:
                return json.loads(resposta)
            except json.JSONDecodeError as erro:
                raise ValueError("saída do LLM não é JSON") from erro
        return resposta

    def chamadas_de(self, sistema: str) -> list[str]:
        return [m for s, m in self.chamadas if s == sistema]


@pytest.fixture
def fazer_evidencias():
    """Evidências fictícias com os scores dados, numeradas a partir de 1."""
    return evidencias


@pytest.fixture
def llm_roteirizado():
    return LLMRoteirizado
