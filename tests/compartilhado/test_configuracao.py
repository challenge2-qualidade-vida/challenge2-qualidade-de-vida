import pytest
from pydantic import ValidationError

from economia.compartilhado.configuracao import Configuracao


def criar(**kwargs) -> Configuracao:
    # _env_file=None isola o teste do .env de quem roda
    return Configuracao(_env_file=None, **kwargs)


def test_valores_padrao(monkeypatch):
    for nome in ("MODELO_EMBEDDINGS", "LIMIAR_SIMILARIDADE", "INGREDIENTES_BASICOS"):
        monkeypatch.delenv(nome, raising=False)
    configuracao = criar()
    assert configuracao.modelo_embeddings == "e5"
    assert configuracao.limiar_similaridade == 0.80
    assert configuracao.ingredientes_basicos == [
        "sal",
        "agua",
        "oleo",
        "salt",
        "water",
        "oil",
    ]


def test_le_das_variaveis_de_ambiente(monkeypatch):
    monkeypatch.setenv("MODELO_EMBEDDINGS", "qwen3")
    monkeypatch.setenv("LIMIAR_SIMILARIDADE", "0.75")
    monkeypatch.setenv("INGREDIENTES_BASICOS", '["sal"]')
    configuracao = criar()
    assert configuracao.modelo_embeddings == "qwen3"
    assert configuracao.limiar_similaridade == 0.75
    assert configuracao.ingredientes_basicos == ["sal"]


@pytest.mark.parametrize(
    ("modelo", "nome", "colecao"),
    [
        ("e5", "intfloat/multilingual-e5-base", "base_conhecimento_e5"),
        ("qwen3", "qwen3-embedding:4b", "base_conhecimento_qwen3"),
    ],
)
def test_uma_colecao_por_modelo(modelo, nome, colecao):
    configuracao = criar(modelo_embeddings=modelo)
    assert configuracao.nome_do_modelo_de_embeddings == nome
    assert configuracao.colecao == colecao


def test_recusa_modelo_desconhecido():
    with pytest.raises(ValidationError):
        criar(modelo_embeddings="outro")


def test_dispositivo_padrao_e_automatico(monkeypatch):
    monkeypatch.delenv("DISPOSITIVO_EMBEDDINGS", raising=False)
    assert criar().dispositivo_embeddings == "auto"


def test_recusa_dispositivo_desconhecido():
    with pytest.raises(ValidationError):
        criar(dispositivo_embeddings="tpu")


def test_recusa_limiar_fora_de_0_a_1():
    with pytest.raises(ValidationError):
        criar(limiar_similaridade=1.5)
