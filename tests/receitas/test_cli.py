"""O CLI monta o caso de uso com as opções da configuração (sem Qdrant nem Ollama de verdade)."""

import pytest

from economia.compartilhado.configuracao import Configuracao
from economia.receitas import cli


@pytest.fixture
def sem_servicos(monkeypatch):
    monkeypatch.setattr(cli, "criar_gerador", lambda configuracao: object())
    monkeypatch.setattr(
        cli, "criar_repositorio", lambda configuracao, amostra=None: object()
    )


@pytest.mark.parametrize("deterministico", [False, True])
def test_criar_responder_com_as_opcoes_da_redacao(sem_servicos, deterministico):
    configuracao = Configuracao(
        _env_file=None,
        prompt_de_resposta="resposta_com_fontes_v2",
        resposta_estruturada=True,
        segunda_tentativa_de_citacao=True,
    )
    caso = cli.criar_responder(configuracao, deterministico=deterministico)
    assert caso._estruturada is True
    assert "trechos_usados" in caso._prompt
    assert "{resposta}" in caso._pedido_de_citacao
    opcoes = caso._llm._opcoes
    assert ("seed" in opcoes) is deterministico


def test_criar_responder_padrao_e_a_versao_1(sem_servicos):
    caso = cli.criar_responder(Configuracao(_env_file=None))
    assert caso._estruturada is False
    assert caso._pedido_de_citacao is None
    assert "NAO_ENCONTRADO" in caso._prompt


def test_llm_da_avaliacao_e_deterministico_e_limitado(sem_servicos):
    configuracao = Configuracao(_env_file=None, ollama_saida_maxima=1000)
    llm = cli.criar_llm(configuracao, deterministico=True)
    assert llm._opcoes == {
        "temperature": 0.0,
        "num_ctx": 8192,
        "seed": 42,
        "num_predict": 1000,
    }
    assert llm._pensar is False


def test_criar_responder_aceita_o_llm_e_o_repositorio_prontos(sem_servicos):
    llm, repositorio = object(), object()
    caso = cli.criar_responder(
        Configuracao(_env_file=None), llm=llm, repositorio=repositorio
    )
    assert caso._llm is llm
    assert caso._repositorio is repositorio


def test_modo_puro_usa_o_prompt_sem_base(sem_servicos):
    caso = cli.criar_caso_de_avaliacao(
        Configuracao(_env_file=None), "puro", llm=object()
    )
    assert "NAO_ENCONTRADO" not in caso._prompt
    assert "trechos" not in caso._prompt.casefold()


def test_nome_do_run_e_do_dataset():
    configuracao = Configuracao(
        _env_file=None,
        ollama_modelo="gemma3:12b",
        prompt_de_resposta="resposta_com_fontes_v2",
    )
    assert (
        cli.nome_do_run(configuracao, "rag")
        == "rag-gemma3:12b-resposta_com_fontes_v2-e5"
    )
    assert (
        cli.nome_do_run(configuracao, "puro") == "puro-gemma3:12b-resposta_sem_base_v1"
    )
    from pathlib import Path

    arquivo = Path("data/avaliacao/perguntas_rag_v3.json")
    assert cli.nome_do_dataset(arquivo, 67, 67) == "miau-ricio-perguntas_rag_v3"
    assert cli.nome_do_dataset(arquivo, 10, 67) == "miau-ricio-perguntas_rag_v3-10de67"


def test_avaliar_respostas_aceita_modo_e_llm():
    parser_args = cli.criar_parser().parse_args(
        [
            "avaliar-respostas",
            "--modo",
            "puro",
            "--llm",
            "gemma3:12b",
            "--saida",
            "x.json",
        ]
    )
    assert parser_args.modo == "puro"
    assert parser_args.llm == "gemma3:12b"
    padrao = cli.criar_parser().parse_args(["avaliar-respostas", "--saida", "x.json"])
    assert padrao.modo == "rag"
    assert padrao.llm is None
