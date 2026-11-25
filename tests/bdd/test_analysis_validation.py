"""Passos dos cenários do Analysis Agent e do Validation Agent (specs/79-analysis-validation)."""

import json

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
from economia.verificacao.aplicacao.avaliacao import CasoDeVerificacao, avaliar_caso
from economia.verificacao.aplicacao.validar_analise import ValidarAnalise
from economia.verificacao.dominio.analise import Alegacao, ClassificacaoDaAlegacao
from economia.verificacao.dominio.evidencias import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)

scenarios("79-analysis-validation/cenarios.feature")

ANALISE = "<prompt verificacao/analise>"
VALIDACAO = "<prompt verificacao/validacao>"
SEM_CONTRADICAO = {"contradiz": False, "explicacao": ""}
DOCUMENTO = DocumentoEvidencia(
    id="guia-alimentar",
    fonte=FonteEvidencia(titulo="Guia Alimentar", instituicao="Ministério da Saúde"),
)


def _numero(texto: str) -> float:
    return float(texto.replace(",", "."))


def _evidencias(*scores: float) -> list[EvidenciaRecuperada]:
    return [
        EvidenciaRecuperada(
            trecho=TrechoEvidencia(
                id=f"guia-alimentar-{n:04d}",
                documento_id=DOCUMENTO.id,
                texto=f"Trecho {n}.",
            ),
            documento=DOCUMENTO,
            score=s,
        )
        for n, s in enumerate(scores, start=1)
    ]


class LLMDosCenarios:
    """Responde com a fila de cada prompt; a última resposta se repete."""

    def __init__(self, respostas: dict[str, list]):
        self._respostas = respostas

    def gerar_json(self, sistema, mensagem, esquema):
        fila = self._respostas[sistema]
        resposta = fila.pop(0) if len(fila) > 1 else fila[0]
        if isinstance(resposta, str):
            try:
                return json.loads(resposta)
            except json.JSONDecodeError as erro:
                raise ValueError("saída do LLM não é JSON") from erro
        return resposta


def _classificacao(classificacao: str, citacoes: list[int]) -> dict:
    return {
        "classificacao": classificacao,
        "justificativa": "Justificativa com base nos trechos.",
        "citacoes": citacoes,
    }


@pytest.fixture
def cenario():
    return {
        "alegacao": Alegacao("Alegação fictícia sobre alimentação"),
        "evidencias": _evidencias(0.90, 0.86),
        "analise": [],
        "validacao": [SEM_CONTRADICAO],
    }


def _agentes(cenario):
    llm = LLMDosCenarios({ANALISE: cenario["analise"], VALIDACAO: cenario["validacao"]})
    return AnalisarAlegacao(llm, ANALISE), ValidarAnalise(
        llm, VALIDACAO, cenario["limiar"]
    )


@given(parsers.parse("o limiar mínimo de confiança de {limiar}"))
def limiar(cenario, limiar):
    cenario["limiar"] = _numero(limiar)


@given(parsers.parse('a alegação "{texto}"'))
def alegacao(cenario, texto):
    cenario["alegacao"] = Alegacao(texto)


@given("duas evidências recuperadas")
def duas_evidencias(cenario):
    cenario["evidencias"] = _evidencias(0.90, 0.86)


@given(parsers.parse("duas evidências recuperadas, a primeira com score {score}"))
def evidencias_com_a_primeira(cenario, score):
    cenario["evidencias"] = _evidencias(_numero(score), 0.80)


@given(parsers.parse("duas evidências recuperadas, a maior com score {score}"))
def evidencias_com_a_maior(cenario, score):
    cenario["evidencias"] = _evidencias(_numero(score), _numero(score) - 0.05)


@given(
    parsers.parse(
        'o LLM classifica como "{classificacao}" citando a evidência {numero:d}'
    )
)
def classifica_citando(cenario, classificacao, numero):
    cenario["analise"].append(_classificacao(classificacao, [numero]))


@given(parsers.parse('o LLM classifica como "{classificacao}" sem citar evidências'))
def classifica_sem_citar(cenario, classificacao):
    cenario["analise"].append(_classificacao(classificacao, []))


