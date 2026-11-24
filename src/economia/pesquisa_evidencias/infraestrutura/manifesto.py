"""Carregamento do manifesto de fontes da pesquisa de evidências."""

import json
from pathlib import Path
from typing import Any


def carregar_manifesto(
    caminho: Path,
) -> dict[str, dict[str, Any]]:
    """Carrega as fontes científicas indexadas pelo caminho relativo."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))

    return {fonte["arquivo"]: fonte for fonte in dados.get("fontes", [])}
