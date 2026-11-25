"""Estado e roteamento do orquestrador da verificação (spec 82, regras 1 a 5).

Quem decide o próximo nó é o código, a partir do `ResultadoDaValidacao` (RN01). As funções
daqui são puras e não conhecem o LangGraph: o laço simples e o grafo usam as mesmas.
"""

from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any

from economia.verificacao.dominio.analise import (
    Alegacao,
    AnaliseDaAlegacao,
    DestinoDoRetorno,
    ResultadoDaValidacao,
)
from economia.verificacao.dominio.evidencias import EvidenciaRecuperada
from economia.verificacao.dominio.veredito import PerfilDeLeitura, Veredito


class No(StrEnum):
    """Nós do fluxo da verificação. `FIM` encerra a verificação."""

    RESEARCH = "research"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    COMMUNICATION = "communication"
    FIM = "fim"


@dataclass(frozen=True)
class ParametrosDaOrquestracao:
    """Limite da primeira busca, teto da busca nos retornos e máximo de retornos (regra 5)."""

    limite_inicial: int = 5
    limite_maximo: int = 10
    maximo_de_retornos: int = 2

    def __post_init__(self) -> None:
        if self.limite_inicial < 1:
            raise ValueError("O limite inicial precisa ser de ao menos 1 trecho.")
        if self.limite_maximo < self.limite_inicial:
            raise ValueError("O teto da busca não pode ser menor que o limite inicial.")
        if self.maximo_de_retornos < 0:
            raise ValueError("O máximo de retornos não pode ser negativo.")


@dataclass(frozen=True)
class EtapaDaVerificacao:
    """Um nó executado: o agente, a entrada, a saída e os segundos (regra 7)."""

    agente: No
    entrada: dict[str, Any]
    saida: dict[str, Any]
    segundos: float


@dataclass(frozen=True)
class EstadoDaVerificacao:
    """O que os agentes leem e escrevem durante uma verificação (arquitetura, seção 4).

    `motivos` são os da reprovação que o Analysis recebe num retorno ao Analysis.
    """

    alegacao: Alegacao
    perfil: PerfilDeLeitura
    limite: int
    evidencias: tuple[EvidenciaRecuperada, ...] = ()
    analise: AnaliseDaAlegacao | None = None
    validacao: ResultadoDaValidacao | None = None
    motivos: tuple[str, ...] = ()
    retornos: int = 0
    historico: tuple[EtapaDaVerificacao, ...] = field(default=())
    veredito: Veredito | None = None

    @property
    def ultimo_no(self) -> No | None:
        return self.historico[-1].agente if self.historico else None


def estado_inicial(
    alegacao: Alegacao, perfil: PerfilDeLeitura, parametros: ParametrosDaOrquestracao
) -> EstadoDaVerificacao:
    return EstadoDaVerificacao(
        alegacao=alegacao, perfil=perfil, limite=parametros.limite_inicial
    )


def rotear_validacao(
    validacao: ResultadoDaValidacao, retornos: int, parametros: ParametrosDaOrquestracao
) -> No:
    """Destino depois do Validation (regras 1 e 4).

    Aprovado, ou reprovado com os retornos esgotados, vai para o Communication. Reprovado,
    volta para o agente que o Validation indicou.
    """
    if validacao.aprovado or retornos >= parametros.maximo_de_retornos:
        return No.COMMUNICATION
    if validacao.retornar_para is DestinoDoRetorno.RESEARCH:
        return No.RESEARCH
    return No.ANALYSIS


def proximo_no(estado: EstadoDaVerificacao, parametros: ParametrosDaOrquestracao) -> No:
    """Próximo nó a partir do último executado. Só depois do Validation há escolha."""
    ultimo = estado.ultimo_no
    if ultimo is None:
        return No.RESEARCH
    if ultimo is No.RESEARCH:
        return No.ANALYSIS
    if ultimo is No.ANALYSIS:
        return No.VALIDATION
    if ultimo is No.VALIDATION:
        if estado.validacao is None:
            raise ValueError("O Validation rodou, mas o estado não tem a validação.")
        return rotear_validacao(estado.validacao, estado.retornos, parametros)
    return No.FIM


def esta_em_retorno(estado: EstadoDaVerificacao) -> bool:
    """O estado traz uma validação reprovada que ainda não virou retorno."""
    return estado.validacao is not None and not estado.validacao.aprovado


def preparar_retorno(
    estado: EstadoDaVerificacao, parametros: ParametrosDaOrquestracao
) -> EstadoDaVerificacao:
    """Aplica o retorno pedido pela validação reprovada (regras 2 e 3) e conta o retorno.

    Ao Research: o limite dobra até o teto e a análise recomeça sem os motivos, que falam do
    score e que o Analysis não corrige. Ao Analysis: as evidências se mantêm e os motivos vão
    para a próxima análise. A validação é limpa, para o retorno não ser aplicado duas vezes.
    """
    validacao = estado.validacao
    if validacao is None or validacao.aprovado:
        raise ValueError("Só uma validação reprovada leva a um retorno.")
    if validacao.retornar_para is DestinoDoRetorno.RESEARCH:
        return replace(
            estado,
            limite=min(estado.limite * 2, parametros.limite_maximo),
            motivos=(),
            validacao=None,
            retornos=estado.retornos + 1,
        )
    return replace(
        estado,
        motivos=validacao.motivos,
        validacao=None,
        retornos=estado.retornos + 1,
    )
