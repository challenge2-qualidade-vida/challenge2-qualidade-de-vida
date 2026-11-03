import os
import tempfile
from pathlib import Path

# Os testes nunca chamam um LLM de verdade: a API sobe no modo sem LLM e os
# testes do assistente usam um LLM falso (ver test_assistente.py).
os.environ["LLM_PROVEDOR"] = "nenhum"

# Os testes nunca gravam no arquivo de contribuições real.
os.environ["ECONOMIA_CONTRIBUICOES"] = str(Path(tempfile.mkdtemp()) / "contribuicoes.json")

# Os testes fazem muitas requisições seguidas; o limite tem teste próprio.
os.environ["ECONOMIA_SEM_LIMITES"] = "1"
