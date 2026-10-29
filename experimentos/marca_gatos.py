# Script usado para gerar as imagens de src/web/img a partir dos originais em docs/marca (ver docs/desenvolvimento/15-identidade-visual.md).
"""Gatos exportados do Canva (fundo creme) → PNG/WebP transparentes para o site."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

origem, destino = Path(sys.argv[1]), Path(sys.argv[2])


def sem_fundo(im, tolerancia=16, so_maior=True):
    a = np.array(im.convert("RGBA")).astype(int)
    rgb = a[..., :3]
    ref = np.median(np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]), axis=0)
    parecido = np.abs(rgb - ref).max(axis=2) <= tolerancia
    rot, _ = ndimage.label(parecido)
    bordas = set(np.unique(np.concatenate([rot[0], rot[-1], rot[:, 0], rot[:, -1]]))) - {0}
    opaco = ~np.isin(rot, list(bordas))
    if so_maior:
        # Fica só o gato: núcleo escuro (sem a sombra clara do chão) + o que ele envolve.
        nucleo = opaco & (rgb.min(axis=2) < 200)
        r2, n = ndimage.label(nucleo)
        maior = np.argmax(ndimage.sum(nucleo, r2, range(1, n + 1))) + 1
        opaco = ndimage.binary_dilation(ndimage.binary_fill_holes(r2 == maior), iterations=2) & opaco
    alfa = Image.fromarray((opaco * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    a[..., 3] = np.array(alfa)
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    return out.crop(out.getbbox())


def salvar(im, nome, largura):
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    im.save(destino / f"{nome}.png", optimize=True)
    im.save(destino / f"{nome}.webp", quality=88, method=6)
    print(nome, im.size, (destino / f"{nome}.webp").stat().st_size // 1024, "KB")


for pagina, nome in [(2, "mia"), (3, "cifrao"), (4, "miauricio"), (5, "recibaldo")]:
    salvar(sem_fundo(Image.open(origem / f"pagina{pagina}.png")), nome, 420)

turma = Image.open(origem / "pagina6.png")
turma = turma.crop((0, 0, turma.width, int(turma.height * 0.665)))   # sem o texto de baixo
salvar(sem_fundo(turma, so_maior=False), "turma", 900)
