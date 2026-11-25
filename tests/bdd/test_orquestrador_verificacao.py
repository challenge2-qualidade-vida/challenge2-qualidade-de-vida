"""Passos dos cenários do orquestrador da verificação (specs/82-orquestrador-verificacao).

Cada cenário roda com os dois motores: o laço simples da aplicação e o grafo LangGraph. O
Analysis e o Communication são os de verdade, com um LLM de respostas prontas; o Research e
o Validation são dublês, para cada cenário ditar as evidências e as decisões da validação.
"""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from economia.api.app import app
from economia.api.dependencias import obter_verificar_alegacao
from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
from economia.verificacao.aplicacao.comunicar_veredito import ComunicarVeredito
from economia.verificacao.aplicacao.orquestracao import No, ParametrosDaOrquestracao
from economia.verificacao.aplicacao.verificar_alegacao import (
    LacoSimples,
    VerificarAlegacao,
)
from economia.verificacao.dominio.analise import DestinoDoRetorno, ResultadoDaValidacao
from economia.verificacao.dominio.evidencias import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)
from economia.verificacao.infraestrutura.grafo_langgraph import GrafoLangGraph

scenarios("82-orquestrador-verificacao/cenarios.feature")

ANALISE = "<prompt verificacao/analise>"
COMUNICACAO = "<prompt verificacao/comunicacao>"
DOCUMENTO = DocumentoEvidencia(
    id="guia-alimentar",
    fonte=FonteEvidencia(
        titulo="Guia Alimentar para a População Brasileira",
        instituicao="Ministério da Saúde",
        ano=2014,
    ),
)
ORDINAIS = {"primeira": 1, "segunda": 2, "terceira": 3}
QUANTIDADES = {"duas": 2, "três": 3}


def _evidencia(numero: int) -> EvidenciaRecuperada:
    return EvidenciaRecuperada(
        trecho=TrechoEvidencia(
            id=f"guia-alimentar-{numero:04d}",
            documento_id=DOCUMENTO.id,
            texto=f"Trecho {numero} sobre o consumo de ovos.",
        ),
        documento=DOCUMENTO,
        score=0.9,
    )


class PesquisaFalsa:
    """Research: guarda os limites pedidos e devolve tantas evidências quanto o limite."""

    def __init__(self):
        self.limites: list[int] = []

    def __call__(self, alegacao: str, limite: int) -> list[EvidenciaRecuperada]:
        self.limites.append(limite)
        return [_evidencia(n) for n in range(1, limite + 1)]


class ValidacaoRoteirizada:
    """Validation: devolve as decisões na ordem; depois da última, repete a padrão."""

    def __init__(self):
        self.decisoes: dict[int, ResultadoDaValidacao] = {}
        self.padrao = ResultadoDaValidacao(aprovado=True)
        self.chamadas = 0

    def executar(self, alegacao, evidencias, analise) -> ResultadoDaValidacao:
        self.chamadas += 1
        return self.decisoes.get(self.chamadas, self.padrao)


class LLMDoCenario:
    """Responde ao Analysis e ao Communication e guarda as mensagens de cada prompt."""

    def __init__(self):
        self.mensagens: dict[str, list[str]] = {ANALISE: [], COMUNICACAO: []}
        self.falha: Exception | None = None

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        if self.falha:
            raise self.falha
        self.mensagens[sistema].append(mensagem)
        if sistema == ANALISE:
            return {
                "classificacao": "parcial",
                "justificativa": "O Guia fala do consumo de ovos [1].",
                "citacoes": [1],
            }
        return {"mensagem": "Em parte. O Guia Alimentar fala do consumo de ovos."}


@pytest.fixture(params=["laco", "langgraph"], autouse=True)
def motor(request):
    return LacoSimples() if request.param == "laco" else GrafoLangGraph()


@pytest.fixture
def contexto(motor):
    return {
        "motor": motor,
        "pesquisa": PesquisaFalsa(),
        "validacao": ValidacaoRoteirizada(),
        "llm": LLMDoCenario(),
    }


def _reprovada(destino: str, motivo: str) -> ResultadoDaValidacao:
    return ResultadoDaValidacao(
        aprovado=False, motivos=(motivo,), retornar_para=DestinoDoRetorno(destino)
    )


def _orquestrador(contexto) -> VerificarAlegacao:
    llm = contexto["llm"]
    return VerificarAlegacao(
        contexto["pesquisa"],
        AnalisarAlegacao(llm, ANALISE),
        contexto["validacao"],
        ComunicarVeredito(llm, COMUNICACAO),
        parametros=contexto["parametros"],
        motor=contexto["motor"],
    )


@pytest.fixture
def cliente(contexto):
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@given(
    parsers.parse(
        "um orquestrador com limite inicial de {inicial:d} trechos, teto de {teto:d} "
        "trechos e no máximo {retornos:d} retornos"
    )
)
def _parametros(contexto, inicial, teto, retornos):
    contexto["parametros"] = ParametrosDaOrquestracao(inicial, teto, retornos)


@given(parsers.parse("que a validação aprova a {ordinal} análise"))
def _aprova(contexto, ordinal):
    contexto["validacao"].decisoes[ORDINAIS[ordinal]] = ResultadoDaValidacao(
        aprovado=True
    )


