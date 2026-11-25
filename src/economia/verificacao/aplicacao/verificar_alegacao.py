"""Caso de uso da verificação de uma alegação: Research → Analysis → Validation →
Communication, com os retornos pedidos pelo Validation (spec 82).

Cada agente é um nó que recebe o estado e devolve o estado seguinte, com a etapa no
histórico. Quem executa os nós é o motor: o laço simples daqui ou o grafo LangGraph da
infraestrutura, que usa os mesmos nós e o mesmo `proximo_no`. A aplicação não importa o
LangGraph.

Falha do LLM ou do Qdrant (tempo esgotado, serviço fora do ar) sobe para quem chamou
(regra 8). Saída inválida do LLM não é falha: cada agente já trata a sua.
"""

import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, replace
from typing import Any, Protocol

from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
from economia.verificacao.aplicacao.comunicar_veredito import ComunicarVeredito
from economia.verificacao.aplicacao.orquestracao import (
    EstadoDaVerificacao,
    EtapaDaVerificacao,
    No,
    ParametrosDaOrquestracao,
    esta_em_retorno,
    estado_inicial,
    preparar_retorno,
    proximo_no,
)
from economia.verificacao.aplicacao.validar_analise import ValidarAnalise
from economia.verificacao.dominio.analise import Alegacao, AnaliseDaAlegacao
from economia.verificacao.dominio.evidencias import EvidenciaRecuperada
from economia.verificacao.dominio.veredito import PerfilDeLeitura, Veredito

Pesquisar = Callable[[str, int], Sequence[EvidenciaRecuperada]]
NoDaVerificacao = Callable[[EstadoDaVerificacao], EstadoDaVerificacao]
Registrar = Callable[[dict], None]


class ObservadorDaVerificacao(Protocol):
    """Registra a verificação e cada etapa (um span por agente). Recebe a saída no fim."""

    def verificacao(self, entrada: dict) -> AbstractContextManager[Registrar]: ...

    def etapa(self, nome: str, entrada: dict) -> AbstractContextManager[Registrar]: ...


class SemObservacao:
    """Observador que não registra nada."""

    @contextmanager
    def verificacao(self, entrada: dict) -> Iterator[Registrar]:
        yield lambda saida: None

    @contextmanager
    def etapa(self, nome: str, entrada: dict) -> Iterator[Registrar]:
        yield lambda saida: None


class MotorDaVerificacao(Protocol):
    """Executa os nós a partir do estado inicial, seguindo `proximo` até o `FIM`."""

    def rodar(
        self,
        estado: EstadoDaVerificacao,
        nos: Mapping[No, NoDaVerificacao],
        proximo: Callable[[EstadoDaVerificacao], No],
    ) -> EstadoDaVerificacao: ...


class LacoSimples:
    """Motor sem dependências: um laço sobre `proximo` (spec 82, etapa 2 do plano)."""

    def rodar(
        self,
        estado: EstadoDaVerificacao,
        nos: Mapping[No, NoDaVerificacao],
        proximo: Callable[[EstadoDaVerificacao], No],
    ) -> EstadoDaVerificacao:
        no = proximo(estado)
        while no is not No.FIM:
            estado = nos[no](estado)
            no = proximo(estado)
        return estado


@dataclass(frozen=True)
class ResultadoDaVerificacao:
    """Veredito, histórico das etapas e número de retornos. `estado` é o estado final."""

    veredito: Veredito
    historico: tuple[EtapaDaVerificacao, ...]
    retornos: int
    estado: EstadoDaVerificacao


def descrever_evidencias(evidencias: Sequence[EvidenciaRecuperada]) -> list[dict]:
    """Ids dos trechos e scores, sem o texto, para o histórico não crescer a cada retorno."""
    return [{"trecho": e.trecho.id, "score": e.score} for e in evidencias]


def descrever_analise(analise: AnaliseDaAlegacao | None) -> dict[str, Any]:
    if analise is None:
        return {
            "classificacao": None,
            "justificativa": None,
            "citacoes": [],
            "confianca": None,
        }
    return {
        "classificacao": str(analise.classificacao),
        "justificativa": analise.justificativa,
        "citacoes": list(analise.citacoes),
        "citacoes_invalidas": list(analise.citacoes_invalidas),
        "confianca": analise.confianca,
    }


