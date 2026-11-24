"""Communication Agent: transforma a análise validada no veredito para a pessoa (spec 72).

O LLM só redige a mensagem, no tamanho do perfil de leitura. A classificação, as fontes e a
aprovação vêm do código (RN01, RN10). Sem análise aprovada, o veredito é um texto fixo, sem
chamar o LLM (RN11). Saída do LLM fora do esquema não derruba o veredito: a mensagem passa a
ser a justificativa da análise.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from economia.verificacao.aplicacao.analisar_alegacao import descrever_evidencia
from economia.verificacao.aplicacao.portas import ModeloDeLinguagem
from economia.verificacao.dominio.analise import (
    Alegacao,
    AnaliseDaAlegacao,
    ResultadoDaValidacao,
    evidencias_citadas,
)
from economia.verificacao.dominio.modelos import EvidenciaRecuperada
from economia.verificacao.dominio.veredito import (
    MAXIMO_DE_FRASES_NO_PERFIL_RAPIDO,
    PerfilDeLeitura,
    Veredito,
    fonte_principal,
    fontes_citadas,
    limitar_frases,
    remover_marcadores_de_citacao,
    veredito_nao_conclusivo,
)

INSTRUCAO_DO_PERFIL = {
    PerfilDeLeitura.CONSUMIDOR_GERAL: (
        "consumidor_geral: explicação completa, em linguagem simples, citando as fontes "
        "pelo título."
    ),
    PerfilDeLeitura.CONSUMIDOR_RAPIDO: (
        f"consumidor_rapido: no máximo {MAXIMO_DE_FRASES_NO_PERFIL_RAPIDO} frases curtas."
    ),
}


class SaidaDaComunicacao(BaseModel):
    """Saída pedida ao LLM (prompt `verificacao/comunicacao`)."""

    mensagem: str


def montar_mensagem(
    alegacao: Alegacao,
    analise: AnaliseDaAlegacao,
    evidencias: Sequence[EvidenciaRecuperada],
    perfil: PerfilDeLeitura,
) -> str:
    """Perfil, alegação, classificação, justificativa e as evidências citadas, numeradas.

    O score não vai ao LLM: quem escolhe as fontes é o código.
    """
    citadas = evidencias_citadas(analise, evidencias)
    blocos = [descrever_evidencia(n, e) for n, e in enumerate(citadas, start=1)]
    return (
        f"Perfil de leitura: {INSTRUCAO_DO_PERFIL[perfil]}\n\n"
        f"Alegação: {alegacao.texto}\n\n"
        f"Classificação: {analise.classificacao.value}\n\n"
        f"Justificativa da análise: {analise.justificativa}\n\n"
        "Evidências citadas:\n\n"
        + ("\n\n".join(blocos) if blocos else "(nenhuma evidência citada)")
    )


class ComunicarVeredito:
    def __init__(self, llm: ModeloDeLinguagem, prompt_do_sistema: str):
        self._llm = llm
        self._prompt = prompt_do_sistema

    def executar(
        self,
        alegacao: Alegacao,
        analise: AnaliseDaAlegacao | None,
        validacao: ResultadoDaValidacao,
        evidencias: Sequence[EvidenciaRecuperada],
        perfil: PerfilDeLeitura,
    ) -> Veredito:
        """Veredito no perfil de leitura pedido."""
        if analise is None or not validacao.aprovado:
            return veredito_nao_conclusivo(analise)

        mensagem = self._redigir(alegacao, analise, evidencias, perfil)
        if perfil is PerfilDeLeitura.CONSUMIDOR_RAPIDO:
            mensagem = limitar_frases(mensagem, MAXIMO_DE_FRASES_NO_PERFIL_RAPIDO)
            principal = fonte_principal(analise, evidencias)
            fontes = (principal,) if principal else ()
        else:
            fontes = fontes_citadas(analise, evidencias)

        return Veredito(
            classificacao=analise.classificacao,
            mensagem=mensagem,
            fontes=fontes,
            aprovado_pela_validacao=True,
        )

    def _redigir(
        self,
        alegacao: Alegacao,
        analise: AnaliseDaAlegacao,
        evidencias: Sequence[EvidenciaRecuperada],
        perfil: PerfilDeLeitura,
    ) -> str:
        """Mensagem do LLM, ou a justificativa sem os marcadores [n] se a saída for inválida."""
        try:
            saida = SaidaDaComunicacao.model_validate(
                self._llm.gerar_json(
                    self._prompt,
                    montar_mensagem(alegacao, analise, evidencias, perfil),
                    SaidaDaComunicacao.model_json_schema(),
                )
            )
        except (ValidationError, ValueError):
            saida = None
        if saida is not None and saida.mensagem.strip():
            return saida.mensagem.strip()
        # a validação aprovada garante justificativa não vazia; sem os marcadores, ela
        # ainda pode sobrar vazia (ex.: só "[1]"), e então vai como veio
        return (
            remover_marcadores_de_citacao(analise.justificativa)
            or analise.justificativa.strip()
        )
