"""Configuração comum dos testes."""

import pytest


@pytest.fixture(autouse=True)
def sem_langfuse_real(monkeypatch):
    """Nenhum teste envia registros ao Langfuse do `.env`: as chaves ficam vazias.

    Os testes de observabilidade usam clientes falsos, passados explicitamente.
    """
    from economia.api.app import obter_langfuse
    from economia.compartilhado.configuracao import obter_configuracao

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    obter_configuracao.cache_clear()
    obter_langfuse.cache_clear()
    yield
    obter_configuracao.cache_clear()
    obter_langfuse.cache_clear()
