"""Fragmentação de documentos científicos em trechos recuperáveis."""

from collections.abc import Callable, Sequence

from economia.pesquisa_evidencias.dominio.modelos import TrechoEvidencia

LIMITE_TOKENS_TRECHO = 450
OVERLAP_TOKENS_TRECHO = 60


def _texto_das_partes(partes: list[tuple[int, str]]) -> str:
    """Reúne as partes de um trecho preservando a separação entre elas."""
    return "\n\n".join(texto for _, texto in partes)


def _maior_quantidade_que_cabe(maximo: int, cabe: Callable[[int], bool]) -> int:
    """Maior n em [0, maximo] com `cabe(n)`, supondo que `cabe` é monotônica.

    Dobra o passo até passar do limite e depois faz busca binária. Assim, cada
    trecho custa O(log n) contagens de tokens, e não uma contagem por palavra.
    """
    if maximo <= 0 or not cabe(1):
        return 0

    baixo, passo = 1, 1
    while baixo < maximo:
        alto = min(maximo, baixo + passo)
        if not cabe(alto):
            break
        baixo, passo = alto, passo * 2
    else:
        return baixo

    # `baixo` cabe e `alto` não cabe.
    while alto - baixo > 1:
        meio = (baixo + alto) // 2
        if cabe(meio):
            baixo = meio
        else:
            alto = meio

    return baixo


def dividir_paragrafo(
    paragrafo: str,
    contar_tokens: Callable[[str], int],
    limite_tokens: int,
) -> list[str]:
    """Divide um parágrafo longo em partes que respeitam o limite de tokens."""
    palavras = paragrafo.split()
    partes: list[str] = []
    inicio = 0

    while inicio < len(palavras):

        def cabe(quantidade: int, inicio: int = inicio) -> bool:
            texto = " ".join(palavras[inicio : inicio + quantidade])
            return contar_tokens(texto) <= limite_tokens

        quantidade = _maior_quantidade_que_cabe(len(palavras) - inicio, cabe)

        if quantidade == 0:
            raise ValueError("Uma palavra isolada ultrapassa o limite de tokens.")

        partes.append(" ".join(palavras[inicio : inicio + quantidade]))
        inicio += quantidade

    return partes


def _obter_overlap(
    partes: list[tuple[int, str]],
    contar_tokens: Callable[[str], int],
    limite_overlap: int,
) -> list[tuple[int, str]]:
    """Recupera palavras do final do trecho, preservando suas páginas."""
    if limite_overlap <= 0:
        return []

    palavras_reversas: list[tuple[int, str]] = []

    for numero_pagina, texto in reversed(partes):
        for palavra in reversed(texto.split()):
            palavras_reversas.append((numero_pagina, palavra))

    def cabe(quantidade: int) -> bool:
        ultimas = reversed(palavras_reversas[:quantidade])
        return contar_tokens(" ".join(p for _, p in ultimas)) <= limite_overlap

    quantidade = _maior_quantidade_que_cabe(len(palavras_reversas), cabe)
    selecionadas = list(reversed(palavras_reversas[:quantidade]))

    # Agrupa palavras consecutivas da mesma página.
    resultado: list[tuple[int, str]] = []

    for numero_pagina, palavra in selecionadas:
        if resultado and resultado[-1][0] == numero_pagina:
            pagina, texto = resultado[-1]
            resultado[-1] = (pagina, f"{texto} {palavra}")
        else:
            resultado.append((numero_pagina, palavra))

    return resultado


def _reduzir_overlap(
    partes: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """Remove a primeira palavra do overlap para liberar espaço."""
    if not partes:
        return []

    numero_pagina, texto = partes[0]
    palavras = texto.split()

    if len(palavras) > 1:
        partes[0] = (numero_pagina, " ".join(palavras[1:]))
    else:
        partes.pop(0)

    return partes


def fragmentar_documento(
    paginas: Sequence[dict[str, str | int]],
    documento_id: str,
    contar_tokens: Callable[[str], int],
    limite_tokens: int = LIMITE_TOKENS_TRECHO,
    overlap_tokens: int | None = None,
) -> list[TrechoEvidencia]:
    """Fragmenta páginas em trechos, preservando origem e contexto."""
    if not documento_id.strip():
        raise ValueError("O documento precisa de identificador.")

    if limite_tokens < 1:
        raise ValueError("O limite de tokens precisa ser positivo.")

    # Quando não informado, o overlap padrão se adapta ao limite escolhido.
    if overlap_tokens is None:
        overlap_tokens = min(OVERLAP_TOKENS_TRECHO, limite_tokens - 1)

    if (
        not isinstance(overlap_tokens, int)
        or isinstance(overlap_tokens, bool)
        or overlap_tokens < 0
        or overlap_tokens >= limite_tokens
    ):
        raise ValueError(
            "O overlap precisa ser um inteiro maior ou igual a zero "
            "e menor que o limite de tokens."
        )

    paragrafos: list[tuple[int, str]] = []

    for pagina in paginas:
        numero = pagina["pagina"]
        texto = str(pagina["texto"])

        if not isinstance(numero, int) or isinstance(numero, bool) or numero < 1:
            raise ValueError("O número da página precisa ser positivo.")

        for paragrafo in texto.split("\n\n"):
            paragrafo = paragrafo.strip()

            if not paragrafo:
                continue

            if contar_tokens(paragrafo) > limite_tokens:
                partes = dividir_paragrafo(
                    paragrafo=paragrafo,
                    contar_tokens=contar_tokens,
                    limite_tokens=limite_tokens,
                )
            else:
                partes = [paragrafo]

            paragrafos.extend((numero, parte) for parte in partes)

    trechos: list[TrechoEvidencia] = []
    partes_atuais: list[tuple[int, str]] = []

    def salvar_trecho() -> None:
        if not partes_atuais:
            return

        numero_trecho = len(trechos) + 1

        trechos.append(
            TrechoEvidencia(
                id=f"{documento_id}_t{numero_trecho:04d}",
                documento_id=documento_id,
                texto=_texto_das_partes(partes_atuais),
                pagina_inicial=partes_atuais[0][0],
                pagina_final=partes_atuais[-1][0],
            )
        )

        partes_atuais.clear()

    for numero_pagina, paragrafo in paragrafos:
        candidato = partes_atuais + [(numero_pagina, paragrafo)]

        if (
            partes_atuais
            and contar_tokens(_texto_das_partes(candidato)) > limite_tokens
        ):
            overlap = _obter_overlap(
                partes=partes_atuais,
                contar_tokens=contar_tokens,
                limite_overlap=overlap_tokens,
            )

            salvar_trecho()

            # Ajusta o overlap caso não exista espaço suficiente
            # para combinar o contexto anterior com o conteúdo novo.
            while overlap:
                candidato_com_overlap = overlap + [(numero_pagina, paragrafo)]

                if (
                    contar_tokens(_texto_das_partes(candidato_com_overlap))
                    <= limite_tokens
                ):
                    break

                overlap = _reduzir_overlap(overlap)

            partes_atuais.extend(overlap)
            partes_atuais.append((numero_pagina, paragrafo))
        else:
            partes_atuais.append((numero_pagina, paragrafo))

    salvar_trecho()

    return trechos
