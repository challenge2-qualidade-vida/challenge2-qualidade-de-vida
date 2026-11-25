"""Testes do estado e do roteamento do orquestrador da verificação (spec 82)."""

from dataclasses import replace

import pytest

from economia.verificacao.aplicacao.orquestracao import (
    EtapaDaVerificacao,
    No,
    ParametrosDaOrquestracao,
    esta_em_retorno,
    estado_inicial,
    preparar_retorno,
    proximo_no,
    rotear_validacao,
)
from economia.verificacao.dominio.analise import (
    Alegacao,
    DestinoDoRetorno,
    ResultadoDaValidacao,
)
from economia.verificacao.dominio.veredito import PerfilDeLeitura

PARAMETROS = ParametrosDaOrquestracao()
APROVADA = ResultadoDaValidacao(aprovado=True)
MOTIVO_DO_SCORE = "A confiança está abaixo do limiar."
MOTIVO_DA_CITACAO = "A citação 7 não está entre as 5 evidências recuperadas."


def _reprovada(
    destino: DestinoDoRetorno, motivo: str = "Motivo."
) -> ResultadoDaValidacao:
    return ResultadoDaValidacao(
        aprovado=False, motivos=(motivo,), retornar_para=destino
    )


def _estado(*nos: No, **campos):
    estado = estado_inicial(
        Alegacao("Ovo aumenta o colesterol?"),
        PerfilDeLeitura.CONSUMIDOR_GERAL,
        PARAMETROS,
    )
    historico = tuple(EtapaDaVerificacao(no, {}, {}, 0.0) for no in nos)
    return replace(estado, historico=historico, **campos)


def test_padroes_seguem_a_spec():
    assert (
        PARAMETROS.limite_inicial,
        PARAMETROS.limite_maximo,
        PARAMETROS.maximo_de_retornos,
    ) == (5, 10, 2)


@pytest.mark.parametrize(
    "campos",
    [
        {"limite_inicial": 0},
        {"limite_inicial": 6, "limite_maximo": 5},
        {"maximo_de_retornos": -1},
    ],
)
def test_parametros_invalidos(campos):
    with pytest.raises(ValueError):
        ParametrosDaOrquestracao(**campos)


def test_estado_inicial_comeca_no_limite_inicial_sem_retornos():
    estado = _estado()

    assert (estado.limite, estado.retornos, estado.historico, estado.ultimo_no) == (
        5,
        0,
        (),
        None,
    )


@pytest.mark.parametrize(
    ("nos", "esperado"),
    [
        ((), No.RESEARCH),
        ((No.RESEARCH,), No.ANALYSIS),
        ((No.RESEARCH, No.ANALYSIS), No.VALIDATION),
        ((No.RESEARCH, No.ANALYSIS, No.VALIDATION, No.COMMUNICATION), No.FIM),
    ],
)
def test_arestas_fixas(nos, esperado):
    assert proximo_no(_estado(*nos), PARAMETROS) is esperado


def test_aprovado_vai_para_o_communication():
    estado = _estado(No.RESEARCH, No.ANALYSIS, No.VALIDATION, validacao=APROVADA)

    assert proximo_no(estado, PARAMETROS) is No.COMMUNICATION


@pytest.mark.parametrize(
    ("destino", "esperado"),
    [
        (DestinoDoRetorno.RESEARCH, No.RESEARCH),
        (DestinoDoRetorno.ANALYSIS, No.ANALYSIS),
    ],
)
def test_reprovado_volta_para_o_destino_da_validacao(destino, esperado):
    estado = _estado(
        No.RESEARCH, No.ANALYSIS, No.VALIDATION, validacao=_reprovada(destino)
    )

    assert proximo_no(estado, PARAMETROS) is esperado


@pytest.mark.parametrize("destino", list(DestinoDoRetorno))
def test_no_limite_de_retornos_vai_para_o_communication(destino):
    estado = _estado(
        No.RESEARCH,
        No.ANALYSIS,
        No.VALIDATION,
        validacao=_reprovada(destino),
        retornos=2,
    )

    assert proximo_no(estado, PARAMETROS) is No.COMMUNICATION


def test_sem_retornos_permitidos_a_reprovacao_vai_direto_ao_communication():
    sem_retornos = ParametrosDaOrquestracao(maximo_de_retornos=0)

    assert (
        rotear_validacao(_reprovada(DestinoDoRetorno.ANALYSIS), 0, sem_retornos)
        is No.COMMUNICATION
    )


def test_validation_sem_validacao_no_estado_e_erro():
    with pytest.raises(ValueError):
        proximo_no(_estado(No.RESEARCH, No.ANALYSIS, No.VALIDATION), PARAMETROS)


def test_retorno_ao_research_dobra_o_limite_e_limpa_os_motivos():
    estado = _estado(
        validacao=_reprovada(DestinoDoRetorno.RESEARCH, MOTIVO_DO_SCORE),
        motivos=("motivo antigo",),
    )

    novo = preparar_retorno(estado, PARAMETROS)

    assert (novo.limite, novo.motivos, novo.retornos, novo.validacao) == (
        10,
        (),
        1,
        None,
    )


def test_retorno_ao_research_nao_passa_do_teto():
    estado = _estado(validacao=_reprovada(DestinoDoRetorno.RESEARCH), limite=10)

    assert preparar_retorno(estado, PARAMETROS).limite == 10


def test_retorno_ao_analysis_mantem_as_evidencias_e_repassa_os_motivos(
    fazer_evidencias,
):
    evidencias = tuple(fazer_evidencias(0.9, 0.8))
    estado = _estado(
        validacao=_reprovada(DestinoDoRetorno.ANALYSIS, MOTIVO_DA_CITACAO),
        evidencias=evidencias,
    )

    novo = preparar_retorno(estado, PARAMETROS)

    assert (novo.limite, novo.evidencias, novo.motivos, novo.retornos) == (
        5,
        evidencias,
        (MOTIVO_DA_CITACAO,),
        1,
    )
    assert not esta_em_retorno(novo)


@pytest.mark.parametrize("validacao", [None, APROVADA])
def test_sem_reprovacao_nao_ha_retorno(validacao):
    estado = _estado(validacao=validacao)

    assert not esta_em_retorno(estado)
    with pytest.raises(ValueError):
        preparar_retorno(estado, PARAMETROS)
