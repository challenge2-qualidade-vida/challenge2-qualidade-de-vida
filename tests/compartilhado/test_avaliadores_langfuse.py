from types import SimpleNamespace

import pytest

from economia.compartilhado.infraestrutura.avaliadores_langfuse import (
    AVALIADORES,
    NOME_DA_REGRA,
    ApiDoLangfuse,
    SemConexaoDoGemini,
    corpo_da_regra,
    corpo_do_avaliador,
    criar_avaliadores,
    provedor_do_gemini,
)

GEMINI = {"provider": "gemini", "adapter": "google-ai-studio"}


class Colecao:
    """Uma coleção da API do SDK (evaluators ou evaluation_rules) em memória."""

    def __init__(self):
        self.itens: dict[str, SimpleNamespace] = {}

    def list(self, limit, cursor=None):
        return SimpleNamespace(
            data=list(self.itens.values()), meta=SimpleNamespace(next_cursor=None)
        )

    def _guardar(self, id, dados):
        self.itens[id] = SimpleNamespace(**{**dados, "id": id})
        return self.itens[id]

    def create(self, request=None, request_options=None, **dados):
        dados = vars(request) if request is not None else dados
        return self._guardar(f"id-{len(self.itens) + 1}", dados)

    def update(self, id, request=None, request_options=None, **dados):
        dados = vars(request) if request is not None else dados
        return self._guardar(id, {**vars(self.itens[id]), **dados})


class ApiFalsa:
    def __init__(self, conexoes=(GEMINI,)):
        self.llm_connections = SimpleNamespace(
            list=lambda limit: SimpleNamespace(
                data=[SimpleNamespace(**c) for c in conexoes]
            )
        )
        self.evaluators = Colecao()
        self.evaluation_rules = Colecao()


def test_provedor_vem_da_conexao_do_gemini():
    conexoes = [{"provider": "openai", "adapter": "openai"}, GEMINI]
    assert provedor_do_gemini(conexoes) == "gemini"


def test_sem_conexao_do_gemini_explica_o_que_fazer():
    with pytest.raises(SemConexaoDoGemini, match="LLM Connection do Gemini"):
        provedor_do_gemini([{"provider": "openai", "adapter": "openai"}])


def test_avaliador_mapeia_as_variaveis_da_observacao_raiz():
    fidelidade = next(a for a in AVALIADORES if a.nome == "fidelidade")
    corpo = corpo_do_avaliador(fidelidade, "gemini", "gemini-2.5-flash")

    assert corpo["model_config_"] == {"provider": "gemini", "model": "gemini-2.5-flash"}
    mapeamento = {
        m["variable"]: (m["source"], m["json_path"]) for m in corpo["variable_mapping"]
    }
    assert mapeamento == {
        "pergunta": ("input", "$.pergunta"),
        "resposta": ("output", "$.texto"),
        "trechos": ("output", "$.trechos"),
    }
    assert corpo["output_definition"]["data_type"] == "NUMERIC"


def test_cada_variavel_do_mapeamento_aparece_no_prompt():
    for avaliador in AVALIADORES:
        prompt = corpo_do_avaliador(avaliador, "gemini", "m")["prompt"]
        for variavel in avaliador.variaveis:
            assert "{{" + variavel + "}}" in prompt


def test_regra_avalia_a_amostra_das_perguntas_sem_erro():
    regra = corpo_da_regra(["a", "b"], 0.2, ["producao", "local"])

    assert regra["sampling"] == 0.2
    filtros = {f["column"]: (f["operator"], f["value"]) for f in regra["filter"]}
    assert filtros == {
        "name": ("any of", ["miau-ricio.pergunta"]),
        "environment": ("any of", ["producao", "local"]),
        "level": ("none of", ["ERROR"]),
    }
    assert regra["evaluator_assignments"] == [
        {"evaluator_id": "a"},
        {"evaluator_id": "b"},
    ]


def test_criar_de_novo_atualiza_em_vez_de_duplicar():
    api = ApiFalsa()

    primeira = criar_avaliadores(ApiDoLangfuse(api), "gemini-2.5-flash", 0.2, ["local"])
    segunda = criar_avaliadores(ApiDoLangfuse(api), "gemini-2.5-pro", 0.2, ["local"])

    assert primeira == segunda
    assert NOME_DA_REGRA in segunda
    assert len(api.evaluators.itens) == 2
    assert len(api.evaluation_rules.itens) == 1
    modelos = {a.model_config_.model for a in api.evaluators.itens.values()}
    assert modelos == {"gemini-2.5-pro"}


def test_sem_gemini_nada_e_criado():
    api = ApiFalsa(conexoes=())
    with pytest.raises(SemConexaoDoGemini):
        criar_avaliadores(ApiDoLangfuse(api), "m", 0.2, ["local"])
    assert api.evaluators.itens == {}
