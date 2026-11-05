"""Tópico 25: recorta o nome "EconoMIA" da arte original, com os furos transparentes.

Rodar:  .venv/bin/python experimentos/gatos3d/nome.py
Depois rode logo.py, que usa esta imagem no logo completo.
"""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

RAIZ = Path(__file__).resolve().parents[2]
CAIXA = (150, 783, 1140, 945)  # o nome, na arte original
LARGURA = 640


def main():
    arte = Image.open(RAIZ / "docs" / "marca" / "logo-original.png").convert("RGB").crop(CAIXA)
    c = np.asarray(arte, float) / 255
    fundo = c[:, :6].reshape(-1, 3).mean(axis=0)  # a borda esquerda é só fundo
    # Quanto mais longe do creme do fundo, mais opaco. Assim o miolo dos "o" e a estrela somem.
    alfa = np.clip((np.linalg.norm(c - fundo, axis=-1) - 0.08) / 0.42, 0, 1)
    # A borda pega a cor da letra vizinha, para o creme não contaminar o contorno.
    cheio = alfa > 0.95
    indices = nd.distance_transform_edt(~cheio, return_distances=False, return_indices=True)
    frente = c[indices[0], indices[1]]
    nome = Image.fromarray((np.dstack([frente, alfa]) * 255).round().astype("uint8"), "RGBA")
    nome = nome.crop(nome.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
    nome = nome.resize((LARGURA, round(nome.height * LARGURA / nome.width)), Image.LANCZOS)
    saida = RAIZ / "src" / "web" / "img"
    nome.save(saida / "logo-nome.png", optimize=True)
    nome.save(saida / "logo-nome.webp", quality=92, method=6, alpha_quality=95)
    print(nome.size)


if __name__ == "__main__":
    main()
