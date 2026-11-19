"""Configuração comum dos testes."""

import pytest


@pytest.fixture(autouse=True)
def sem_langfuse_real(request, monkeypatch, tmp_path):
    """Nenhum teste envia registros ao Langfuse do `.env` nem lê a cópia local dos prompts.

    As chaves ficam vazias e a cópia local vai para uma pasta temporária. Os testes de
    observabilidade usam clientes falsos, passados explicitamente. Os testes de contrato
    (`-m langfuse`) usam o Langfuse de verdade.
    """
    from economia.api.app import _fabrica_do_caso_de_uso, obter_langfuse
    from economia.compartilhado.configuracao import obter_configuracao
    from economia.compartilhado.infraestrutura import prompts_langfuse

    monkeypatch.setattr(prompts_langfuse, "PASTA_DO_CACHE", tmp_path / "cache")
    if request.node.get_closest_marker("langfuse") is None:
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    caches = (obter_configuracao, obter_langfuse, _fabrica_do_caso_de_uso)
    for cache in caches:
        cache.cache_clear()
    yield
    for cache in caches:
        cache.cache_clear()


class PromptsFalsos:
    """Dublê de `PromptsDoLangfuse`: o texto de cada prompt é a própria referência."""

    def __init__(self):
        self.pedidos: list[str] = []
        self.prompts_lidos: dict = {}
        self.versoes: dict = {}

    def carregar(self, agente: str, referencia: str) -> str:
        self.pedidos.append(f"{agente}/{referencia}")
        return f"<prompt {agente}/{referencia}>"


@pytest.fixture
def prompts_falsos():
    return PromptsFalsos()
