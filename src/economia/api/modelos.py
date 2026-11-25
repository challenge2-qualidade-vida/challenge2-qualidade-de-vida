"""Modelos HTTP da API EconoMIA."""

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RequisicaoVerificacao(BaseModel):
    """Dados recebidos pelo endpoint de pesquisa de evidências."""

    pergunta: str = Field(min_length=1)
    limite: int = Field(default=5, ge=1, le=20)

    @field_validator("pergunta")
    @classmethod
    def validar_pergunta(cls, valor: str) -> str:
        """Remove espaços externos e rejeita perguntas vazias."""
        pergunta = valor.strip()
        if not pergunta:
            raise ValueError("A pergunta não pode ser vazia.")
        return pergunta


class FonteEvidenciaResposta(BaseModel):
    """Origem bibliográfica da evidência."""

    titulo: str
    instituicao: str
    ano: int | None
    url: HttpUrl | None


class DocumentoEvidenciaResposta(BaseModel):
    """Identificação do documento de origem."""

    id: str
    arquivo: str
    hash_sha256: str
    fonte: FonteEvidenciaResposta


class TrechoEvidenciaResposta(BaseModel):
    """Trecho recuperado e sua localização no documento."""

    id: str
    texto: str
    pagina_inicial: int | None
    pagina_final: int | None
    secao: str | None


class EvidenciaResposta(BaseModel):
    """Evidência recuperada com sua proveniência."""

    trecho: TrechoEvidenciaResposta
    documento: DocumentoEvidenciaResposta
    score: float = Field(ge=-1.0, le=1.0)


class RespostaVerificacao(BaseModel):
    """Resultado da recuperação de evidências."""

    pergunta: str
    total_evidencias: int
    evidencias: list[EvidenciaResposta]


TAMANHO_MAXIMO_DA_ALEGACAO = 500


class RequisicaoDaAlegacao(BaseModel):
    """Alegação a verificar e o perfil de leitura do veredito (spec 82)."""

    alegacao: str = Field(
        min_length=1,
        max_length=TAMANHO_MAXIMO_DA_ALEGACAO,
        examples=["Ovo aumenta o colesterol?"],
    )
    perfil: Literal["consumidor_geral", "consumidor_rapido"] = "consumidor_geral"

    @field_validator("alegacao", mode="before")
    @classmethod
    def sem_espacos_nas_pontas(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor


class FonteDoVeredito(BaseModel):
    titulo: str
    instituicao: str
    ano: int | None
    url: str | None


class VereditoResposta(BaseModel):
    classificacao: Literal["reciclada", "parcial", "nova"] | None
    mensagem: str
    fontes: list[FonteDoVeredito]
    aprovado_pela_validacao: bool


class EtapaResposta(BaseModel):
    agente: Literal["research", "analysis", "validation", "communication"]
    entrada: dict[str, Any]
    saida: dict[str, Any]
    segundos: float


class RespostaDaAlegacao(BaseModel):
    """Veredito, número de retornos e as etapas de cada agente, na ordem em que rodaram.

    O histórico leva os ids dos trechos e os scores, não o texto dos trechos.
    """

    veredito: VereditoResposta
    retornos: int
    historico: list[EtapaResposta]
