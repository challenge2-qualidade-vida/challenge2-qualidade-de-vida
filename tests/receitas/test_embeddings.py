import math

import numpy as np

from economia.receitas.infraestrutura.embeddings_e5 import (
    GeradorE5,
    escolher_dispositivo,
)
from economia.receitas.infraestrutura.embeddings_ollama import GeradorOllama


class ModeloFalso:
    def __init__(self):
        self.recebidos = []

    def encode(self, textos, **kwargs):
        self.recebidos.append((list(textos), kwargs))
        return np.ones((len(textos), 3))


def test_e5_usa_os_prefixos_e_normaliza():
    modelo = ModeloFalso()
    gerador = GeradorE5(modelo=modelo)
    gerador.gerar_para_trechos(["arroz"])
    gerador.gerar_para_pergunta("o que faço com arroz?")
    assert modelo.recebidos[0][0] == ["passage: arroz"]
    assert modelo.recebidos[1][0] == ["query: o que faço com arroz?"]
    assert modelo.recebidos[0][1]["normalize_embeddings"] is True


def test_dispositivo_explicito_nao_consulta_o_torch():
    assert escolher_dispositivo("cpu") == "cpu"


class ClienteOllamaFalso:
    def __init__(self):
        self.recebidos = []

    def embed(self, model, input, truncate):
        self.recebidos.append((model, input))
        return {"embeddings": [[3.0, 4.0] for _ in input]}


def test_ollama_poe_a_instrucao_so_na_pergunta_e_normaliza():
    cliente = ClienteOllamaFalso()
    gerador = GeradorOllama(cliente=cliente)
    [vetor] = gerador.gerar_para_trechos(["arroz"])
    gerador.gerar_para_pergunta("o que faço com arroz?")
    assert cliente.recebidos[0] == ("qwen3-embedding:4b", ["arroz"])
    pergunta = cliente.recebidos[1][1][0]
    assert pergunta.startswith("Instruct: ")
    assert pergunta.endswith("\nQuery: o que faço com arroz?")
    assert math.isclose(math.hypot(*vetor), 1.0)
    assert vetor == [0.6, 0.8]
