"""Registro da verificação no Langfuse: um trace por alegação e um span por agente.

Serve à avaliação (`caso`, com a classificação esperada) e ao orquestrador (`verificacao`,
uma alegação avulsa). As chamadas ao LLM entram como gerações dentro do span do agente, pelo
`RegistroDeGeracoes`. O span do Validation leva os motivos e o destino no metadado, para o
retorno aparecer no trace. Os dados passam pelo mascaramento do cliente (RN30). Uma falha do
Langfuse não interrompe a verificação.
"""

import logging
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from typing import Any

from economia.verificacao.aplicacao.avaliacao import CasoDeVerificacao

logger = logging.getLogger(__name__)

NOME_DO_REGISTRO = "verificacao.alegacao"


class ObservadorLangfuse:
    def __init__(self, cliente: Any, tags: tuple[str, ...] = ("verificacao",)):
        self._cliente = cliente
        self._tags = list(tags)

    @contextmanager
    def _observacao(
        self,
        nome: str,
        tipo: str,
        entrada: dict,
        propagar: bool = False,
        metadado: Callable[[dict], dict | None] = lambda saida: None,
    ) -> Iterator[Callable[[dict], None]]:
        with ExitStack() as pilha:
            observacao = None
            try:
                if propagar:
                    from langfuse import propagate_attributes

                    pilha.enter_context(
                        propagate_attributes(trace_name=nome, tags=self._tags)
                    )
                observacao = pilha.enter_context(
                    self._cliente.start_as_current_observation(
                        name=nome, as_type=tipo, input=entrada
                    )
                )
            except Exception:
                logger.warning(
                    "Falha ao abrir o registro %s no Langfuse", nome, exc_info=True
                )

            def registrar(saida: dict) -> None:
                if observacao is None:
                    return
                try:
                    extra = metadado(saida)
                    if extra:
                        observacao.update(output=saida, metadata=extra)
                    else:
                        observacao.update(output=saida)
                except Exception:
                    logger.warning(
                        "Falha ao registrar a saída de %s", nome, exc_info=True
                    )

            yield registrar

    def caso(self, caso: CasoDeVerificacao):
        return self._observacao(
            NOME_DO_REGISTRO,
            "chain",
            {
                "id": caso.id,
                "alegacao": caso.alegacao,
                "classificacao_esperada": str(caso.classificacao_esperada),
            },
            propagar=True,
        )

    def verificacao(self, entrada: dict):
        """Trace de uma alegação avulsa, sem a classificação esperada (orquestrador, #82)."""
        return self._observacao(NOME_DO_REGISTRO, "chain", entrada, propagar=True)

    def etapa(self, nome: str, entrada: dict):
        tipo = "retriever" if nome == "research" else "agent"
        metadado = _retorno_da_validacao if nome == "validation" else lambda saida: None
        return self._observacao(f"verificacao.{nome}", tipo, entrada, metadado=metadado)


def _retorno_da_validacao(saida: dict) -> dict | None:
    """Motivos e destino de uma validação reprovada, para o retorno aparecer no trace."""
    if saida.get("aprovado", True):
        return None
    return {
        "motivos": saida.get("motivos", []),
        "retornar_para": saida.get("retornar_para"),
    }
