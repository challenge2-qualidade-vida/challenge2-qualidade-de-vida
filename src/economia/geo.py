"""Localização: mercados perto do usuário e ranking dos alimentos proteicos.

A localização vem do navegador (com permissão) e só é usada para calcular
distâncias: nunca é gravada. Os preços vêm da base da EconoMIA (coleta do
grupo e NFC-e). Os supermercados do OpenStreetMap mostram onde ainda faltam
preços.
"""

import math
from dataclasses import dataclass

import httpx

from .dados import Base, Mercado, preco_por_kg

# Regiões do DF com coordenadas aproximadas do centro, para quem não quer
# compartilhar a localização exata.
REGIOES_DF = {
    "asa_norte": ("Asa Norte", -15.7617, -47.8825),
    "asa_sul": ("Asa Sul", -15.8160, -47.9030),
    "guara": ("Guará", -15.8230, -47.9790),
    "taguatinga": ("Taguatinga", -15.8333, -48.0564),
    "aguas_claras": ("Águas Claras", -15.8344, -48.0263),
    "ceilandia": ("Ceilândia", -15.8199, -48.1085),
    "samambaia": ("Samambaia", -15.8770, -48.0830),
    "sobradinho": ("Sobradinho", -15.6530, -47.7900),
    "gama": ("Gama", -16.0190, -48.0660),
    "planaltina": ("Planaltina", -15.6200, -47.6500),
}

# Custo de carro por km rodado (parâmetro do grupo): gasolina ~R$ 6,50/L ÷ 10 km/L.
# O usuário pode mudar nas Configurações do app.
CUSTO_POR_KM = 0.65

# Raio de busca: padrão de 10 km, ajustável de 1 a 100 km nas Configurações.
RAIO_PADRAO_KM = 10
RAIO_MINIMO_KM = 1
RAIO_MAXIMO_KM = 100
# O OpenStreetMap é um serviço gratuito e compartilhado: consultas acima de 10 km pesam demais.
RAIO_MAXIMO_OSM_KM = 10

# Alimentos proteicos que entram no ranking ("carne, frango, ..."), na ordem da tela.
GRUPOS_PROTEICOS = ("proteina_animal", "laticinios", "leguminosas")

# Servidores públicos e gratuitos do Overpass; se um falhar (é comum estarem
# sobrecarregados), tenta o próximo.
URLS_OVERPASS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
_cache_osm: dict[tuple, list[dict]] = {}


