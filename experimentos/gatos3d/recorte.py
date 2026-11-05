"""Tópico 25: tira o fundo liso da imagem gerada, sem franja clara no pelo.

Rodar:  .venv/bin/python experimentos/gatos3d/recorte.py <gato> <original> <máscara do rembg> <saída> [imagem da moeda]
"""

import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd

# patas: centro e raios de cada pata, para o contorno da base, onde fundo e pelo branco se confundem.
# corpo e canto: elipse que arredonda o que sobrou atrás do corpo, a partir do ponto de `canto`.
# moeda: troca a moeda por outra, com (x, y, raio) na imagem e na fonte.
# incluir: polígonos que a máscara perdeu, como o recibo branco sobre o fundo claro.
# soltos: elipses onde vale procurar pelo longe do corpo, como a ponta do rabo.
# corte: retângulo final, com folga para a cabeça girar.
GATOS = {
    "mia": {
        "patas": [(258, 922, 52, 38), (358, 925, 62, 42), (478, 925, 62, 42), (616, 922, 70, 38)],
        "corpo": (470, 715, 292, 252), "canto": (560, 840),
        "moeda": ((427, 632, 29), (452, 666, 35)),
        "corte": (60, 0, 850, 990),
    },
    "cifrao": {
        "patas": [(196, 897, 52, 48), (345, 903, 97, 62), (587, 900, 95, 62), (726, 892, 46, 48)],
        "corte": (40, 0, 856, 985),
    },
    "miauricio": {
        "patas": [(180, 865, 42, 52), (285, 908, 85, 45), (580, 915, 85, 47), (683, 898, 22, 34)],
        "corte": (55, 0, 880, 985),
    },
    "recibaldo": {
        "patas": [(215, 870, 75, 80), (362, 923, 80, 42), (538, 923, 82, 42), (697, 880, 79, 68)],
        "incluir": [[(722, 543), (830, 572), (748, 885), (647, 853)]],
        "soltos": [(815, 855, 85, 65)],
        "corte": (80, 40, 896, 985),
    },
}
INICIO_CHAO, ALTURA_CHAO = 880, 972  # faixa da sombra no chão; abaixo dela, nada é pelo


def main():
    nome, original, mascara, saida = sys.argv[1:5]
    g = GATOS[nome]
    img = Image.open(original).convert("RGB")
    c = np.asarray(img, float) / 255
    base = np.asarray(Image.open(mascara).getchannel("A"), float) / 255

    yy, xx = np.mgrid[: base.shape[0], : base.shape[1]]

    def dentro_de(cx, cy, rx, ry, folga=0.08):
        return np.clip((1 + folga - ((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2) / folga, 0, 1)

    patas = np.max([dentro_de(*p) for p in g["patas"]], axis=0)
    desenho = Image.new("L", img.size, 0)
    for poligono in g.get("incluir", []):
        ImageDraw.Draw(desenho).polygon(poligono, fill=255)

    # O miolo do gato é a máscara sem buracos: ela confundia o rosa das orelhas com o fundo.
    miolo = (base > 0.5) | (patas >= 1) | (np.asarray(desenho) > 0)
    miolo = nd.binary_fill_holes(miolo)
    miolo = nd.binary_erosion(miolo, iterations=6)

    # Cor do fundo em cada ponto: média só do que está longe do gato.
    longe = (~nd.binary_dilation(miolo, iterations=48)).astype(float)
    peso = nd.gaussian_filter(longe, 40) + 1e-4
    fundo = np.stack([nd.gaussian_filter(c[..., i] * longe, 40) / peso for i in range(3)], -1)

    # Na borda, a transparência vem de quanto o fio difere do fundo claro.
    # Perto do chão a exigência sobe, para a sombra não virar pelo.
    diferenca = np.linalg.norm(c - fundo, axis=-1)
    fio = np.clip((diferenca - 0.06) / 0.5, 0, 1)
    fio[INICIO_CHAO:] = np.clip((diferenca[INICIO_CHAO:] - 0.42) / 0.3, 0, 1)
    fio *= nd.binary_dilation(miolo, iterations=34)
    # Nas partes soltas só o que é bem escuro é pelo: o fundo ali é mal estimado.
    for solto in g.get("soltos", []):
        zona = (dentro_de(*solto) > 0) & ~nd.binary_dilation(miolo, iterations=10)
        fio[zona] = np.clip((0.5 - c.mean(axis=-1)[zona]) / 0.2, 0, 1)
    fio[ALTURA_CHAO:] = 0
    alfa = np.maximum(nd.gaussian_filter(miolo.astype(float), 1.2), fio)

    # Fio fraco pega a cor do pelo mais próximo: assim nada do fundo claro fica na borda.
    dentro = nd.binary_erosion(miolo, iterations=3) | (fio > 0.9)
    indices = nd.distance_transform_edt(~dentro, return_distances=False, return_indices=True)
    frente = np.where(dentro[..., None], c, c[indices[0], indices[1]])
    alfa = np.where(nd.binary_erosion(miolo, iterations=3), 1.0, alfa)

    if "corpo" in g:
        canto = (xx > g["canto"][0]) & (yy > g["canto"][1])
        alfa[canto] *= np.maximum(dentro_de(*g["corpo"]), patas)[canto]
    pes = yy > 905
    alfa[pes] *= patas[pes]
    alfa = nd.gaussian_filter(alfa, 0.5)

    final = Image.fromarray((np.dstack([frente, alfa]) * 255).round().astype("uint8"), "RGBA")
    if "moeda" in g:
        (dx, dy, dr), (cx, cy, r) = g["moeda"]
        moeda = Image.open(sys.argv[5]).convert("RGB").crop((cx - r, cy - r, cx + r, cy + r)).resize((dr * 2, dr * 2), Image.LANCZOS)
        recorte = Image.new("L", (dr * 8, dr * 8), 0)
        ImageDraw.Draw(recorte).ellipse((6, 6, dr * 8 - 6, dr * 8 - 6), fill=255)
        recorte = recorte.resize((dr * 2, dr * 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
        final.paste(moeda, (dx - dr, dy - dr), recorte)
    final = final.crop(g["corte"])
    final.save(saida)
    print(nome, final.size)


if __name__ == "__main__":
    main()
