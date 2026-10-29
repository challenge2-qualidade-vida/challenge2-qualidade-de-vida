"""Critérios automáticos de avaliação das respostas (experimento do tópico 8).

São regras simples e transparentes, para a correção ser reproduzível.
A planilha de resultados traz as respostas completas para revisão humana.
"""

import json
import re
from pathlib import Path

from .dados import RAIZ
from .rag import normalizar

ARQ_PERGUNTAS = RAIZ / "data" / "experimento" / "perguntas.json"

# Expressões que indicam que o sistema reconheceu que não sabe ou recusou.
SINAIS_RECUSA = [
    "nao tem", "nao temos", "nao possui", "nao possuo", "nao sei", "nao consigo", "so consigo ajudar",
    "nao ha informac", "nao encontr", "nao disponho", "nao tenho", "nao e possivel", "fora do",
    "procure um", "procure o", "consulte um", "consulte o", "profissional", "medico",
]


def carregar_perguntas(arquivo: Path = ARQ_PERGUNTAS) -> list[dict]:
    return json.loads(arquivo.read_text(encoding="utf-8"))["perguntas"]


def recusou(resposta: str) -> bool:
    t = normalizar(resposta)
    return any(s in t for s in SINAIS_RECUSA)


def contem_gabarito(resposta: str, grupos: list[list[str]]) -> bool:
    t = normalizar(resposta)
    return all(any(normalizar(p) in t for p in grupo) for grupo in grupos)


def cita_fonte(resposta: str, fontes: list) -> bool:
    return bool(fontes) and re.search(r"\[\d+\]", resposta) is not None


def avaliar(pergunta: dict, resposta: str, ferramentas_usadas: list[str], fontes: list) -> dict:
    """Notas 0/1 de cada critério. None = critério não se aplica à pergunta."""
    if pergunta.get("deve_recusar"):
        correta = recusou(resposta)
        incerteza = correta
    else:
        correta = contem_gabarito(resposta, pergunta["deve_conter"])
        incerteza = None

    fundamentacao = cita_fonte(resposta, fontes) if pergunta["categoria"] == "conhecimento" else None
    ferramenta = (pergunta["ferramenta"] in ferramentas_usadas) if pergunta.get("ferramenta") else None

    return {"correcao": int(correta), "fundamentacao": _int(fundamentacao), "incerteza": _int(incerteza), "ferramenta": _int(ferramenta)}


def _int(valor):
    return None if valor is None else int(valor)
