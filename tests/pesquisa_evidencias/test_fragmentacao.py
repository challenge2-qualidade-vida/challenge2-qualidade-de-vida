import pytest

from economia.pesquisa_evidencias.aplicacao.fragmentacao import (
    fragmentar_documento,
)
from economia.pesquisa_evidencias.dominio.modelos import TrechoEvidencia


def contar_palavras(texto: str) -> int:
    """Contador falso para testar a lógica sem carregar o E5."""
    return len(texto.split())


def test_fragmenta_documento_curto_em_um_trecho():
    paginas = [
        {
            "pagina": 1,
            "texto": "Primeiro parágrafo.\n\nSegundo parágrafo.",
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=10,
        overlap_tokens=0,
    )

    assert len(trechos) == 1
    assert isinstance(trechos[0], TrechoEvidencia)
    assert trechos[0].documento_id == "doc_001"
    assert trechos[0].pagina_inicial == 1
    assert trechos[0].pagina_final == 1
    assert "Primeiro parágrafo." in trechos[0].texto
    assert "Segundo parágrafo." in trechos[0].texto


def test_cria_novo_trecho_ao_atingir_limite():
    paginas = [
        {
            "pagina": 1,
            "texto": "um dois três quatro\n\ncinco seis sete oito",
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=4,
        overlap_tokens=0,
    )

    assert len(trechos) == 2
    assert trechos[0].texto == "um dois três quatro"
    assert trechos[1].texto == "cinco seis sete oito"


def test_preserva_paginas_ao_agrupar_paragrafos():
    paginas = [
        {"pagina": 1, "texto": "Primeiro parágrafo."},
        {"pagina": 2, "texto": "Segundo parágrafo."},
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=10,
        overlap_tokens=0,
    )

    assert len(trechos) == 1
    assert trechos[0].pagina_inicial == 1
    assert trechos[0].pagina_final == 2


def test_gera_identificadores_sequenciais():
    paginas = [
        {
            "pagina": 1,
            "texto": "um dois três quatro\n\ncinco seis sete oito",
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=4,
        overlap_tokens=0,
    )

    assert [trecho.id for trecho in trechos] == [
        "doc_001_t0001",
        "doc_001_t0002",
    ]


def test_divide_paragrafo_maior_que_limite():
    paginas = [
        {
            "pagina": 1,
            "texto": "um dois três quatro cinco",
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=3,
        overlap_tokens=0,
    )

    assert len(trechos) == 2
    assert trechos[0].texto == "um dois três"
    assert trechos[1].texto == "quatro cinco"

    assert all(contar_palavras(trecho.texto) <= 3 for trecho in trechos)

    assert all(
        trecho.pagina_inicial == 1 and trecho.pagina_final == 1 for trecho in trechos
    )


def test_rejeita_documento_sem_identificador():
    with pytest.raises(ValueError):
        fragmentar_documento(
            paginas=[],
            documento_id=" ",
            contar_tokens=contar_palavras,
        )


def test_rejeita_limite_invalido():
    with pytest.raises(ValueError):
        fragmentar_documento(
            paginas=[],
            documento_id="doc_001",
            contar_tokens=contar_palavras,
            limite_tokens=0,
        )


def test_documento_sem_paginas_retorna_lista_vazia():
    trechos = fragmentar_documento(
        paginas=[],
        documento_id="doc_001",
        contar_tokens=contar_palavras,
    )

    assert trechos == []


def test_preserva_integralmente_conteudo_de_paragrafo_dividido():
    texto_original = "um dois três quatro cinco seis sete oito nove"

    paginas = [
        {
            "pagina": 3,
            "texto": texto_original,
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=3,
        overlap_tokens=0,
    )

    texto_reconstruido = " ".join(trecho.texto for trecho in trechos)

    assert texto_reconstruido == texto_original


def test_reutiliza_final_do_trecho_anterior_no_overlap():
    paginas = [
        {
            "pagina": 1,
            "texto": "um dois três quatro\n\ncinco seis sete oito",
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=6,
        overlap_tokens=2,
    )

    assert len(trechos) >= 2

    palavras_primeiro = trechos[0].texto.split()
    palavras_segundo = trechos[1].texto.split()

    assert palavras_segundo[:2] == palavras_primeiro[-2:]
    assert contar_palavras(trechos[1].texto) <= 6


def test_overlap_preserva_pagina_de_origem():
    paginas = [
        {"pagina": 1, "texto": "um dois três quatro"},
        {"pagina": 2, "texto": "cinco seis sete oito"},
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=6,
        overlap_tokens=2,
    )

    assert len(trechos) >= 2
    assert trechos[1].pagina_inicial == 1
    assert trechos[1].pagina_final == 2
    assert trechos[1].texto.startswith("três quatro")


def test_preserva_conteudo_original_com_overlap():
    texto_original = "um dois três quatro cinco seis sete oito"

    paginas = [
        {
            "pagina": 1,
            "texto": texto_original,
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=5,
        overlap_tokens=2,
    )

    palavras_reconstruidas = []

    for indice, trecho in enumerate(trechos):
        palavras = trecho.texto.split()

        if indice > 0:
            palavras = palavras[2:]

        palavras_reconstruidas.extend(palavras)

    assert " ".join(palavras_reconstruidas) == texto_original


def test_overlap_padrao_se_adapta_a_limite_menor():
    paginas = [
        {
            "pagina": 1,
            "texto": (
                "um dois três quatro cinco seis\n\n" "sete oito nove dez onze doze"
            ),
        }
    ]

    trechos = fragmentar_documento(
        paginas=paginas,
        documento_id="doc_001",
        contar_tokens=contar_palavras,
        limite_tokens=10,
    )

    assert len(trechos) == 2

    palavras_primeiro = trechos[0].texto.split()
    palavras_segundo = trechos[1].texto.split()

    # O overlap padrão deve ser calculado automaticamente.
    # Como o novo conteúdo precisa caber no limite, o overlap
    # é reduzido até que a combinação respeite os 10 tokens.
    assert palavras_segundo[:4] == palavras_primeiro[-4:]

    assert all(contar_palavras(trecho.texto) <= 10 for trecho in trechos)
