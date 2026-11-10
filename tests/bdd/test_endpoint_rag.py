"""Passos dos cenários do endpoint do RAG (specs/24-endpoint-rag/cenarios.feature)."""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

from economia.api.app import INDISPONIVEL, app, obter_caso_de_uso
from economia.receitas.aplicacao.indexar_base import indexar, montar_trechos
from economia.receitas.aplicacao.responder_pergunta import (
    AVISO_DE_PRECO,
    NAO_ENCONTREI,
    ResponderPergunta,
)
from economia.receitas.dominio.modelos import Documento, Fonte, Secao

FEATURE = "24-endpoint-rag/cenarios.feature"


@scenario(FEATURE, "Pergunta respondida com as fontes")
def test_pergunta_respondida():
    pass


@scenario(FEATURE, "Pergunta sem informação na base")
def test_pergunta_sem_informacao():
    pass


@scenario(FEATURE, "Pergunta de preço recebe o aviso")
def test_pergunta_de_preco():
    pass


@scenario(FEATURE, "Pergunta vazia é recusada")
def test_pergunta_vazia():
    pass


@scenario(FEATURE, "Serviço do RAG fora do ar")
def test_servico_fora_do_ar():
    pass


@pytest.fixture
def cliente(contexto):
    def caso_de_uso():
        if contexto.get("fora_do_ar"):
            return _CasoQueFalha()
        return ResponderPergunta(
            contexto["gerador"],
            contexto["repositorio"],
            contexto["llm"],
            prompt_do_sistema="sistema",
            limiar=contexto["limiar"],
        )

    app.dependency_overrides[obter_caso_de_uso] = caso_de_uso
    yield TestClient(app)
    app.dependency_overrides.clear()


class _CasoQueFalha:
    def responder(self, pergunta):
        raise ConnectionError("Qdrant fora do ar")


@given(parsers.parse('que a base contém a orientação "{titulo}" da "{instituicao}"'))
def base_com_orientacao(contexto, titulo, instituicao):
    documento = Documento(
        documento_id="orientacao-teste",
        titulo=titulo,
        secoes=(
            Secao(
                titulo=titulo,
                paragrafos=(
                    "Para conservar folhas, guarde na geladeira em saco fechado.",
                ),
            ),
        ),
        fonte=Fonte(
            titulo=titulo, instituicao=instituicao, ano=2020, url="https://exemplo.org"
        ),
    )
    trechos, _ = montar_trechos([], [documento])
    indexar(trechos, contexto["gerador"], contexto["repositorio"])


@given("que o banco vetorial está fora do ar")
def banco_fora_do_ar(contexto):
    contexto["fora_do_ar"] = True


@when(parsers.parse('eu envio a pergunta "{pergunta}" para a API'))
def enviar(contexto, cliente, pergunta):
    contexto["http"] = cliente.post(
        "/api/v1/receitas/perguntas", json={"pergunta": pergunta}
    )


@then("a API responde com sucesso")
def sucesso(contexto):
    assert contexto["http"].status_code == 200, contexto["http"].text


@then("a resposta foi encontrada na base")
def encontrada(contexto):
    assert contexto["http"].json()["encontrou"] is True


@then(parsers.parse('a fonte {numero:d} da resposta é "{titulo}"'))
def fonte(contexto, numero, titulo):
    fontes = contexto["http"].json()["fontes"]
    assert fontes[numero - 1]["numero"] == numero
    assert fontes[numero - 1]["titulo"] == titulo
    assert fontes[numero - 1]["url"] == "https://exemplo.org"


@then("a resposta diz que não encontrou a informação")
def nao_encontrou(contexto):
    corpo = contexto["http"].json()
    assert corpo["encontrou"] is False
    assert corpo["texto"] == NAO_ENCONTREI


@then("a resposta não tem fontes")
def sem_fontes(contexto):
    assert contexto["http"].json()["fontes"] == []


@then("a resposta traz o aviso de preço")
def aviso(contexto):
    assert contexto["http"].json()["texto"] == AVISO_DE_PRECO


@then("a API recusa a pergunta como inválida")
def invalida(contexto):
    assert contexto["http"].status_code == 422


@then("a API responde que o Miau-ricio está indisponível")
def indisponivel(contexto):
    assert contexto["http"].status_code == 503
    assert contexto["http"].json()["detail"] == INDISPONIVEL
