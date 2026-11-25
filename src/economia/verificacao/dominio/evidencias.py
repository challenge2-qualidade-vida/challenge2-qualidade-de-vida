"""Evidências como a verificação as enxerga.

A verificação não importa o domínio da Pesquisa de evidências: estes modelos guardam só o
que o Analysis, o Validation e o Communication usam (texto, seção, fonte e score). A
tradução do que o Research devolve fica em `infraestrutura/pesquisa_de_evidencias.py`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FonteEvidencia:
    """Origem bibliográfica da evidência, mostrada nas fontes do veredito."""

    titulo: str
    instituicao: str
    ano: int | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        if not self.titulo.strip():
            raise ValueError("A fonte precisa de título.")
        if not self.instituicao.strip():
            raise ValueError("A fonte precisa da instituição de origem.")


@dataclass(frozen=True)
class DocumentoEvidencia:
    """Documento de origem da evidência."""

    id: str
    fonte: FonteEvidencia

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("O documento precisa de identificador.")


@dataclass(frozen=True)
class TrechoEvidencia:
    """Trecho citável da evidência."""

    id: str
    documento_id: str
    texto: str
    secao: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("O trecho precisa de identificador.")
        if not self.texto.strip():
            raise ValueError("O trecho precisa conter texto.")


@dataclass(frozen=True)
class EvidenciaRecuperada:
    """Trecho, documento de origem e similaridade com a alegação.

    O score não é probabilidade de veracidade.
    """

    trecho: TrechoEvidencia
    documento: DocumentoEvidencia
    score: float

    def __post_init__(self) -> None:
        if self.trecho.documento_id != self.documento.id:
            raise ValueError(
                "O trecho e o documento informado precisam ter o mesmo identificador."
            )
        if not -1.0 <= self.score <= 1.0:
            raise ValueError("O score de similaridade deve estar entre -1 e 1.")
