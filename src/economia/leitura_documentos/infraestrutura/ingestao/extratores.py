"""Extração de texto de documentos da base de conhecimento."""
from pathlib import Path
import pymupdf

def extrair_pdf(caminho: Path) -> str:
    """Extrai texto de PDF textual, preservando separação entre páginas."""
    paginas = []
    with pymupdf.open(caminho) as documento:
        for numero, pagina in enumerate(documento, start=1):
            texto = pagina.get_text("text")
            if texto.strip():
                paginas.append(f"[Página {numero}]\\n{texto}")
    return "\\n\\n".join(paginas)

def extrair_texto(caminho: Path) -> str:
    """Extrai texto dos formatos suportados."""
    extensao = caminho.suffix.lower()
    if extensao == ".pdf":
        return extrair_pdf(caminho)
    if extensao in {".txt", ".md"}:
        return caminho.read_text(encoding="utf-8")
    raise ValueError(f"Formato não suportado: {extensao}")
