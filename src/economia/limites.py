"""Limite de requisições por IP (tópico 20), em memória e sem serviço externo.

Protege o plano gratuito do LLM e a base de preços colaborativa de abuso quando
o site fica público. Reinicia junto com o servidor, o que basta para este porte.
"""

import os
import time
from collections import defaultdict, deque

JANELA_S = 60
# Requisições por minuto, por IP. As demais rotas não têm limite.
LIMITES = {
    "/api/chat": 20,
    "/api/cesta": 40,
    "/api/osm": 10,
    "/api/nfce/imagem": 10,
    "/api/nfce/url": 10,
    "/api/nfce/confirmar": 10,
}


class Limitador:
    def __init__(self, limites: dict[str, int] = LIMITES, janela_s: float = JANELA_S, relogio=time.monotonic):
        self.limites = limites
        self.janela_s = janela_s
        self.relogio = relogio
        self.acessos: dict[tuple[str, str], deque] = defaultdict(deque)

    def permitir(self, ip: str, rota: str) -> bool:
        limite = self.limites.get(rota)
        if limite is None:
            return True
        agora = self.relogio()
        fila = self.acessos[(ip, rota)]
        while fila and agora - fila[0] >= self.janela_s:
            fila.popleft()
        if len(fila) >= limite:
            return False
        fila.append(agora)
        return True


def limitador_do_ambiente() -> Limitador | None:
    """ECONOMIA_SEM_LIMITES=1 desliga o limite (usado nos testes e nos experimentos)."""
    return None if os.environ.get("ECONOMIA_SEM_LIMITES") == "1" else Limitador()
