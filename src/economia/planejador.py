"""Compara comprar em um só mercado com dividir a compra entre dois.

Roda o otimizador para cada mercado e para cada par de mercados e decide
se a economia de ir a dois lugares paga o custo do deslocamento.
"""

from dataclasses import dataclass, field, replace
from itertools import combinations

from .dados import Base
from .otimizador import Cesta, Pedido, montar_cesta


@dataclass
class Plano:
    pedido: Pedido
    custo_deslocamento: float
    cestas_por_mercado: dict[str, Cesta | None]
    um_mercado: Cesta | None
    dois_mercados: Cesta | None
    recomendacao: str | None          # "um", "dois" ou None (sem solução)
    minimo_necessario: float | None = None
    avisos: list[str] = field(default_factory=list)

    @property
    def cesta_recomendada(self) -> Cesta | None:
        return self.dois_mercados if self.recomendacao == "dois" else self.um_mercado

    @property
    def economia_bruta_dois(self) -> float:
        """Quanto a cesta em dois mercados custa a menos, antes do deslocamento."""
        if not (self.um_mercado and self.dois_mercados):
            return 0.0
        return round(self.um_mercado.custo_total - self.dois_mercados.custo_total, 2)

    @property
    def economia_liquida_dois(self) -> float:
        return round(self.economia_bruta_dois - self.custo_deslocamento, 2)


def _mais_barata(cestas) -> Cesta | None:
    validas = [c for c in cestas if c is not None]
    return min(validas, key=lambda c: c.custo_total, default=None)


def planejar(base: Base, pedido: Pedido, custo_deslocamento: float = 0.0, mercados: list[str] | None = None) -> Plano:
    """`mercados` limita a comparação (ex.: só os mercados perto do usuário). None = todos."""
    mercados = sorted(m for m in (mercados or base.mercados) if m in base.mercados)

    por_mercado = {m: montar_cesta(base, pedido, (m,)) for m in mercados}
    um = _mais_barata(por_mercado.values())

    # Na opção de dois mercados, o deslocamento sai do mesmo orçamento.
    pedido_par = pedido
    if pedido.orcamento is not None:
        pedido_par = replace(pedido, orcamento=pedido.orcamento - custo_deslocamento)
    pares = []
    if pedido_par.orcamento is None or pedido_par.orcamento > 0:
        pares = [montar_cesta(base, pedido_par, par) for par in combinations(mercados, 2)]
    # Só conta como "dois mercados" se a solução usa de fato os dois.
    dois = _mais_barata(c for c in pares if c is not None and len(c.mercados) == 2)

    if um is None and dois is None:
        # Mínimo real: um mercado só, ou dois mercados mais o deslocamento.
        opcoes = [c.custo_total for m in mercados if (c := montar_cesta(base, pedido, (m,), respeitar_orcamento=False))]
        opcoes += [
            c.custo_total + custo_deslocamento
            for par in combinations(mercados, 2)
            if (c := montar_cesta(base, pedido, par, respeitar_orcamento=False)) and len(c.mercados) == 2
        ]
        return Plano(
            pedido=pedido,
            custo_deslocamento=custo_deslocamento,
            cestas_por_mercado=por_mercado,
            um_mercado=None,
            dois_mercados=None,
            recomendacao=None,
            minimo_necessario=round(min(opcoes), 2) if opcoes else None,
        )

    if um is None:
        recomendacao = "dois"
    elif dois is None or dois.custo_total + custo_deslocamento >= um.custo_total - 0.005:
        recomendacao = "um"
    else:
        recomendacao = "dois"

    return Plano(
        pedido=pedido,
        custo_deslocamento=custo_deslocamento,
        cestas_por_mercado=por_mercado,
        um_mercado=um,
        dois_mercados=dois,
        recomendacao=recomendacao,
    )
