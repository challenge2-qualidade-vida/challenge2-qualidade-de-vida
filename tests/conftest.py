import os

# Os testes nunca chamam um LLM de verdade: a API sobe no modo sem LLM e os
# testes do assistente usam um LLM falso (ver test_assistente.py).
os.environ["LLM_PROVEDOR"] = "nenhum"
