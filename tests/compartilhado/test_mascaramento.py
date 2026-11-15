import pytest

from economia.compartilhado import mascaramento
from economia.compartilhado.mascaramento import FALHA, mascarar, mascarar_texto


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("meu e-mail é maria@exemplo.com", "meu e-mail é [EMAIL]"),
        ("contato: joao.silva+mercado@exemplo.com.br", "contato: [EMAIL]"),
        ("meu CPF é 123.456.789-09", "meu CPF é [CPF]"),
        ("cpf 12345678909", "cpf [CPF]"),
        ("me liga no (61) 98765-4321", "me liga no [TELEFONE]"),
        ("fixo 61 3333-4444", "fixo [TELEFONE]"),
        ("cartão 4111 1111 1111 1111", "cartão [CARTAO]"),
        (
            "chave 5326 1112 3456 7800 0123 6500 1000 0012 3410 0001 2345",
            "chave [CHAVE_NFCE]",
        ),
    ],
)
def test_dados_pessoais_viram_marcadores(texto, esperado):
    assert mascarar_texto(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "como conservo alface?",
        "receita com 2 ovos e 300 g de farinha",
        "o arroz custa 25,90 no mercado",
        "guarde por 3 a 5 dias a 4 °C",
    ],
)
def test_pergunta_sem_dado_pessoal_passa_igual(texto):
    assert mascarar_texto(texto) == texto


def test_mascara_dentro_de_dicionarios_e_listas():
    dado = {
        "pergunta": "sou maria@exemplo.com",
        "trechos": ["ligue (61) 98765-4321", 3],
        "score": 0.9,
    }
    assert mascarar(data=dado) == {
        "pergunta": "sou [EMAIL]",
        "trechos": ["ligue [TELEFONE]", 3],
        "score": 0.9,
    }


def test_falha_no_mascaramento_nao_envia_o_conteudo(monkeypatch):
    def quebrar(_):
        raise RuntimeError("padrão inválido")

    monkeypatch.setattr(mascaramento, "mascarar_dado", quebrar)
    assert mascarar(data="sou maria@exemplo.com") == FALHA
