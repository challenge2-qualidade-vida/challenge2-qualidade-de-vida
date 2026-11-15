"""Registro das perguntas da API no Langfuse: tracing, pessoa, conversa e scores (spec 29).

Cada pergunta vira um registro `miau-ricio.pergunta`. A busca no Qdrant e as chamadas ao LLM
entram como filhas (`RepositorioObservado` e `RegistroDeGeracoes`), porque rodam dentro da
observação aberta aqui. O identificador anônimo vira o `user_id`, e a conversa, o `session_id`.

A observação raiz leva a pergunta, a resposta e os trechos: é sobre ela que os evaluators
gerenciados (fidelidade e relevância) rodam, e eles não leem as observações filhas.

Nada aqui pode mudar a resposta: toda falha do Langfuse é registrada no log e ignorada.
"""

import logging
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from typing import Any

from economia.conversa.dominio.identificadores import (
    IdentificadorAnonimo,
    IdentificadorDaConversa,
)

logger = logging.getLogger(__name__)

NOME_DO_REGISTRO = "miau-ricio.pergunta"


def scores_da_resposta(
    resposta: Any, pergunta: str, segundos: float
) -> dict[str, float]:
    """Scores calculados pelo código (RN01). Booleanos viram 1 ou 0."""
    from economia.receitas.aplicacao.responder_pergunta import (
        AVISO_DE_PRECO,
        e_pergunta_de_preco,
    )

    scores = {
        "encontrou": float(resposta.encontrou),
        "fonte_citada": float(bool(resposta.fontes)),
        "latencia_s": round(segundos, 3),
        "erro": 0.0,
    }
    if e_pergunta_de_preco(pergunta):
        scores["aviso_de_preco"] = float(AVISO_DE_PRECO in resposta.texto)
    return scores


_BOOLEANOS = {"encontrou", "fonte_citada", "aviso_de_preco", "erro"}


class RegistroDaPergunta:
    """A observação aberta de uma pergunta. Sem Langfuse, os métodos não fazem nada."""

    def __init__(self, observacao: Any = None):
        self._observacao = observacao

    def _pontuar(self, scores: dict[str, float]) -> None:
        for nome, valor in scores.items():
            self._observacao.score_trace(
                name=nome,
                value=valor,
                data_type="BOOLEAN" if nome in _BOOLEANOS else "NUMERIC",
            )

    def concluir(self, pergunta: str, resposta: Any, segundos: float) -> None:
        if self._observacao is None:
            return
        try:
            self._observacao.update(
                output={
                    "texto": resposta.texto,
                    "encontrou": resposta.encontrou,
                    "fontes": [f.descricao for f in resposta.fontes],
                    "trechos": [
                        f"[{t.posicao}] {t.titulo}: {t.resumo}"
                        for t in resposta.trechos_recuperados
                        if t.acima_do_limiar
                    ],
                },
                metadata={"limiar": resposta.limiar, "segundos": resposta.segundos},
            )
            self._pontuar(scores_da_resposta(resposta, pergunta, segundos))
        except Exception:
            logger.warning("Falha ao registrar a resposta no Langfuse", exc_info=True)

    def falhar(self, erro: BaseException, segundos: float) -> None:
        if self._observacao is None:
            return
        try:
            self._observacao.update(
                level="ERROR", status_message=f"{type(erro).__name__}: {erro}"[:500]
            )
            self._pontuar({"erro": 1.0, "latencia_s": round(segundos, 3)})
        except Exception:
            logger.warning("Falha ao registrar o erro no Langfuse", exc_info=True)


class ObservadorDePerguntas:
    """Abre o registro de cada pergunta. Com `cliente=None`, nada é enviado."""

    def __init__(self, cliente: Any | None):
        self._cliente = cliente

    @contextmanager
    def registrar(
        self,
        pergunta: str,
        pessoa: IdentificadorAnonimo | None = None,
        conversa: IdentificadorDaConversa | None = None,
    ) -> Iterator[RegistroDaPergunta]:
        if self._cliente is None:
            yield RegistroDaPergunta()
            return
        with ExitStack() as pilha:
            try:
                from langfuse import propagate_attributes

                pilha.enter_context(
                    propagate_attributes(
                        user_id=pessoa.valor if pessoa else None,
                        session_id=conversa.valor if conversa else None,
                        trace_name=NOME_DO_REGISTRO,
                        tags=["miau-ricio", "api"],
                    )
                )
                observacao = pilha.enter_context(
                    self._cliente.start_as_current_observation(
                        name=NOME_DO_REGISTRO,
                        as_type="agent",
                        input={"pergunta": pergunta},
                    )
                )
            except Exception:
                logger.warning("Falha ao abrir o registro no Langfuse", exc_info=True)
                observacao = None
            yield RegistroDaPergunta(observacao)
