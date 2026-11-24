"""Análise e validação de uma alegação (spec 79).

A classificação mede o quanto a base de evidências já cobre a alegação, não se ela é
verdadeira. A confiança e todas as conferências são calculadas aqui, pelo código (RN01).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from economia.verificacao.dominio.modelos import EvidenciaRecuperada


@dataclass(frozen=True)
class Alegacao:
    """Afirmação sobre alimentação que chega para ser verificada."""

    texto: str

    def __post_init__(self) -> None:
        if not self.texto.strip():
            raise ValueError("A alegação não pode ser vazia.")


class ClassificacaoDaAlegacao(StrEnum):
    """O quanto a base cobre a alegação."""

    RECICLADA = "reciclada"  # a base já tem evidência que cobre a alegação
    PARCIAL = "parcial"  # a base cobre só uma parte
    NOVA = "nova"  # a base não cobre


class DestinoDoRetorno(StrEnum):
    """Agente para o qual o trabalho volta quando a validação reprova."""

    RESEARCH = "research"  # a evidência é insuficiente
    ANALYSIS = "analysis"  # a análise está errada


@dataclass(frozen=True)
class AnaliseDaAlegacao:
    """Classificação, justificativa e as evidências citadas, pelos ids dos trechos.

    `citacoes_invalidas` guarda os números citados pelo LLM que não estão entre as evidências,
    para o Validation reprovar a análise. A confiança é o maior score entre as citadas.
    """

    classificacao: ClassificacaoDaAlegacao
    justificativa: str
    citacoes: tuple[str, ...] = ()
    citacoes_invalidas: tuple[int, ...] = ()
    confianca: float = 0.0

    def __post_init__(self) -> None:
        if not -1.0 <= self.confianca <= 1.0:
            raise ValueError("A confiança deve estar entre -1 e 1.")


@dataclass(frozen=True)
class ResultadoDaValidacao:
    """Decisão do Validation: aprovado, ou os motivos e o agente que refaz o trabalho."""

    aprovado: bool
    motivos: tuple[str, ...] = ()
    retornar_para: DestinoDoRetorno | None = None

    def __post_init__(self) -> None:
        if self.aprovado and (self.motivos or self.retornar_para is not None):
            raise ValueError("Uma validação aprovada não tem motivos nem retorno.")
        if not self.aprovado and (not self.motivos or self.retornar_para is None):
            raise ValueError(
                "Uma validação reprovada precisa dos motivos e do retorno."
            )


@dataclass(frozen=True)
class Reprovacao:
    """Uma conferência que falhou: o motivo e para onde o trabalho volta."""

    motivo: str
    destino: DestinoDoRetorno


def montar_analise(
    classificacao: ClassificacaoDaAlegacao,
    justificativa: str,
    numeros_citados: Sequence[int],
    evidencias: Sequence[EvidenciaRecuperada],
) -> AnaliseDaAlegacao:
    """Converte os números citados (a partir de 1) nos ids dos trechos e calcula a confiança.

    Números repetidos contam uma vez. Os que estão fora da lista ficam como citações inválidas.
    """
    validos: list[int] = []
    invalidos: list[int] = []
    for numero in numeros_citados:
        destino = validos if 1 <= numero <= len(evidencias) else invalidos
        if numero not in destino:
            destino.append(numero)
    citadas = [evidencias[n - 1] for n in validos]
    return AnaliseDaAlegacao(
        classificacao=classificacao,
        justificativa=justificativa.strip(),
        citacoes=tuple(e.trecho.id for e in citadas),
        citacoes_invalidas=tuple(invalidos),
        confianca=max((e.score for e in citadas), default=0.0),
    )


def evidencias_citadas(
    analise: AnaliseDaAlegacao, evidencias: Sequence[EvidenciaRecuperada]
) -> list[EvidenciaRecuperada]:
    """Evidências citadas pela análise, na ordem das citações."""
    por_id = {e.trecho.id: e for e in evidencias}
    return [por_id[i] for i in analise.citacoes if i in por_id]


def conferir_analise(
    analise: AnaliseDaAlegacao | None,
    evidencias: Sequence[EvidenciaRecuperada],
    limiar: float,
) -> list[Reprovacao]:
    """Conferências determinísticas do Validation, na ordem da spec. Lista vazia: passou."""
    if analise is None:
        return [
            Reprovacao(
                "O Analysis não devolveu uma análise válida (JSON fora do esquema).",
                DestinoDoRetorno.ANALYSIS,
            )
        ]

    reprovacoes: list[Reprovacao] = []
    if not analise.justificativa.strip():
        reprovacoes.append(
            Reprovacao("A justificativa está vazia.", DestinoDoRetorno.ANALYSIS)
        )
    for numero in analise.citacoes_invalidas:
        reprovacoes.append(
            Reprovacao(
                f"A citação {numero} não está entre as {len(evidencias)} evidências "
                "recuperadas.",
                DestinoDoRetorno.ANALYSIS,
            )
        )

    citadas = evidencias_citadas(analise, evidencias)
    if analise.classificacao is ClassificacaoDaAlegacao.NOVA:
        fortes = {e.trecho.id for e in evidencias if e.score >= limiar}
        if fortes and not fortes.intersection(analise.citacoes):
            reprovacoes.append(
                Reprovacao(
                    f"A análise diz que a alegação é nova, mas não cita nenhuma das "
                    f"{len(fortes)} evidências com score de {limiar:.3f} ou mais: precisa "
                    "mostrar essas evidências e explicar por que não cobrem a alegação.",
                    DestinoDoRetorno.ANALYSIS,
                )
            )
    elif not citadas:
        reprovacoes.append(
            Reprovacao(
                f"Uma alegação {analise.classificacao} precisa citar ao menos uma "
                "evidência recuperada.",
                DestinoDoRetorno.ANALYSIS,
            )
        )
    elif analise.confianca < limiar:
        reprovacoes.append(
            Reprovacao(
                f"A confiança {analise.confianca:.3f} está abaixo do limiar mínimo de "
                f"{limiar:.3f}: a evidência é insuficiente.",
                DestinoDoRetorno.RESEARCH,
            )
        )
    return reprovacoes


def decidir(reprovacoes: Sequence[Reprovacao]) -> ResultadoDaValidacao:
    """Aprova sem reprovações. Com motivos para os dois destinos, volta para o Research."""
    if not reprovacoes:
        return ResultadoDaValidacao(aprovado=True)
    destinos = {r.destino for r in reprovacoes}
    destino = (
        DestinoDoRetorno.RESEARCH
        if DestinoDoRetorno.RESEARCH in destinos
        else DestinoDoRetorno.ANALYSIS
    )
    return ResultadoDaValidacao(
        aprovado=False,
        motivos=tuple(r.motivo for r in reprovacoes),
        retornar_para=destino,
    )
