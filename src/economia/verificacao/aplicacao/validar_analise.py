"""Validation Agent: confere a análise antes do veredito (spec 79, papel da Mia).

Primeiro as conferências determinísticas, no código (RN01). Se todas passam, o LLM diz se a
justificativa contradiz as evidências citadas. Quem decide para onde o trabalho volta é o
código, não o LLM.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from economia.verificacao.aplicacao.analisar_alegacao import descrever_evidencia
from economia.verificacao.aplicacao.portas import ModeloDeLinguagem
from economia.verificacao.dominio.analise import (
    Alegacao,
    AnaliseDaAlegacao,
    DestinoDoRetorno,
    Reprovacao,
    ResultadoDaValidacao,
    conferir_analise,
    decidir,
    evidencias_citadas,
)
from economia.verificacao.dominio.modelos import EvidenciaRecuperada

SAIDA_INVALIDA = (
    "A conferência de contradição não devolveu uma resposta válida; "
    "a análise precisa ser refeita."
)


class SaidaDaContradicao(BaseModel):
    """Saída pedida ao LLM (prompt `verificacao/validacao`)."""

    contradiz: bool
    explicacao: str = ""


def montar_mensagem_de_contradicao(
    alegacao: Alegacao,
    analise: AnaliseDaAlegacao,
    citadas: Sequence[EvidenciaRecuperada],
) -> str:
    """Alegação, análise e só as evidências citadas, numeradas como na análise."""
    blocos = [descrever_evidencia(n, e) for n, e in enumerate(citadas, start=1)]
    return (
        f"Alegação: {alegacao.texto}\n\n"
        f"Classificação: {analise.classificacao}\n"
        f"Justificativa: {analise.justificativa}\n\n"
        "Evidências citadas:\n\n"
        + ("\n\n".join(blocos) if blocos else "(nenhuma evidência citada)")
    )


class ValidarAnalise:
    def __init__(self, llm: ModeloDeLinguagem, prompt_do_sistema: str, limiar: float):
        self._llm = llm
        self._prompt = prompt_do_sistema
        self._limiar = limiar

    @property
    def limiar(self) -> float:
        return self._limiar

    def executar(
        self,
        alegacao: Alegacao,
        evidencias: Sequence[EvidenciaRecuperada],
        analise: AnaliseDaAlegacao | None,
    ) -> ResultadoDaValidacao:
        reprovacoes = conferir_analise(analise, evidencias, self._limiar)
        if reprovacoes or analise is None:
            return decidir(reprovacoes)
        contradicao = self._conferir_contradicao(alegacao, analise, evidencias)
        return decidir([contradicao] if contradicao else [])

    def _conferir_contradicao(
        self,
        alegacao: Alegacao,
        analise: AnaliseDaAlegacao,
        evidencias: Sequence[EvidenciaRecuperada],
    ) -> Reprovacao | None:
        mensagem = montar_mensagem_de_contradicao(
            alegacao, analise, evidencias_citadas(analise, evidencias)
        )
        try:
            saida = SaidaDaContradicao.model_validate(
                self._llm.gerar_json(
                    self._prompt, mensagem, SaidaDaContradicao.model_json_schema()
                )
            )
        except (ValidationError, ValueError):
            return Reprovacao(SAIDA_INVALIDA, DestinoDoRetorno.ANALYSIS)
        if not saida.contradiz:
            return None
        explicacao = saida.explicacao.strip()
        motivo = "A justificativa contradiz as evidências citadas"
        return Reprovacao(
            f"{motivo}: {explicacao}" if explicacao else f"{motivo}.",
            DestinoDoRetorno.ANALYSIS,
        )
