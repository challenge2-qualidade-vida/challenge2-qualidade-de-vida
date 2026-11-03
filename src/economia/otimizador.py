"""Otimizador da cesta: programação linear inteira com SciPy (milp).

Variável de decisão: quantas embalagens comprar de cada oferta
(produto × mercado). Objetivo: menor custo. Restrições: metas nutricionais,
frutas e hortaliças, variedade, restrições alimentares e orçamento.
"""

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .dados import Base, Preco, Produto, preco_por_kg
from .metas import (
    DIAS_POR_PERIODO,
    GRUPOS_PROTEINA_ANIMAL,
    LIMITE_FLV_POR_ALIMENTO,
    LIMITE_KCAL_POR_ALIMENTO,
    LIMITE_KCAL_POR_GRUPO,
    PROTEINA_ANIMAL_MINIMA,
    metas_totais,
    tags_excluidas,
)

NUTRIENTES = ("kcal", "proteina_g", "fibra_g")


@dataclass(frozen=True)
class Pedido:
    orcamento: float | None
    pessoas: int
    periodo: str = "mes"
    restricoes: tuple[str, ...] = ()
    # Alimentos que o usuário não quer nesta cesta (botão "Trocar").
    sem_alimentos: tuple[str, ...] = ()
    # O que já tem em casa: (alimento, gramas). Conta para as metas e não custa nada.
    em_casa: tuple[tuple[str, float], ...] = ()

    @property
    def dias(self) -> int:
        return DIAS_POR_PERIODO[self.periodo]


@dataclass
class ItemCesta:
    produto_id: str
    produto: str
    alimento_id: str
    alimento: str
    grupo: str
    mercado_id: str
    mercado: str
    quantidade: int
    preco_unitario: float
    subtotal: float
    preco_kg: float
    data_preco: str
    fonte_preco: str


@dataclass
class Cesta:
    mercados: tuple[str, ...]
    itens: list[ItemCesta]
    custo_total: float
    obtido: dict[str, float]
    metas: dict[str, float]
    dentro_do_orcamento: bool
    custo_por_mercado: dict[str, float] = field(default_factory=dict)
    # Parte de `obtido` que veio do que o usuário já tinha em casa.
    em_casa: dict[str, float] = field(default_factory=dict)

    def _comprado(self, nutriente: str) -> float:
        return self.obtido[nutriente] - self.em_casa.get(nutriente, 0)

    @property
    def custo_por_1000_kcal(self) -> float:
        return self.custo_total / self._comprado("kcal") * 1000 if self._comprado("kcal") > 0 else 0.0

    @property
    def custo_por_g_proteina(self) -> float:
        return self.custo_total / self._comprado("proteina_g") if self._comprado("proteina_g") > 0 else 0.0


def _nutrientes_em_casa(base: Base, pedido: Pedido, excluidas: set[str]) -> tuple[dict[str, float], float]:
    """Nutrientes do que já está em casa e o saldo de proteína animal (ver a meta de 20%)."""
    total = {n: 0.0 for n in NUTRIENTES} | {"flv_g": 0.0}
    saldo_animal = 0.0
    for alimento_id, g in pedido.em_casa:
        a = base.alimentos[alimento_id]
        if excluidas & set(a.tags):
            continue
        total["kcal"] += a.kcal * g / 100
        total["proteina_g"] += a.proteina_g * g / 100
        total["fibra_g"] += a.fibra_g * g / 100
        if a.grupo == "flv":
            total["flv_g"] += g
        saldo_animal += ((a.grupo in GRUPOS_PROTEINA_ANIMAL) - PROTEINA_ANIMAL_MINIMA) * a.proteina_g * g / 100
    return total, saldo_animal


def _ofertas(base: Base, mercados: tuple[str, ...], excluidas: set[str], sem_alimentos: tuple[str, ...] = ()) -> list[tuple[Produto, Preco]]:
    ofertas = []
    for pr in base.precos:
        if pr.mercado not in mercados:
            continue
        produto = base.produtos[pr.produto]
        if produto.alimento in sem_alimentos or excluidas & set(base.alimentos[produto.alimento].tags):
            continue
        ofertas.append((produto, pr))
    return ofertas


