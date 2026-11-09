"""Normalização conservadora do texto extraído."""

import re


def normalizar_texto(texto: str) -> str:
    """Remove espaços redundantes sem juntar parágrafos."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")

    linhas = [
        re.sub(r"[ \t]+", " ", linha).strip()
        for linha in texto.split("\n")
    ]

    texto = "\n".join(linhas)
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()
