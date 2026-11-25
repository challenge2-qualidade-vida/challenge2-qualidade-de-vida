"""Veredito da verificação, adaptado ao perfil de leitura (spec 83).

As fontes, a fonte principal e a aprovação são montadas aqui, pelo código (RN01, RN10). O LLM
só redige o texto da mensagem, na camada de aplicação.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from economia.pesquisa_evidencias.dominio.modelos import (
    EvidenciaRecuperada,
    FonteEvidencia,
)
from economia.verificacao.dominio.analise import (
    AnaliseDaAlegacao,
    ClassificacaoDaAlegacao,
    evidencias_citadas,
)

MENSAGEM_NAO_CONCLUSIVA = (
    "Não foi possível concluir a verificação desta alegação. As evidências da nossa base "
    "não foram suficientes para uma resposta confiável."
)
MAXIMO_DE_FRASES_NO_PERFIL_RAPIDO = 2

# fim de frase: ponto, exclamação ou interrogação seguidos de espaço
_FIM_DE_FRASE = re.compile(r"(?<=[.!?])\s+")
# marcadores de citação do Analysis: [1], [1, 2], [1,2]
_MARCADOR_DE_CITACAO = re.compile(r"\s*\[\d+(?:\s*,\s*\d+)*\]")


class PerfilDeLeitura(StrEnum):
    """Forma de apresentar o veredito."""

    CONSUMIDOR_GERAL = "consumidor_geral"  # explicação completa, com as fontes
    CONSUMIDOR_RAPIDO = "consumidor_rapido"  # uma ou duas frases, com a fonte principal


@dataclass(frozen=True)
class Veredito:
    """Resposta final da verificação: classificação, mensagem, fontes e aprovação.

    Sem classificação (não houve análise), o veredito não tem fontes nem é aprovado.
    """

    classificacao: ClassificacaoDaAlegacao | None
    mensagem: str
    fontes: tuple[FonteEvidencia, ...] = ()
    aprovado_pela_validacao: bool = False

    def __post_init__(self) -> None:
        if not self.mensagem.strip():
            raise ValueError("O veredito precisa de mensagem.")
        if self.classificacao is None and (self.fontes or self.aprovado_pela_validacao):
            raise ValueError(
                "Um veredito sem classificação não tem fontes nem aprovação."
            )


def fontes_citadas(
    analise: AnaliseDaAlegacao, evidencias: Sequence[EvidenciaRecuperada]
) -> tuple[FonteEvidencia, ...]:
    """Uma fonte por documento citado, sem repetir, na ordem das citações."""
    vistos: set[str] = set()
    fontes: list[FonteEvidencia] = []
    for evidencia in evidencias_citadas(analise, evidencias):
        if evidencia.documento.id not in vistos:
            vistos.add(evidencia.documento.id)
            fontes.append(evidencia.documento.fonte)
    return tuple(fontes)


def fonte_principal(
    analise: AnaliseDaAlegacao, evidencias: Sequence[EvidenciaRecuperada]
) -> FonteEvidencia | None:
    """Fonte da evidência citada com o maior score; em empate, a primeira citada."""
    citadas = evidencias_citadas(analise, evidencias)
    if not citadas:
        return None
    return max(citadas, key=lambda e: e.score).documento.fonte


def limitar_frases(texto: str, maximo: int) -> str:
    """As primeiras `maximo` frases do texto."""
    frases = [f for f in _FIM_DE_FRASE.split(texto.strip()) if f]
    return " ".join(frases[:maximo])


def remover_marcadores_de_citacao(texto: str) -> str:
    """Texto sem os marcadores [n] que o Analysis usa para citar as evidências."""
    return _MARCADOR_DE_CITACAO.sub("", texto).strip()


def veredito_nao_conclusivo(analise: AnaliseDaAlegacao | None) -> Veredito:
    """Veredito de quando a validação não aprovou a análise ou não houve análise (RN11).

    A classificação da análise é mantida para o registro, mas sem fontes: elas não foram
    confirmadas pela validação.
    """
    return Veredito(
        classificacao=analise.classificacao if analise else None,
        mensagem=MENSAGEM_NAO_CONCLUSIVA,
    )
