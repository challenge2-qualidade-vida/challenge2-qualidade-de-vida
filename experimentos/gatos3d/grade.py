"""Tópico 25: junta as poses renderizadas em uma única imagem para o site.

Rodar:  .venv/bin/python experimentos/gatos3d/grade.py <pasta das poses> mia
Gera:   src/web/img/gatos3d/<gato>.webp (a grade) e <gato>-frente.webp (imagem parada)
"""

import json
import sys
from pathlib import Path

from PIL import Image

COLUNAS, LINHAS = 13, 9
LARGURA_CELULA = 360


def main():
    pasta, gato = Path(sys.argv[1]), sys.argv[2]
    saida = Path(__file__).resolve().parents[2] / "src" / "web" / "img" / "gatos3d"
    saida.mkdir(parents=True, exist_ok=True)
    poses = {(l, c): Image.open(pasta / f"p_{l}_{c}.png").convert("RGBA") for l in range(LINHAS) for c in range(COLUNAS)}
    # Corta o mesmo retângulo em todas as poses, senão o gato "pula" ao trocar.
    caixas = [im.getbbox() for im in poses.values()]
    caixa = (min(b[0] for b in caixas), min(b[1] for b in caixas), max(b[2] for b in caixas), max(b[3] for b in caixas))
    w, h = caixa[2] - caixa[0], caixa[3] - caixa[1]
    cw, ch = LARGURA_CELULA, round(h * LARGURA_CELULA / w)
    grade = Image.new("RGBA", (cw * COLUNAS, ch * LINHAS))
    for (l, c), im in poses.items():
        grade.paste(im.crop(caixa).resize((cw, ch), Image.LANCZOS), (c * cw, l * ch))
    grade.save(saida / f"{gato}.webp", quality=84, method=6)
    frente = poses[(LINHAS // 2, COLUNAS // 2)].crop(caixa)
    frente.resize((cw, ch), Image.LANCZOS).save(saida / f"{gato}-frente.webp", quality=88, method=6)
    print(json.dumps({"colunas": COLUNAS, "linhas": LINHAS, "celula": [cw, ch]}))
    print((saida / f"{gato}.webp").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