@given("o LLM não aponta contradição")
def sem_contradicao(cenario):
    cenario["validacao"] = [SEM_CONTRADICAO]


@given("o LLM aponta que a justificativa contradiz a evidência")
def com_contradicao(cenario):
    cenario["validacao"] = [
        {"contradiz": True, "explicacao": "A evidência diz o contrário."}
    ]


@given("o LLM devolve um texto que não é JSON")
def saida_invalida(cenario):
    cenario["analise"].append("A alegação parece reciclada.")


@given(parsers.parse('um caso de avaliação com a classificação esperada "{esperada}"'))
def caso_de_avaliacao(cenario, esperada):
    cenario["caso"] = CasoDeVerificacao(
        "v01", cenario["alegacao"].texto, ClassificacaoDaAlegacao(esperada)
    )


@given("na primeira análise o LLM cita uma evidência inexistente")
def primeira_analise_invalida(cenario):
    cenario["analise"].append(_classificacao("reciclada", [7]))


@given(
    parsers.parse(
        'na segunda análise o LLM classifica como "{classificacao}" citando a evidência {numero:d}'
    )
)
def segunda_analise(cenario, classificacao, numero):
    cenario["analise"].append(_classificacao(classificacao, [numero]))


@given("um caso de avaliação em que toda análise cita uma evidência inexistente")
def caso_sempre_invalido(cenario):
    cenario["caso"] = CasoDeVerificacao(
        "v02", cenario["alegacao"].texto, ClassificacaoDaAlegacao.RECICLADA
    )
    cenario["analise"].append(_classificacao("reciclada", [7]))


@when("o Analysis Agent analisa e o Validation Agent valida")
def analisa_e_valida(cenario):
    analisar, validar = _agentes(cenario)
    analise = analisar.executar(cenario["alegacao"], cenario["evidencias"])
    cenario["resultado_da_analise"] = analise
    cenario["validacao_feita"] = validar.executar(
        cenario["alegacao"], cenario["evidencias"], analise
    )


@when("a avaliação roda o caso")
def roda_o_caso(cenario):
    analisar, validar = _agentes(cenario)
    cenario["caso_avaliado"] = avaliar_caso(
        cenario["caso"], lambda texto, limite: cenario["evidencias"], analisar, validar
    )


@then(parsers.parse("a análise cita o trecho da evidência {numero:d}"))
def cita_o_trecho(cenario, numero):
    esperado = cenario["evidencias"][numero - 1].trecho.id
    assert cenario["resultado_da_analise"].citacoes == (esperado,)


@then(parsers.parse("a confiança é {confianca}"))
def confianca(cenario, confianca):
    assert cenario["resultado_da_analise"].confianca == pytest.approx(
        _numero(confianca)
    )


@then("a validação é aprovada sem retorno")
def aprovada(cenario):
    resultado = cenario["validacao_feita"]
    assert resultado.aprovado, resultado.motivos
    assert resultado.retornar_para is None


@then(parsers.parse('a validação é reprovada com retorno para o "{destino}"'))
def reprovada(cenario, destino):
    resultado = cenario["validacao_feita"]
    assert not resultado.aprovado
    assert resultado.motivos
    assert resultado.retornar_para == destino


@then(parsers.parse("a análise registra a citação {numero:d} como inválida"))
def citacao_invalida(cenario, numero):
    assert numero in cenario["resultado_da_analise"].citacoes_invalidas


@then("não há análise")
def sem_analise(cenario):
    assert cenario["resultado_da_analise"] is None


@then(
    parsers.parse(
        'o caso acerta a classificação com {retornos:d} retorno para o "{destino}"'
    )
)
def acerta_com_retorno(cenario, retornos, destino):
    caso = cenario["caso_avaliado"]
    assert caso.acertou
    assert caso.aprovado
    assert caso.destinos == (destino,) * retornos


@then(parsers.parse("o caso termina reprovado depois de {retornos:d} retornos"))
def termina_reprovado(cenario, retornos):
    caso = cenario["caso_avaliado"]
    assert not caso.aprovado
    assert caso.retornos == retornos
