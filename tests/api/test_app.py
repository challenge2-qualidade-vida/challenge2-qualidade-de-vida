from fastapi.testclient import TestClient

from economia.api.app import app, obter_caso_de_uso, para_a_api
from economia.receitas.dominio.modelos import (
    Fonte,
    RespostaComFontes,
    TipoDeTrecho,
    Trecho,
    TrechoRecuperado,
)


def receita(id, titulo):
    return Trecho(
        id=id,
        tipo=TipoDeTrecho.RECEITA,
        documento_id=id,
        titulo=titulo,
        texto="t",
        conteudo="c",
        fonte=Fonte(titulo="afrodite.json", instituicao="GitHub", url="https://ex.org"),
        ingredientes=("ovo", "farinha"),
    )


def test_saude():
    assert TestClient(app).get("/saude").json() == {"status": "ok"}


def test_para_a_api_numera_as_fontes_e_traz_o_que_falta():
    a, b = receita("a", "Omelete"), receita("b", "Bolo")
    resposta = RespostaComFontes(
        texto="Faça a omelete [1] ou o bolo [2].",
        encontrou=True,
        trechos=(TrechoRecuperado(a, 0.9), TrechoRecuperado(b, 0.88)),
        fontes=(a.fonte,),
        ingredientes_disponiveis=("ovo",),
        faltando=(("a", ()), ("b", ("farinha",))),
    )
    saida = para_a_api(resposta, 2.345)
    assert [(f.numero, f.titulo, f.tipo) for f in saida.fontes] == [
        (1, "Omelete", "receita"),
        (2, "Bolo", "receita"),
    ]
    assert saida.fontes[0].descricao.startswith("Omelete. afrodite.json")
    assert [(f.receita, f.ingredientes) for f in saida.faltando] == [
        ("Omelete", []),
        ("Bolo", ["farinha"]),
    ]
    assert saida.ingredientes_disponiveis == ["ovo"]
    assert saida.segundos == 2.3


def test_pergunta_longa_demais_e_recusada():
    class Caso:
        def responder(self, pergunta):  # pragma: no cover - não deve ser chamado
            raise AssertionError

    app.dependency_overrides[obter_caso_de_uso] = Caso
    try:
        r = TestClient(app).post(
            "/api/v1/receitas/perguntas", json={"pergunta": "x" * 501}
        )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_pergunta_chega_sem_espacos_nas_pontas():
    recebidas = []

    class Caso:
        def responder(self, pergunta):
            recebidas.append(pergunta)
            return RespostaComFontes(texto="Não encontrei.", encontrou=False)

    app.dependency_overrides[obter_caso_de_uso] = Caso
    try:
        r = TestClient(app).post(
            "/api/v1/receitas/perguntas", json={"pergunta": "  arroz?  "}
        )
        assert r.status_code == 200
        assert recebidas == ["arroz?"]
    finally:
        app.dependency_overrides.clear()


def test_para_a_api_traz_os_trechos_recuperados_com_score_e_fonte():
    a, b = receita("a", "Omelete"), receita("b", "Bolo")
    resposta = RespostaComFontes(
        texto="Faça o bolo [1].",
        encontrou=True,
        trechos=(TrechoRecuperado(b, 0.88),),
        fontes=(b.fonte,),
        recuperados=(TrechoRecuperado(a, 0.9), TrechoRecuperado(b, 0.88)),
    )
    saida = para_a_api(resposta, 1.0, limiar=0.885)
    assert [
        (t.posicao, t.titulo, t.score, t.acima_do_limiar, t.fonte)
        for t in saida.trechos_recuperados
    ] == [
        (1, "Omelete", 0.9, True, None),
        (2, "Bolo", 0.88, False, 1),
    ]
    assert saida.limiar == 0.885
    assert saida.trechos_recuperados[0].origem == "afrodite.json"


def test_resumo_do_trecho_e_curto_e_corta_na_palavra():
    from economia.api.app import TAMANHO_DO_RESUMO, _resumo

    assert _resumo("  arroz   e\nfeijão ") == "arroz e feijão"
    longo = _resumo("palavra " * 100)
    assert len(longo) <= TAMANHO_DO_RESUMO + 1
    assert longo.endswith("palavra…")
