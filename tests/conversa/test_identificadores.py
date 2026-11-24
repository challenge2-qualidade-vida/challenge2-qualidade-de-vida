import pytest

from economia.conversa.dominio.identificadores import (
    IdentificadorAnonimo,
    IdentificadorDaConversa,
)

VALIDO = "3f2b8c1e-9a4d-4e6f-8b2a-1c3d5e7f9a0b"


def test_le_uuid_v4_e_normaliza_para_minusculas():
    assert IdentificadorAnonimo.ler(VALIDO.upper()) == IdentificadorAnonimo(VALIDO)
    assert IdentificadorDaConversa.ler(f"  {VALIDO} ").valor == VALIDO


@pytest.mark.parametrize(
    "valor",
    [
        None,
        "",
        "maria@exemplo.com",
        "123.456.789-09",
        "3f2b8c1e-9a4d-1e6f-8b2a-1c3d5e7f9a0b",  # versão 1, não 4
        "3f2b8c1e9a4d4e6f8b2a1c3d5e7f9a0b",
    ],
)
def test_valor_fora_do_formato_e_ignorado(valor):
    assert IdentificadorAnonimo.ler(valor) is None
    assert IdentificadorDaConversa.ler(valor) is None


def test_construir_com_valor_invalido_falha():
    with pytest.raises(ValueError):
        IdentificadorAnonimo("maria@exemplo.com")
