"""Testes do caso de uso VerificarAlegacao e dos dois motores (spec 82)."""

import ast
from contextlib import contextmanager
from pathlib import Path

import pytest

from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
from economia.verificacao.aplicacao.comunicar_veredito import ComunicarVeredito
from economia.verificacao.aplicacao.orquestracao import No, ParametrosDaOrquestracao
from economia.verificacao.aplicacao.validar_analise import ValidarAnalise
from economia.verificacao.aplicacao.verificar_alegacao import (
    LacoSimples,
    VerificarAlegacao,
)
from economia.verificacao.dominio.veredito import MENSAGEM_NAO_CONCLUSIVA
from economia.verificacao.infraestrutura.grafo_langgraph import GrafoLangGraph

ANALISE = "analise"
VALIDACAO = "validacao"
COMUNICACAO = "comunicacao"
SEM_CONTRADICAO = {"contradiz": False}
MENSAGEM = {"mensagem": "Sim. O Guia Alimentar recomenda evitar ultraprocessados."}
RAIZ = Path(__file__).parents[2] / "src" / "economia" / "verificacao"


def _reciclada(*citacoes):
    return {
        "classificacao": "reciclada",
        "justificativa": "J [1]",
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
    tempos = iter(range(1000))
    return lambda: float(next(tempos))


@pytest.fixture(params=["laco", "langgraph"])
def motor(request):
    return LacoSimples() if request.param == "laco" else GrafoLangGraph()


def _orquestrador(llm, pesquisa, motor, **opcoes):
    return VerificarAlegacao(
        pesquisa,
        AnalisarAlegacao(llm, ANALISE),
        ValidarAnalise(llm, VALIDACAO, 0.845),
        ComunicarVeredito(llm, COMUNICACAO),
        motor=motor,
        **opcoes,
    )


def test_aprovado_direto_com_os_agentes_de_verdade(
    fazer_evidencias, llm_roteirizado, motor
):
    llm = llm_roteirizado(
        analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )

    r = _orquestrador(llm, PesquisaFalsa(fazer_evidencias(0.9)), motor).executar(
        "Ultraprocessados devem ser evitados", "consumidor_geral"
    )

    assert [str(e.agente) for e in r.historico] == [
        "research",
        "analysis",
        "validation",
        "communication",
    ]
    assert r.retornos == 0
    assert r.veredito.aprovado_pela_validacao
    assert r.veredito.mensagem == MENSAGEM["mensagem"]
    assert [f.titulo for f in r.veredito.fontes] == [
        "Guia Alimentar para a População Brasileira"
    ]


def test_retorno_ao_research_guarda_os_motivos_e_o_destino_na_etapa(
    fazer_evidencias, llm_roteirizado, motor
):
    llm = llm_roteirizado(
        analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )
    pesquisa = PesquisaFalsa(fazer_evidencias(0.80), fazer_evidencias(0.88))

    r = _orquestrador(llm, pesquisa, motor).executar("Alegação", "consumidor_geral")

    validacoes = [e for e in r.historico if e.agente is No.VALIDATION]
    assert validacoes[0].saida["aprovado"] is False
    assert validacoes[0].saida["retornar_para"] == "research"
    assert "abaixo do limiar" in validacoes[0].saida["motivos"][0]
    assert validacoes[1].saida == {
        "aprovado": True,
        "motivos": [],
        "retornar_para": None,
    }
    assert pesquisa.limites == [5, 10]
    assert r.historico[3].entrada == {"limite": 10}
    assert r.veredito.aprovado_pela_validacao


def test_limite_de_retornos_da_veredito_nao_conclusivo_sem_chamar_o_communication(
    fazer_evidencias, llm_roteirizado, motor
):
    llm = llm_roteirizado(
        analise=[_reciclada(7)], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )

    r = _orquestrador(llm, PesquisaFalsa(fazer_evidencias(0.9)), motor).executar(
        "Alegação", "consumidor_geral"
    )

    assert r.retornos == 2
    assert r.veredito.mensagem == MENSAGEM_NAO_CONCLUSIVA
    assert not r.veredito.aprovado_pela_validacao
    assert llm.chamadas_de(COMUNICACAO) == []
    assert r.historico[-1].agente is No.COMMUNICATION


def test_saida_invalida_do_analysis_nao_e_falha(
    fazer_evidencias, llm_roteirizado, motor
):
    llm = llm_roteirizado(
        analise=["não é json"], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )

    r = _orquestrador(llm, PesquisaFalsa(fazer_evidencias(0.9)), motor).executar(
        "Alegação", "consumidor_rapido"
    )

    assert r.historico[1].saida["classificacao"] is None
    assert r.veredito.classificacao is None
    assert r.veredito.mensagem == MENSAGEM_NAO_CONCLUSIVA


def test_parametros_configuraveis(fazer_evidencias, llm_roteirizado, motor):
    llm = llm_roteirizado(
        analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )
    pesquisa = PesquisaFalsa(fazer_evidencias(0.80))
    parametros = ParametrosDaOrquestracao(
        limite_inicial=3, limite_maximo=20, maximo_de_retornos=3
    )

    r = _orquestrador(llm, pesquisa, motor, parametros=parametros).executar(
        "Alegação", "consumidor_geral"
    )

    assert pesquisa.limites == [3, 6, 12, 20]
    assert r.retornos == 3


def test_cada_etapa_tem_os_segundos_do_relogio(
    fazer_evidencias, llm_roteirizado, motor
):
    llm = llm_roteirizado(
        analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )

    r = _orquestrador(
        llm, PesquisaFalsa(fazer_evidencias(0.9)), motor, relogio=_relogio()
    ).executar("Alegação", "consumidor_geral")

    assert [e.segundos for e in r.historico] == [1.0, 1.0, 1.0, 1.0]


def test_observador_registra_a_verificacao_e_cada_etapa(
    fazer_evidencias, llm_roteirizado, motor
):
    registros = []

    class Observador:
        @contextmanager
        def verificacao(self, entrada):
            registros.append(("abre", entrada))
            yield lambda saida: registros.append(("verificacao", saida))

        @contextmanager
        def etapa(self, nome, entrada):
            yield lambda saida: registros.append((nome, saida))

    llm = llm_roteirizado(
        analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )
    _orquestrador(
        llm, PesquisaFalsa(fazer_evidencias(0.9)), motor, observador=Observador()
    ).executar("Alegação", "consumidor_geral")

    assert [nome for nome, _ in registros] == [
        "abre",
        "research",
        "analysis",
        "validation",
        "communication",
        "verificacao",
    ]
    assert registros[0][1] == {"alegacao": "Alegação", "perfil": "consumidor_geral"}
    assert registros[-1][1] == {
        "classificacao": "reciclada",
        "aprovado_pela_validacao": True,
        "retornos": 0,
    }


def test_falha_do_llm_interrompe_a_verificacao(fazer_evidencias, motor):
    class LLMForaDoAr:
        def gerar_json(self, sistema, mensagem, esquema):
            raise ConnectionError("Ollama fora do ar")

    with pytest.raises(ConnectionError):
        _orquestrador(
            LLMForaDoAr(), PesquisaFalsa(fazer_evidencias(0.9)), motor
        ).executar("Alegação", "consumidor_geral")


def test_falha_do_research_interrompe_a_verificacao(llm_roteirizado, motor):
    def pesquisa_fora_do_ar(texto, limite):
        raise TimeoutError("Qdrant não respondeu")

    with pytest.raises(TimeoutError):
        _orquestrador(llm_roteirizado(), pesquisa_fora_do_ar, motor).executar(
            "Alegação", "consumidor_geral"
        )


@pytest.mark.parametrize(
    ("alegacao", "perfil"), [("   ", "consumidor_geral"), ("A", "x")]
)
def test_entrada_invalida(llm_roteirizado, alegacao, perfil):
    with pytest.raises(ValueError):
        _orquestrador(llm_roteirizado(), PesquisaFalsa([]), None).executar(
            alegacao, perfil
        )


def test_grafo_tem_um_no_por_agente_e_a_aresta_condicional(llm_roteirizado):
    orquestrador = _orquestrador(llm_roteirizado(), PesquisaFalsa([]), None)

    grafo = (
        GrafoLangGraph().compilar(orquestrador.nos, orquestrador.proximo).get_graph()
    )

    assert {n for n in grafo.nodes if not n.startswith("__")} == {
        "research",
        "analysis",
        "validation",
        "communication",
    }
    condicionais = {(a.source, a.target) for a in grafo.edges if a.conditional}
    assert condicionais == {
        ("validation", "research"),
        ("validation", "analysis"),
        ("validation", "communication"),
    }


def _modulos_importados(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module)
    return nomes


@pytest.mark.parametrize(
    "arquivo",
    [a for c in ("dominio", "aplicacao") for a in sorted((RAIZ / c).rglob("*.py"))],
    ids=lambda a: str(a.relative_to(RAIZ)),
)
def test_dominio_e_aplicacao_nao_importam_o_langgraph(arquivo):
    assert not {m for m in _modulos_importados(arquivo) if m.startswith("langgraph")}


def test_historico_leva_so_os_ids_e_os_scores_dos_trechos(
    fazer_evidencias, llm_roteirizado, motor
):
    """O histórico não leva o texto dos trechos, para não crescer a cada retorno (spec 82)."""
    llm = llm_roteirizado(
        analise=[_reciclada(1)], validacao=[SEM_CONTRADICAO], comunicacao=[MENSAGEM]
    )
    evidencias = fazer_evidencias(0.9, 0.85)

    r = _orquestrador(llm, PesquisaFalsa(evidencias), motor).executar(
        "Ultraprocessados devem ser evitados", "consumidor_geral"
    )

    research = r.historico[0]
    assert research.agente is No.RESEARCH
    assert research.saida["evidencias"] == [
        {"trecho": e.trecho.id, "score": e.score} for e in evidencias
    ]
    for etapa in r.historico:
        for evidencia in evidencias:
            assert evidencia.trecho.texto not in repr(etapa.entrada)
            assert evidencia.trecho.texto not in repr(etapa.saida)
