"""Tópico 25: tira o fundo liso da imagem gerada, sem franja clara no pelo.

Rodar:  .venv/bin/python experimentos/gatos3d/recorte_mia.py <original> <máscara do rembg> <imagem da moeda> <saída>
"""

import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd

# Moeda: centro e raio na imagem da Mia e na imagem de onde ela vem.
MOEDA_DESTINO = (427, 632, 29)
MOEDA_ORIGEM = (452, 666, 35)
# Patas: centro e raios.
PATAS = [(258, 922, 52, 38), (358, 925, 62, 42), (478, 925, 62, 42), (616, 922, 70, 38)]
INICIO_CHAO, ALTURA_CHAO = 880, 972  # faixa da sombra no chão; abaixo dela, nada é pelo


def main():
    original, mascara, fonte_moeda, saida = sys.argv[1:5]
    img = Image.open(original).convert("RGB")
    c = np.asarray(img, float) / 255
    base = np.asarray(Image.open(mascara).getchannel("A"), float) / 255

    # O miolo do gato é a máscara sem buracos: ela confundia o rosa das orelhas com o fundo.
    miolo = nd.binary_fill_holes(base > 0.5)
    miolo = nd.binary_erosion(miolo, iterations=6)
    perto = nd.binary_dilation(miolo, iterations=34)

    # Cor do fundo em cada ponto: média só do que está longe do gato.
    longe = (~nd.binary_dilation(miolo, iterations=48)).astype(float)
    peso = nd.gaussian_filter(longe, 40) + 1e-4
    fundo = np.stack([nd.gaussian_filter(c[..., i] * longe, 40) / peso for i in range(3)], -1)

    # Na borda, a transparência vem de quanto o fio difere do fundo claro.
    # Perto do chão a exigência sobe, para a sombra não virar pelo.
    diferenca = np.linalg.norm(c - fundo, axis=-1)
    fio = np.clip((diferenca - 0.06) / 0.5, 0, 1)
    fio[INICIO_CHAO:] = np.clip((diferenca[INICIO_CHAO:] - 0.42) / 0.3, 0, 1)
    fio *= perto
    fio[ALTURA_CHAO:] = 0
    alfa = np.maximum(nd.gaussian_filter(miolo.astype(float), 1.2), fio)

    # O fio pega a cor do pelo mais próximo: assim nada do fundo claro fica na borda.
    dentro = nd.binary_erosion(miolo, iterations=3)
    indices = nd.distance_transform_edt(~dentro, return_distances=False, return_indices=True)
    vizinho = c[indices[0], indices[1]]
    frente = np.where(dentro[..., None], c, vizinho)
    alfa = np.where(dentro, 1.0, alfa)

    # Na base, o fundo e os pelos brancos se confundem: o contorno vem das medidas das patas.
    yy, xx = np.mgrid[: alfa.shape[0], : alfa.shape[1]]
    def dentro_de(cx, cy, rx, ry, folga=0.08):
        return np.clip((1 + folga - ((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2) / folga, 0, 1)
    patas = np.max([dentro_de(*p) for p in PATAS], axis=0)
    corpo = dentro_de(470, 715, 292, 252)
    canto = (xx > 560) & (yy > 840)
    alfa[canto] *= np.maximum(corpo, patas)[canto]
    pes = yy > 905
    alfa[pes] *= patas[pes]
    alfa = nd.gaussian_filter(alfa, 0.5)

    final = Image.fromarray((np.dstack([frente, alfa]) * 255).round().astype("uint8"), "RGBA")

    # A moeda desta imagem saiu com um símbolo estranho; a da outra tem o cifrão.
    cx, cy, r = MOEDA_ORIGEM
    dx, dy, dr = MOEDA_DESTINO
    moeda = Image.open(fonte_moeda).convert("RGB").crop((cx - r, cy - r, cx + r, cy + r)).resize((dr * 2, dr * 2), Image.LANCZOS)
    recorte = Image.new("L", (dr * 8, dr * 8), 0)
    ImageDraw.Draw(recorte).ellipse((6, 6, dr * 8 - 6, dr * 8 - 6), fill=255)
    recorte = recorte.resize((dr * 2, dr * 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    final.paste(moeda, (dx - dr, dy - dr), recorte)
    final.save(saida)
    print(final.size, final.getchannel("A").getbbox())


if __name__ == "__main__":
    main()
