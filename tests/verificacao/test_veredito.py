"""Regras do veredito: fontes, fonte principal, frases e marcadores (spec 72)."""

import pytest

from economia.verificacao.dominio.analise import (
    AnaliseDaAlegacao,
    ClassificacaoDaAlegacao,
    montar_analise,
)
from economia.verificacao.dominio.modelos import (
    DocumentoEvidencia,
    EvidenciaRecuperada,
    FonteEvidencia,
    TrechoEvidencia,
)
from economia.verificacao.dominio.veredito import (
    MENSAGEM_NAO_CONCLUSIVA,
    Veredito,
    fonte_principal,
    fontes_citadas,
    limitar_frases,
    remover_marcadores_de_citacao,
    veredito_nao_conclusivo,
)

GUIA = FonteEvidencia(
    titulo="Guia Alimentar", instituicao="Ministério da Saúde", ano=2014
)
TACO = FonteEvidencia(titulo="Tabela TACO", instituicao="NEPA/Unicamp", ano=2011)


def _evidencia(numero: int, fonte: FonteEvidencia, score: float) -> EvidenciaRecuperada:
    documento = DocumentoEvidencia(
        id=fonte.titulo.lower().replace(" ", "-"),
        fonte=fonte,
        arquivo="documento.pdf",
        hash_sha256="abc",
    )
    return EvidenciaRecuperada(
        trecho=TrechoEvidencia(
            id=f"{documento.id}-{numero:04d}",
            documento_id=documento.id,
            texto=f"Trecho {numero}.",
        ),
        documento=documento,
        score=score,
    )


def _analise(evidencias, citadas) -> AnaliseDaAlegacao:
    return montar_analise(
        ClassificacaoDaAlegacao.PARCIAL, "Justificativa [1].", citadas, evidencias
    )


def test_fontes_sem_repetir_documento_na_ordem_das_citacoes():
    evidencias = [
        _evidencia(1, GUIA, 0.9),
        _evidencia(2, TACO, 0.8),
        _evidencia(3, GUIA, 0.7),
    ]

    fontes = fontes_citadas(_analise(evidencias, [2, 1, 3]), evidencias)

    assert fontes == (TACO, GUIA)


def test_fontes_so_das_evidencias_citadas():
    evidencias = [_evidencia(1, GUIA, 0.9), _evidencia(2, TACO, 0.8)]

    assert fontes_citadas(_analise(evidencias, [2]), evidencias) == (TACO,)


def test_sem_citacao_nao_ha_fontes():
    evidencias = [_evidencia(1, GUIA, 0.9)]
    analise = _analise(evidencias, [])

    assert fontes_citadas(analise, evidencias) == ()
    assert fonte_principal(analise, evidencias) is None


def test_fonte_principal_e_a_da_evidencia_citada_de_maior_score():
    evidencias = [_evidencia(1, GUIA, 0.80), _evidencia(2, TACO, 0.91)]

    assert fonte_principal(_analise(evidencias, [1, 2]), evidencias) == TACO


def test_fonte_principal_ignora_evidencia_nao_citada():
    evidencias = [_evidencia(1, GUIA, 0.80), _evidencia(2, TACO, 0.99)]

    assert fonte_principal(_analise(evidencias, [1]), evidencias) == GUIA


def test_fonte_principal_em_empate_fica_com_a_primeira_citada():
    evidencias = [_evidencia(1, GUIA, 0.85), _evidencia(2, TACO, 0.85)]

    assert fonte_principal(_analise(evidencias, [2, 1]), evidencias) == TACO


@pytest.mark.parametrize(
    ("texto", "maximo", "esperado"),
    [
        (
            "Sim. O Guia recomenda evitar. Vale para todos.",
            2,
            "Sim. O Guia recomenda evitar.",
        ),
        ("Uma frase só.", 2, "Uma frase só."),
        ("Pode? Pode! E mais uma.", 2, "Pode? Pode!"),
        ("  Com espaços.   Muitos.  ", 1, "Com espaços."),
    ],
)
def test_limitar_frases(texto, maximo, esperado):
    assert limitar_frases(texto, maximo) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("O Guia trata de ovos [1].", "O Guia trata de ovos."),
        ("Em parte [1, 2], mas não [3].", "Em parte, mas não."),
        ("Sem marcador.", "Sem marcador."),
    ],
)
def test_remover_marcadores_de_citacao(texto, esperado):
    assert remover_marcadores_de_citacao(texto) == esperado


def test_veredito_nao_conclusivo_mantem_a_classificacao_sem_fontes():
    evidencias = [_evidencia(1, GUIA, 0.9)]

    veredito = veredito_nao_conclusivo(_analise(evidencias, [1]))

    assert veredito.classificacao == ClassificacaoDaAlegacao.PARCIAL
    assert veredito.mensagem == MENSAGEM_NAO_CONCLUSIVA
    assert veredito.fontes == ()
    assert not veredito.aprovado_pela_validacao


def test_veredito_nao_conclusivo_sem_analise_nao_tem_classificacao():
    veredito = veredito_nao_conclusivo(None)

    assert veredito.classificacao is None
    assert veredito.fontes == ()


def test_veredito_precisa_de_mensagem():
    with pytest.raises(ValueError, match="mensagem"):
        Veredito(classificacao=ClassificacaoDaAlegacao.NOVA, mensagem="  ")


def test_veredito_sem_classificacao_nao_pode_ser_aprovado():
    with pytest.raises(ValueError, match="sem classificação"):
        Veredito(classificacao=None, mensagem="Texto.", aprovado_pela_validacao=True)