@dataclass
class MercadoProximo:
    id: str
    nome: str
    regiao: str
    distancia_km: float
    custo_ida_volta: float
    # Direção a partir do usuário (0 = norte, 90 = leste), para desenhar o radar na tela.
    rumo_graus: float = 0.0


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em linha reta (fórmula de haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def custo_ida_volta(km: float, custo_por_km: float = CUSTO_POR_KM) -> float:
    """Custo estimado de ir e voltar de carro. Distância em linha reta × 1,3 ≈ distância pelas ruas."""
    return round(km * 1.3 * 2 * custo_por_km, 2)


def rumo_graus(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Direção do ponto 2 visto do ponto 1, em graus a partir do norte."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return round((math.degrees(math.atan2(x, y)) + 360) % 360, 1)


def validar_coordenadas(lat: float, lon: float) -> None:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Coordenadas inválidas.")


def mercados_proximos(base: Base, lat: float, lon: float, raio_km: float, custo_por_km: float = CUSTO_POR_KM) -> list[MercadoProximo]:
    validar_coordenadas(lat, lon)
    proximos = []
    for m in base.mercados.values():
        if m.lat is None or m.lon is None:
            continue
        d = distancia_km(lat, lon, m.lat, m.lon)
        if d <= raio_km:
            proximos.append(MercadoProximo(
                m.id, m.nome, m.regiao, round(d, 1), custo_ida_volta(d, custo_por_km),
                rumo_graus(lat, lon, m.lat, m.lon) if d > 0.05 else 0.0,
            ))
    return sorted(proximos, key=lambda m: m.distancia_km)


def custo_segundo_mercado(proximos: list[MercadoProximo]) -> float:
    """Estimativa do custo de ir a um 2º mercado: a ida e volta ao 2º mais próximo."""
    return proximos[1].custo_ida_volta if len(proximos) > 1 else 0.0


def ranking_proteinas(base: Base, mercados: list[str]) -> dict:
    """Para cada alimento proteico: o menor preço por kg em cada mercado e o custo de 100 g de proteína."""
    alimentos = []
    vitorias = {m: 0 for m in mercados}
    for a in base.alimentos.values():
        if a.grupo not in GRUPOS_PROTEICOS or a.proteina_g <= 0:
            continue
        por_mercado = {}
        for pr in base.precos:
            produto = base.produtos[pr.produto]
            if produto.alimento != a.id or pr.mercado not in mercados:
                continue
            kg = preco_por_kg(produto, pr)
            atual = por_mercado.get(pr.mercado)
            if atual is None or kg < atual["preco_kg"]:
                por_mercado[pr.mercado] = {
                    "produto": produto.nome,
                    "preco": pr.preco,
                    "preco_kg": round(kg, 2),
                    # R$ por 100 g de proteína: preço do kg ÷ (proteína em 1 kg) × 100
                    "custo_100g_proteina": round(kg / (a.proteina_g * 10) * 100, 2),
                    "data": pr.data,
                    "fonte": pr.fonte,
                }
        if not por_mercado:
            continue
        melhor = min(por_mercado, key=lambda m: por_mercado[m]["preco_kg"])
        if len(por_mercado) > 1:
            vitorias[melhor] += 1
        alimentos.append({
            "alimento_id": a.id,
            "alimento": a.nome.split(" (")[0],
            "grupo": a.grupo,
            "proteina_100g": a.proteina_g,
            "precos": por_mercado,
            "melhor_mercado": melhor,
            "economia_vs_mais_caro_pct": round(
                (max(v["preco_kg"] for v in por_mercado.values()) - por_mercado[melhor]["preco_kg"])
                / max(v["preco_kg"] for v in por_mercado.values()) * 100, 1),
        })

    # Ordena pela proteína mais barata (custo de 100 g de proteína no melhor mercado).
    alimentos.sort(key=lambda x: x["precos"][x["melhor_mercado"]]["custo_100g_proteina"])

    # "Carrinho de proteínas": 1 kg de cada alimento proteico que TODOS os mercados têm.
    comuns = [x for x in alimentos if all(m in x["precos"] for m in mercados)]
    carrinho = {m: round(sum(x["precos"][m]["preco_kg"] for x in comuns), 2) for m in mercados}
    return {
        "alimentos": alimentos,
        "vitorias": vitorias,
        "carrinho": {"itens": [x["alimento"] for x in comuns], "total_por_mercado": carrinho,
                     "melhor_mercado": min(carrinho, key=carrinho.get) if comuns else None},
    }


def comparar_mercados(proximos: list[MercadoProximo], ranking: dict) -> list[dict]:
    """Junta distância e preço: quem é o mais perto, o mais barato e o de melhor custo-benefício.

    Preço = "carrinho de proteínas" (1 kg de cada alimento proteico que todos os
    mercados do raio têm). Custo real = carrinho + ida e volta.
    """
    totais = ranking["carrinho"]["total_por_mercado"] if ranking else {}
    tem_carrinho = bool(ranking and ranking["carrinho"]["itens"])
    linhas = []
    for m in proximos:
        carrinho = totais.get(m.id) if tem_carrinho else None
        linhas.append({
            "id": m.id, "nome": m.nome, "regiao": m.regiao,
            "distancia_km": m.distancia_km, "custo_ida_volta": m.custo_ida_volta, "rumo_graus": m.rumo_graus,
            "carrinho_proteinas": carrinho,
            "custo_real": round(carrinho + m.custo_ida_volta, 2) if carrinho is not None else None,
            "selos": [],
        })
    if linhas:
        min(linhas, key=lambda l: l["distancia_km"])["selos"].append("mais_perto")
        com_preco = [l for l in linhas if l["carrinho_proteinas"] is not None]
        if len(com_preco) > 1:
            min(com_preco, key=lambda l: l["carrinho_proteinas"])["selos"].append("melhor_preco")
            min(com_preco, key=lambda l: l["custo_real"])["selos"].append("melhor_custo_beneficio")
    return linhas


# ---------- OpenStreetMap ----------

def consulta_overpass(lat: float, lon: float, raio_m: int) -> str:
    return (
        f"[out:json][timeout:15];"
        f"(node[\"shop\"~\"supermarket|wholesale\"](around:{raio_m},{lat},{lon});"
        f"way[\"shop\"~\"supermarket|wholesale\"](around:{raio_m},{lat},{lon}););"
        f"out center 40;"
    )


def ler_overpass(dados: dict, lat: float, lon: float, conhecidos: list[Mercado]) -> list[dict]:
    """Supermercados do OpenStreetMap, com distância e se já têm preços na EconoMIA."""
    nomes_com_preco = {m.nome.lower() for m in conhecidos}
    saida = []
    for el in dados.get("elements", []):
        nome = el.get("tags", {}).get("name")
        la, lo = el.get("lat") or el.get("center", {}).get("lat"), el.get("lon") or el.get("center", {}).get("lon")
        if not nome or la is None or lo is None:
            continue
        saida.append({
            "nome": nome,
            "distancia_km": round(distancia_km(lat, lon, la, lo), 1),
            "tem_precos": nome.lower() in nomes_com_preco,
        })
    saida.sort(key=lambda m: m["distancia_km"])
    # O mesmo mercado pode vir como ponto e como prédio.
    vistos, unicos = set(), []
    for m in saida:
        if m["nome"] not in vistos:
            vistos.add(m["nome"])
            unicos.append(m)
    return unicos


def supermercados_osm(base: Base, lat: float, lon: float, raio_km: float) -> list[dict]:
    """Consulta o OpenStreetMap (gratuito). A posição é arredondada (~1 km) antes de sair do servidor."""
    validar_coordenadas(lat, lon)
    lat_r, lon_r = round(lat, 2), round(lon, 2)
    raio_m = int(min(raio_km, RAIO_MAXIMO_OSM_KM) * 1000)
    chave = (lat_r, lon_r, raio_m)
    if chave not in _cache_osm:
        erro: Exception | None = None
        for url in URLS_OVERPASS:
            try:
                r = httpx.post(
                    url,
                    data={"data": consulta_overpass(lat_r, lon_r, raio_m)},
                    headers={"User-Agent": "EconoMIA/0.1 (projeto academico, Residencia em IA Brasilia)"},
                    timeout=20,
                )
                r.raise_for_status()
                _cache_osm[chave] = r.json().get("elements", [])
                break
            except (httpx.HTTPError, ValueError) as e:
                erro = e
        else:
            raise httpx.HTTPError(f"todos os servidores do OpenStreetMap falharam ({erro})")
    return ler_overpass({"elements": _cache_osm[chave]}, lat_r, lon_r, list(base.mercados.values()))
