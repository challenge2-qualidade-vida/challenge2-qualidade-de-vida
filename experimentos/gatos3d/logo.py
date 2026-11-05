"""Tópico 25: gera o logo e os ícones do app com o rosto da Mia.

Rodar:  .venv/bin/python experimentos/gatos3d/logo.py <mia_final.png sem o corte>
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

SAIDA = Path(__file__).resolve().parents[2] / "src" / "web" / "img"
CAIXA = (70, 10, 840, 590)  # cabeça com as orelhas
FUNDO_ICONE = (176, 141, 38, 255)


def rosto(mia):
    """Só a cabeça: abaixo das bochechas, o corte acompanha a curva do queixo."""
    a = np.asarray(mia.convert("RGBA")).copy()
    yy, xx = np.mgrid[: a.shape[0], : a.shape[1]]
    queixo = ((xx - 447) / 345) ** 2 + ((yy - 300) / 282) ** 2 < 1
    manter = nd.gaussian_filter(((yy < 400) | queixo).astype(float), 1.5)
    a[..., 3] = (a[..., 3] * manter).astype("uint8")
    return Image.fromarray(a, "RGBA").crop(CAIXA)


def icone(cabeca, lado):
    k = 4
    t = lado * k
    c = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, t - 1, t - 1), radius=int(t * 0.22), fill=FUNDO_ICONE)
    e = t * 0.88 / cabeca.width
    h = cabeca.resize((int(cabeca.width * e), int(cabeca.height * e)), Image.LANCZOS)
    c.alpha_composite(h, ((t - h.width) // 2, (t - h.height) // 2))
    return c.resize((lado, lado), Image.LANCZOS)


def main():
    cabeca = rosto(Image.open(sys.argv[1]))
    pequeno = cabeca.resize((360, round(360 * cabeca.height / cabeca.width)), Image.LANCZOS)
    pequeno.save(SAIDA / "logo-gato.png", optimize=True)
    pequeno.save(SAIDA / "logo-gato.webp", quality=88, method=6, alpha_quality=92)
    for lado in (32, 192, 512):
        icone(cabeca, lado).save(SAIDA / f"icone-{lado}.png", optimize=True)

    # Logo completo, usado no README: o rosto em cima e o nome embaixo.
    nome = Image.open(SAIDA / "logo-nome.png").convert("RGBA")
    grande = cabeca.resize((560, round(560 * cabeca.height / cabeca.width)), Image.LANCZOS)
    logo = Image.new("RGBA", (600, grande.height + nome.height + 30), (0, 0, 0, 0))
    logo.alpha_composite(grande, (20, 0))
    logo.alpha_composite(nome, ((600 - nome.width) // 2, grande.height + 20))
    logo.save(SAIDA / "logo.png", optimize=True)
    logo.save(SAIDA / "logo.webp", quality=88, method=6, alpha_quality=92)


if __name__ == "__main__":
    main()
