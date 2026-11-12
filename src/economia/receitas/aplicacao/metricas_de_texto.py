"""Métricas que comparam a resposta gerada com a resposta de referência.

- ROUGE-1 F1: palavras em comum, sem olhar a ordem.
- ROUGE-L F1: maior subsequência comum de palavras, então a ordem conta.
- Cosseno: proximidade de sentido entre os embeddings dos dois textos.

O ROUGE penaliza a resposta certa escrita com outras palavras, e o cosseno não confere números.
As medidas servem para comparar execuções, não como nota absoluta. Todas as contas são
determinísticas (RN01).
"""

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence

from economia.receitas.aplicacao.portas import GeradorDeEmbeddings

# citações da resposta do RAG, como [2] ou [1, 3]: não fazem parte do texto comparado
_CITACAO = re.compile(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]")
# número com vírgula ou ponto conta como uma palavra só ("13,3")
_PALAVRA = re.compile(r"\d+(?:[.,]\d+)*|[a-z]+")


def palavras(texto: str) -> list[str]:
    """Palavras do texto, sem acento, sem caixa, sem pontuação e sem as citações."""
    sem_citacao = _CITACAO.sub(" ", texto)
    decomposto = unicodedata.normalize("NFKD", sem_citacao.casefold())
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return _PALAVRA.findall(sem_acento)


def _f1(em_comum: int, na_resposta: int, na_referencia: int) -> float:
    if not em_comum:
        return 0.0
    precisao = em_comum / na_resposta
    revocacao = em_comum / na_referencia
    return 2 * precisao * revocacao / (precisao + revocacao)


def rouge_1_f1(resposta: str, referencia: str) -> float:
    """F1 das palavras em comum. Palavra repetida conta até o que os dois textos têm."""
    da_resposta, da_referencia = palavras(resposta), palavras(referencia)
    em_comum = sum((Counter(da_resposta) & Counter(da_referencia)).values())
    return _f1(em_comum, len(da_resposta), len(da_referencia))


def _maior_subsequencia_comum(a: Sequence[str], b: Sequence[str]) -> int:
    """Tamanho da maior subsequência comum, guardando só a linha anterior da tabela."""
    anterior = [0] * (len(b) + 1)
    for palavra in a:
        atual = [0]
        for j, outra in enumerate(b, start=1):
            atual.append(
                anterior[j - 1] + 1
                if palavra == outra
                else max(anterior[j], atual[j - 1])
            )
        anterior = atual
    return anterior[-1]


def rouge_l_f1(resposta: str, referencia: str) -> float:
    """F1 sobre a maior subsequência comum de palavras."""
    da_resposta, da_referencia = palavras(resposta), palavras(referencia)
    em_comum = _maior_subsequencia_comum(da_resposta, da_referencia)
    return _f1(em_comum, len(da_resposta), len(da_referencia))


def cosseno(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosseno entre dois vetores. Vetor nulo dá 0."""
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(x * x for x in b))
    if not norma_a or not norma_b:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / (norma_a * norma_b)


def similaridade_com_a_referencia(
    resposta: str, referencia: str, gerador: GeradorDeEmbeddings
) -> float:
    """Cosseno entre os embeddings da resposta e da referência.

    A comparação é simétrica (nenhum dos textos é a pergunta), então os dois recebem o mesmo
    prefixo do modelo.
    """
    da_resposta, da_referencia = gerador.gerar_para_trechos([resposta, referencia])
    return cosseno(da_resposta, da_referencia)
