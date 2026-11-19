"""Identificadores da pessoa e da conversa, enquanto não existe login.

O `IdentificadorAnonimo` é gerado no navegador e reconhece a mesma pessoa entre conversas.
É um UUID v4 aleatório: não contém nem deriva de dado pessoal (RN30). O identificador da
`Conversa` segue o mesmo formato. Valores fora do formato são ignorados, para não entrar
texto livre (um e-mail, por exemplo) no lugar do identificador.
"""

import re
from dataclasses import dataclass

_UUID_V4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def uuid_v4(valor: str | None) -> str | None:
    """O valor em minúsculas, se for um UUID v4; senão, `None`."""
    if not valor:
        return None
    valor = valor.strip().lower()
    return valor if _UUID_V4.match(valor) else None


@dataclass(frozen=True)
class IdentificadorAnonimo:
    valor: str

    def __post_init__(self):
        if uuid_v4(self.valor) != self.valor:
            raise ValueError("O identificador anônimo precisa ser um UUID v4")

    @classmethod
    def ler(cls, valor: str | None) -> "IdentificadorAnonimo | None":
        normalizado = uuid_v4(valor)
        return cls(normalizado) if normalizado else None


@dataclass(frozen=True)
class IdentificadorDaConversa:
    valor: str

    def __post_init__(self):
        if uuid_v4(self.valor) != self.valor:
            raise ValueError("O identificador da conversa precisa ser um UUID v4")

    @classmethod
    def ler(cls, valor: str | None) -> "IdentificadorDaConversa | None":
        normalizado = uuid_v4(valor)
        return cls(normalizado) if normalizado else None
