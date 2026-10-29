"""Recibaldo: lê a NFC-e (cupom fiscal) pelo QR code e transforma em preços.

Fluxo: foto do cupom → QR code (OpenCV) → URL da SEFAZ → página da nota →
itens (produto, quantidade, preço) → sugestão de produto da base →
o usuário confere → os preços entram na base com fonte "nfce".

Por que o QR code e não OCR da foto: a página da SEFAZ traz os dados oficiais
da nota, sem erro de leitura. O OCR de cupom amassado erra muito.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import httpx
import numpy as np
from bs4 import BeautifulSoup

from .dados import ARQ_CONTRIBUICOES, Base
from .rag import tokenizar

# Só estes domínios podem ser consultados (evita que o servidor seja usado
# para acessar endereços arbitrários: proteção contra SSRF).
DOMINIOS_PERMITIDOS = ("fazenda.df.gov.br",)
TAMANHO_MAXIMO_PAGINA = 2_000_000
TAMANHO_MAXIMO_IMAGEM = 5_000_000

# Palavras genéricas que não ajudam a identificar o alimento.
PALAVRAS_IGNORADAS = {"tipo", "cru", "crua", "inteiro", "sem", "pele", "com", "fatiado", "kg", "un"}


class ErroNFCe(Exception):
    pass


@dataclass
class ItemNota:
    descricao: str
    quantidade: float
    unidade: str
    valor_unitario: float
    valor_total: float
    # Sugestão de produto da base (o usuário confirma antes de salvar).
    produto_id: str | None = None
    produto: str | None = None
    preco_embalagem: float | None = None
    confianca: str = "revisar"        # "alta" ou "revisar"


@dataclass
class Nota:
    emitente: str
    cnpj: str
    data: str                          # AAAA-MM-DD
    itens: list[ItemNota] = field(default_factory=list)
    chave: str | None = None


# ---------- QR code ----------

def ler_qrcode(imagem: bytes) -> str:
    if len(imagem) > TAMANHO_MAXIMO_IMAGEM:
        raise ErroNFCe("Imagem maior que 5 MB.")
    matriz = cv2.imdecode(np.frombuffer(imagem, np.uint8), cv2.IMREAD_GRAYSCALE)
    if matriz is None:
        raise ErroNFCe("Não consegui abrir a imagem. Envie uma foto em JPG ou PNG.")
    detector = cv2.QRCodeDetector()
    texto, _, _ = detector.detectAndDecode(matriz)
    if not texto:
        # Segunda tentativa: imagem ampliada e com contraste, ajuda em fotos pequenas.
        ampliada = cv2.resize(matriz, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        texto, _, _ = detector.detectAndDecode(cv2.equalizeHist(ampliada))
    if not texto:
        raise ErroNFCe("Não encontrei um QR code na imagem. Tente uma foto mais próxima e com boa luz.")
    return texto.strip()


# ---------- URL e chave de acesso ----------

def validar_url(url: str) -> str:
    partes = urlparse(url)
    host = (partes.hostname or "").lower()
    if partes.scheme not in ("http", "https") or not any(host == d or host.endswith("." + d) for d in DOMINIOS_PERMITIDOS):
        raise ErroNFCe("Este QR code não é de uma NFC-e do Distrito Federal (SEFAZ-DF).")
    return url


def digito_verificador(chave43: str) -> int:
    """Módulo 11 da chave de acesso (pesos 2 a 9, da direita para a esquerda)."""
    soma = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(chave43)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def extrair_chave(url: str) -> str | None:
    """Chave de 44 dígitos do parâmetro p= (formato chave|versão|ambiente|...)."""
    p = parse_qs(urlparse(url).query).get("p", [""])[0]
    chave = re.sub(r"\D", "", p.split("|")[0])
    if len(chave) != 44 or chave[20:22] != "65" or digito_verificador(chave[:43]) != int(chave[43]):
        return None
    return chave


def baixar_pagina(url: str) -> str:
    destino = httpx.URL(url)
    for _ in range(3):
        # Cada redirecionamento também precisa ser de um domínio permitido.
        validar_url(str(destino))
        try:
            r = httpx.get(destino, timeout=15, follow_redirects=False, headers={"User-Agent": "EconoMIA (projeto academico)"})
        except httpx.HTTPError as e:
            raise ErroNFCe(f"Não consegui acessar a SEFAZ: {e}") from e
        if not r.is_redirect:
            break
        destino = destino.join(r.headers.get("location", ""))
    else:
        raise ErroNFCe("A SEFAZ redirecionou vezes demais.")
    if r.status_code != 200:
        raise ErroNFCe(f"A SEFAZ respondeu com erro {r.status_code}.")
    if len(r.content) > TAMANHO_MAXIMO_PAGINA:
        raise ErroNFCe("Página da nota grande demais.")
    return r.text


# ---------- Página da nota ----------

def _numero_br(texto: str) -> float:
    limpo = re.sub(r"[^\d,.]", "", texto)
    return float(limpo.replace(".", "").replace(",", "."))


def extrair_nota(html: str) -> Nota:
    """Lê o layout padrão da consulta pública da NFC-e (tabela #tabResult).

    Dados do consumidor (CPF, nome) existem na página, mas nunca são lidos.
    """
    soup = BeautifulSoup(html, "html.parser")
    emitente = soup.select_one("#u20, .txtTopo")
    texto = soup.get_text(" ", strip=True)
    cnpj = re.search(r"CNPJ:?\s*([\d./-]{14,18})", texto)
    emissao = re.search(r"Emiss[ãa]o:?\s*(\d{2}/\d{2}/\d{4})", texto)

    itens = []
    for linha in soup.select("#tabResult tr"):
        nome = linha.select_one(".txtTit")
        qtd, un, unit, total = (linha.select_one(c) for c in (".Rqtd", ".RUN", ".RvlUnit", ".valor"))
        if not (nome and qtd and unit and total):
            continue
        itens.append(ItemNota(
            descricao=nome.get_text(strip=True),
            quantidade=_numero_br(qtd.get_text().split(":")[-1]),
            unidade=(un.get_text().split(":")[-1].strip().upper() if un else "UN"),
            valor_unitario=_numero_br(unit.get_text().split(":")[-1]),
            valor_total=_numero_br(total.get_text()),
        ))
    if not itens:
        raise ErroNFCe("Não encontrei itens na página da nota. O layout da SEFAZ pode ter mudado.")

    data = datetime.strptime(emissao.group(1), "%d/%m/%Y").strftime("%Y-%m-%d") if emissao else datetime.now().strftime("%Y-%m-%d")
    return Nota(
        emitente=emitente.get_text(strip=True) if emitente else "Mercado (NFC-e)",
        cnpj=re.sub(r"\D", "", cnpj.group(1)) if cnpj else "",
        data=data,
        itens=itens,
    )


# ---------- Associação com a base ----------

def _tamanho_g(descricao: str) -> float | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(KG|K|GR?|LT?|ML)\b", descricao.upper())
    if not m:
        return None
    valor = float(m.group(1).replace(",", "."))
    return valor * 1000 if m.group(2) in ("KG", "K", "L", "LT") else valor


def associar(base: Base, item: ItemNota) -> ItemNota:
    """Sugere o produto da base que corresponde ao item da nota."""
    palavras = set(tokenizar(item.descricao))
    melhor, pontos = None, 0
    for alimento in base.alimentos.values():
        chaves = [t for t in tokenizar(alimento.nome.split(" (")[0]) if t not in PALAVRAS_IGNORADAS and not t.isdigit()]
        if chaves and chaves[0] in palavras:
            p = sum(t in palavras for t in chaves)
            if p > pontos:
                melhor, pontos = alimento, p
    if melhor is None:
        return item

    produtos = [p for p in base.produtos.values() if p.alimento == melhor.id]
    if item.unidade == "KG":
        produto = next((p for p in produtos if p.embalagem_g == 1000), None)
        preco = round(item.valor_unitario * (produto.embalagem_g / 1000), 2) if produto else None
    else:
        tamanho = _tamanho_g(item.descricao)
        produto = next((p for p in produtos if tamanho and abs(p.embalagem_g - tamanho) < 1), None)
        preco = item.valor_unitario if produto else None

    if produto:
        item.produto_id, item.produto, item.preco_embalagem, item.confianca = produto.id, produto.nome, preco, "alta"
    else:
        item.produto = f"{melhor.nome} (tamanho não encontrado na base)"
    return item


def processar(base: Base, html: str, url: str | None = None) -> Nota:
    nota = extrair_nota(html)
    nota.chave = extrair_chave(url) if url else None
    nota.itens = [associar(base, i) for i in nota.itens]
    return nota


# ---------- Salvar contribuição ----------

def salvar_contribuicao(emitente: str, cnpj: str, data: str, itens: list[dict], arquivo: Path = ARQ_CONTRIBUICOES) -> int:
    """Grava os preços confirmados pelo usuário. Devolve quantos preços entraram."""
    atual = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {"mercados": [], "precos": []}
    mercado_id = f"nfce-{cnpj}" if cnpj else f"nfce-{re.sub(r'[^a-z0-9]', '', emitente.lower())[:20]}"
    if not any(m["id"] == mercado_id for m in atual["mercados"]):
        atual["mercados"].append({"id": mercado_id, "nome": emitente.title(), "regiao": "via NFC-e"})
    novos = 0
    for i in itens:
        if not i.get("produto_id") or not i.get("preco") or i["preco"] <= 0:
            continue
        atual["precos"].append({"produto": i["produto_id"], "mercado": mercado_id, "preco": round(float(i["preco"]), 2), "data": data, "fonte": "nfce"})
        novos += 1
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")
    return novos


def nota_json(nota: Nota) -> dict:
    return asdict(nota)
