from economia.compartilhado.infraestrutura.embeddings_e5 import (
    NOME_DO_MODELO,
    contador_de_tokens_e5,
)


class TokenizadorFalso:
    def __init__(self):
        self.textos_recebidos = []
        self.model_max_length = None

    def __call__(self, texto, add_special_tokens):
        self.textos_recebidos.append((texto, add_special_tokens))
        return {"input_ids": [101, 200, 300, 102]}


def test_contador_carrega_tokenizador_do_modelo_e5(monkeypatch):
    import transformers

    tokenizador_falso = TokenizadorFalso()
    modelos_carregados = []

    def carregar_modelo(nome):
        modelos_carregados.append(nome)
        return tokenizador_falso

    monkeypatch.setattr(
        transformers.AutoTokenizer,
        "from_pretrained",
        carregar_modelo,
    )

    contar = contador_de_tokens_e5()

    assert modelos_carregados == [NOME_DO_MODELO]
    assert tokenizador_falso.model_max_length == 1_000_000
    assert contar("arroz") == 4


def test_contador_inclui_prefixo_passage_e_tokens_especiais(
    monkeypatch,
):
    import transformers

    tokenizador_falso = TokenizadorFalso()

    monkeypatch.setattr(
        transformers.AutoTokenizer,
        "from_pretrained",
        lambda nome: tokenizador_falso,
    )

    contar = contador_de_tokens_e5()
    resultado = contar("arroz e feijão")

    assert resultado == 4
    assert tokenizador_falso.textos_recebidos == [("passage: arroz e feijão", True)]
