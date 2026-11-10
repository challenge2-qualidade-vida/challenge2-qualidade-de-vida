"""Configuração do backend, lida das variáveis de ambiente (e do .env) num único lugar."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
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
    # Abaixo do limiar, a resposta diz que não encontrou (RN11). Um por modelo: os scores de cada
    # modelo têm escalas diferentes. Calibrados com o `comparar` no conjunto perguntas_rag_v2.
    limiar_similaridade_e5: float = Field(default=0.845, ge=0.0, le=1.0)
    limiar_similaridade_qwen3: float = Field(default=0.620, ge=0.0, le=1.0)
    # LIMIAR_SIMILARIDADE (um só limiar) foi substituído pelos dois acima. Lido só para dar erro:
    # ignorado em silêncio, o .env antigo cairia no padrão sem aviso.
    limiar_unico_antigo: float | None = Field(
        default=None, validation_alias="limiar_similaridade", exclude=True
    )
    tolerancia_empate: float = Field(default=0.01, ge=0.0, le=1.0)
    # sempre disponíveis, em português e em inglês (receitas do RecipeNLG); lista provisória
    ingredientes_basicos: list[str] = ["sal", "agua", "oleo", "salt", "water", "oil"]
    # redação da resposta do Miau-ricio: prompt versionado, saída estruturada (JSON com os
    # trechos usados) e segunda tentativa quando o LLM responde sem citar os trechos
    prompt_de_resposta: str = "resposta_com_fontes_v1"
    resposta_estruturada: bool = False
    segunda_tentativa_de_citacao: bool = False

    @field_validator("limiar_unico_antigo")
    @classmethod
    def _recusar_limiar_unico(cls, valor: float | None) -> None:
        if valor is not None:
            raise ValueError(
                "LIMIAR_SIMILARIDADE não existe mais: use LIMIAR_SIMILARIDADE_E5 e "
                "LIMIAR_SIMILARIDADE_QWEN3 (cada modelo tem a sua escala de score)"
            )

    @property
    def limiar_similaridade(self) -> float:
        """Limiar do modelo de embeddings em uso."""
        return {
            "e5": self.limiar_similaridade_e5,
            "qwen3": self.limiar_similaridade_qwen3,
        }[self.modelo_embeddings]

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
