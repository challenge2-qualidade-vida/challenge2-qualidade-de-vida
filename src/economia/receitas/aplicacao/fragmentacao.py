"""Divisão das receitas e dos textos de orientação em trechos (chunking).

Regras (ver docs/semana-2/estrategia-rag.md):
- uma receita é um trecho, com título e ingredientes antes do modo de preparo;
- um documento de orientação é dividido por seção e, dentro dela, por parágrafo,
  em trechos de até `limite` tokens, com `sobreposicao` tokens repetidos entre trechos
  seguidos. Um trecho nunca junta duas seções.

A contagem de tokens é injetada: a infraestrutura passa o tokenizador do modelo de embeddings.
"""

from collections.abc import Callable

from economia.receitas.dominio.modelos import (
    Documento,
    Receita,
    Secao,
    TipoDeTrecho,
    Trecho,
)

ContadorDeTokens = Callable[[str], int]

LIMITE_DA_RECEITA = 512
LIMITE_DO_TRECHO = 350
SOBREPOSICAO = 50


def contar_palavras(texto: str) -> int:
    """Contador aproximado: uma palavra por token. Usado nos testes e como padrão."""
    return len(texto.split())


def _cortar(texto: str, limite: int, contar: ContadorDeTokens) -> str:
    """Corta o fim do texto, palavra por palavra, até caber no limite."""
    if contar(texto) <= limite:
        return texto
    palavras = texto.split()
    # busca binária pelo maior prefixo que cabe
    menor, maior = 0, len(palavras)
    while menor < maior:
        meio = (menor + maior + 1) // 2
        if contar(" ".join(palavras[:meio])) <= limite:
            menor = meio
        else:
            maior = meio - 1
    return " ".join(palavras[:menor])


def texto_da_receita(
    receita: Receita,
    limite: int = LIMITE_DA_RECEITA,
    contar: ContadorDeTokens = contar_palavras,
) -> str:
    """Texto que vira embedding: título e ingredientes primeiro; o corte pega o modo de preparo."""
    ingredientes = "; ".join(i.texto.strip() for i in receita.ingredientes)
    preparo = " ".join(p.strip() for p in receita.modo_de_preparo if p.strip())
    texto = f"Receita: {receita.titulo.strip()}. Ingredientes: {ingredientes}. Modo de preparo: {preparo}"
    return _cortar(texto, limite, contar)


def fragmentar_receita(
    receita: Receita,
    limite: int = LIMITE_DA_RECEITA,
    contar: ContadorDeTokens = contar_palavras,
) -> Trecho:
    """Uma receita vira um trecho. O texto completo fica em `conteudo`."""
    if not receita.esta_completa:
        raise ValueError(
            f"Receita sem ingredientes ou modo de preparo: {receita.documento_id}"
        )
    linhas = [f"# {receita.titulo.strip()}", "", "Ingredientes:"]
    linhas += [f"- {i.texto.strip()}" for i in receita.ingredientes]
    linhas += ["", "Modo de preparo:"]
    linhas += [p.strip() for p in receita.modo_de_preparo if p.strip()]
    return Trecho(
        id=receita.documento_id,
        tipo=TipoDeTrecho.RECEITA,
        documento_id=receita.documento_id,
        titulo=receita.titulo.strip(),
        texto=texto_da_receita(receita, limite, contar),
        conteudo="\n".join(linhas),
        fonte=receita.fonte,
        idioma=receita.idioma,
        ingredientes=tuple((i.nome or i.texto).strip() for i in receita.ingredientes),
    )


def _cauda(texto: str, tokens: int, contar: ContadorDeTokens) -> str:
    """Últimas palavras do texto que somam até `tokens` tokens (a sobreposição)."""
    if tokens <= 0:
        return ""
    palavras = texto.split()
    inicio = len(palavras)
    while inicio > 0 and contar(" ".join(palavras[inicio - 1 :])) <= tokens:
        inicio -= 1
    return " ".join(palavras[inicio:])


def _dividir_paragrafo_longo(
    paragrafo: str, limite: int, sobreposicao: int, contar: ContadorDeTokens
) -> list[str]:
    """Divide um parágrafo maior que o limite em janelas de palavras com sobreposição."""
    partes: list[str] = []
    resto = paragrafo
    while contar(resto) > limite:
        # uma palavra maior que o limite entra sozinha, para a divisão sempre avançar
        parte = _cortar(resto, limite, contar) or resto.split()[0]
        partes.append(parte)
        cauda = _cauda(parte, sobreposicao, contar)
        if len(cauda.split()) >= len(parte.split()):
            # a cauda repetiria a parte inteira e a divisão não avançaria
            cauda = ""
        sobra = resto.split()[len(parte.split()) :]
        resto = " ".join(([cauda] if cauda else []) + sobra)
    partes.append(resto)
    return partes


def _textos_da_secao(
    secao: Secao, limite: int, sobreposicao: int, contar: ContadorDeTokens
) -> list[str]:
    """Junta parágrafos seguidos até o limite. Cada trecho novo começa com a cauda do anterior."""
    paragrafos: list[str] = []
    for paragrafo in (p.strip() for p in secao.paragrafos):
        if paragrafo:
            paragrafos += _dividir_paragrafo_longo(
                paragrafo, limite, sobreposicao, contar
            )

    textos: list[str] = []
    atual = ""
    for paragrafo in paragrafos:
        candidato = f"{atual}\n\n{paragrafo}" if atual else paragrafo
        if contar(candidato) <= limite:
            atual = candidato
            continue
        textos.append(atual)
        cauda = _cauda(atual, sobreposicao, contar)
        candidato = f"{cauda}\n\n{paragrafo}" if cauda else paragrafo
        # se a cauda não couber junto, o parágrafo entra sozinho
        atual = candidato if contar(candidato) <= limite else paragrafo
    if atual:
        textos.append(atual)
    return textos


def fragmentar_documento(
    documento: Documento,
    limite: int = LIMITE_DO_TRECHO,
    sobreposicao: int = SOBREPOSICAO,
    contar: ContadorDeTokens = contar_palavras,
) -> list[Trecho]:
    """Divide o documento por seção e por parágrafo, em trechos de até `limite` tokens."""
    if sobreposicao >= limite:
        raise ValueError("A sobreposição precisa ser menor que o limite do trecho.")
    trechos: list[Trecho] = []
    for n_secao, secao in enumerate(documento.secoes):
        for n_parte, texto in enumerate(
            _textos_da_secao(secao, limite, sobreposicao, contar)
        ):
            trechos.append(
                Trecho(
                    id=f"{documento.documento_id}:{n_secao}:{n_parte}",
                    tipo=TipoDeTrecho.CONHECIMENTO,
                    documento_id=documento.documento_id,
                    titulo=documento.titulo,
                    texto=texto,
                    conteudo=texto,
                    fonte=documento.fonte,
                    idioma=documento.idioma,
                    capitulo=secao.capitulo,
                    secao=secao.titulo,
                    pagina=secao.pagina,
                )
            )
    return trechos
