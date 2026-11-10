"""Testes da rota de saúde da API."""

from fastapi.testclient import TestClient

from economia.api.main import app

client = TestClient(app)


def test_healthcheck_retorna_status_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
