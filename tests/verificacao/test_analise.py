"""Testes do domínio da análise: confiança, conferências e destino do retorno (RN01)."""

import pytest

from economia.verificacao.dominio.analise import (
    Alegacao,
    AnaliseDaAlegacao,
    ClassificacaoDaAlegacao,
    DestinoDoRetorno,
    Reprovacao,
    ResultadoDaValidacao,
    conferir_analise,
    decidir,
    montar_analise,
)

LIMIAR = 0.845
RECICLADA = ClassificacaoDaAlegacao.RECICLADA
PARCIAL = ClassificacaoDaAlegacao.PARCIAL
NOVA = ClassificacaoDaAlegacao.NOVA


def test_alegacao_vazia_e_recusada():
    with pytest.raises(ValueError):
        Alegacao("   ")


def test_converte_numeros_em_ids_e_a_confianca_e_o_maior_score(fazer_evidencias):
    evidencias = fazer_evidencias(0.90, 0.86, 0.80)

    analise = montar_analise(PARCIAL, " Justificativa. ", [3, 2, 3], evidencias)

    assert analise.citacoes == ("guia-alimentar-0003", "guia-alimentar-0002")
    assert analise.citacoes_invalidas == ()
    assert analise.confianca == 0.86
    assert analise.justificativa == "Justificativa."


def test_numeros_fora_da_lista_ficam_como_citacoes_invalidas(fazer_evidencias):
    analise = montar_analise(PARCIAL, "J", [7, 0, 7, 1], fazer_evidencias(0.9, 0.8))

    assert analise.citacoes == ("guia-alimentar-0001",)
    assert analise.citacoes_invalidas == (7, 0)


def test_sem_citacao_valida_a_confianca_e_zero(fazer_evidencias):
    assert montar_analise(NOVA, "J", [], fazer_evidencias(0.9)).confianca == 0.0


def test_validacao_aprovada_nao_tem_motivos():
    with pytest.raises(ValueError):
        ResultadoDaValidacao(aprovado=True, motivos=("x",))


def test_validacao_reprovada_precisa_de_motivo_e_destino():
    with pytest.raises(ValueError):
        ResultadoDaValidacao(aprovado=False, retornar_para=DestinoDoRetorno.ANALYSIS)
    with pytest.raises(ValueError):
        ResultadoDaValidacao(aprovado=False, motivos=("x",))


def _destinos(reprovacoes):
    return [r.destino for r in reprovacoes]


def test_sem_analise_volta_para_o_analysis(fazer_evidencias):
    assert _destinos(conferir_analise(None, fazer_evidencias(0.9), LIMIAR)) == [
        DestinoDoRetorno.ANALYSIS
    ]


def test_reciclada_com_citacao_forte_passa(fazer_evidencias):
    evidencias = fazer_evidencias(0.90, 0.80)
    analise = montar_analise(RECICLADA, "Coberta [1].", [1], evidencias)

    assert conferir_analise(analise, evidencias, LIMIAR) == []


def test_justificativa_vazia_reprova(fazer_evidencias):
    evidencias = fazer_evidencias(0.90)
    analise = montar_analise(RECICLADA, "  ", [1], evidencias)

    assert _destinos(conferir_analise(analise, evidencias, LIMIAR)) == [
        DestinoDoRetorno.ANALYSIS
    ]


def test_citacao_invalida_reprova_com_o_numero_no_motivo(fazer_evidencias):
    evidencias = fazer_evidencias(0.90, 0.80)
    analise = montar_analise(PARCIAL, "J", [1, 7], evidencias)

    reprovacoes = conferir_analise(analise, evidencias, LIMIAR)

    assert [r.motivo for r in reprovacoes] == [
        "A citação 7 não está entre as 2 evidências recuperadas."
    ]


@pytest.mark.parametrize("classificacao", [RECICLADA, PARCIAL])
def test_reciclada_ou_parcial_sem_citacao_volta_para_o_analysis(
    fazer_evidencias, classificacao
):
    evidencias = fazer_evidencias(0.90)
    analise = montar_analise(classificacao, "J", [], evidencias)

    assert _destinos(conferir_analise(analise, evidencias, LIMIAR)) == [
        DestinoDoRetorno.ANALYSIS
    ]


def test_confianca_abaixo_do_limiar_volta_para_o_research(fazer_evidencias):
    evidencias = fazer_evidencias(0.80, 0.78)
    analise = montar_analise(RECICLADA, "J", [1], evidencias)

    assert _destinos(conferir_analise(analise, evidencias, LIMIAR)) == [
        DestinoDoRetorno.RESEARCH
    ]


def test_confianca_igual_ao_limiar_passa(fazer_evidencias):
    evidencias = fazer_evidencias(LIMIAR)
    analise = montar_analise(RECICLADA, "J", [1], evidencias)

    assert conferir_analise(analise, evidencias, LIMIAR) == []


def test_nova_sem_citar_a_evidencia_forte_volta_para_o_analysis(fazer_evidencias):
    evidencias = fazer_evidencias(0.92, 0.80)
    analise = montar_analise(NOVA, "A base não trata disso.", [], evidencias)

    assert _destinos(conferir_analise(analise, evidencias, LIMIAR)) == [
        DestinoDoRetorno.ANALYSIS
    ]


def test_nova_que_cita_so_a_evidencia_fraca_tambem_reprova(fazer_evidencias):
    evidencias = fazer_evidencias(0.92, 0.80)
    analise = montar_analise(NOVA, "J [2].", [2], evidencias)

    assert _destinos(conferir_analise(analise, evidencias, LIMIAR)) == [
        DestinoDoRetorno.ANALYSIS
    ]


def test_nova_que_cita_a_evidencia_forte_passa(fazer_evidencias):
    evidencias = fazer_evidencias(0.92, 0.80)
    analise = montar_analise(NOVA, "O trecho [1] trata de outro tema.", [1], evidencias)

    assert conferir_analise(analise, evidencias, LIMIAR) == []


def test_nova_sem_evidencia_no_limiar_passa_sem_citacao(fazer_evidencias):
    evidencias = fazer_evidencias(0.78, 0.70)
    analise = montar_analise(NOVA, "A base não trata disso.", [], evidencias)

    assert conferir_analise(analise, evidencias, LIMIAR) == []


def test_nova_sem_evidencias_passa(fazer_evidencias):
    analise = AnaliseDaAlegacao(classificacao=NOVA, justificativa="Nada na base.")

    assert conferir_analise(analise, [], LIMIAR) == []


def test_decidir_sem_reprovacoes_aprova():
    assert decidir([]) == ResultadoDaValidacao(aprovado=True)


def test_com_os_dois_destinos_volta_para_o_research():
    resultado = decidir(
        [
            Reprovacao("a", DestinoDoRetorno.ANALYSIS),
            Reprovacao("b", DestinoDoRetorno.RESEARCH),
        ]
    )

    assert resultado.retornar_para is DestinoDoRetorno.RESEARCH
    assert resultado.motivos == ("a", "b")