@given(
    parsers.parse(
        'que a validação devolve a {ordinal} análise para o "{destino}" com o motivo '
        '"{motivo}"'
    )
)
def _devolve_uma(contexto, ordinal, destino, motivo):
    contexto["validacao"].decisoes[ORDINAIS[ordinal]] = _reprovada(destino, motivo)


@given(
    parsers.parse(
        'que a validação devolve as {quantidade} primeiras análises para o "{destino}" '
        'com o motivo "{motivo}"'
    )
)
def _devolve_as_primeiras(contexto, quantidade, destino, motivo):
    for n in range(1, QUANTIDADES[quantidade] + 1):
        contexto["validacao"].decisoes[n] = _reprovada(destino, motivo)


@given(
    parsers.parse(
        'que a validação devolve todas as análises para o "{destino}" com o motivo '
        '"{motivo}"'
    )
)
def _devolve_todas(contexto, destino, motivo):
    contexto["validacao"].padrao = _reprovada(destino, motivo)


@given("que o LLM não responde")
def _llm_fora(contexto):
    contexto["llm"].falha = ConnectionError("Ollama fora do ar")


@when(parsers.parse('a alegação "{alegacao}" é verificada no perfil "{perfil}"'))
def _verificar(contexto, alegacao, perfil):
    contexto["resultado"] = _orquestrador(contexto).executar(alegacao, perfil)


@when(
    parsers.parse(
        'a API recebe POST /api/v1/verificacoes com a alegação "{alegacao}" e o perfil '
        '"{perfil}"'
    )
)
def _post(contexto, cliente, alegacao, perfil):
    orquestrador = _orquestrador(contexto)
    app.dependency_overrides[obter_verificar_alegacao] = lambda: orquestrador
    contexto["http"] = cliente.post(
        "/api/v1/verificacoes", json={"alegacao": alegacao, "perfil": perfil}
    )


def _agentes(contexto) -> list[str]:
    return [str(e.agente) for e in contexto["resultado"].historico]


@then(parsers.parse('os agentes rodam na ordem "{ordem}"'))
def _ordem(contexto, ordem):
    assert _agentes(contexto) == [a.strip() for a in ordem.split(",")]


@then("o veredito foi aprovado pela validação")
def _aprovado(contexto):
    assert contexto["resultado"].veredito.aprovado_pela_validacao


@then("o veredito não foi aprovado pela validação")
def _nao_aprovado(contexto):
    veredito = contexto["resultado"].veredito
    assert not veredito.aprovado_pela_validacao
    assert veredito.fontes == ()


@then(parsers.re(r"a verificação teve (?P<retornos>\d+) retornos?"))
def _retornos(contexto, retornos):
    assert contexto["resultado"].retornos == int(retornos)


@then(parsers.parse('o Research busca com os limites "{limites}"'))
def _limites(contexto, limites):
    assert contexto["pesquisa"].limites == [int(n) for n in limites.split(",")]


@then("a segunda análise não recebe motivos")
def _sem_motivos(contexto):
    analises = [e for e in contexto["resultado"].historico if e.agente is No.ANALYSIS]
    assert analises[1].entrada == {"motivos": []}
    assert "reprovada" not in contexto["llm"].mensagens[ANALISE][1]


@then(parsers.parse('a segunda análise recebe o motivo "{motivo}"'))
def _com_motivo(contexto, motivo):
    analises = [e for e in contexto["resultado"].historico if e.agente is No.ANALYSIS]
    assert analises[1].entrada == {"motivos": [motivo]}
    assert motivo in contexto["llm"].mensagens[ANALISE][1]


@then(parsers.parse("o Analysis roda {vezes:d} vezes"))
def _analysis_roda(contexto, vezes):
    assert _agentes(contexto).count("analysis") == vezes


@then(parsers.parse('o último agente é o "{agente}"'))
def _ultimo(contexto, agente):
    assert _agentes(contexto)[-1] == agente


@then(parsers.parse('o Communication recebe o perfil "{perfil}"'))
def _perfil(contexto, perfil):
    etapa = contexto["resultado"].historico[-1]
    assert (etapa.agente, etapa.entrada) == (No.COMMUNICATION, {"perfil": perfil})
    assert f"Perfil de leitura: {perfil}" in contexto["llm"].mensagens[COMUNICACAO][0]


@then(parsers.parse("a resposta tem o status {status:d}"))
def _status(contexto, status):
    assert contexto["http"].status_code == status


@then(parsers.parse("a resposta traz o veredito e {etapas:d} etapas no histórico"))
def _corpo(contexto, etapas):
    corpo = contexto["http"].json()
    assert corpo["veredito"]["aprovado_pela_validacao"] is True
    assert corpo["veredito"]["fontes"][0]["titulo"] == DOCUMENTO.fonte.titulo
    assert len(corpo["historico"]) == etapas
    # o histórico leva os ids e os scores, sem o texto dos trechos
    assert corpo["historico"][0]["saida"]["evidencias"][0] == {
        "trecho": "guia-alimentar-0001",
        "score": 0.9,
    }


@then(parsers.parse("a resposta tem o status {status:d} em Problem Details"))
def _problema(contexto, status):
    resposta = contexto["http"]
    assert resposta.status_code == status
    assert resposta.headers["content-type"].startswith("application/problem+json")
    problema = resposta.json()
    assert (problema["status"], problema["instance"]) == (
        status,
        "/api/v1/verificacoes",
    )
    assert problema["detail"]
