"""Testes da avaliação do fluxo Research → Analysis → Validation."""

import json
from contextlib import contextmanager

from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
from economia.verificacao.aplicacao.avaliacao import (
    CasoDeVerificacao,
    avaliar,
    avaliar_caso,
    carregar_casos,
    tabela_markdown,
)
from economia.verificacao.aplicacao.validar_analise import ValidarAnalise
from economia.verificacao.dominio.analise import ClassificacaoDaAlegacao

ANALISE = "analise"
VALIDACAO = "validacao"
SEM_CONTRADICAO = {"contradiz": False}
CASO = CasoDeVerificacao(
    "v01", "Ultraprocessados devem ser evitados", ClassificacaoDaAlegacao.RECICLADA
)


def _reciclada(*citacoes):
    return {
        "classificacao": "reciclada",
        "justificativa": "J",
        "citacoes": list(citacoes),
    }


class PesquisaFalsa:
    def __init__(self, *respostas):
        self._respostas = list(respostas)
        self.limites: list[int] = []

    def __call__(self, texto, limite):
        self.limites.append(limite)
        return (
            self._respostas.pop(0) if len(self._respostas) > 1 else self._respostas[0]
        )


def _relogio():
    tempos = iter(range(0, 1000, 2))
    return lambda: float(next(tempos))


def _agentes(llm):
    return AnalisarAlegacao(llm, ANALISE), ValidarAnalise(llm, VALIDACAO, 0.845)


def test_aprovado_direto(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO])

    r = avaliar_caso(
        CASO, PesquisaFalsa(fazer_evidencias(0.9)), *_agentes(llm), relogio=_relogio()
    )

    assert (r.obtida, r.acertou, r.aprovado, r.aprovado_direto, r.retornos) == (
        "reciclada",
        True,
        True,
        True,
        0,
    )
    assert r.citacoes == ("guia-alimentar-0001",)
    assert r.segundos == 2.0


def test_retorno_ao_analysis_repete_com_os_motivos(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(
        analise=[_reciclada(7), _reciclada(1)], validacao=[SEM_CONTRADICAO]
    )
    pesquisa = PesquisaFalsa(fazer_evidencias(0.9, 0.8))

    r = avaliar_caso(CASO, pesquisa, *_agentes(llm))

    assert (r.acertou, r.aprovado, r.aprovado_direto, r.destinos) == (
        True,
        True,
        False,
        ("analysis",),
    )
    assert "A citação 7 não está entre" in llm.chamadas_de(ANALISE)[1]
    assert pesquisa.limites == [5]


def test_retorno_ao_research_dobra_o_limite_ate_20(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO])
    pesquisa = PesquisaFalsa(fazer_evidencias(0.80))

    r = avaliar_caso(
        CASO,
        pesquisa,
        *_agentes(llm),
        limite=12,
        maximo_de_retornos=2,
        limite_maximo=20,
    )

    assert pesquisa.limites == [12, 20, 20]
    assert r.destinos == ("research", "research")
    assert not r.aprovado
    assert len(r.motivos) == 3


def test_research_com_evidencia_melhor_aprova(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO])
    pesquisa = PesquisaFalsa(fazer_evidencias(0.80), fazer_evidencias(0.88))

    r = avaliar_caso(CASO, pesquisa, *_agentes(llm))

    assert pesquisa.limites == [5, 10]
    assert (r.aprovado, r.destinos, r.confianca, r.maior_score) == (
        True,
        ("research",),
        0.88,
        0.88,
    )


def test_para_no_limite_de_retornos(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(analise=[_reciclada(7)], validacao=[SEM_CONTRADICAO])

    r = avaliar_caso(CASO, PesquisaFalsa(fazer_evidencias(0.9)), *_agentes(llm))

    assert (r.aprovado, r.retornos) == (False, 2)
    assert len(llm.chamadas_de(ANALISE)) == 3


def test_sem_analise_conta_como_erro(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(analise=["não é json"], validacao=[SEM_CONTRADICAO])

    r = avaliar_caso(CASO, PesquisaFalsa(fazer_evidencias(0.9)), *_agentes(llm))

    assert (r.obtida, r.acertou, r.confianca, r.justificativa) == (
        None,
        False,
        None,
        None,
    )


def test_observador_registra_o_caso_e_cada_etapa(fazer_evidencias, llm_roteirizado):
    registros = []

    class Observador:
        @contextmanager
        def caso(self, caso):
            yield lambda saida: registros.append(("caso", saida))

        @contextmanager
        def etapa(self, nome, entrada):
            yield lambda saida: registros.append((nome, saida))

    llm = llm_roteirizado(analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO])
    avaliar_caso(
        CASO,
        PesquisaFalsa(fazer_evidencias(0.9)),
        *_agentes(llm),
        observador=Observador(),
    )

    assert [nome for nome, _ in registros] == [
        "research",
        "analysis",
        "validation",
        "communication",
        "caso",
    ]
    assert registros[2][1]["aprovado"] is True


def test_resumo_e_tabela(fazer_evidencias, llm_roteirizado):
    casos = [
        CASO,
        CasoDeVerificacao("v02", "Alegação | com barra", ClassificacaoDaAlegacao.NOVA),
    ]
    llm = llm_roteirizado(analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO])
    progresso = []

    resumo = avaliar(
        casos,
        PesquisaFalsa(fazer_evidencias(0.9)),
        *_agentes(llm),
        ao_progredir=lambda n, total, r: progresso.append((n, total, r.id)),
        relogio=_relogio(),
    )

    assert progresso == [(1, 2, "v01"), (2, 2, "v02")]
    assert (
        resumo.casos,
        resumo.acuracia,
        resumo.aprovacao_direta,
        resumo.media_de_retornos,
    ) == (
        2,
        0.5,
        1.0,
        0.0,
    )
    tabela = tabela_markdown(resumo)
    assert (
        "| v02 | Alegação \\| com barra | nova | reciclada | não | sim | 0 | 0.900 | 2.0 |"
        in tabela
    )
    assert "| Acurácia da classificação | 50% |" in tabela


def test_carregar_casos(tmp_path):
    arquivo = tmp_path / "casos.json"
    arquivo.write_text(
        json.dumps(
            {
                "casos": [
                    {"id": "v01", "alegacao": "A", "classificacao_esperada": "parcial"}
                ]
            }
        ),
        encoding="utf-8",
    )

    assert carregar_casos(arquivo) == [
        CasoDeVerificacao("v01", "A", ClassificacaoDaAlegacao.PARCIAL)
    ]


def test_retorno_ao_research_analisa_de_novo_sem_os_motivos(
    fazer_evidencias, llm_roteirizado
):
    llm = llm_roteirizado(analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO])
    pesquisa = PesquisaFalsa(fazer_evidencias(0.80), fazer_evidencias(0.88))

    avaliar_caso(CASO, pesquisa, *_agentes(llm))

    assert "reprovada" not in llm.chamadas_de(ANALISE)[1]


def test_teto_da_busca_nos_retornos_e_configuravel(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO])
    pesquisa = PesquisaFalsa(fazer_evidencias(0.80))

    avaliar_caso(CASO, pesquisa, *_agentes(llm), limite_maximo=10)

    assert pesquisa.limites == [5, 10, 10]
