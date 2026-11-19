"""Ponto de entrada da API EconoMIA (Dockerfile e README). A aplicação fica em `app.py`."""

from economia.api.app import app

__all__ = ["app"]
