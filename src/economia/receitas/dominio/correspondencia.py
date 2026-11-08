"""Contagem determinística dos ingredientes que faltam numa receita (RN01, RN13).

A versão 1 compara texto normalizado: minúsculas, sem acento e singular simples.
A correspondência completa pelo `Alimento` do catálogo e as substituições (RN28) ficam para depois.
"""

import re
import unicodedata
from collections.abc import Iterable, Sequence

_PALAVRA = re.compile(r"[a-z]+")


def _singular_pt(palavra: str) -> str:
    for plural, singular in (
        ("oes", "ao"),
        ("aes", "ao"),
        ("ais", "al"),
        ("eis", "el"),
        ("ns", "m"),
    ):
        if palavra.endswith(plural) and len(palavra) > len(plural):
            return palavra[: -len(plural)] + singular
    if re.search(r"(r|z|s)es$", palavra) and len(palavra) > 4:
        return palavra[:-2]  # colheres → colher, nozes → noz
    if palavra.endswith("s") and len(palavra) > 3:
        return palavra[:-1]
    return palavra


def _singular_en(palavra: str) -> str:
    if palavra.endswith("ies") and len(palavra) > 4:
        return palavra[:-3] + "y"  # berries → berry
    if re.search(r"(o|s|x|ch|sh)es$", palavra) and len(palavra) > 4:
        return palavra[:-2]  # tomatoes → tomato
    if palavra.endswith("s") and not palavra.endswith("ss") and len(palavra) > 3:
        return palavra[:-1]
    return palavra


def normalizar(texto: str, idioma: str = "pt") -> tuple[str, ...]:
    """Palavras do texto em minúsculas, sem acento e no singular."""
    sem_acento = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    )
    singular = _singular_en if idioma == "en" else _singular_pt
    return tuple(singular(p) for p in _PALAVRA.findall(sem_acento))


def _contem(palavras: Sequence[str], procuradas: Sequence[str]) -> bool:
    """`procuradas` aparece em sequência dentro de `palavras`."""
    tamanho = len(procuradas)
    if tamanho == 0:
        return False
    return any(
        tuple(palavras[n : n + tamanho]) == tuple(procuradas)
        for n in range(len(palavras) - tamanho + 1)
    )


def ingredientes_que_faltam(
    ingredientes: Iterable[str],
    disponiveis: Iterable[str],
    basicos: Iterable[str] = (),
    idioma: str = "pt",
) -> list[str]:
    """Ingredientes da receita que não estão entre os disponíveis nem entre os básicos.

    Um ingrediente conta como disponível quando o nome de um item disponível aparece nele
    ("farinha" está em "2 xícaras de farinha de trigo").
    """
    procurados = [normalizar(d, idioma) for d in (*disponiveis, *basicos)]
    procurados = [p for p in procurados if p]
    faltam = []
    for ingrediente in ingredientes:
        palavras = normalizar(ingrediente, idioma)
        if not any(_contem(palavras, p) for p in procurados):
            faltam.append(ingrediente)
    return faltam
