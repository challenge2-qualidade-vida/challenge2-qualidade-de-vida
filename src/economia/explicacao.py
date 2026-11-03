"""Explica o plano em frases simples, sem LLM.

O texto sai direto dos números calculados, então não há como "alucinar".
O LLM (tópico 7) pode reescrever estas frases de forma mais conversada,
mas os fatos vêm daqui.
"""

from .dados import Base
from .metas import NOMES_RESTRICOES
from .planejador import Plano

NOMES_PERIODO = {"semana": "1 semana", "quinzena": "15 dias", "mes": "1 mês"}


def reais(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def data_br(iso: str) -> str:
    ano, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{ano}"


def _nome_curto(nome: str) -> str:
    return nome.split(" (")[0].lower()


def _nomes(base: Base, ids) -> str:
    nomes = [base.mercados[m].nome for m in ids]
    return " e ".join(nomes)


def _principais_fontes(cesta, nutriente: str, base: Base, n: int = 2) -> list[tuple[str, float]]:
    por_alimento: dict[str, float] = {}
    for item in cesta.itens:
        a = base.alimentos[item.alimento_id]
        valor = getattr(a, nutriente) * base.produtos[item.produto_id].embalagem_g / 100 * item.quantidade
        por_alimento[a.nome] = por_alimento.get(a.nome, 0) + valor
    total = sum(por_alimento.values())
    ordenados = sorted(por_alimento.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return [(nome, valor / total) for nome, valor in ordenados]


def explicar(plano: Plano, base: Base) -> list[str]:
    p = plano.pedido
    frases = []
    pessoas = f"{p.pessoas} pessoa" + ("s" if p.pessoas > 1 else "")
    contexto = f"Cesta para {pessoas} por {NOMES_PERIODO[p.periodo]}"
    if p.restricoes:
        contexto += " (" + ", ".join(NOMES_RESTRICOES[r].lower() for r in p.restricoes) + ")"
    frases.append(contexto + ".")
    if p.sem_alimentos:
        frases.append("Você pediu para trocar: " + ", ".join(_nome_curto(base.alimentos[a].nome) for a in p.sem_alimentos) + ". As metas continuam valendo.")
    if p.em_casa:
        frases.append("Já descontamos o que você tem em casa: " + ", ".join(f"{g / 1000:.1f} kg de {_nome_curto(base.alimentos[a].nome)}".replace(".", ",") for a, g in p.em_casa) + ".")

    if plano.recomendacao is None:
        if plano.minimo_necessario is None:
            frases.append("Não foi possível montar uma cesta com essas restrições e os produtos disponíveis.")
        else:
            frases.append(
                f"Com {reais(p.orcamento)} não dá para cumprir as metas nutricionais. "
                f"A cesta mínima que cumpre as metas custa {reais(plano.minimo_necessario)}. "
                "Você pode reduzir o período, ou rever as restrições."
                + (" Os alimentos que você pediu para trocar também podem voltar." if p.sem_alimentos else "")
            )
        return frases

    if not plano.cesta_recomendada.itens:
        frases.append("O que você tem em casa já cumpre as metas para esse período: não precisa comprar nada.")
        return frases

    um, dois = plano.um_mercado, plano.dois_mercados
    if um:
        frases.append(f"A cesta mais barata em um só mercado é no {_nomes(base, um.mercados)}: {reais(um.custo_total)}.")
    if dois:
        texto = f"Dividindo entre {_nomes(base, dois.mercados)}, sai por {reais(dois.custo_total)}"
        if um:
            texto += f" ({reais(plano.economia_bruta_dois)} a menos)"
            if plano.custo_deslocamento > 0:
                texto += f". Com {reais(plano.custo_deslocamento)} de deslocamento, a economia real é de {reais(plano.economia_liquida_dois)}"
            texto += ": compensa ir aos dois." if plano.recomendacao == "dois" else ": não compensa ir a dois lugares."
        else:
            texto += "."
        frases.append(texto)

    cesta = plano.cesta_recomendada
    if p.orcamento is not None:
        sobra = p.orcamento - cesta.custo_total - (plano.custo_deslocamento if plano.recomendacao == "dois" else 0)
        frases.append(f"Sobram {reais(sobra)} do seu orçamento de {reais(p.orcamento)}.")

    fontes = _principais_fontes(cesta, "proteina_g", base)
    frases.append(
        "A proteína vem principalmente de "
        + " e ".join(f"{_nome_curto(nome)} ({pct:.0%})" for nome, pct in fontes)
        + ", as opções com menor custo por grama de proteína nos preços disponíveis."
    )
    frases.append(
        f"Custo por 1.000 kcal: {reais(cesta.custo_por_1000_kcal)}. "
        f"Custo por grama de proteína: {reais(cesta.custo_por_g_proteina)}."
    )

    datas = sorted({i.data_preco for i in cesta.itens})
    fontes_preco = sorted({i.fonte_preco for i in cesta.itens})
    aviso = f"Preços de {', '.join(data_br(d) for d in datas)} (fonte: {', '.join(fontes_preco)})."
    if "exemplo" in fontes_preco:
        aviso += " Atenção: são preços de exemplo, não preços reais."
    frases.append(aviso)
    frases.append(
        "As metas consideram todas as pessoas como adultos (2.000 kcal por dia). "
        "É uma orientação para alimentação equilibrada da população geral e não substitui um nutricionista."
    )
    return frases
