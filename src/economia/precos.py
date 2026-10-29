"""Consulta de preços e avaliação de promoções. Contas determinísticas.

São as ferramentas que o LLM chama quando a pergunta envolve preço: ele
nunca calcula nem inventa valores sozinho.
"""

from .dados import Base, preco_por_kg
from .rag import tokenizar


def encontrar_produtos(base: Base, termo: str) -> list[str]:
    """Ids dos produtos cujo nome (ou nome do alimento) contém todas as palavras do termo."""
    palavras = tokenizar(termo)
    if not palavras:
        return []
    achados = []
    for p in base.produtos.values():
        alvo = " ".join(tokenizar(p.nome + " " + base.alimentos[p.alimento].nome))
        if all(w in alvo for w in palavras):
            achados.append(p.id)
    return achados


def consultar_precos(base: Base, termo: str) -> dict:
    ids = encontrar_produtos(base, termo)
    produtos = []
    for pid in ids:
        produto = base.produtos[pid]
        ofertas = [
            {
                "mercado": base.mercados[pr.mercado].nome,
                "preco": pr.preco,
                "preco_kg": round(preco_por_kg(produto, pr), 2),
                "data": pr.data,
                "fonte": pr.fonte,
            }
            for pr in base.precos
            if pr.produto == pid
        ]
        ofertas.sort(key=lambda o: o["preco_kg"])
        produtos.append({"produto": produto.nome, "embalagem_g": produto.embalagem_g, "ofertas": ofertas})
    return {"termo": termo, "encontrados": len(produtos), "produtos": produtos}


def avaliar_promocao(base: Base, termo: str, preco: float, embalagem_g: float | None = None) -> dict:
    """Compara o preço por kg da promoção com o menor preço por kg normal do mesmo alimento."""
    ids = encontrar_produtos(base, termo)
    if not ids:
        return {"conclusao": "sem_dados", "mensagem": f"Não há preços de '{termo}' na base para comparar."}

    alimento = base.produtos[ids[0]].alimento
    if embalagem_g is None:
        embalagem_g = base.produtos[ids[0]].embalagem_g
    if preco <= 0 or embalagem_g <= 0:
        return {"conclusao": "invalido", "mensagem": "Preço e embalagem precisam ser maiores que zero."}

    preco_kg_promo = preco / embalagem_g * 1000
    referencias = [
        (preco_por_kg(base.produtos[pr.produto], pr), pr)
        for pr in base.precos
        if base.produtos[pr.produto].alimento == alimento
    ]
    melhor_kg, melhor = min(referencias, key=lambda r: r[0])
    diferenca = (preco_kg_promo - melhor_kg) / melhor_kg

    if diferenca <= -0.02:
        conclusao = "vale_a_pena"
    elif diferenca < 0.02:
        conclusao = "empate"
    else:
        conclusao = "nao_vale"

    return {
        "conclusao": conclusao,
        "alimento": base.alimentos[alimento].nome,
        "preco_kg_promocao": round(preco_kg_promo, 2),
        "melhor_preco_kg_normal": round(melhor_kg, 2),
        "melhor_oferta_normal": {
            "produto": base.produtos[melhor.produto].nome,
            "mercado": base.mercados[melhor.mercado].nome,
            "preco": melhor.preco,
            "data": melhor.data,
            "fonte": melhor.fonte,
        },
        "diferenca_percentual": round(diferenca * 100, 1),
        "lembrete": "Só é economia se o produto for necessário e der para consumir antes da validade.",
    }

