"""Avaliação do fluxo Research → Analysis → Validation num conjunto de alegações (spec 79).

Um retorno ao Research busca de novo com o dobro do limite (máximo 20); um retorno ao
Analysis repete a análise com os motivos. O limite é de 2 retornos por caso. O laço daqui é
só da avaliação: no fluxo real, o laço e o limite ficam no orquestrador LangGraph.
"""

import json
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
from economia.verificacao.aplicacao.validar_analise import ValidarAnalise
from economia.verificacao.dominio.analise import (
    Alegacao,
    AnaliseDaAlegacao,
    ClassificacaoDaAlegacao,
    DestinoDoRetorno,
)
from economia.verificacao.dominio.evidencias import EvidenciaRecuperada

LIMITE_INICIAL = 5
LIMITE_MAXIMO = 20
MAXIMO_DE_RETORNOS = 2

Pesquisar = Callable[[str, int], Sequence[EvidenciaRecuperada]]


@dataclass(frozen=True)
class CasoDeVerificacao:
    id: str
    alegacao: str
    classificacao_esperada: ClassificacaoDaAlegacao


def carregar_casos(arquivo: Path) -> list[CasoDeVerificacao]:
    """Casos do conjunto de avaliação (`{"casos": [{id, alegacao, classificacao_esperada}]}`)."""
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    return [
        CasoDeVerificacao(
            id=c["id"],
            alegacao=c["alegacao"],
            classificacao_esperada=ClassificacaoDaAlegacao(c["classificacao_esperada"]),
        )
        for c in dados["casos"]
    ]


class ObservadorDeEtapas(Protocol):
    """Registra o caso e cada etapa (um span por agente). A etapa recebe a saída no fim."""

    def caso(
        self, caso: CasoDeVerificacao
    ) -> AbstractContextManager[Callable[[dict], None]]: ...

    def etapa(
        self, nome: str, entrada: dict
    ) -> AbstractContextManager[Callable[[dict], None]]: ...


class SemObservacao:
    """Observador que não registra nada."""

    @contextmanager
    def caso(self, caso: CasoDeVerificacao) -> Iterator[Callable[[dict], None]]:
        yield lambda saida: None

    @contextmanager
    def etapa(self, nome: str, entrada: dict) -> Iterator[Callable[[dict], None]]:
        yield lambda saida: None


@dataclass(frozen=True)
class ResultadoDoCaso:
    id: str
    alegacao: str
    esperada: str
    obtida: str | None
    acertou: bool
    aprovado: bool
    aprovado_direto: bool
    retornos: int
    destinos: tuple[str, ...]
    motivos: tuple[tuple[str, ...], ...]
    justificativa: str | None
    citacoes: tuple[str, ...]
    confianca: float | None
    maior_score: float | None
    segundos: float


@dataclass(frozen=True)
class ResumoDaVerificacao:
    casos: int
    acuracia: float
    aprovacao_direta: float
    aprovacao_final: float
    media_de_retornos: float
    latencia_media: float
    resultados: list[ResultadoDoCaso] = field(default_factory=list)


def _analise_em_dict(analise: AnaliseDaAlegacao | None) -> dict[str, Any] | None:
    if analise is None:
        return None
    return {
        "classificacao": str(analise.classificacao),
        "justificativa": analise.justificativa,
        "citacoes": list(analise.citacoes),
        "citacoes_invalidas": list(analise.citacoes_invalidas),
        "confianca": analise.confianca,
    }


