"""Testes da rota de verificação de alegações (#82)."""

import pytest
from fastapi.testclient import TestClient

from economia.api.app import app
from economia.api.dependencias import obter_verificar_alegacao
from economia.verificacao.aplicacao.orquestracao import (
    EtapaDaVerificacao,
    No,
    ParametrosDaOrquestracao,
    estado_inicial,
)
from economia.verificacao.aplicacao.verificar_alegacao import ResultadoDaVerificacao
from economia.verificacao.dominio.analise import Alegacao, ClassificacaoDaAlegacao
from economia.verificacao.dominio.evidencias import FonteEvidencia
from economia.verificacao.dominio.veredito import PerfilDeLeitura, Veredito

ROTA = "/api/v1/verificacoes"
FONTE = FonteEvidencia(
    titulo="Guia Alimentar para a População Brasileira",
    instituicao="Ministério da Saúde",
    ano=2014,
)


class OrquestradorFalso:
    def __init__(self, erro: Exception | None = None):
        self.erro = erro
        self.pedidos: list[tuple[str, str]] = []

    def executar(self, alegacao, perfil):
        self.pedidos.append((alegacao, perfil))
        if self.erro:
            raise self.erro
        estado = estado_inicial(
            Alegacao(alegacao), PerfilDeLeitura(perfil), ParametrosDaOrquestracao()
        )
        return ResultadoDaVerificacao(
            veredito=Veredito(
                classificacao=ClassificacaoDaAlegacao.PARCIAL,
                mensagem="Em parte.",
                fontes=(FONTE,),
                aprovado_pela_validacao=True,
            ),
            historico=(
                EtapaDaVerificacao(
                    No.RESEARCH,
                    {"limite": 5},
                    {"evidencias": [{"trecho": "guia-0123", "score": 0.87}]},
                    0.4,
                ),
            ),
            retornos=0,
            estado=estado,
        )


@pytest.fixture
def cliente():
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _usar(orquestrador):
    app.dependency_overrides[obter_verificar_alegacao] = lambda: orquestrador
    return orquestrador


def _problema(resposta, status):
    assert resposta.status_code == status
    assert resposta.headers["content-type"].startswith("application/problem+json")
    problema = resposta.json()
    assert (problema["status"], problema["instance"]) == (status, ROTA)
    return problema


def test_devolve_o_veredito_e_o_historico(cliente):
    orquestrador = _usar(OrquestradorFalso())

    resposta = cliente.post(
        ROTA,
        json={
            "alegacao": "  Ovo aumenta o colesterol?  ",
            "perfil": "consumidor_rapido",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json() == {
        "veredito": {
            "classificacao": "parcial",
            "mensagem": "Em parte.",
            "fontes": [
                {
                    "titulo": FONTE.titulo,
                    "instituicao": FONTE.instituicao,
                    "ano": 2014,
                    "url": None,
                }
            ],
            "aprovado_pela_validacao": True,
        },
        "retornos": 0,
        "historico": [
            {
                "agente": "research",
                "entrada": {"limite": 5},
                "saida": {"evidencias": [{"trecho": "guia-0123", "score": 0.87}]},
                "segundos": 0.4,
            }
        ],
    }
    assert orquestrador.pedidos == [("Ovo aumenta o colesterol?", "consumidor_rapido")]


def test_perfil_padrao_e_consumidor_geral(cliente):
    orquestrador = _usar(OrquestradorFalso())

    cliente.post(ROTA, json={"alegacao": "Ovo aumenta o colesterol?"})

    assert orquestrador.pedidos[0][1] == "consumidor_geral"


@pytest.mark.parametrize(
    ("corpo", "detalhe"),
    [
        ({"alegacao": "   "}, "A alegação precisa ter de 1 a 500 caracteres."),
        ({"alegacao": "a" * 501}, "A alegação precisa ter de 1 a 500 caracteres."),
        (
            {"alegacao": "Ovo faz mal?", "perfil": "nutricionista"},
            "O perfil de leitura deve ser consumidor_geral ou consumidor_rapido.",
        ),
    ],
)
def test_entrada_invalida_e_422(cliente, corpo, detalhe):
    orquestrador = _usar(OrquestradorFalso())

    problema = _problema(cliente.post(ROTA, json=corpo), 422)

    assert problema["detail"] == detalhe
    assert orquestrador.pedidos == []


@pytest.mark.parametrize(
    "erro", [ConnectionError("Ollama fora do ar"), TimeoutError("Qdrant não respondeu")]
)
def test_llm_ou_qdrant_indisponivel_e_503(cliente, erro):
    _usar(OrquestradorFalso(erro))

    problema = _problema(cliente.post(ROTA, json={"alegacao": "Ovo faz mal?"}), 503)

    assert "indisponível" in problema["detail"]


def test_qdrant_com_resposta_inesperada_e_503(cliente):
    from qdrant_client.http.exceptions import ResponseHandlingException

    _usar(OrquestradorFalso(ResponseHandlingException(OSError("sem conexão"))))

    _problema(cliente.post(ROTA, json={"alegacao": "Ovo faz mal?"}), 503)


def test_erro_inesperado_e_500_sem_detalhes_internos(cliente):
    _usar(OrquestradorFalso(ValueError("segredo interno")))

    problema = _problema(cliente.post(ROTA, json={"alegacao": "Ovo faz mal?"}), 500)

    assert "segredo" not in problema["detail"]


def test_rota_esta_no_openapi():
    assert ROTA in app.openapi()["paths"]


def test_orquestrador_da_api_usa_o_cliente_do_langfuse_com_mascaramento(monkeypatch):
    """RN30: a verificação registra no mesmo cliente da API, criado com o `mask`."""
    from economia.api import app as modulo_da_app
    from economia.api import dependencias
    from economia.verificacao import cli

    cliente_do_langfuse = object()
    recebido = {}

    def criar(configuracao, langfuse=None):
        recebido["langfuse"] = langfuse
        return "orquestrador"

    monkeypatch.setattr(modulo_da_app, "obter_langfuse", lambda: cliente_do_langfuse)
    monkeypatch.setattr(cli, "criar_verificar_alegacao", criar)
    dependencias.obter_verificar_alegacao.cache_clear()
    try:
        assert dependencias.obter_verificar_alegacao() == "orquestrador"
    finally:
        dependencias.obter_verificar_alegacao.cache_clear()

    assert recebido["langfuse"] is cliente_do_langfuse
