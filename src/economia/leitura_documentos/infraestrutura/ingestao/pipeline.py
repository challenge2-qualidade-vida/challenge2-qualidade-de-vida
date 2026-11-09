"""Pipeline reproduzível de preparação da base de conhecimento."""
import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from .extratores import extrair_texto
from .normalizadores import normalizar_texto

LOGGER = logging.getLogger(__name__)
EXTENSOES_SUPORTADAS = {".pdf", ".txt", ".md"}

def carregar_manifesto(caminho: Path) -> dict[str, dict[str, Any]]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return {item["arquivo"]: item for item in dados.get("fontes", [])}

def preparar_documentos(pasta_entrada: Path, caminho_manifesto: Path,
                        caminho_saida: Path, caminho_relatorio: Path) -> dict[str, int]:
    """Extrai documentos catalogados e grava JSONL e relatório."""
    fontes = carregar_manifesto(caminho_manifesto)
    registros = []
    relatorio = {"processados": [], "sem_texto": [], "sem_metadados": [], "erros": []}
    for caminho in sorted(pasta_entrada.rglob("*")):
        if not caminho.is_file() or caminho.suffix.lower() not in EXTENSOES_SUPORTADAS:
            continue
        relativo = caminho.relative_to(pasta_entrada).as_posix()
        metadados = fontes.get(relativo)
        if not metadados:
            relatorio["sem_metadados"].append({"arquivo": relativo, "motivo": "Ausente no fontes.json"})
            continue
        try:
            texto = normalizar_texto(extrair_texto(caminho))
            if not texto:
                relatorio["sem_texto"].append({"arquivo": relativo, "motivo": "Sem texto extraível; pode exigir OCR"})
                continue
            hash_texto = hashlib.sha256(texto.encode("utf-8")).hexdigest()
            identificador = hashlib.sha256(relativo.encode("utf-8")).hexdigest()[:16]
            registros.append({
                "id": identificador, "texto": texto, "fonte": metadados["titulo"],
                "instituicao": metadados["instituicao"], "ano": metadados["ano"],
                "tipo_conteudo": metadados["tipo_conteudo"], "url": metadados["url"],
                "arquivo": relativo, "hash_sha256": hash_texto,
            })
            relatorio["processados"].append({"arquivo": relativo, "hash_sha256": hash_texto})
        except Exception as erro:
            LOGGER.exception("Falha ao processar %s", relativo)
            relatorio["erros"].append({"arquivo": relativo, "motivo": str(erro)})
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text("".join(json.dumps(x, ensure_ascii=False) + "\\n" for x in registros), encoding="utf-8")
    caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)
    caminho_relatorio.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    return {chave: len(valor) for chave, valor in relatorio.items()}

def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara documentos para o RAG do EconoMIA.")
    parser.add_argument("--entrada", type=Path, default=Path("data/base-conhecimento"))
    parser.add_argument("--manifesto", type=Path, default=Path("data/base-conhecimento/fontes.json"))
    parser.add_argument("--saida", type=Path, default=Path("data/processed/documentos.jsonl"))
    parser.add_argument("--relatorio", type=Path, default=Path("data/processed/relatorio_ingestao.json"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    resultado = preparar_documentos(args.entrada, args.manifesto, args.saida, args.relatorio)
    for categoria, quantidade in resultado.items():
        print(f"{categoria}: {quantidade}")

if __name__ == "__main__":
    main()
