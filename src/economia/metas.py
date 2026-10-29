"""Metas nutricionais, limites de variedade e restrições alimentares.

Cada número aqui tem uma fonte (ver docs/desenvolvimento/02-otimizador.md).
Os que são escolha do grupo estão marcados como "parâmetro do grupo".
"""

DIAS_POR_PERIODO = {"semana": 7, "quinzena": 15, "mes": 30}

# Valores diários de referência para adultos (ANVISA, IN nº 75/2020).
META_DIARIA_POR_PESSOA = {"kcal": 2000, "proteina_g": 50, "fibra_g": 25}

# Frutas, legumes e verduras: pelo menos 400 g por dia (OMS).
FLV_G_POR_PESSOA_DIA = 400

# Variedade (parâmetros do grupo): nenhum alimento passa de 25% da energia
# e nenhuma fruta/hortaliça passa de 40% da meta de FLV.
LIMITE_KCAL_POR_ALIMENTO = 0.25
LIMITE_FLV_POR_ALIMENTO = 0.40

# Açúcar: menos de 10% da energia (OMS, açúcares livres).
# Óleos: 10% (parâmetro do grupo; o Guia Alimentar pede "pequenas quantidades").
LIMITE_KCAL_POR_GRUPO = {"acucar": 0.10, "oleos": 0.10}

# Restrição escolhida pelo usuário → tags dos alimentos que saem da cesta.
RESTRICOES = {
    "sem_porco": {"carne_porco"},
    "sem_carne_vermelha": {"carne_vermelha"},
    "vegetariano": {"carne", "peixe"},
    "sem_lactose": {"lactose"},
    "sem_gluten": {"gluten"},
    "sem_ovo": {"ovo"},
}

NOMES_RESTRICOES = {
    "sem_porco": "Sem carne de porco",
    "sem_carne_vermelha": "Sem carne vermelha",
    "vegetariano": "Vegetariano",
    "sem_lactose": "Sem lactose",
    "sem_gluten": "Sem glúten",
    "sem_ovo": "Sem ovo",
}


def metas_totais(pessoas: int, dias: int) -> dict[str, float]:
    """Metas da cesta inteira: meta diária × pessoas × dias."""
    fator = pessoas * dias
    metas = {k: v * fator for k, v in META_DIARIA_POR_PESSOA.items()}
    metas["flv_g"] = FLV_G_POR_PESSOA_DIA * fator
    return metas


def tags_excluidas(restricoes: list[str]) -> set[str]:
    desconhecidas = set(restricoes) - RESTRICOES.keys()
    if desconhecidas:
        raise ValueError(f"Restrição desconhecida: {', '.join(sorted(desconhecidas))}")
    return set().union(*(RESTRICOES[r] for r in restricoes)) if restricoes else set()
