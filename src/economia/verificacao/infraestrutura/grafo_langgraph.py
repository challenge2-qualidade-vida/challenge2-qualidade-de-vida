"""Motor da verificação com o LangGraph (spec 82, etapa 4 do plano).

Um nó por agente, todos chamando os nós do `VerificarAlegacao`. A aresta condicional depois
do Validation usa o `proximo`, o mesmo `proximo_no` do laço simples: o LangGraph só executa,
quem decide o caminho é o código (RN01). O estado do grafo guarda o `EstadoDaVerificacao`
inteiro numa chave só, e cada nó devolve o estado novo.
"""

from collections.abc import Callable, Mapping
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from economia.verificacao.aplicacao.orquestracao import EstadoDaVerificacao, No
from economia.verificacao.aplicacao.verificar_alegacao import NoDaVerificacao

# cada retorno roda até 3 nós (research, analysis, validation); a folga cobre o primeiro
# passe e o Communication
PASSOS_POR_RETORNO = 3
PASSOS_FIXOS = 5
MAXIMO_DE_RETORNOS_PREVISTO = 10


class EstadoDoGrafo(TypedDict):
    estado: EstadoDaVerificacao


def _no_do_grafo(no: NoDaVerificacao) -> Callable[[EstadoDoGrafo], EstadoDoGrafo]:
    def executar(estado: EstadoDoGrafo) -> EstadoDoGrafo:
        return {"estado": no(estado["estado"])}

    return executar


class GrafoLangGraph:
    """Monta o grafo a cada execução: os nós vêm do caso de uso que chama o motor."""

    def __init__(self, maximo_de_retornos: int = MAXIMO_DE_RETORNOS_PREVISTO):
        self._limite_de_passos = PASSOS_FIXOS + PASSOS_POR_RETORNO * maximo_de_retornos

    def compilar(
        self,
        nos: Mapping[No, NoDaVerificacao],
        proximo: Callable[[EstadoDaVerificacao], No],
    ):
        grafo = StateGraph(EstadoDoGrafo)
        for no, executar in nos.items():
            grafo.add_node(str(no), _no_do_grafo(executar))

        def rotear(estado: EstadoDoGrafo) -> str:
            return str(proximo(estado["estado"]))

        grafo.add_edge(START, str(No.RESEARCH))
        grafo.add_edge(str(No.RESEARCH), str(No.ANALYSIS))
        grafo.add_edge(str(No.ANALYSIS), str(No.VALIDATION))
        grafo.add_conditional_edges(
            str(No.VALIDATION),
            rotear,
            {
                str(No.RESEARCH): str(No.RESEARCH),
                str(No.ANALYSIS): str(No.ANALYSIS),
                str(No.COMMUNICATION): str(No.COMMUNICATION),
            },
        )
        grafo.add_edge(str(No.COMMUNICATION), END)
        return grafo.compile()

    def rodar(
        self,
        estado: EstadoDaVerificacao,
        nos: Mapping[No, NoDaVerificacao],
        proximo: Callable[[EstadoDaVerificacao], No],
    ) -> EstadoDaVerificacao:
        if proximo(estado) is not No.RESEARCH:
            raise ValueError("O grafo começa sempre pelo Research.")
        final = self.compilar(nos, proximo).invoke(
            {"estado": estado}, config={"recursion_limit": self._limite_de_passos}
        )
        return final["estado"]
