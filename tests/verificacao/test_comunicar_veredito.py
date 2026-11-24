"""Communication Agent com um LLM de respostas prontas (spec 83)."""

from economia.verificacao.aplicacao.comunicar_veredito import (
    ComunicarVeredito,
    montar_mensagem,
)
from economia.verificacao.dominio.analise import (
    Alegacao,
    ClassificacaoDaAlegacao,
    DestinoDoRetorno,
    ResultadoDaValidacao,
    montar_analise,
)
from economia.verificacao.dominio.veredito import (
    MENSAGEM_NAO_CONCLUSIVA,
    PerfilDeLeitura,
)

PROMPT = "<prompt verificacao/comunicacao>"
ALEGACAO = Alegacao("Ovo aumenta o colesterol?")
APROVADA = ResultadoDaValidacao(aprovado=True)
REPROVADA = ResultadoDaValidacao(
    aprovado=False,
    motivos=("A confiança está abaixo do limiar.",),
    retornar_para=DestinoDoRetorno.RESEARCH,
)


def _analise(
    evidencias, citadas, classificacao="parcial", justificativa="Em parte [1]."
):
    return montar_analise(
        ClassificacaoDaAlegacao(classificacao), justificativa, citadas, evidencias
    )


def _agente(llm):
    return ComunicarVeredito(llm, PROMPT)


def test_perfil_geral_usa_a_mensagem_do_llm_e_as_fontes_citadas(
    fazer_evidencias, llm_roteirizado
):
    evidencias = fazer_evidencias(0.87, 0.80)
    llm = llm_roteirizado(**{PROMPT: [{"mensagem": "  Em parte, segundo o Guia.  "}]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise(evidencias, [1, 2]),
        APROVADA,
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_GERAL,
    )

    assert veredito.mensagem == "Em parte, segundo o Guia."
    assert veredito.classificacao == ClassificacaoDaAlegacao.PARCIAL
    assert veredito.aprovado_pela_validacao
    assert [f.titulo for f in veredito.fontes] == [
        "Guia Alimentar para a População Brasileira"
    ]


def test_perfil_rapido_corta_em_duas_frases_e_fica_com_a_fonte_principal(
    fazer_evidencias, llm_roteirizado
):
    evidencias = fazer_evidencias(0.87, 0.80)
    llm = llm_roteirizado(**{PROMPT: [{"mensagem": "Sim. Evite. Vale para todos."}]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise(evidencias, [1, 2], "reciclada"),
        APROVADA,
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_RAPIDO,
    )

    assert veredito.mensagem == "Sim. Evite."
    assert len(veredito.fontes) == 1


def test_validacao_reprovada_nao_chama_o_llm(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.87)
    llm = llm_roteirizado(**{PROMPT: [{"mensagem": "não deveria ser usada"}]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise(evidencias, [1], "reciclada"),
        REPROVADA,
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_GERAL,
    )

    assert veredito.mensagem == MENSAGEM_NAO_CONCLUSIVA
    assert not veredito.aprovado_pela_validacao
    assert veredito.classificacao == ClassificacaoDaAlegacao.RECICLADA
    assert veredito.fontes == ()
    assert llm.chamadas == []


def test_sem_analise_nao_chama_o_llm(fazer_evidencias, llm_roteirizado):
    llm = llm_roteirizado(**{PROMPT: [{"mensagem": "não deveria ser usada"}]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        None,
        REPROVADA,
        fazer_evidencias(0.87),
        PerfilDeLeitura.CONSUMIDOR_GERAL,
    )

    assert veredito.classificacao is None
    assert veredito.mensagem == MENSAGEM_NAO_CONCLUSIVA
    assert llm.chamadas == []


def test_saida_que_nao_e_json_usa_a_justificativa_sem_marcadores(
    fazer_evidencias, llm_roteirizado
):
    evidencias = fazer_evidencias(0.87)
    llm = llm_roteirizado(**{PROMPT: ["isto não é JSON"]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise(evidencias, [1], justificativa="O Guia trata de ovos [1]."),
        APROVADA,
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_GERAL,
    )

    assert veredito.mensagem == "O Guia trata de ovos."
    assert veredito.aprovado_pela_validacao


def test_saida_fora_do_esquema_usa_a_justificativa(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.87)
    llm = llm_roteirizado(**{PROMPT: [{"texto": "campo errado"}]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise(evidencias, [1]),
        APROVADA,
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_GERAL,
    )

    assert veredito.mensagem == "Em parte."


def test_mensagem_vazia_do_llm_usa_a_justificativa(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.87)
    llm = llm_roteirizado(**{PROMPT: [{"mensagem": "   "}]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise(evidencias, [1]),
        APROVADA,
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_GERAL,
    )

    assert veredito.mensagem == "Em parte."


def test_justificativa_so_com_marcador_vai_como_veio(fazer_evidencias, llm_roteirizado):
    evidencias = fazer_evidencias(0.87)
    llm = llm_roteirizado(**{PROMPT: ["não é JSON"]})

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise(evidencias, [1], justificativa="[1]"),
        APROVADA,
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_GERAL,
    )

    assert veredito.mensagem == "[1]"


def test_alegacao_nova_sem_evidencia_nao_tem_fontes(llm_roteirizado):
    llm = llm_roteirizado(
        **{PROMPT: [{"mensagem": "A base não traz informação sobre isso."}]}
    )

    veredito = _agente(llm).executar(
        ALEGACAO,
        _analise([], [], "nova", "Nenhuma evidência."),
        APROVADA,
        [],
        PerfilDeLeitura.CONSUMIDOR_RAPIDO,
    )

    assert veredito.classificacao == ClassificacaoDaAlegacao.NOVA
    assert veredito.fontes == ()


def test_mensagem_ao_llm_leva_o_perfil_e_so_as_evidencias_citadas(
    fazer_evidencias, llm_roteirizado
):
    evidencias = fazer_evidencias(0.87, 0.80)

    mensagem = montar_mensagem(
        ALEGACAO,
        _analise(evidencias, [2]),
        evidencias,
        PerfilDeLeitura.CONSUMIDOR_RAPIDO,
    )

    assert "consumidor_rapido" in mensagem
    assert ALEGACAO.texto in mensagem
    assert "Classificação: parcial" in mensagem
    assert "Trecho 2" in mensagem
    assert "Trecho 1" not in mensagem
    assert "0.8" not in mensagem  # o score não vai ao LLM
