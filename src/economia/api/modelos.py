"""Modelos HTTP da API EconoMIA."""

from pydantic import BaseModel, Field, HttpUrl


class RequisicaoVerificacao(BaseModel):
    """Dados recebidos pelo endpoint de pesquisa de evidências."""

    pergunta: str = Field(min_length=1)
    limite: int = Field(default=5, ge=1, le=20)


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
