"""Avaliação do fluxo da verificação num conjunto de alegações (specs 79 e 82).

Cada caso roda pelo orquestrador (`VerificarAlegacao`): Research → Analysis → Validation →
Communication, com os retornos e o teto da busca do orquestrador. As métricas e o formato do
resultado são os da #79, mais a mensagem do veredito por caso. Sem o Communication, a
avaliação usa a justificativa da análise como mensagem, sem chamar o LLM.
"""

import json
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
from economia.verificacao.aplicacao.orquestracao import No, ParametrosDaOrquestracao
from economia.verificacao.aplicacao.validar_analise import ValidarAnalise
from economia.verificacao.aplicacao.verificar_alegacao import (
    MotorDaVerificacao,
    Pesquisar,
    VerificarAlegacao,
)
from economia.verificacao.dominio.analise import (
    Alegacao,
    AnaliseDaAlegacao,
    ClassificacaoDaAlegacao,
    ResultadoDaValidacao,
)
from economia.verificacao.dominio.evidencias import EvidenciaRecuperada
from economia.verificacao.dominio.veredito import (
    PerfilDeLeitura,
    Veredito,
    fontes_citadas,
    veredito_nao_conclusivo,
)

_PADRAO = ParametrosDaOrquestracao()
LIMITE_INICIAL = _PADRAO.limite_inicial
LIMITE_MAXIMO = _PADRAO.limite_maximo
MAXIMO_DE_RETORNOS = _PADRAO.maximo_de_retornos


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


class _EtapasDoCaso:
    """Observador do orquestrador dentro do trace do caso: o trace já foi aberto."""

    def __init__(self, observador: ObservadorDeEtapas):
        self._observador = observador

    @contextmanager
    def verificacao(self, entrada: dict) -> Iterator[Callable[[dict], None]]:
        yield lambda saida: None

    def etapa(self, nome: str, entrada: dict):
        return self._observador.etapa(nome, entrada)


class SemComunicacao:
    """Communication sem LLM: a mensagem é a justificativa da análise aprovada."""

    def executar(
        self,
        alegacao: Alegacao,
        analise: AnaliseDaAlegacao | None,
        validacao: ResultadoDaValidacao,
        evidencias: Sequence[EvidenciaRecuperada],
        perfil: PerfilDeLeitura,
    ) -> Veredito:
        if analise is None or not validacao.aprovado or not analise.justificativa:
            return veredito_nao_conclusivo(analise)
        return Veredito(
            classificacao=analise.classificacao,
            mensagem=analise.justificativa,
            fontes=fontes_citadas(analise, evidencias),
            aprovado_pela_validacao=True,
        )


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
    mensagem: str | None = None


@dataclass(frozen=True)
class ResumoDaVerificacao:
    casos: int
    acuracia: float
    aprovacao_direta: float
    aprovacao_final: float
    media_de_retornos: float
    latencia_media: float
    resultados: list[ResultadoDoCaso] = field(default_factory=list)


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
    comunicar=None,
    perfil: PerfilDeLeitura = PerfilDeLeitura.CONSUMIDOR_GERAL,
    motor: MotorDaVerificacao | None = None,
) -> ResultadoDoCaso:
    """Roda o caso pelo orquestrador e lê do histórico os retornos, destinos e motivos."""
    observador = observador or SemObservacao()
    parametros = ParametrosDaOrquestracao(
        limite_inicial=limite,
        limite_maximo=max(limite_maximo, limite),
        maximo_de_retornos=maximo_de_retornos,
    )
    orquestrador = VerificarAlegacao(
        pesquisar,
        analisar,
        validar,
        comunicar or SemComunicacao(),
        parametros=parametros,
        motor=motor,
        observador=_EtapasDoCaso(observador),
    )
    inicio = relogio()
    with observador.caso(caso) as registrar_caso:
        resultado = orquestrador.executar(caso.alegacao, perfil)
        segundos = round(relogio() - inicio, 3)
        final = resultado.estado
        analise = final.analise
        validacoes = [e.saida for e in resultado.historico if e.agente is No.VALIDATION]
        reprovadas = [v for v in validacoes if not v["aprovado"]]
        aprovado = bool(validacoes) and validacoes[-1]["aprovado"]
        obtida = str(analise.classificacao) if analise else None
        resultado_do_caso = ResultadoDoCaso(
            id=caso.id,
            alegacao=caso.alegacao,
            esperada=str(caso.classificacao_esperada),
            obtida=obtida,
            acertou=obtida == caso.classificacao_esperada,
            aprovado=aprovado,
            aprovado_direto=aprovado and resultado.retornos == 0,
            retornos=resultado.retornos,
            destinos=tuple(
                v["retornar_para"] for v in reprovadas[: resultado.retornos]
            ),
            motivos=tuple(tuple(v["motivos"]) for v in reprovadas),
            justificativa=analise.justificativa if analise else None,
            citacoes=analise.citacoes if analise else (),
            confianca=analise.confianca if analise else None,
            maior_score=max((e.score for e in final.evidencias), default=None),
            segundos=segundos,
            mensagem=resultado.veredito.mensagem,
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
    comunicar=None,
    motor: MotorDaVerificacao | None = None,
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
            comunicar=comunicar,
            motor=motor,
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
