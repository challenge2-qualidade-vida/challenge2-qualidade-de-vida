"""Mascaramento de dados pessoais antes do registro no Langfuse (RN30).

Funções puras, sem dependência do Langfuse: a infraestrutura passa `mascarar` ao cliente
(`Langfuse(mask=...)`), e o SDK a aplica a toda entrada, saída e metadado antes do envio.

O mascaramento é por padrões. Pega e-mail, CPF, telefone, cartão e chave de NFC-e; não pega
nomes próprios nem restrições de saúde escritas por extenso (ver os riscos na spec 29).
"""

import logging
import re
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger(__name__)

FALHA = "[MASCARAMENTO_FALHOU]"

# a ordem importa: a chave de NFC-e (44 dígitos) e o cartão vêm antes do CPF e do telefone,
# para um número longo não ser cortado em pedaços por um padrão mais curto
_PADROES: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"(?<!\d)(?:\d{4}\s?){11}(?!\d)"), "[CHAVE_NFCE]"),
    (re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)"), "[CARTAO]"),
    (re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)"), "[CPF]"),
    (
        re.compile(r"(?<!\d)(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}[-\s]?\d{4}(?!\d)"),
        "[TELEFONE]",
    ),
)


def mascarar_texto(texto: str) -> str:
    """Troca os dados pessoais do texto pelos marcadores."""
    for padrao, marcador in _PADROES:
        texto = padrao.sub(marcador, texto)
    return texto


def mascarar_dado(dado: Any) -> Any:
    """Mascara textos dentro de dicionários, listas e tuplas. O resto passa igual."""
    if isinstance(dado, str):
        return mascarar_texto(dado)
    if isinstance(dado, Mapping):
        return {chave: mascarar_dado(valor) for chave, valor in dado.items()}
    if isinstance(dado, list | tuple):
        return [mascarar_dado(valor) for valor in dado]
    return dado


def mascarar(*, data: Any, **_: Any) -> Any:
    """Função de mascaramento no formato do SDK do Langfuse.

    Se o mascaramento falhar, nada do conteúdo original é enviado: o registro leva só o
    marcador de falha.
    """
    try:
        return mascarar_dado(data)
    except Exception:
        logger.warning(
            "Falha no mascaramento: o registro vai sem o conteúdo", exc_info=True
        )
        return FALHA
