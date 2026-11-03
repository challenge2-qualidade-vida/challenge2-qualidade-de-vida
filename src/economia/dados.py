"""Carrega as bases de alimentos (nutrição) e de preços.

Os arquivos ficam em data/ e são JSON simples, para o grupo editar à mão
durante a coleta de preços.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARQ_ALIMENTOS = RAIZ / "data" / "alimentos" / "alimentos.json"
ARQ_PRECOS = RAIZ / "data" / "precos" / "precos.json"
# Preços confirmados pelos usuários a partir de NFC-e (tópico 10).
ARQ_CONTRIBUICOES = Path(os.environ.get("ECONOMIA_CONTRIBUICOES", RAIZ / "data" / "precos" / "contribuicoes.json"))


@dataclass(frozen=True)
class Alimento:
    id: str
    nome: str
    grupo: str
    tags: tuple[str, ...]
    kcal: float          # por 100 g
    proteina_g: float    # por 100 g
    fibra_g: float       # por 100 g
    fonte_nutricao: str = ""   # preenchido só quando o valor não vem da TACO


@dataclass(frozen=True)
class Mercado:
    id: str
    nome: str
    regiao: str
    # Localização (graus). None = sem localização (ex.: mercado vindo de NFC-e).
    lat: float | None = None
    lon: float | None = None


@dataclass(frozen=True)
class Produto:
    id: str
    alimento: str
    nome: str
    embalagem_g: float


@dataclass(frozen=True)
class Preco:
    produto: str
    mercado: str
    preco: float
    data: str
    fonte: str


@dataclass(frozen=True)
class Base:
    alimentos: dict[str, Alimento]
    mercados: dict[str, Mercado]
    produtos: dict[str, Produto]
    precos: list[Preco]
    aviso: str


def carregar(arq_alimentos: Path = ARQ_ALIMENTOS, arq_precos: Path = ARQ_PRECOS, arq_contribuicoes: Path | None = None) -> Base:
    bruto_a = json.loads(arq_alimentos.read_text(encoding="utf-8"))
    bruto_p = json.loads(arq_precos.read_text(encoding="utf-8"))

    arq_contribuicoes = arq_contribuicoes or ARQ_CONTRIBUICOES
    if arq_contribuicoes.exists():
        contrib = json.loads(arq_contribuicoes.read_text(encoding="utf-8"))
        ids = {m["id"] for m in bruto_p["mercados"]}
        bruto_p["mercados"] += [m for m in contrib["mercados"] if m["id"] not in ids]
        # Mesmo produto no mesmo mercado: fica o preço mais recente.
        recentes: dict[tuple, dict] = {}
        for pr in bruto_p["precos"] + contrib["precos"]:
            chave = (pr["produto"], pr["mercado"])
            if chave not in recentes or pr["data"] >= recentes[chave]["data"]:
                recentes[chave] = pr
        bruto_p["precos"] = list(recentes.values())

    alimentos = {
        a["id"]: Alimento(
            id=a["id"],
            nome=a["nome"],
            grupo=a["grupo"],
            tags=tuple(a["tags"]),
            kcal=a["por_100g"]["kcal"],
            proteina_g=a["por_100g"]["proteina_g"],
            fibra_g=a["por_100g"]["fibra_g"],
            fonte_nutricao=a.get("fonte_nutricao", ""),
        )
        for a in bruto_a["alimentos"]
    }
    mercados = {m["id"]: Mercado(**m) for m in bruto_p["mercados"]}
    produtos = {p["id"]: Produto(**p) for p in bruto_p["produtos"]}
    precos = [Preco(**p) for p in bruto_p["precos"]]

    return Base(alimentos, mercados, produtos, precos, bruto_p.get("aviso", ""))


def preco_por_kg(produto: Produto, preco: Preco) -> float:
    """Preço por kg (ou por litro, para líquidos tratados como 1 kg = 1 L)."""
    return preco.preco / produto.embalagem_g * 1000
