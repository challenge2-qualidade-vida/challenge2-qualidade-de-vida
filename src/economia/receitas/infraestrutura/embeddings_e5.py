"""Embeddings com o intfloat/multilingual-e5-base (sentence-transformers, no processo)."""

from collections.abc import Sequence
from typing import Any

NOME_DO_MODELO = "intfloat/multilingual-e5-base"
LIMITE_DE_TOKENS = 512
PREFIXO_DA_PERGUNTA = "query: "
PREFIXO_DO_TRECHO = "passage: "


def escolher_dispositivo(preferencia: str = "auto") -> str:
    """auto: mps no Mac com Apple Silicon, cuda com GPU NVIDIA, senão cpu."""
    if preferencia != "auto":
        return preferencia
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class GeradorE5:
    """Gerador de embeddings do e5. Os prefixos `query:` e `passage:` fazem parte do treino do modelo."""

    nome = NOME_DO_MODELO
    dimensao = 768

    def __init__(
        self, dispositivo: str = "auto", tamanho_do_lote: int = 16, modelo: Any = None
    ):
        if modelo is None:
            from sentence_transformers import SentenceTransformer

            modelo = SentenceTransformer(
                NOME_DO_MODELO, device=escolher_dispositivo(dispositivo)
            )
            modelo.max_seq_length = LIMITE_DE_TOKENS
        self._modelo = modelo
        self._tamanho_do_lote = tamanho_do_lote

    def _gerar(self, textos: list[str]) -> list[list[float]]:
        vetores = self._modelo.encode(
            textos,
            batch_size=self._tamanho_do_lote,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [list(map(float, v)) for v in vetores]

    def gerar_para_trechos(self, textos: Sequence[str]) -> list[list[float]]:
        return self._gerar([f"{PREFIXO_DO_TRECHO}{t}" for t in textos])

    def gerar_para_pergunta(self, pergunta: str) -> list[float]:
        return self._gerar([f"{PREFIXO_DA_PERGUNTA}{pergunta}"])[0]


def contador_de_tokens_e5():
    """Conta os tokens como o e5 vê o trecho: com o prefixo `passage:` e os tokens especiais.

    Os dois modelos recebem os mesmos trechos, cortados por este contador, para a comparação ser justa.
    Só carrega o tokenizador, não o modelo.
    """
    from transformers import AutoTokenizer

    tokenizador = AutoTokenizer.from_pretrained(NOME_DO_MODELO)
    # o corte conta textos maiores que 512 antes de cortar; sem isso, o tokenizador avisa a cada vez
    tokenizador.model_max_length = 1_000_000

    def contar(texto: str) -> int:
        return len(
            tokenizador(f"{PREFIXO_DO_TRECHO}{texto}", add_special_tokens=True)[
                "input_ids"
            ]
        )

    return contar
