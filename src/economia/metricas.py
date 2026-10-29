"""Métricas do projeto (README, seção Métricas), calculadas sobre cenários.

1. Economia média por cesta (× cesta de referência estilo DIEESE)
2. Aderência ao orçamento
3. Adequação nutricional (metas + variedade + restrições)
4. Custo por 1.000 kcal e por grama de proteína
5. Qualidade dos dados
6. Precisão de preço (verificação na gôndola, feita pelo grupo)
"""

import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .dados import RAIZ, Base, preco_por_kg
from .metas import RESTRICOES, metas_totais
from .otimizador import Cesta, Pedido
from .planejador import planejar

ARQ_REFERENCIA = RAIZ / "data" / "experimento" / "cesta_referencia.json"


@dataclass
class Referencia:
    custo: float
    obtido: dict[str, float]
    metas: dict[str, float]

    @property
    def cumpre_metas(self) -> bool:
        return all(self.obtido[k] >= self.metas[k] - 1e-6 for k in self.metas)

    @property
    def custo_mesma_energia(self) -> float:
        return self.custo * self.metas["kcal"] / self.obtido["kcal"]


def menor_preco_kg(base: Base, alimento: str) -> float:
    return min(preco_por_kg(base.produtos[p.produto], p) for p in base.precos if base.produtos[p.produto].alimento == alimento)


def cesta_referencia(base: Base, pessoas: int, dias: int, arquivo: Path = ARQ_REFERENCIA) -> Referencia:
    """Cesta estilo DIEESE com o menor preço por kg da base (sem arredondar embalagens)."""
    fator = pessoas * dias / 30
    custo, obtido = 0.0, {"kcal": 0.0, "proteina_g": 0.0, "fibra_g": 0.0, "flv_g": 0.0}
    for item in json.loads(arquivo.read_text(encoding="utf-8"))["itens"]:
        kg = item["kg_mes"] * fator
        a = base.alimentos[item["alimento"]]
        custo += kg * menor_preco_kg(base, a.id)
        obtido["kcal"] += a.kcal * kg * 10
        obtido["proteina_g"] += a.proteina_g * kg * 10
        obtido["fibra_g"] += a.fibra_g * kg * 10
        if a.grupo == "flv":
            obtido["flv_g"] += kg * 1000
    return Referencia(round(custo, 2), obtido, metas_totais(pessoas, dias))


def cumpre_metas(cesta: Cesta) -> bool:
    return all(cesta.obtido[k] >= cesta.metas[k] - 1e-6 for k in cesta.metas)


def respeita_restricoes(base: Base, cesta: Cesta, restricoes: tuple[str, ...]) -> bool:
    proibidas = set().union(*(RESTRICOES[r] for r in restricoes)) if restricoes else set()
    return not any(proibidas & set(base.alimentos[i.alimento_id].tags) for i in cesta.itens)


def proteina_animal(base: Base, cesta: Cesta) -> float:
    """Fração da proteína da cesta que vem de carnes, ovos, peixe, leite e queijo."""
    animal = 0.0
    for i in cesta.itens:
        if i.grupo in ("proteina_animal", "laticinios"):
            a = base.alimentos[i.alimento_id]
            animal += a.proteina_g * base.produtos[i.produto_id].embalagem_g / 100 * i.quantidade
    return animal / cesta.obtido["proteina_g"]


def variedade(cesta: Cesta) -> tuple[int, int]:
    """(nº de grupos de alimentos, nº de frutas/hortaliças diferentes)."""
    grupos = {i.grupo for i in cesta.itens}
    flv = {i.alimento_id for i in cesta.itens if i.grupo == "flv"}
    return len(grupos), len(flv)


