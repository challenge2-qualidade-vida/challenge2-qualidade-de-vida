# Script usado para gerar as imagens de src/web/img a partir dos originais em docs/marca (ver docs/desenvolvimento/15-identidade-visual.md).
"""Recorta os personagens e a logo, com fundo transparente, para o site."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

origem, destino = Path(sys.argv[1]), Path(sys.argv[2])
destino.mkdir(parents=True, exist_ok=True)


def fundo_transparente(im, tolerancia):
    """Torna transparente o fundo claro ligado às bordas (flood fill)."""
    a = np.array(im.convert("RGBA")).astype(int)
    rgb = a[..., :3]
    ref = np.median(np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]), axis=0)
    parecido = (np.abs(rgb - ref).max(axis=2) <= tolerancia) | (rgb.min(axis=2) >= 238)
    rotulos, _ = ndimage.label(parecido)
    bordas = set(np.unique(np.concatenate([rotulos[0], rotulos[-1], rotulos[:, 0], rotulos[:, -1]]))) - {0}
    fundo = np.isin(rotulos, list(bordas))
    # Suaviza a borda: 1 px de transição.
    alfa = np.where(fundo, 0, 255).astype(np.uint8)
    alfa = np.array(Image.fromarray(alfa).filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(0.8)))
    a[..., 3] = np.minimum(a[..., 3], alfa)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def salvar(im, nome, largura):
    caixa = im.getbbox()
    im = im.crop(caixa)
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    im.save(destino / f"{nome}.png", optimize=True)
    im.save(destino / f"{nome}.webp", quality=88, method=6)
    print(nome, im.size, (destino / f"{nome}.webp").stat().st_size // 1024, "KB webp")


# --- Quatro personagens (imagem sem texto) ---
turma = Image.open(origem / "imagem3").convert("RGBA")
turma = turma.crop((0, 0, turma.width, turma.height - 12))      # tira a faixa cinza de baixo
turma = fundo_transparente(turma, 18)
arr = np.array(turma)
opaco = arr[..., 3] > 40
# Núcleo escuro (contornos e pelagem): as sombras do chão são claras e ficam de fora,
# então os gatos se separam. Depois os "buracos" (peito, patas, cupom) são preenchidos.
nucleo = opaco & (arr[..., :3].min(axis=2) < 200)
rotulos, n = ndimage.label(nucleo)
tamanhos = ndimage.sum(nucleo, rotulos, range(1, n + 1))
maiores = (np.argsort(tamanhos)[::-1][:4] + 1).tolist()
centros = {r: ndimage.center_of_mass(nucleo, rotulos, r) for r in maiores}
por_x = sorted(maiores, key=lambda r: centros[r][1])
mia, cifrao = por_x[0], por_x[1]
miauricio, recibaldo = sorted(por_x[2:], key=lambda r: centros[r][0])
for nome, r in [("mia", mia), ("cifrao", cifrao), ("miauricio", miauricio), ("recibaldo", recibaldo)]:
    cheio = ndimage.binary_fill_holes(rotulos == r)
    cheio = ndimage.binary_dilation(cheio, iterations=2) & opaco   # recupera a borda clara do contorno
    so = arr.copy()
    so[..., 3] = np.where(cheio, arr[..., 3], 0)
    salvar(Image.fromarray(so), nome, 420)

# --- Logo ---
logo = fundo_transparente(Image.open(origem / "imagem4"), 14)
salvar(logo, "logo", 600)
w, h = logo.size
salvar(logo.crop((0, int(h * 0.07), w, int(h * 0.63))), "logo-gato", 360)
salvar(logo.crop((0, int(h * 0.64), w, int(h * 0.76))), "logo-nome", 520)
# Favicon e ícone: cabeça do gato num círculo creme
cabeca = logo.crop((int(w * 0.27), int(h * 0.08), int(w * 0.75), int(h * 0.48)))
lado = max(cabeca.size)
icone = Image.new("RGBA", (lado, lado), (250, 245, 234, 255))
icone.alpha_composite(cabeca, ((lado - cabeca.width) // 2, (lado - cabeca.height) // 2))
for tam in (32, 192, 512):
    icone.resize((tam, tam), Image.LANCZOS).save(destino / f"icone-{tam}.png", optimize=True)
print("icones ok")
