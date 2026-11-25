"""Passos dos cenários do Communication Agent (specs/83-communication-agent)."""

import json

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from economia.verificacao.aplicacao.comunicar_veredito import ComunicarVeredito
from economia.verificacao.dominio.analise import (
    Alegacao,
    ClassificacaoDaAlegacao,
    DestinoDoRetorno,
    ResultadoDaValidacao,
    montar_analise,
)
from economia.verificacao.dominio.evidencias import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)
from economia.verificacao.dominio.veredito import (
    MENSAGEM_NAO_CONCLUSIVA,
    PerfilDeLeitura,
)

scenarios("83-communication-agent/cenarios.feature")

PROMPT = "<prompt verificacao/comunicacao>"
DOCUMENTO = DocumentoEvidencia(
    id="guia-alimentar",
    fonte=FonteEvidencia(
        titulo="Guia Alimentar para a População Brasileira",
        instituicao="Ministério da Saúde",
        ano=2014,
    ),
)


def _numero(texto: str) -> float:
    return float(texto.replace(",", "."))


class LLMDoCenario:
    """Devolve sempre a mesma resposta e registra as chamadas."""

    def __init__(self):
        self.resposta: dict | str = {"mensagem": "Mensagem padrão."}
        self.chamadas = 0

    def gerar_json(self, sistema, mensagem, esquema):
        self.chamadas += 1
        if isinstance(self.resposta, str):
            # o gerar_json real levanta ValueError quando a saída não é JSON
            try:
                return json.loads(self.resposta)
            except json.JSONDecodeError as erro:
                raise ValueError("saída do LLM não é JSON") from erro
        return self.resposta


@pytest.fixture
def contexto():
    return {"llm": LLMDoCenario(), "evidencias": []}


@given(parsers.parse("duas evidências recuperadas, com scores {a} e {b}"))
def _duas_evidencias(contexto, a, b):
    contexto["evidencias"] = [
        EvidenciaRecuperada(
            trecho=TrechoEvidencia(
                id=f"guia-alimentar-{n:04d}",
                documento_id=DOCUMENTO.id,
                texto=f"Trecho {n}.",
            ),
            documento=DOCUMENTO,
            score=_numero(s),
        )
        for n, s in enumerate((a, b), start=1)
    ]


@given("nenhuma evidência recuperada")
def _nenhuma_evidencia(contexto):
    contexto["evidencias"] = []


@given(parsers.parse('uma análise "{classificacao}" que cita as duas evidências'))
def _analise_que_cita_as_duas(contexto, classificacao):
    contexto["analise"] = montar_analise(
        ClassificacaoDaAlegacao(classificacao),
        "Justificativa [1] [2].",
        [1, 2],
        contexto["evidencias"],
    )


@given(parsers.parse('uma análise "{classificacao}" sem citações'))
def _analise_sem_citacoes(contexto, classificacao):
    contexto["analise"] = montar_analise(
        ClassificacaoDaAlegacao(classificacao),
        "Nenhuma evidência.",
        [],
        contexto["evidencias"],
    )


@given(
    parsers.parse('uma análise "{classificacao}" com a justificativa "{justificativa}"')
)
def _analise_com_justificativa(contexto, classificacao, justificativa):
    contexto["analise"] = montar_analise(
        ClassificacaoDaAlegacao(classificacao),
        justificativa,
        [1],
        contexto["evidencias"],
    )


@given("uma validação aprovada")
def _validacao_aprovada(contexto):
    contexto["validacao"] = ResultadoDaValidacao(aprovado=True)


@given(parsers.parse('uma validação reprovada com o motivo "{motivo}"'))
def _validacao_reprovada(contexto, motivo):
    contexto["validacao"] = ResultadoDaValidacao(
        aprovado=False, motivos=(motivo,), retornar_para=DestinoDoRetorno.RESEARCH
    )


@given(parsers.parse('o LLM escreve a mensagem "{mensagem}"'))
def _llm_escreve(contexto, mensagem):
    contexto["llm"].resposta = {"mensagem": mensagem}


@given("o LLM devolve um texto que não é JSON")
def _llm_sem_json(contexto):
    contexto["llm"].resposta = "isto não é JSON"


@when(parsers.parse('o Communication Agent monta o veredito para o perfil "{perfil}"'))
def _comunicar(contexto, perfil):
    contexto["veredito"] = ComunicarVeredito(contexto["llm"], PROMPT).executar(
        Alegacao("Ovo aumenta o colesterol?"),
        contexto["analise"],
        contexto["validacao"],
        contexto["evidencias"],
        PerfilDeLeitura(perfil),
    )


@then(parsers.parse('o veredito tem a classificação "{classificacao}"'))
def _tem_classificacao(contexto, classificacao):
    assert contexto["veredito"].classificacao == ClassificacaoDaAlegacao(classificacao)


@then("o veredito foi aprovado pela validação")
def _aprovado(contexto):
    assert contexto["veredito"].aprovado_pela_validacao


@then("o veredito não foi aprovado pela validação")
def _nao_aprovado(contexto):
    assert not contexto["veredito"].aprovado_pela_validacao


@then(parsers.parse('o veredito tem 1 fonte, o "{titulo}"'))
def _uma_fonte(contexto, titulo):
    assert [f.titulo for f in contexto["veredito"].fontes] == [titulo]


@then("o veredito não tem fontes")
def _sem_fontes(contexto):
    assert contexto["veredito"].fontes == ()


@then(parsers.parse('a mensagem é "{mensagem}"'))
def _mensagem_e(contexto, mensagem):
    assert contexto["veredito"].mensagem == mensagem


@then("a mensagem diz que a verificação não foi conclusiva")
def _mensagem_nao_conclusiva(contexto):
    assert contexto["veredito"].mensagem == MENSAGEM_NAO_CONCLUSIVA


@then("o LLM não é chamado")
def _llm_nao_chamado(contexto):
    assert contexto["llm"].chamadas == 0
