"""Entidades e objetos de valor do RAG de receitas.

A camada de domínio não importa frameworks, banco nem bibliotecas de LLM.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class TipoDeTrecho(StrEnum):
    """Se o trecho é uma receita ou parte de um texto de orientação."""

    RECEITA = "receita"
    CONHECIMENTO = "conhecimento"


@dataclass(frozen=True)
class Fonte:
    """Documento de onde veio uma informação (RN10)."""

    titulo: str
    instituicao: str
    ano: int | None = None
    url: str | None = None
    licenca: str | None = None

    def __post_init__(self) -> None:
        if not self.titulo.strip():
            raise ValueError("A fonte precisa de título.")
        if not self.instituicao.strip():
            raise ValueError("A fonte precisa da instituição ou do site de origem.")


@dataclass(frozen=True)
class Ingrediente:
    """Ingrediente de uma receita.

    `texto` é a linha original, com a quantidade (ex.: "2 xícaras de farinha").
    `nome` é o alimento sem a quantidade, quando o dataset informa (campo NER do RecipeNLG).
    A ligação com o `Alimento` do catálogo fica para depois da versão 1.
    """

    texto: str
    nome: str | None = None

    def __post_init__(self) -> None:
        if not self.texto.strip():
            raise ValueError("O ingrediente precisa de texto.")


@dataclass(frozen=True)
class Receita:
    """Preparo com ingredientes e modo de fazer, sempre com fonte."""

    documento_id: str
    titulo: str
    ingredientes: tuple[Ingrediente, ...]
    modo_de_preparo: tuple[str, ...]
    fonte: Fonte
    idioma: str = "pt"

    @property
    def esta_completa(self) -> bool:
        """Receita com ingredientes e modo de preparo. As incompletas saem na curadoria."""
        return bool(self.ingredientes) and any(p.strip() for p in self.modo_de_preparo)


@dataclass(frozen=True)
class Secao:
    """Seção de um documento de orientação, com os parágrafos na ordem do texto."""

    titulo: str
    paragrafos: tuple[str, ...]
    capitulo: str | None = None
    pagina: int | None = None


@dataclass(frozen=True)
class Documento:
    """Texto de orientação da base de conhecimento (ex.: Guia Alimentar), dividido em seções."""

    documento_id: str
    titulo: str
    secoes: tuple[Secao, ...]
    fonte: Fonte
    idioma: str = "pt"


@dataclass(frozen=True)
class Trecho:
    """Parte de um documento da base de conhecimento usada pelo RAG.

    `texto` é o que vira embedding. `conteudo` é o texto completo mostrado na resposta.
    """

    id: str
    tipo: TipoDeTrecho
    documento_id: str
    titulo: str
    texto: str
    conteudo: str
    fonte: Fonte
    idioma: str = "pt"
    capitulo: str | None = None
    secao: str | None = None
    pagina: int | None = None
    ingredientes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrechoRecuperado:
    """Trecho devolvido pela busca, com o score de similaridade (cosseno, de -1 a 1)."""

    trecho: Trecho
    score: float


@dataclass(frozen=True)
class RespostaComFontes:
    """Resposta do Miau-ricio com os trechos usados e as fontes montadas pelo código (RN10).

    `encontrou` é falso quando a base não tem a informação (RN11) ou quando a pergunta
    é sobre preço atual (RN04). Nesses casos, não há trechos nem fontes.
    """

    texto: str
    encontrou: bool
    trechos: tuple[TrechoRecuperado, ...] = ()
    fontes: tuple[Fonte, ...] = field(default=())

    def __post_init__(self) -> None:
        if self.encontrou and not self.fontes:
            raise ValueError(
                "Resposta baseada na base de conhecimento precisa citar a fonte (RN10)."
            )
        if not self.encontrou and (self.trechos or self.fontes):
            raise ValueError(
                "Resposta sem informação na base não pode ter trechos nem fontes."
            )
