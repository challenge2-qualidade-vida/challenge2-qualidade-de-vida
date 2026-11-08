"""Leitura dos prompts versionados em `prompts/<agente>/<nome>_v<versao>.md`."""

from pathlib import Path

PASTA_DOS_PROMPTS = Path(__file__).resolve().parents[4] / "prompts"


def carregar_prompt(agente: str, nome: str, pasta: Path = PASTA_DOS_PROMPTS) -> str:
    """Texto do prompt. `nome` inclui a versão (ex.: "resposta_com_fontes_v1")."""
    caminho = pasta / agente / f"{nome}.md"
    if not caminho.is_file():
        raise FileNotFoundError(f"Prompt não encontrado: {caminho}")
    return caminho.read_text(encoding="utf-8").strip()
