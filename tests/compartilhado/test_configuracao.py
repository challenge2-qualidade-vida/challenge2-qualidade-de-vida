import pytest
from pydantic import ValidationError

from economia.compartilhado.configuracao import Configuracao


def criar(**kwargs) -> Configuracao:
    # _env_file=None isola o teste do .env de quem roda
    return Configuracao(_env_file=None, **kwargs)


def test_valores_padrao(monkeypatch):
    for nome in (
        "MODELO_EMBEDDINGS",
        "LIMIAR_SIMILARIDADE_E5",
        "LIMIAR_SIMILARIDADE_QWEN3",
        "INGREDIENTES_BASICOS",
        "OLLAMA_TEMPO_LIMITE",
    ):
        monkeypatch.delenv(nome, raising=False)
    configuracao = criar()
    assert configuracao.modelo_embeddings == "e5"
    assert configuracao.limiar_similaridade == 0.845
    assert configuracao.limiar_similaridade_qwen3 == 0.620
    assert configuracao.ollama_tempo_limite == 1800
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
    monkeypatch.setenv("LIMIAR_SIMILARIDADE_QWEN3", "0.75")
    monkeypatch.setenv("INGREDIENTES_BASICOS", '["sal"]')
    configuracao = criar()
    assert configuracao.modelo_embeddings == "qwen3"
    assert configuracao.limiar_similaridade == 0.75
    assert configuracao.ingredientes_basicos == ["sal"]


@pytest.mark.parametrize(("modelo", "limiar"), [("e5", 0.8), ("qwen3", 0.6)])
def test_limiar_acompanha_o_modelo(modelo, limiar):
    # os scores de cada modelo têm escalas diferentes; o limiar de um não serve para o outro
    configuracao = criar(limiar_similaridade_e5=0.8, limiar_similaridade_qwen3=0.6)
    trocada = configuracao.model_copy(update={"modelo_embeddings": modelo})
    assert trocada.limiar_similaridade == limiar


def test_limiar_unico_antigo_e_recusado():
    # LIMIAR_SIMILARIDADE valia para os dois modelos e escondia o limiar errado
    with pytest.raises(ValidationError, match="LIMIAR_SIMILARIDADE_E5"):
        criar(limiar_similaridade=0.845)


def test_limiar_unico_antigo_no_ambiente_e_recusado(monkeypatch):
    monkeypatch.setenv("LIMIAR_SIMILARIDADE", "0.845")
    with pytest.raises(ValidationError, match="LIMIAR_SIMILARIDADE_QWEN3"):
        criar()


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


@pytest.mark.parametrize(
    "campo", ["limiar_similaridade_e5", "limiar_similaridade_qwen3"]
)
def test_recusa_limiar_fora_de_0_a_1(campo):
    with pytest.raises(ValidationError):
        criar(**{campo: 1.5})


def test_colecao_da_amostra_tem_sufixo():
    configuracao = criar(modelo_embeddings="qwen3")
    assert configuracao.colecao_da_amostra(400) == "base_conhecimento_qwen3_amostra400"
    assert configuracao.colecao_da_amostra(None) == configuracao.colecao


def test_langfuse_so_fica_configurado_com_as_duas_chaves(monkeypatch):
    for nome in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"):
        monkeypatch.delenv(nome, raising=False)
    assert criar().langfuse_configurado is False
    assert criar(langfuse_public_key="pk").langfuse_configurado is False
    configurada = criar(langfuse_public_key="pk", langfuse_secret_key="sk")
    assert configurada.langfuse_configurado is True
    assert configurada.langfuse_base_url == "https://us.cloud.langfuse.com"


def test_saida_maxima_padrao(monkeypatch):
    monkeypatch.delenv("OLLAMA_SAIDA_MAXIMA", raising=False)
    assert criar().ollama_saida_maxima == 2048
