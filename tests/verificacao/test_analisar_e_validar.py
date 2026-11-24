"""Testes do Analysis Agent e do Validation Agent com um LLM falso."""

from economia.verificacao.aplicacao.analisar_alegacao import (
    AnalisarAlegacao,
    SaidaDaAnalise,
    montar_mensagem,
)
from economia.verificacao.aplicacao.validar_analise import (
    SAIDA_INVALIDA,
    ValidarAnalise,
)
from economia.verificacao.dominio.analise import (
    Alegacao,
    ClassificacaoDaAlegacao,
    DestinoDoRetorno,
    montar_analise,
)

ALEGACAO = Alegacao("Ultraprocessados devem ser evitados")
ANALISE = "<prompt verificacao/analise>"
VALIDACAO = "<prompt verificacao/validacao>"
LIMIAR = 0.845
SEM_CONTRADICAO = {"contradiz": False, "explicacao": ""}


def test_mensagem_numera_as_evidencias_sem_mostrar_o_score(fazer_evidencias):
    mensagem = montar_mensagem(ALEGACAO, fazer_evidencias(0.9123, 0.8))

    assert "Alegação: Ultraprocessados devem ser evitados" in mensagem
    assert (
        "[1] Guia Alimentar para a População Brasileira (Ministério da Saúde, 2014)"
        in mensagem
    )
    assert "[2] " in mensagem
    assert "0.9123" not in mensagem


def test_mensagem_de_retorno_traz_os_motivos(fazer_evidencias):
    mensagem = montar_mensagem(
        ALEGACAO, fazer_evidencias(0.9), ["A citação 7 não existe."]
    )

    assert "- A citação 7 não existe." in mensagem


def test_mensagem_sem_evidencias():
    assert "(nenhuma evidência recuperada)" in montar_mensagem(ALEGACAO, [])


def test_analysis_converte_a_saida_do_llm(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(
        **{
            ANALISE: [
                {
                    "classificacao": "reciclada",
                    "justificativa": "Coberta [1].",
                    "citacoes": [1],
                }
            ]
        }
    )
    evidencias = fazer_evidencias(0.90, 0.80)

    analise = AnalisarAlegacao(llm, ANALISE).executar(ALEGACAO, evidencias)

    assert analise is not None
    assert analise.classificacao is ClassificacaoDaAlegacao.RECICLADA
    assert analise.citacoes == ("guia-alimentar-0001",)
    assert analise.confianca == 0.90


def test_analysis_pede_o_esquema_da_saida(fazer_evidencias):
    class LLMQueGuardaOEsquema:
        esquema = None

        def gerar_json(self, sistema, mensagem, esquema):
            self.esquema = esquema
            return {"classificacao": "nova", "justificativa": "J", "citacoes": []}

    llm = LLMQueGuardaOEsquema()
    AnalisarAlegacao(llm, ANALISE).executar(ALEGACAO, fazer_evidencias(0.7))

    assert llm.esquema == SaidaDaAnalise.model_json_schema()


def test_saida_que_nao_e_json_nao_vira_analise(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(**{ANALISE: ["isto não é JSON"]})

    assert (
        AnalisarAlegacao(llm, ANALISE).executar(ALEGACAO, fazer_evidencias(0.9)) is None
    )


def test_saida_fora_do_esquema_nao_vira_analise(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(
        **{
            ANALISE: [
                {"classificacao": "verdadeira", "justificativa": "J", "citacoes": []}
            ]
        }
    )

    assert (
        AnalisarAlegacao(llm, ANALISE).executar(ALEGACAO, fazer_evidencias(0.9)) is None
    )


def test_validation_aprova_sem_contradicao(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.90)
    analise = montar_analise(
        ClassificacaoDaAlegacao.RECICLADA, "J [1].", [1], evidencias
    )
    llm = llm_roteirizado(**{VALIDACAO: [SEM_CONTRADICAO]})

    resultado = ValidarAnalise(llm, VALIDACAO, LIMIAR).executar(
        ALEGACAO, evidencias, analise
    )

    assert resultado.aprovado
    assert resultado.retornar_para is None
    mensagem = llm.chamadas_de(VALIDACAO)[0]
    assert "Justificativa: J [1]." in mensagem
    assert "Trecho 1 sobre alimentação." in mensagem


def test_contradicao_so_roda_depois_das_conferencias(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.90)
    analise = montar_analise(ClassificacaoDaAlegacao.PARCIAL, "J", [7], evidencias)
    llm = llm_roteirizado(**{VALIDACAO: [SEM_CONTRADICAO]})

    resultado = ValidarAnalise(llm, VALIDACAO, LIMIAR).executar(
        ALEGACAO, evidencias, analise
    )

    assert resultado.retornar_para is DestinoDoRetorno.ANALYSIS
    assert llm.chamadas == []


def test_contradicao_reprova_com_a_explicacao(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.90)
    analise = montar_analise(
        ClassificacaoDaAlegacao.RECICLADA, "J [1].", [1], evidencias
    )
    llm = llm_roteirizado(
        **{VALIDACAO: [{"contradiz": True, "explicacao": "O trecho diz o contrário."}]}
    )

    resultado = ValidarAnalise(llm, VALIDACAO, LIMIAR).executar(
        ALEGACAO, evidencias, analise
    )

    assert resultado.retornar_para is DestinoDoRetorno.ANALYSIS
    assert resultado.motivos == (
        "A justificativa contradiz as evidências citadas: O trecho diz o contrário.",
    )


def test_saida_invalida_da_contradicao_reprova(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.90)
    analise = montar_analise(
        ClassificacaoDaAlegacao.RECICLADA, "J [1].", [1], evidencias
    )
    llm = llm_roteirizado(**{VALIDACAO: ["não sei"]})

    resultado = ValidarAnalise(llm, VALIDACAO, LIMIAR).executar(
        ALEGACAO, evidencias, analise
    )

    assert resultado.motivos == (SAIDA_INVALIDA,)
    assert resultado.retornar_para is DestinoDoRetorno.ANALYSIS


def test_sem_analise_reprova_sem_chamar_o_llm(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(**{VALIDACAO: [SEM_CONTRADICAO]})

    resultado = ValidarAnalise(llm, VALIDACAO, LIMIAR).executar(
        ALEGACAO, fazer_evidencias(0.9), None
    )

    assert resultado.retornar_para is DestinoDoRetorno.ANALYSIS
    assert llm.chamadas == []
