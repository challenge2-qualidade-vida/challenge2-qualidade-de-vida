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
