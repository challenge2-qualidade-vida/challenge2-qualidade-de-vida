"""Analysis Agent: classifica a alegação a partir das evidências, citando as fontes (spec 79).

O LLM devolve a classificação, a justificativa e os números das evidências citadas. O código
converte os números nos ids dos trechos e calcula a confiança (RN01). Saída fora do esquema
não vira análise.
"""

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ValidationError

from economia.pesquisa_evidencias.dominio.modelos import EvidenciaRecuperada
from economia.verificacao.aplicacao.portas import ModeloDeLinguagem
from economia.verificacao.dominio.analise import (
    Alegacao,
    AnaliseDaAlegacao,
    ClassificacaoDaAlegacao,
    montar_analise,
)


class SaidaDaAnalise(BaseModel):
    """Saída pedida ao LLM (prompt `verificacao/analise`)."""

    classificacao: Literal["reciclada", "parcial", "nova"]
    justificativa: str
    citacoes: list[int] = []


def descrever_evidencia(numero: int, evidencia: EvidenciaRecuperada) -> str:
    """Evidência numerada, com a fonte, para o LLM citar pelo número."""
    fonte = evidencia.documento.fonte
    cabecalho = f"[{numero}] {fonte.titulo} ({fonte.instituicao}"
    cabecalho += f", {fonte.ano})" if fonte.ano else ")"
    if evidencia.trecho.secao:
        cabecalho += f" — {evidencia.trecho.secao}"
    return f"{cabecalho}\n{evidencia.trecho.texto}"


def montar_mensagem(
    alegacao: Alegacao,
    evidencias: Sequence[EvidenciaRecuperada],
    motivos: Sequence[str] = (),
) -> str:
    """Alegação, evidências numeradas a partir de 1 e, num retorno, os motivos da reprovação.

    O score não vai ao LLM: a confiança é calculada pelo código.
    """
    blocos = [descrever_evidencia(n, e) for n, e in enumerate(evidencias, start=1)]
    mensagem = f"Alegação: {alegacao.texto}\n\nEvidências:\n\n" + (
        "\n\n".join(blocos) if blocos else "(nenhuma evidência recuperada)"
    )
    if motivos:
        lista = "\n".join(f"- {m}" for m in motivos)
        mensagem += f"\n\nA análise anterior foi reprovada pelos motivos abaixo. Corrija:\n{lista}"
    return mensagem


class AnalisarAlegacao:
    def __init__(self, llm: ModeloDeLinguagem, prompt_do_sistema: str):
        self._llm = llm
        self._prompt = prompt_do_sistema

    def executar(
        self,
        alegacao: Alegacao,
        evidencias: Sequence[EvidenciaRecuperada],
        motivos: Sequence[str] = (),
    ) -> AnaliseDaAlegacao | None:
        """Análise da alegação, ou `None` quando a saída do LLM não segue o esquema."""
        try:
            saida = SaidaDaAnalise.model_validate(
                self._llm.gerar_json(
                    self._prompt,
                    montar_mensagem(alegacao, evidencias, motivos),
                    SaidaDaAnalise.model_json_schema(),
                )
            )
        except (ValidationError, ValueError):
            return None
        return montar_analise(
            ClassificacaoDaAlegacao(saida.classificacao),
            saida.justificativa,
            saida.citacoes,
            evidencias,
        )
