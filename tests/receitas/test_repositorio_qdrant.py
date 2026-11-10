import pytest
from qdrant_client import QdrantClient

from economia.receitas.dominio.modelos import TipoDeTrecho
from economia.receitas.infraestrutura.repositorio_qdrant import (
    RepositorioQdrant,
    de_payload,
    id_do_ponto,
    para_payload,
)


@pytest.fixture
def repositorio():
    # modo em memória do qdrant-client: mesma API, sem servidor
    repo = RepositorioQdrant(QdrantClient(":memory:"), "teste")
    repo.preparar(dimensao=2)
    return repo


def test_payload_ida_e_volta_preserva_o_trecho(trecho):
    original = trecho("afrodite:1", ingredientes=("ovo", "cenoura"))
    assert de_payload(para_payload(original)) == original


def test_id_do_ponto_e_estavel_e_e_uuid():
    assert id_do_ponto("guia:0:0") == id_do_ponto("guia:0:0")
    assert id_do_ponto("guia:0:0") != id_do_ponto("guia:0:1")
    assert len(id_do_ponto("x")) == 36


def test_busca_ordena_por_similaridade(repositorio, trecho):
    repositorio.gravar([trecho("perto"), trecho("longe")], [[1.0, 0.0], [0.0, 1.0]])
    resultado = repositorio.buscar([0.9, 0.1], limite=2)
    assert [r.trecho.id for r in resultado] == ["perto", "longe"]
    assert resultado[0].score > resultado[1].score


def test_busca_filtra_por_tipo(repositorio, trecho):
    repositorio.gravar(
        [trecho("receita"), trecho("guia", tipo=TipoDeTrecho.CONHECIMENTO)],
        [[1.0, 0.0], [1.0, 0.0]],
    )
    resultado = repositorio.buscar([1.0, 0.0], limite=5, tipo=TipoDeTrecho.CONHECIMENTO)
    assert [r.trecho.id for r in resultado] == ["guia"]


def test_gravar_de_novo_substitui_o_trecho(repositorio, trecho):
    repositorio.gravar([trecho("a")], [[1.0, 0.0]])
    repositorio.gravar([trecho("a")], [[0.0, 1.0]])
    assert repositorio.contar() == 1


def test_preparar_com_recriar_apaga_a_colecao(repositorio, trecho):
    repositorio.gravar([trecho("a")], [[1.0, 0.0]])
    repositorio.preparar(dimensao=2, recriar=True)
    assert repositorio.contar() == 0


def test_contar_colecao_que_nao_existe():
    assert RepositorioQdrant(QdrantClient(":memory:"), "nenhuma").contar() == 0