def montar_cesta(base: Base, pedido: Pedido, mercados: tuple[str, ...], respeitar_orcamento: bool = True) -> Cesta | None:
    """Cesta mais barata comprando só nos `mercados` dados. None se não houver solução."""
    if pedido.pessoas < 1:
        raise ValueError("pessoas deve ser pelo menos 1")
    metas = metas_totais(pedido.pessoas, pedido.dias)
    excluidas = tags_excluidas(list(pedido.restricoes))
    casa, saldo_animal = _nutrientes_em_casa(base, pedido, excluidas)
    ofertas = _ofertas(base, mercados, excluidas, pedido.sem_alimentos)
    if not ofertas:
        return None

    alimentos = [base.alimentos[p.alimento] for p, _ in ofertas]
    gramas = np.array([p.embalagem_g for p, _ in ofertas])
    custo = np.array([pr.preco for _, pr in ofertas])
    nutr = {
        "kcal": np.array([a.kcal for a in alimentos]) * gramas / 100,
        "proteina_g": np.array([a.proteina_g for a in alimentos]) * gramas / 100,
        "fibra_g": np.array([a.fibra_g for a in alimentos]) * gramas / 100,
    }
    flv = np.array([g if a.grupo == "flv" else 0.0 for a, g in zip(alimentos, gramas)])

    linhas, minimos, maximos = [], [], []

    def restringir(linha, minimo=-np.inf, maximo=np.inf):
        linhas.append(linha)
        minimos.append(minimo)
        maximos.append(maximo)

    for n in NUTRIENTES:
        restringir(nutr[n], minimo=metas[n] - casa[n])
    restringir(flv, minimo=metas["flv_g"] - casa["flv_g"])

    # Variedade. O limite nunca fica abaixo de uma embalagem, senão cestas
    # pequenas (1 pessoa, 1 semana) ficariam impossíveis de montar.
    for alimento_id in {a.id for a in alimentos}:
        mascara = np.array([a.id == alimento_id for a in alimentos], dtype=float)
        kcal_a = nutr["kcal"] * mascara
        restringir(kcal_a, maximo=max(LIMITE_KCAL_POR_ALIMENTO * metas["kcal"], kcal_a.max()))
        if flv[mascara > 0].any():
            flv_a = flv * mascara
            restringir(flv_a, maximo=max(LIMITE_FLV_POR_ALIMENTO * metas["flv_g"], flv_a.max()))

    for grupo, limite in LIMITE_KCAL_POR_GRUPO.items():
        mascara = np.array([a.grupo == grupo for a in alimentos], dtype=float)
        if mascara.any():
            kcal_g = nutr["kcal"] * mascara
            restringir(kcal_g, maximo=max(limite * metas["kcal"], kcal_g.max()))

    animal = np.array([a.grupo in GRUPOS_PROTEINA_ANIMAL for a in alimentos], dtype=float)
    if animal.any():
        # proteína animal ≥ 20% da proteína total  ⇔  Σ (animal − 0,2) × proteína × x ≥ 0
        restringir((animal - PROTEINA_ANIMAL_MINIMA) * nutr["proteina_g"], minimo=-saldo_animal)

    if respeitar_orcamento and pedido.orcamento is not None:
        restringir(custo, maximo=pedido.orcamento)

    res = milp(
        c=custo,
        constraints=LinearConstraint(np.array(linhas), minimos, maximos),
        integrality=np.ones(len(ofertas)),
        bounds=Bounds(0, 1000),
        options={"time_limit": 20},
    )
    if res.x is None or res.status not in (0, 1):
        return None

    qtd = np.round(res.x).astype(int)
    itens = []
    for (produto, pr), alimento, q in zip(ofertas, alimentos, qtd):
        if q == 0:
            continue
        itens.append(
            ItemCesta(
                produto_id=produto.id,
                produto=produto.nome,
                alimento_id=alimento.id,
                alimento=alimento.nome,
                grupo=alimento.grupo,
                mercado_id=pr.mercado,
                mercado=base.mercados[pr.mercado].nome,
                quantidade=int(q),
                preco_unitario=pr.preco,
                subtotal=round(pr.preco * q, 2),
                preco_kg=round(preco_por_kg(produto, pr), 2),
                data_preco=pr.data,
                fonte_preco=pr.fonte,
            )
        )
    itens.sort(key=lambda i: (i.mercado_id, i.grupo, i.produto))

    total = round(float(custo @ qtd), 2)
    obtido = {n: float(nutr[n] @ qtd) + casa[n] for n in NUTRIENTES}
    obtido["flv_g"] = float(flv @ qtd) + casa["flv_g"]
    por_mercado: dict[str, float] = {}
    for i in itens:
        por_mercado[i.mercado_id] = round(por_mercado.get(i.mercado_id, 0) + i.subtotal, 2)

    return Cesta(
        mercados=tuple(sorted(por_mercado)),
        itens=itens,
        custo_total=total,
        obtido=obtido,
        metas=metas,
        dentro_do_orcamento=pedido.orcamento is None or total <= pedido.orcamento + 1e-6,
        custo_por_mercado=por_mercado,
        em_casa=casa if pedido.em_casa else {},
    )
