"""Caso de uso da avaliação: responder só com o LLM, sem a base de conhecimento (LLM puro).

Serve de linha de base para medir quanto o RAG melhora as respostas. Mesma persona, mesma
regra de preço (RN04, aplicada pelo código antes do LLM) e saída estruturada, como no RAG v2.

Não é exposto à pessoa usuária: a resposta não vem da base e não tem fonte, então não atende
a RN10. Por isso o tipo é `RespostaSemBase`, e não `RespostaComFontes`.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from economia.receitas.aplicacao.portas import ModeloDeLinguagem
from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO,
    NAO_ENCONTREI,
    e_pergunta_de_preco,
)
from economia.receitas.dominio.modelos import TrechoRecuperado


@dataclass(frozen=True)
class RespostaSemBase:
    """Resposta do LLM puro. Os campos de trechos ficam vazios: não houve busca."""

    texto: str
    encontrou: bool
    trechos: tuple[TrechoRecuperado, ...] = ()
    recuperados: tuple[TrechoRecuperado, ...] = ()


class RespostaDoLLMSemBase(BaseModel):
    """Saída estruturada do LLM no modo puro."""

    encontrou: bool
    resposta: str = ""


class ResponderSemBase:
    def __init__(self, llm: ModeloDeLinguagem, prompt_do_sistema: str):
        self._llm = llm
        self._prompt = prompt_do_sistema

    def responder(self, pergunta: str) -> RespostaSemBase:
        if e_pergunta_de_preco(pergunta):
            return RespostaSemBase(texto=AVISO_DE_PRECO, encontrou=False)
        try:
            saida = RespostaDoLLMSemBase.model_validate(
                self._llm.gerar_json(
                    self._prompt,
                    f"Pergunta: {pergunta}",
                    RespostaDoLLMSemBase.model_json_schema(),
                )
            )
        except (ValidationError, ValueError):
            return RespostaSemBase(texto=NAO_ENCONTREI, encontrou=False)
        if not saida.encontrou or not saida.resposta.strip():
            return RespostaSemBase(texto=NAO_ENCONTREI, encontrou=False)
        return RespostaSemBase(texto=saida.resposta.strip(), encontrou=True)
