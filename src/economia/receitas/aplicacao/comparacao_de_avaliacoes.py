"""Compara duas execuções da avaliação (antes e depois de uma mudança na base ou no modelo).

Lê os arquivos gravados por `comparar` (recuperação) e por `avaliar-respostas` (respostas) e
calcula a diferença de cada métrica, no total e por categoria. Contas determinísticas (RN01).
"""

from collections.abc import Mapping
from dataclasses import dataclass

METRICAS_DE_RECUPERACAO = (
    "recall",
    "mrr",
    "score_medio_com_resposta",
    "score_medio_sem_resposta",
    "separacao",
    "latencia_media",
)
METRICAS_DE_RESPOSTA = (
    "acuracia",
    "taxa_de_resposta",
    "recusa_correta",
    "aviso_de_preco",
    "fonte_esperada",
    "latencia_media",
)
METRICAS_POR_CATEGORIA = {
    "recuperacao": ("recall", "mrr"),
    "respostas": ("acuracia", "fonte_esperada"),
}


@dataclass(frozen=True)
class Diferenca:
    metrica: str
    antes: float | None
    depois: float | None

    @property
    def delta(self) -> float | None:
        if self.antes is None or self.depois is None:
            return None
        return round(self.depois - self.antes, 4)


def tipo_da_execucao(execucao: Mapping) -> str:
    """`recuperacao` (arquivo do `comparar`) ou `respostas` (arquivo do `avaliar-respostas`)."""
    return "recuperacao" if "modelos" in execucao else "respostas"


def resumo_da_execucao(execucao: Mapping) -> Mapping:
    """O bloco com as métricas: o primeiro modelo, na recuperação; o próprio arquivo, nas respostas."""
    if tipo_da_execucao(execucao) == "recuperacao":
        if not execucao["modelos"]:
            raise ValueError(
                "A execução de recuperação não tem nenhum modelo avaliado."
            )
        return execucao["modelos"][0]
    return execucao


def comparar_execucoes(antes: Mapping, depois: Mapping) -> list[Diferenca]:
    """Diferença das métricas gerais entre duas execuções do mesmo tipo."""
    tipo = tipo_da_execucao(antes)
    if tipo != tipo_da_execucao(depois):
        raise ValueError("As duas execuções precisam ser do mesmo tipo.")
    metricas = (
        METRICAS_DE_RECUPERACAO if tipo == "recuperacao" else METRICAS_DE_RESPOSTA
    )
    a, d = resumo_da_execucao(antes), resumo_da_execucao(depois)
    return [Diferenca(m, a.get(m), d.get(m)) for m in metricas]


def comparar_categorias(antes: Mapping, depois: Mapping) -> dict[str, list[Diferenca]]:
    """Diferença das métricas de cada categoria. Categoria nova aparece com `antes` vazio."""
    tipo = tipo_da_execucao(antes)
    metricas = METRICAS_POR_CATEGORIA[tipo]
    cat_antes = resumo_da_execucao(antes).get("por_categoria", {})
    cat_depois = resumo_da_execucao(depois).get("por_categoria", {})
    return {
        categoria: [
            Diferenca(
                m,
                cat_antes.get(categoria, {}).get(m),
                cat_depois.get(categoria, {}).get(m),
            )
            for m in metricas
        ]
        for categoria in sorted(set(cat_antes) | set(cat_depois))
    }


def formatar_delta(delta: float | None) -> str:
    if delta is None:
        return "—"
    return f"{delta:+.3f}"
