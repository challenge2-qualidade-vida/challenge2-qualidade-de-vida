from fastapi.testclient import TestClient

from economia import api
from economia.limites import Limitador


def test_bloqueia_acima_do_limite_e_libera_depois_da_janela():
    agora = [0.0]
    lim = Limitador({"/x": 2}, janela_s=60, relogio=lambda: agora[0])
    assert lim.permitir("1.1.1.1", "/x") and lim.permitir("1.1.1.1", "/x")
    assert not lim.permitir("1.1.1.1", "/x")
    assert lim.permitir("2.2.2.2", "/x")
    agora[0] = 61
    assert lim.permitir("1.1.1.1", "/x")


def test_rota_sem_limite_sempre_passa():
    lim = Limitador({"/x": 1})
    assert all(lim.permitir("1.1.1.1", "/y") for _ in range(100))


def test_api_responde_429_em_portugues(monkeypatch):
    monkeypatch.setattr(api, "limitador", Limitador({"/api/chat": 1}))
    cliente = TestClient(api.app)
    assert cliente.post("/api/chat", json={"mensagem": "oi"}).status_code == 200
    r = cliente.post("/api/chat", json={"mensagem": "oi"})
    assert r.status_code == 429
    assert "Muitas tentativas" in r.json()["detail"]
    assert cliente.get("/api/saude").status_code == 200