def cenarios() -> list[Pedido]:
    """Grade de casos: 1–6 pessoas, semana e mês, 4 níveis de orçamento, 5 perfis de restrição."""
    pedidos = []
    restricoes = [(), ("vegetariano",), ("sem_lactose",), ("sem_porco",), ("sem_gluten",)]
    for pessoas in (1, 2, 4, 6):
        for periodo, dias in (("semana", 7), ("mes", 30)):
            # Orçamento por pessoa por dia: apertado → folgado.
            for por_dia in (5.0, 6.0, 8.0, 12.0):
                for r in restricoes:
                    pedidos.append(Pedido(round(por_dia * pessoas * dias, 2), pessoas, periodo, r))
    return pedidos


def avaliar_cenarios(base: Base, custo_deslocamento: float = 10.0) -> list[dict]:
    linhas = []
    for p in cenarios():
        plano = planejar(base, p, custo_deslocamento)
        ref = cesta_referencia(base, p.pessoas, p.dias)
        c = plano.cesta_recomendada
        linha = {
            "pessoas": p.pessoas, "periodo": p.periodo, "orcamento": p.orcamento,
            "restricoes": "+".join(p.restricoes) or "nenhuma",
            "viavel": c is not None, "referencia_custo": ref.custo, "referencia_cumpre_metas": ref.cumpre_metas,
        }
        if c:
            grupos, flv = variedade(c)
            custo_real = c.custo_total + (custo_deslocamento if plano.recomendacao == "dois" else 0)
            linha.update({
                "custo": round(custo_real, 2),
                "dentro_orcamento": custo_real <= p.orcamento + 1e-6,
                "cumpre_metas": cumpre_metas(c),
                "respeita_restricoes": respeita_restricoes(base, c, p.restricoes),
                "grupos": grupos, "flv_diferentes": flv,
                "economia_pct": round((ref.custo - custo_real) / ref.custo * 100, 1),
                # Mesma energia: a referência escalada para a meta de kcal da cesta.
                "economia_ajustada_pct": round((ref.custo_mesma_energia - custo_real) / ref.custo_mesma_energia * 100, 1),
                "proteina_animal_pct": round(proteina_animal(base, c) * 100, 1),
                "custo_1000kcal": round(custo_real / c.obtido["kcal"] * 1000, 2),
                "custo_g_proteina": round(custo_real / c.obtido["proteina_g"], 3),
                "ref_custo_1000kcal": round(ref.custo / ref.obtido["kcal"] * 1000, 2),
                "ref_custo_g_proteina": round(ref.custo / ref.obtido["proteina_g"], 3),
                "minimo_necessario": None,
            })
        else:
            linha["minimo_necessario"] = plano.minimo_necessario
        linhas.append(linha)
    return linhas


def qualidade_dos_dados(base: Base, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    total = len(base.precos)
    com_origem = sum(1 for p in base.precos if p.data and p.fonte)
    idades = [(hoje - date.fromisoformat(p.data)).days for p in base.precos]
    por_fonte: dict[str, int] = {}
    for p in base.precos:
        por_fonte[p.fonte] = por_fonte.get(p.fonte, 0) + 1
    combinacoes = len(base.produtos) * len(base.mercados)
    return {
        "precos": total,
        "com_data_e_fonte_pct": round(com_origem / total * 100, 1),
        "ate_30_dias_pct": round(sum(i <= 30 for i in idades) / total * 100, 1),
        "idade_media_dias": round(sum(idades) / total, 1),
        "por_fonte": por_fonte,
        "cobertura_pct": round(total / combinacoes * 100, 1),
    }


def precisao_de_preco(arquivo: Path, margem: float = 0.05) -> dict | None:
    """Lê a planilha de verificação na gôndola: produto_id, mercado, preco_app, preco_gondola."""
    if not arquivo.exists():
        return None
    with open(arquivo, encoding="utf-8") as f:
        linhas = [l for l in csv.DictReader(f) if l.get("preco_gondola")]
    if not linhas:
        return None
    dentro = sum(abs(float(l["preco_app"]) - float(l["preco_gondola"])) <= margem * float(l["preco_gondola"]) for l in linhas)
    return {"itens_verificados": len(linhas), "dentro_da_margem_pct": round(dentro / len(linhas) * 100, 1), "margem": margem}
