"""API da EconoMIA (FastAPI). Também serve o site em src/web/.

Rodar:  uvicorn economia.api:app --app-dir src --reload
Docs automáticas: http://localhost:8000/docs
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import geo, nfce
from .agentes import Orquestrador
from .dados import carregar, preco_por_kg
from .explicacao import explicar
from .llm import cliente_do_ambiente
from .metas import DIAS_POR_PERIODO, NOMES_RESTRICOES, RESTRICOES
from .otimizador import Cesta, Pedido
from .planejador import planejar
from .rag import BaseConhecimento

PASTA_WEB = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="EconoMIA", description="Cesta de compras econômica e equilibrada.", version="0.1.0")
base = carregar()
conhecimento = BaseConhecimento(base)
orquestrador = Orquestrador(base, conhecimento, cliente_do_ambiente())


def recarregar_base():
    """Relê as bases depois que o usuário confirma preços de uma NFC-e."""
    global base, conhecimento, orquestrador
    base = carregar()
    conhecimento = BaseConhecimento(base)
    orquestrador = Orquestrador(base, conhecimento, orquestrador.cliente)


class MensagemHistorico(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=4000)


class PedidoChat(BaseModel):
    mensagem: str = Field(..., min_length=1, max_length=1000)
    historico: list[MensagemHistorico] = []


class PedidoCardapio(BaseModel):
    alimentos: list[str] = Field(..., min_length=1, max_length=40)
    restricoes: list[str] = []


class PedidoNFCeURL(BaseModel):
    url: str = Field(..., max_length=2000)


class ItemConfirmado(BaseModel):
    produto_id: str
    preco: float = Field(..., gt=0, lt=10000)


class ConfirmacaoNFCe(BaseModel):
    emitente: str = Field(..., max_length=200)
    cnpj: str = Field("", max_length=14, pattern=r"^\d*$")
    data: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    itens: list[ItemConfirmado] = Field(..., min_length=1, max_length=200)


class PedidoCesta(BaseModel):
    orcamento: float | None = Field(None, gt=0, description="Orçamento em R$. Vazio = sem limite.")
    pessoas: int = Field(..., ge=1, le=20)
    periodo: Literal["semana", "quinzena", "mes"] = "mes"
    restricoes: list[str] = []
    custo_deslocamento: float = Field(0, ge=0, description="Custo de ir a um segundo mercado, em R$.")
    mercados: list[str] | None = Field(None, description="Só estes mercados (ex.: os próximos do usuário). Vazio = todos.")


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
    if pedido.mercados is not None and not set(pedido.mercados) & base.mercados.keys():
        raise HTTPException(422, "Nenhum dos mercados informados existe na base.")
    plano = planejar(base, p, pedido.custo_deslocamento, pedido.mercados)
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
            {"produto_id": produto.id, "produto": produto.nome, "alimento_id": produto.alimento,
             "alimento": base.alimentos[produto.alimento].nome, "precos": {}},
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


@app.get("/api/creditos")
def creditos_imagens():
    """Autor e licença de cada foto de alimento (Wikimedia Commons). As licenças CC exigem crédito."""
    arquivo = Path(__file__).resolve().parents[2] / "data" / "alimentos" / "imagens.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    return [
        {"alimento_id": k, "alimento": base.alimentos[k].nome if k in base.alimentos else k, **v}
        for k, v in dados.items()
    ]


@app.get("/api/conhecimento")
def buscar_conhecimento(pergunta: str, k: int = 3):
    """Busca na base de conhecimento (Guia Alimentar, TACO, critérios do grupo)."""
    return {
        "pergunta": pergunta,
        "trechos": [
            {"id": r.trecho.id, "titulo": r.trecho.titulo, "texto": r.trecho.texto, "fonte": r.trecho.fonte, "similaridade": r.similaridade}
            for r in conhecimento.buscar(pergunta, k=min(max(k, 1), 10))
        ],
    }


@app.get("/api/llm")
def status_llm():
    c = orquestrador.cliente
    return {"ativo": c is not None, "provedor": c.provedor if c else None, "modelo": c.modelo if c else None}


@app.post("/api/chat")
def chat(pedido: PedidoChat):
    r = orquestrador.responder(pedido.mensagem, [h.model_dump() for h in pedido.historico])
    return asdict(r)


@app.post("/api/cardapio")
def cardapio(pedido: PedidoCardapio):
    """Miau-ricio sugere refeições com os alimentos da cesta; Mia confere as restrições."""
    return asdict(orquestrador.cardapio(pedido.alimentos, pedido.restricoes))


def _processar_url(url: str) -> dict:
    try:
        html = nfce.baixar_pagina(url)
        return nfce.nota_json(nfce.processar(base, html, url))
    except nfce.ErroNFCe as e:
        raise HTTPException(422, str(e)) from e


@app.post("/api/nfce/imagem")
async def nfce_imagem(arquivo: UploadFile = File(...)):
    """Recibaldo: lê o QR code da foto do cupom e consulta a nota na SEFAZ-DF."""
    conteudo = await arquivo.read(nfce.TAMANHO_MAXIMO_IMAGEM + 1)
    try:
        url = nfce.ler_qrcode(conteudo)
        nfce.validar_url(url)
    except nfce.ErroNFCe as e:
        raise HTTPException(422, str(e)) from e
    return _processar_url(url)


@app.post("/api/nfce/url")
def nfce_url(pedido: PedidoNFCeURL):
    """Mesma coisa, para quem copiou o link do QR code."""
    return _processar_url(pedido.url)


@app.post("/api/nfce/confirmar")
def nfce_confirmar(pedido: ConfirmacaoNFCe):
    """Grava os preços que o usuário conferiu. Nenhum dado do consumidor é salvo."""
    desconhecidos = {i.produto_id for i in pedido.itens} - base.produtos.keys()
    if desconhecidos:
        raise HTTPException(422, f"Produto desconhecido: {', '.join(sorted(desconhecidos))}")
    n = nfce.salvar_contribuicao(pedido.emitente, pedido.cnpj, pedido.data, [i.model_dump() for i in pedido.itens])
    recarregar_base()
    return {"salvos": n}


# ---------- Localização (tópico 13) ----------

LAT = Query(..., ge=-90, le=90)
LON = Query(..., ge=-180, le=180)
RAIO = Query(geo.RAIO_PADRAO_KM, ge=geo.RAIO_MINIMO_KM, le=geo.RAIO_MAXIMO_KM, description="Raio em km (1 a 100; padrão 10)")
CUSTO_KM = Query(geo.CUSTO_POR_KM, ge=0, le=5, description="Custo do carro por km rodado, em R$")


@app.get("/api/configuracoes")
def configuracoes_padrao():
    """Valores padrão e limites das Configurações do app."""
    return {
        "raio_km": {"padrao": geo.RAIO_PADRAO_KM, "minimo": geo.RAIO_MINIMO_KM, "maximo": geo.RAIO_MAXIMO_KM},
        "custo_por_km": {"padrao": geo.CUSTO_POR_KM, "minimo": 0.2, "maximo": 2.0},
        "raio_maximo_mapa_km": geo.RAIO_MAXIMO_OSM_KM,
        "ordenacao": {"padrao": "custo_beneficio", "opcoes": ["distancia", "preco", "custo_beneficio"]},
    }


@app.get("/api/regioes")
def regioes():
    return [{"id": k, "nome": n, "lat": la, "lon": lo} for k, (n, la, lo) in geo.REGIOES_DF.items()]


@app.get("/api/proximos")
def proximos(lat: float = LAT, lon: float = LON, raio_km: float = RAIO, custo_por_km: float = CUSTO_KM):
    """Mercados com preços perto do usuário, ranking das proteínas e comparação distância × preço.

    A posição não é gravada.
    """
    perto = geo.mercados_proximos(base, lat, lon, raio_km, custo_por_km)
    ids = [m.id for m in perto]
    ranking = geo.ranking_proteinas(base, ids) if ids else None
    com_local = [m for m in base.mercados.values() if m.lat is not None]
    return {
        "raio_km": raio_km,
        "mercados": geo.comparar_mercados(perto, ranking),
        "total_com_localizacao": len(com_local),
        "mais_proximo_fora_do_raio_km": min(
            (round(geo.distancia_km(lat, lon, m.lat, m.lon), 1) for m in com_local if m.id not in ids), default=None),
        "custo_segundo_mercado": geo.custo_segundo_mercado(perto),
        "custo_por_km": custo_por_km,
        "proteinas": ranking,
        "sem_localizacao": [m.nome for m in base.mercados.values() if m.lat is None],
    }


@app.get("/api/osm")
def osm(lat: float = LAT, lon: float = LON, raio_km: float = RAIO):
    """Supermercados reais perto do usuário, pelo OpenStreetMap (gratuito)."""
    try:
        return {"supermercados": geo.supermercados_osm(base, lat, lon, raio_km), "fonte": "© colaboradores do OpenStreetMap"}
    except (httpx.HTTPError, ValueError) as e:
        raise HTTPException(502, f"Não foi possível consultar o OpenStreetMap agora: {e}") from e


if PASTA_WEB.exists():
    app.mount("/", StaticFiles(directory=PASTA_WEB, html=True), name="web")
