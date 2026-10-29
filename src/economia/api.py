"""API da EconoMIA (FastAPI). Também serve o site em src/web/.

Rodar:  uvicorn economia.api:app --app-dir src --reload
Docs automáticas: http://localhost:8000/docs
"""

from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .dados import carregar, preco_por_kg
from .explicacao import explicar
from .metas import DIAS_POR_PERIODO, NOMES_RESTRICOES, RESTRICOES
from .otimizador import Cesta, Pedido
from .planejador import planejar

PASTA_WEB = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="EconoMIA", description="Cesta de compras econômica e equilibrada.", version="0.1.0")
base = carregar()


class PedidoCesta(BaseModel):
    orcamento: float | None = Field(None, gt=0, description="Orçamento em R$. Vazio = sem limite.")
    pessoas: int = Field(..., ge=1, le=20)
    periodo: Literal["semana", "quinzena", "mes"] = "mes"
    restricoes: list[str] = []
    custo_deslocamento: float = Field(0, ge=0, description="Custo de ir a um segundo mercado, em R$.")


def cesta_json(cesta: Cesta | None) -> dict | None:
    if cesta is None:
        return None
    dados = asdict(cesta)
    dados["custo_por_1000_kcal"] = round(cesta.custo_por_1000_kcal, 2)
    dados["custo_por_g_proteina"] = round(cesta.custo_por_g_proteina, 3)
    dados["obtido"] = {k: round(v, 1) for k, v in cesta.obtido.items()}
    return dados


def montar_resposta(pedido: PedidoCesta) -> dict:
    invalidas = set(pedido.restricoes) - RESTRICOES.keys()
    if invalidas:
        raise HTTPException(422, f"Restrição desconhecida: {', '.join(sorted(invalidas))}")
    p = Pedido(pedido.orcamento, pedido.pessoas, pedido.periodo, tuple(pedido.restricoes))
    plano = planejar(base, p, pedido.custo_deslocamento)
    return {
        "recomendacao": plano.recomendacao,
        "cesta_recomendada": cesta_json(plano.cesta_recomendada),
        "um_mercado": cesta_json(plano.um_mercado),
        "dois_mercados": cesta_json(plano.dois_mercados),
        "economia_bruta_dois": plano.economia_bruta_dois,
        "economia_liquida_dois": plano.economia_liquida_dois,
        "custo_deslocamento": plano.custo_deslocamento,
        "custo_por_mercado": {m: (c.custo_total if c else None) for m, c in plano.cestas_por_mercado.items()},
        "minimo_necessario": plano.minimo_necessario,
        "explicacao": explicar(plano, base),
        "aviso_dados": base.aviso,
    }


@app.get("/api/saude")
def saude():
    return {"status": "ok"}


@app.get("/api/opcoes")
def opcoes():
    return {
        "mercados": [asdict(m) for m in base.mercados.values()],
        "restricoes": [{"id": k, "nome": v} for k, v in NOMES_RESTRICOES.items()],
        "periodos": [{"id": k, "dias": v} for k, v in DIAS_POR_PERIODO.items()],
        "aviso_dados": base.aviso,
    }


@app.get("/api/precos")
def precos():
    """Tabela de preços por produto e mercado, com preço por kg."""
    linhas = {}
    for pr in base.precos:
        produto = base.produtos[pr.produto]
        linha = linhas.setdefault(
            produto.id,
            {"produto_id": produto.id, "produto": produto.nome, "alimento": base.alimentos[produto.alimento].nome, "precos": {}},
        )
        linha["precos"][pr.mercado] = {
            "preco": pr.preco,
            "preco_kg": round(preco_por_kg(produto, pr), 2),
            "data": pr.data,
            "fonte": pr.fonte,
        }
    return {"mercados": [asdict(m) for m in base.mercados.values()], "produtos": list(linhas.values())}


@app.post("/api/cesta")
def cesta(pedido: PedidoCesta):
    return montar_resposta(pedido)


if PASTA_WEB.exists():
    app.mount("/", StaticFiles(directory=PASTA_WEB, html=True), name="web")
