"""Contrato dos prompts do prompt management do Langfuse (spec 29).

Os prompts ficam só no Langfuse. Estes testes buscam as versões `latest` e `production` de cada
prompt e conferem o que o código espera encontrar nelas: as variáveis que ele preenche e os
campos que ele lê da resposta do LLM. Assim, uma versão nova que quebra o código é pega antes
de receber o rótulo `production`.

Rodam com as chaves do `.env` (`pytest -m langfuse`) e são pulados sem elas.
"""

import pytest

from economia.compartilhado.configuracao import Configuracao
from economia.compartilhado.infraestrutura.avaliadores_langfuse import AVALIADORES
from economia.compartilhado.infraestrutura.observabilidade_langfuse import (
    criar_cliente,
)

pytestmark = pytest.mark.langfuse

ROTULOS = ("latest", "production")

# prompt → trechos que toda versão precisa ter, porque o código depende deles
CONTRATOS = {
    # a segunda tentativa troca {resposta} pela resposta sem citação
    "miau-ricio/pedido_de_citacao": ("{resposta}", "[1]"),
    # o código lê os dois campos do JSON (IngredientesDaPergunta)
    "miau-ricio/extrair_ingredientes": ("ingredientes_pt", "ingredientes_en"),
    # o modo puro lê os dois campos do JSON (RespostaSemBase)
    "miau-ricio/resposta_sem_base": ("encontrou", "resposta"),
    # o texto livre não tem variáveis; o código só precisa de um prompt não vazio
    "miau-ricio/resposta_com_fontes": (),
    # o Analysis lê os três campos do JSON (SaidaDaAnalise, spec 79)
    "verificacao/analise": ("classificacao", "justificativa", "citacoes"),
    # o Validation lê os dois campos do JSON (SaidaDaContradicao, spec 79)
    "verificacao/validacao": ("contradiz", "explicacao"),
    # o Communication lê o campo do JSON (SaidaDaComunicacao, spec 83)
    "verificacao/comunicacao": ("mensagem",),
    **{
        f"juiz/{a.prompt}": tuple("{{" + v + "}}" for v in a.variaveis)
        for a in AVALIADORES
    },
}


@pytest.fixture(scope="module")
def langfuse():
    cliente = criar_cliente(Configuracao())
    if cliente is None:
        pytest.skip("sem LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY no .env")
    return cliente


def _prompt(langfuse, nome, rotulo):
    try:
        return langfuse.get_prompt(nome, label=rotulo, cache_ttl_seconds=0)
    except Exception as erro:
        raise AssertionError(f"{nome}@{rotulo} não está no Langfuse: {erro}") from erro


@pytest.mark.parametrize("rotulo", ROTULOS)
@pytest.mark.parametrize("nome", sorted(CONTRATOS))
def test_prompt_cumpre_o_contrato(langfuse, nome, rotulo):
    prompt = _prompt(langfuse, nome, rotulo)

    assert prompt.prompt.strip(), f"{nome}@{rotulo} (v{prompt.version}) está vazio"
    faltando = [trecho for trecho in CONTRATOS[nome] if trecho not in prompt.prompt]
    assert not faltando, f"{nome}@{rotulo} (v{prompt.version}) sem {faltando}"


def test_prompt_estruturado_pede_os_trechos_usados(langfuse):
    """Com a resposta estruturada ligada, o prompt configurado precisa pedir `trechos_usados`."""
    from economia.compartilhado.infraestrutura.prompts_langfuse import resolver

    configuracao = Configuracao()
    if not configuracao.resposta_estruturada:
        pytest.skip("a resposta estruturada está desligada na configuração")
    nome, rotulo = resolver("miau-ricio", configuracao.prompt_de_resposta)
    assert "trechos_usados" in _prompt(langfuse, nome, rotulo).prompt


def test_versao_estruturada_v2_pede_os_trechos_usados(langfuse):
    prompt = _prompt(langfuse, "miau-ricio/resposta_com_fontes", "v2")
    assert "trechos_usados" in prompt.prompt