def avaliar_caso(
    caso: CasoDeVerificacao,
    pesquisar: Pesquisar,
    analisar: AnalisarAlegacao,
    validar: ValidarAnalise,
    limite: int = LIMITE_INICIAL,
    maximo_de_retornos: int = MAXIMO_DE_RETORNOS,
    limite_maximo: int = LIMITE_MAXIMO,
    observador: ObservadorDeEtapas | None = None,
    relogio: Callable[[], float] = time.perf_counter,
) -> ResultadoDoCaso:
    observador = observador or SemObservacao()
    alegacao = Alegacao(caso.alegacao)
    inicio = relogio()
    destinos: list[DestinoDoRetorno] = []
    motivos_por_retorno: list[tuple[str, ...]] = []

    with observador.caso(caso) as registrar_caso:

        def buscar(limite_da_busca: int) -> list[EvidenciaRecuperada]:
            with observador.etapa(
                "research", {"alegacao": alegacao.texto, "limite": limite_da_busca}
            ) as registrar:
                achadas = list(pesquisar(alegacao.texto, limite_da_busca))
                registrar(
                    {
                        "evidencias": [
                            {"trecho": e.trecho.id, "score": e.score} for e in achadas
                        ]
                    }
                )
            return achadas

        evidencias = buscar(limite)
        motivos: tuple[str, ...] = ()
        while True:
            with observador.etapa(
                "analysis", {"alegacao": alegacao.texto, "motivos": list(motivos)}
            ) as registrar:
                analise = analisar.executar(alegacao, evidencias, motivos)
                registrar({"analise": _analise_em_dict(analise)})
            with observador.etapa(
                "validation", {"analise": _analise_em_dict(analise)}
            ) as registrar:
                resultado = validar.executar(alegacao, evidencias, analise)
                registrar(
                    {
                        "aprovado": resultado.aprovado,
                        "motivos": list(resultado.motivos),
                        "retornar_para": resultado.retornar_para,
                    }
                )
            if resultado.aprovado or len(destinos) >= maximo_de_retornos:
                break
            assert resultado.retornar_para is not None
            destinos.append(resultado.retornar_para)
            motivos_por_retorno.append(resultado.motivos)
            if resultado.retornar_para is DestinoDoRetorno.RESEARCH:
                # evidências novas, análise do zero: os motivos falam do score, que o
                # Analysis não corrige, e com eles o LLM comenta a reprovação em vez de analisar
                limite = min(limite * 2, limite_maximo)
                evidencias = buscar(limite)
                motivos = ()
            else:
                motivos = resultado.motivos

        obtida = str(analise.classificacao) if analise else None
        resultado_do_caso = ResultadoDoCaso(
            id=caso.id,
            alegacao=caso.alegacao,
            esperada=str(caso.classificacao_esperada),
            obtida=obtida,
            acertou=obtida == caso.classificacao_esperada,
            aprovado=resultado.aprovado,
            aprovado_direto=resultado.aprovado and not destinos,
            retornos=len(destinos),
            destinos=tuple(str(d) for d in destinos),
            motivos=tuple(motivos_por_retorno)
            + (() if resultado.aprovado else (resultado.motivos,)),
            justificativa=analise.justificativa if analise else None,
            citacoes=analise.citacoes if analise else (),
            confianca=analise.confianca if analise else None,
            maior_score=max((e.score for e in evidencias), default=None),
            segundos=round(relogio() - inicio, 3),
        )
        registrar_caso(
            {
                "obtida": obtida,
                "acertou": resultado_do_caso.acertou,
                "aprovado": resultado_do_caso.aprovado,
                "retornos": resultado_do_caso.retornos,
            }
        )
    return resultado_do_caso


def resumir(resultados: Sequence[ResultadoDoCaso]) -> ResumoDaVerificacao:
    total = len(resultados)

    def fracao(condicao: Callable[[ResultadoDoCaso], bool]) -> float:
        return (
            round(sum(1 for r in resultados if condicao(r)) / total, 3)
            if total
            else 0.0
        )

    def media(valor: Callable[[ResultadoDoCaso], float]) -> float:
        return round(sum(valor(r) for r in resultados) / total, 3) if total else 0.0

    return ResumoDaVerificacao(
        casos=total,
        acuracia=fracao(lambda r: r.acertou),
        aprovacao_direta=fracao(lambda r: r.aprovado_direto),
        aprovacao_final=fracao(lambda r: r.aprovado),
        media_de_retornos=media(lambda r: r.retornos),
        latencia_media=media(lambda r: r.segundos),
        resultados=list(resultados),
    )


def avaliar(
    casos: Sequence[CasoDeVerificacao],
    pesquisar: Pesquisar,
    analisar: AnalisarAlegacao,
    validar: ValidarAnalise,
    limite: int = LIMITE_INICIAL,
    maximo_de_retornos: int = MAXIMO_DE_RETORNOS,
    limite_maximo: int = LIMITE_MAXIMO,
    observador: ObservadorDeEtapas | None = None,
    ao_progredir: Callable[[int, int, ResultadoDoCaso], None] | None = None,
    relogio: Callable[[], float] = time.perf_counter,
) -> ResumoDaVerificacao:
    resultados = []
    for n, caso in enumerate(casos, start=1):
        resultado = avaliar_caso(
            caso,
            pesquisar,
            analisar,
            validar,
            limite,
            maximo_de_retornos,
            limite_maximo,
            observador,
            relogio,
        )
        resultados.append(resultado)
        if ao_progredir:
            ao_progredir(n, len(casos), resultado)
    return resumir(resultados)


def _celula(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", " ")


def tabela_markdown(resumo: ResumoDaVerificacao) -> str:
    """Tabela por caso e linha de totais, para a seção 9 da arquitetura."""
    linhas = [
        "| Caso | Alegação | Esperada | Obtida | Acertou | Aprovada | Retornos | Confiança | Latência (s) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in resumo.resultados:
        retornos = f"{r.retornos} ({', '.join(r.destinos)})" if r.retornos else "0"
        confianca = "—" if r.confianca is None else f"{r.confianca:.3f}"
        linhas.append(
            f"| {r.id} | {_celula(r.alegacao)} | {r.esperada} | {r.obtida or 'sem análise'} "
            f"| {'sim' if r.acertou else 'não'} | {'sim' if r.aprovado else 'não'} "
            f"| {retornos} | {confianca} | {r.segundos:.1f} |"
        )
    linhas += [
        "",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| Casos | {resumo.casos} |",
        f"| Acurácia da classificação | {resumo.acuracia:.0%} |",
        f"| Aprovação direta | {resumo.aprovacao_direta:.0%} |",
        f"| Aprovação ao fim dos retornos | {resumo.aprovacao_final:.0%} |",
        f"| Média de retornos | {resumo.media_de_retornos:.2f} |",
        f"| Latência média | {resumo.latencia_media:.1f} s |",
    ]
    return "\n".join(linhas)
