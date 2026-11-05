"""Tópico 25: monta a imagem da turma com os quatro gatos já recortados.

Rodar:  .venv/bin/python experimentos/gatos3d/turma.py <pasta com <gato>_final.png>
"""

import sys
from pathlib import Path

from PIL import Image

# Desenhados nesta ordem: quem vem depois fica na frente. O Recibaldo mostra o recibo inteiro.
POSICOES = (("mia", 0, 620), ("miauricio", 1480, 660), ("cifrao", 1000, 650), ("recibaldo", 480, 640))


def main():
    pasta = Path(sys.argv[1])
    largura, altura = 2030, 700
    turma = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    for nome, x, h in POSICOES:
        gato = Image.open(pasta / f"{nome}_final.png")
        gato = gato.resize((round(gato.width * h / gato.height), h), Image.LANCZOS)
        turma.alpha_composite(gato, (x, altura - h - 10))
    turma = turma.crop(turma.getbbox())
    turma = turma.resize((1400, round(turma.height * 1400 / turma.width)), Image.LANCZOS)
    saida = Path(__file__).resolve().parents[2] / "src" / "web" / "img"
    turma.save(saida / "turma.webp", quality=86, method=6, alpha_quality=92)
    turma.save(saida / "turma.png", optimize=True)
    print(turma.size)


if __name__ == "__main__":
    main()
