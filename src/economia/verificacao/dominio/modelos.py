
"""Modelos de domínio da pesquisa de evidências científicas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FonteEvidencia:
    """Origem bibliográfica de uma evidência."""

    titulo: str
    instituicao: str
    ano: int | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        if not self.titulo.strip():
            raise ValueError("A fonte precisa de título.")
        if not self.instituicao.strip():
            raise ValueError("A fonte precisa da instituição de origem.")
        if self.ano is not None and self.ano <= 0:
            raise ValueError("O ano da fonte precisa ser positivo.")


@dataclass(frozen=True)
class DocumentoEvidencia:
    """Documento incorporado à base de conhecimento científico."""

    id: str
    fonte: FonteEvidencia
    arquivo: str
    hash_sha256: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("O documento precisa de identificador.")
        if not self.arquivo.strip():
            raise ValueError("O documento precisa do caminho do arquivo.")
        if not self.hash_sha256.strip():
            raise ValueError("O documento precisa do hash do conteúdo.")


@dataclass(frozen=True)
class TrechoEvidencia:
    """Unidade textual recuperável, vinculada ao documento de origem."""

    id: str
    documento_id: str
    texto: str
    pagina_inicial: int | None = None
    pagina_final: int | None = None
    secao: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("O trecho precisa de identificador.")
        if not self.documento_id.strip():
            raise ValueError("O trecho precisa identificar seu documento.")
        if not self.texto.strip():
            raise ValueError("O trecho precisa conter texto.")
        if self.pagina_inicial is not None and self.pagina_inicial < 1:
            raise ValueError("A página inicial precisa ser positiva.")
        if self.pagina_final is not None and self.pagina_final < 1:
            raise ValueError("A página final precisa ser positiva.")
        if (
            self.pagina_inicial is not None
            and self.pagina_final is not None
            and self.pagina_final < self.pagina_inicial
        ):
            raise ValueError("A página final não pode anteceder a inicial.")


@dataclass(frozen=True)
class EvidenciaRecuperada:
    """Trecho recuperado, documento de origem e similaridade semântica."""

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
