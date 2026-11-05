"""Tópico 26: junta os alimentos gerados em uma única imagem para a cena 3D.

Rodar:  .venv/bin/python experimentos/gatos3d/comida.py <pasta com <id>_recorte.png>
A ordem de ORDEM precisa ser a mesma de ATLAS em src/web/cena3d.js.
"""

import sys
from pathlib import Path

from PIL import Image

ORDEM = [
    "tomate", "banana", "ovo", "arroz", "cenoura", "laranja", "feijao_carioca",
    "repolho", "abobora", "leite", "frango_coxa", "macarrao", "maca", "batata",
    "mandioca", "cebola", "feijao_preto", "lentilha", "farinha_mandioca", "aveia", "acucar",
    "oleo_soja", "sardinha", "frango_peito", "patinho", "lombo_porco", "mucarela", "pao_frances",
]
COLUNAS, CELULA, MARGEM = 7, 192, 6


def main():
    pasta = Path(sys.argv[1])
    linhas = (len(ORDEM) + COLUNAS - 1) // COLUNAS
    atlas = Image.new("RGBA", (COLUNAS * CELULA, linhas * CELULA), (0, 0, 0, 0))
    for i, nome in enumerate(ORDEM):
        arquivo = pasta / f"{nome}_recorte.png"
        if not arquivo.exists():
            print("falta", nome)
            continue
        im = Image.open(arquivo).convert("RGBA")
        im = im.crop(im.getchannel("A").getbbox())
        # Todo alimento ocupa a célula do mesmo jeito, com margem para o filtro não vazar.
        im.thumbnail((CELULA - MARGEM * 2, CELULA - MARGEM * 2), Image.LANCZOS)
        x = (i % COLUNAS) * CELULA + (CELULA - im.width) // 2
        y = (i // COLUNAS) * CELULA + (CELULA - im.height) // 2
        atlas.alpha_composite(im, (x, y))
    saida = Path(__file__).resolve().parents[2] / "src" / "web" / "img" / "comida.webp"
    atlas.save(saida, quality=84, method=6, alpha_quality=90)
    print(atlas.size, saida.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
