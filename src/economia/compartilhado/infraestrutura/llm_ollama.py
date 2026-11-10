"""Adaptador do LLM local servido pelo Ollama.

Fica atrás da porta `ModeloDeLinguagem`: trocar de provedor (API, #13) não muda a aplicação.
"""

import json
from typing import Any


class ModeloOllama:
    def __init__(
        self,
        url: str = "http://localhost:11434",
        modelo: str = "qwen2.5:7b",
        temperatura: float = 0.2,
        contexto: int = 8192,
        tempo_limite: float = 1800,
        cliente: Any = None,
    ):
        if cliente is None:
            import ollama

            cliente = ollama.Client(host=url, timeout=tempo_limite)
        self._cliente = cliente
        self.modelo = modelo
        # o padrão do Ollama é 4096 tokens; cinco receitas longas mais as instruções passam
        # disso, e o Ollama corta o começo do prompt sem avisar
        self._opcoes = {"temperature": temperatura, "num_ctx": contexto}

    def _conversar(self, sistema: str, mensagem: str, formato: Any = None) -> str:
        resposta = self._cliente.chat(
            model=self.modelo,
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": mensagem},
            ],
            options=self._opcoes,
            format=formato,
        )
        return resposta["message"]["content"].strip()

    def gerar(self, sistema: str, mensagem: str) -> str:
        """Texto livre."""
        return self._conversar(sistema, mensagem)

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        """Saída estruturada: o Ollama restringe a geração ao esquema JSON."""
        return json.loads(self._conversar(sistema, mensagem, formato=esquema))
