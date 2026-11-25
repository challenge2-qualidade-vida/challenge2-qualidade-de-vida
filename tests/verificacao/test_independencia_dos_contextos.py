"""A verificação não depende do domínio da Pesquisa de evidências (modelo de domínio, seção 2).

As camadas `dominio`, `aplicacao` e `infraestrutura` da verificação não importam nada de
`economia.pesquisa_evidencias`. Só a CLI, que monta as peças, chama o caso de uso do Research.
"""

import ast
from pathlib import Path

import pytest

from economia.verificacao.dominio.evidencias import EvidenciaRecuperada
from economia.verificacao.infraestrutura.pesquisa_de_evidencias import (
    PesquisaDeEvidencias,
    traduzir_evidencia,
)

RAIZ = Path(__file__).parents[2] / "src" / "economia" / "verificacao"
CAMADAS = ("dominio", "aplicacao", "infraestrutura")


def _modulos_importados(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module)
    return nomes


@pytest.mark.parametrize(
    "arquivo",
    [a for c in CAMADAS for a in sorted((RAIZ / c).rglob("*.py"))],
    ids=lambda a: str(a.relative_to(RAIZ)),
)
def test_camadas_da_verificacao_nao_importam_a_pesquisa_de_evidencias(arquivo):
    proibidos = {
        m
        for m in _modulos_importados(arquivo)
        if m.startswith("economia.pesquisa_evidencias")
    }
    assert not proibidos


def test_traduz_a_evidencia_do_research_para_a_verificacao():
    from economia.pesquisa_evidencias.dominio import modelos as research

    fonte = research.FonteEvidencia(
        titulo="Guia Alimentar para a População Brasileira",
        instituicao="Ministério da Saúde",
        ano=2014,
        url="https://exemplo.invalid/guia",
    )
    documento = research.DocumentoEvidencia(
        id="guia", fonte=fonte, arquivo="guia.pdf", hash_sha256="abc"
    )
    evidencia = research.EvidenciaRecuperada(
        trecho=research.TrechoEvidencia(
            id="guia-0001",
            documento_id="guia",
            texto="Evite ultraprocessados.",
            pagina_inicial=3,
            secao="Capítulo 2",
        ),
        documento=documento,
        score=0.9,
    )

    traduzida = traduzir_evidencia(evidencia)

    assert isinstance(traduzida, EvidenciaRecuperada)
    assert traduzida.trecho.id == "guia-0001"
    assert traduzida.trecho.texto == "Evite ultraprocessados."
    assert traduzida.trecho.secao == "Capítulo 2"
    assert traduzida.documento.id == "guia"
    assert traduzida.documento.fonte.titulo == fonte.titulo
    assert traduzida.documento.fonte.instituicao == fonte.instituicao
    assert traduzida.documento.fonte.ano == 2014
    assert traduzida.documento.fonte.url == fonte.url
    assert traduzida.score == 0.9

    pesquisa = PesquisaDeEvidencias(lambda pergunta, limite: [evidencia] * limite)
    assert pesquisa("ovo faz mal?", 2) == [traduzida, traduzida]
