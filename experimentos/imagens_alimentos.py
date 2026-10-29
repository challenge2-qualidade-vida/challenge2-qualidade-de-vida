"""Baixa uma foto de licença livre (Wikimedia Commons) para cada alimento da base.

Rodar:
    .venv/bin/python experimentos/imagens_alimentos.py            # todos
    .venv/bin/python experimentos/imagens_alimentos.py arroz ovo  # só alguns

Gera src/web/img/alimentos/<id>.webp (240×240) e data/alimentos/imagens.json
com título, autor, licença e link de cada foto (as licenças CC exigem crédito).
"""

import io
import json
import re
import sys
from pathlib import Path

import httpx
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "src" / "web" / "img" / "alimentos"
ARQ_CREDITOS = RAIZ / "data" / "alimentos" / "imagens.json"
API = "https://commons.wikimedia.org/w/api.php"
CABECALHO = {"User-Agent": "EconoMIA/0.1 (https://github.com/dida0982/challenge2-qualidade-de-vida) python-httpx"}

# Busca no Commons e qual opção usar (0 = primeira). As opções foram escolhidas
# olhando uma folha com as 6 primeiras fotos livres de cada busca: a primeira
# nem sempre é o alimento cru (ex.: "carne moída" trazia um produto vegetal).
BUSCAS = {
    "arroz": ("white rice grains bowl", 0),
    "macarrao": ("dried pasta", 0),
    "aveia": ("rolled oats", 0),
    "pao_frances": ("pão francês", 0),
    "farinha_mandioca": ("farinha de mandioca", 0),
    "feijao_carioca": ("feijão carioca", 0),
    "feijao_preto": ("black turtle beans", 0),
    "lentilha": ("brown lentils", 1),
    "ovo": ("chicken eggs brown", 0),
    "frango_peito": ("chicken breast raw meat", 0),
    "frango_coxa": ("raw chicken drumsticks", 0),
    "patinho": ("minced beef raw", 0),
    "lombo_porco": ("raw pork", 2),
    "sardinha": ("canned sardines tin", 0),
    "leite": ("Glas Milch", 4),
    "mucarela": ("mozzarella", 1),
    "batata": ("potatoes tubers", 1),
    "mandioca": ("mandioca raiz", 3),
    "cenoura": ("carrot vegetables", 4),
    "tomate": ("tomatoes red fruit", 2),
    "cebola": ("onions", 0),
    "repolho": ("white cabbage head", 1),
    "abobora": ("kabocha", 3),
    "banana": ("bananas bunch", 0),
    "laranja": ("oranges fruit", 0),
    "maca": ("red apples", 0),
    "oleo_soja": ("soybean oil bottle", 0),
    "acucar": ("white sugar crystals", 1),
}

LICENCAS_OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? [0-9.]+|cc by(-sa)?)", re.I)
LICENCAS_NAO = re.compile(r"\b(nc|nd)\b", re.I)


def limpar_html(texto: str) -> str:
    return re.sub(r"<[^>]+>", "", texto or "").strip()


def candidatos(busca: str) -> list[dict]:
    r = httpx.get(API, headers=CABECALHO, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"filetype:bitmap {busca}", "gsrlimit": 12,
        "prop": "imageinfo", "iiprop": "url|mime|extmetadata|size", "iiurlwidth": 480,
    })
    r.raise_for_status()
    paginas = sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    saida = []
    for p in paginas:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licenca = limpar_html(meta.get("LicenseShortName", {}).get("value", ""))
        if info.get("mime") not in ("image/jpeg", "image/png") or not LICENCAS_OK.match(licenca) or LICENCAS_NAO.search(licenca):
            continue
        if min(info.get("width", 0), info.get("height", 0)) < 300:
            continue
        saida.append({
            "titulo": p["title"].removeprefix("File:"),
            "pagina": info.get("descriptionurl"),
            "miniatura": info.get("thumburl"),
            "autor": limpar_html(meta.get("Artist", {}).get("value", "")) or "desconhecido",
            "licenca": licenca,
            "licenca_url": meta.get("LicenseUrl", {}).get("value", ""),
        })
    return saida


def baixar(alimento: str, busca: str, escolha: int = 0) -> dict | None:
    opcoes = candidatos(busca)
    if len(opcoes) <= escolha:
        print(f"  {alimento}: nenhuma foto livre encontrada para '{busca}'")
        return None
    c = opcoes[escolha]
    r = httpx.get(c["miniatura"], headers=CABECALHO, timeout=60)
    r.raise_for_status()
    im = ImageOps.fit(Image.open(io.BytesIO(r.content)).convert("RGB"), (240, 240), Image.LANCZOS, centering=(0.5, 0.5))
    PASTA.mkdir(parents=True, exist_ok=True)
    im.save(PASTA / f"{alimento}.webp", quality=82, method=6)
    print(f"  {alimento}: {c['titulo']} ({c['licenca']})")
    return {k: v for k, v in c.items() if k != "miniatura"} | {"arquivo": f"img/alimentos/{alimento}.webp", "busca": busca}


def main():
    creditos = json.loads(ARQ_CREDITOS.read_text(encoding="utf-8")) if ARQ_CREDITOS.exists() else {}
    # Formato: id  ou  id=número (para testar outra opção da busca)
    pedidos = sys.argv[1:] or list(BUSCAS)
    for pedido in pedidos:
        alimento, _, n = pedido.partition("=")
        busca, escolha = BUSCAS[alimento]
        info = baixar(alimento, busca, int(n) if n else escolha)
        if info:
            creditos[alimento] = info
    ARQ_CREDITOS.write_text(json.dumps(dict(sorted(creditos.items())), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