class VerificarAlegacao:
    def __init__(
        self,
        pesquisar: Pesquisar,
        analisar: AnalisarAlegacao,
        validar: ValidarAnalise,
        comunicar: ComunicarVeredito,
        parametros: ParametrosDaOrquestracao | None = None,
        motor: MotorDaVerificacao | None = None,
        observador: ObservadorDaVerificacao | None = None,
        relogio: Callable[[], float] = time.perf_counter,
    ):
        self._pesquisar = pesquisar
        self._analisar = analisar
        self._validar = validar
        self._comunicar = comunicar
        self.parametros = parametros or ParametrosDaOrquestracao()
        self._motor = motor or LacoSimples()
        self._observador = observador or SemObservacao()
        self._relogio = relogio

    def executar(
        self, alegacao: Alegacao | str, perfil: PerfilDeLeitura | str
    ) -> ResultadoDaVerificacao:
        alegacao = alegacao if isinstance(alegacao, Alegacao) else Alegacao(alegacao)
        perfil = PerfilDeLeitura(perfil)
        with self._observador.verificacao(
            {"alegacao": alegacao.texto, "perfil": str(perfil)}
        ) as registrar:
            final = self._motor.rodar(
                estado_inicial(alegacao, perfil, self.parametros),
                self.nos,
                self.proximo,
            )
            if final.veredito is None:
                raise RuntimeError("A verificação terminou sem o veredito.")
            registrar(
                {
                    "classificacao": (
                        str(final.veredito.classificacao)
                        if final.veredito.classificacao
                        else None
                    ),
                    "aprovado_pela_validacao": final.veredito.aprovado_pela_validacao,
                    "retornos": final.retornos,
                }
            )
        return ResultadoDaVerificacao(
            veredito=final.veredito,
            historico=final.historico,
            retornos=final.retornos,
            estado=final,
        )

    @property
    def nos(self) -> dict[No, NoDaVerificacao]:
        return {
            No.RESEARCH: self.research,
            No.ANALYSIS: self.analysis,
            No.VALIDATION: self.validation,
            No.COMMUNICATION: self.communication,
        }

    def proximo(self, estado: EstadoDaVerificacao) -> No:
        return proximo_no(estado, self.parametros)

    def _etapa(
        self,
        estado: EstadoDaVerificacao,
        agente: No,
        entrada: dict,
        rodar: Callable[[], tuple[dict, dict[str, Any]]],
    ) -> EstadoDaVerificacao:
        """Roda o agente dentro do span e acrescenta a etapa ao histórico.

        `rodar` devolve a saída da etapa e os campos do estado que o agente escreveu.
        """
        inicio = self._relogio()
        with self._observador.etapa(
            str(agente), {"alegacao": estado.alegacao.texto, **entrada}
        ) as registrar:
            saida, campos = rodar()
            registrar(saida)
        etapa = EtapaDaVerificacao(
            agente, entrada, saida, round(self._relogio() - inicio, 3)
        )
        return replace(estado, historico=(*estado.historico, etapa), **campos)

    def _no_retorno(self, estado: EstadoDaVerificacao) -> EstadoDaVerificacao:
        return (
            preparar_retorno(estado, self.parametros)
            if esta_em_retorno(estado)
            else estado
        )

    def research(self, estado: EstadoDaVerificacao) -> EstadoDaVerificacao:
        estado = self._no_retorno(estado)

        def rodar():
            evidencias = tuple(self._pesquisar(estado.alegacao.texto, estado.limite))
            return (
                {"evidencias": descrever_evidencias(evidencias)},
                {"evidencias": evidencias, "analise": None},
            )

        return self._etapa(estado, No.RESEARCH, {"limite": estado.limite}, rodar)

    def analysis(self, estado: EstadoDaVerificacao) -> EstadoDaVerificacao:
        estado = self._no_retorno(estado)

        def rodar():
            analise = self._analisar.executar(
                estado.alegacao, estado.evidencias, estado.motivos
            )
            return descrever_analise(analise), {"analise": analise}

        return self._etapa(
            estado, No.ANALYSIS, {"motivos": list(estado.motivos)}, rodar
        )

    def validation(self, estado: EstadoDaVerificacao) -> EstadoDaVerificacao:
        def rodar():
            validacao = self._validar.executar(
                estado.alegacao, estado.evidencias, estado.analise
            )
            saida = {
                "aprovado": validacao.aprovado,
                "motivos": list(validacao.motivos),
                "retornar_para": (
                    str(validacao.retornar_para) if validacao.retornar_para else None
                ),
            }
            return saida, {"validacao": validacao}

        return self._etapa(estado, No.VALIDATION, {}, rodar)

    def communication(self, estado: EstadoDaVerificacao) -> EstadoDaVerificacao:
        if estado.validacao is None:
            raise ValueError("O Communication precisa do resultado da validação.")
        validacao = estado.validacao

        def rodar():
            veredito = self._comunicar.executar(
                estado.alegacao,
                estado.analise,
                validacao,
                estado.evidencias,
                estado.perfil,
            )
            saida = {
                "classificacao": (
                    str(veredito.classificacao) if veredito.classificacao else None
                ),
                "aprovado_pela_validacao": veredito.aprovado_pela_validacao,
            }
            return saida, {"veredito": veredito}

        return self._etapa(
            estado, No.COMMUNICATION, {"perfil": str(estado.perfil)}, rodar
        )
