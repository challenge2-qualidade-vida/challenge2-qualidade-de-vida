"""Configuração do backend, lida das variáveis de ambiente (e do .env) num único lugar."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

NOMES_DOS_MODELOS_DE_EMBEDDINGS = {
    "e5": "intfloat/multilingual-e5-base",
    "qwen3": "qwen3-embedding:4b",
}


class Configuracao(BaseSettings):
    """Valores de configuração. Cada campo vem da variável de ambiente de mesmo nome, em maiúsculas."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"
    ollama_modelo: str = "qwen2.5:7b"
    ollama_contexto: int = Field(default=8192, ge=2048)
    # segundos de espera por resposta do LLM; na CPU, cinco receitas no prompt passam de 10 min
    ollama_tempo_limite: float = Field(default=1800, gt=0)
    modelo_embeddings: Literal["e5", "qwen3"] = "e5"
    # auto: mps no Mac com Apple Silicon, cuda se houver GPU NVIDIA, senão cpu
    dispositivo_embeddings: Literal["auto", "cpu", "mps", "cuda"] = "auto"
    limiar_similaridade: float = Field(default=0.845, ge=0.0, le=1.0)
    tolerancia_empate: float = Field(default=0.01, ge=0.0, le=1.0)
    # sempre disponíveis, em português e em inglês (receitas do RecipeNLG); lista provisória
    ingredientes_basicos: list[str] = ["sal", "agua", "oleo", "salt", "water", "oil"]

    @property
    def nome_do_modelo_de_embeddings(self) -> str:
        """Nome completo do modelo de embeddings em uso."""
        return NOMES_DOS_MODELOS_DE_EMBEDDINGS[self.modelo_embeddings]

    @property
    def colecao(self) -> str:
        """Coleção do Qdrant do modelo em uso: uma por modelo, porque as dimensões diferem."""
        return self.colecao_da_amostra(None)

    def colecao_da_amostra(self, amostra: int | None) -> str:
        """Coleção da base inteira ou de uma amostra fixa de receitas (ex.: _amostra400)."""
        sufixo = f"_amostra{amostra}" if amostra else ""
        return f"base_conhecimento_{self.modelo_embeddings}{sufixo}"


@lru_cache
def obter_configuracao() -> Configuracao:
    """Devolve a configuração, lida uma vez por processo."""
    return Configuracao()
