"""Dublês dos cenários BDD do RAG de receitas: rodam sem modelo, sem Ollama e sem servidor Qdrant."""

import hashlib
import math
import re
import unicodedata

import pytest
from qdrant_client import QdrantClient

from economia.receitas.infraestrutura.repositorio_qdrant import RepositorioQdrant

PALAVRAS_VAZIAS = {
    "a", "o", "as", "os", "e", "de", "da", "do", "das", "dos", "com", "que", "eu", "um", "uma",
    "para", "por", "em", "no", "na", "posso", "fazer", "como", "receita", "ingredientes", "modo",
    "preparo", "misture", "asse", "leve", "ao", "forno",
}  # fmt: skip


def palavras(texto: str) -> list[str]:
    sem_acento = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    )
    return [p for p in re.findall(r"[a-z]+", sem_acento) if p not in PALAVRAS_VAZIAS]


class GeradorSacoDePalavras:
    """Embedding falso e determinístico: cada palavra soma 1 numa posição fixa do vetor."""

    nome = "saco-de-palavras"
    dimensao = 256

    def _vetor(self, texto: str) -> list[float]:
        vetor = [0.0] * self.dimensao
        for palavra in palavras(texto):
            posicao = int(hashlib.md5(palavra.encode()).hexdigest(), 16) % self.dimensao
            vetor[posicao] += 1.0
        norma = math.sqrt(sum(x * x for x in vetor)) or 1.0
        return [x / norma for x in vetor]

    def gerar_para_trechos(self, textos):
        return [self._vetor(t) for t in textos]

    def gerar_para_pergunta(self, pergunta):
        return self._vetor(pergunta)


class LLMQueCitaTudo:
    """LLM falso que cita todos os trechos recebidos, na ordem."""

    def gerar(self, sistema, mensagem):
        numeros = re.findall(r"^\[(\d+)\]", mensagem, flags=re.MULTILINE)
        return "Veja: " + " ".join(f"[{n}]" for n in numeros)

    def gerar_json(self, sistema, mensagem, esquema):
        """Extração ingênua: o que vem depois de "com", separado por vírgula e "e"."""
        trecho = mensagem.split(" com ", 1)[1] if " com " in mensagem else ""
        itens = re.split(r",| e ", trecho.rstrip("?"))
        return {
            "ingredientes_pt": [i.strip() for i in itens if i.strip()],
            "ingredientes_en": [],
        }


@pytest.fixture
def contexto():
    return {
        "receitas": [],
        "documentos": [],
        "gerador": GeradorSacoDePalavras(),
        "repositorio": RepositorioQdrant(QdrantClient(":memory:"), "bdd"),
        "llm": LLMQueCitaTudo(),
        # o saco de palavras dá scores menores que um modelo de verdade
        "limiar": 0.2,
        "tolerancia": 0.01,
    }
