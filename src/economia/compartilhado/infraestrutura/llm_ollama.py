"""Adaptador do LLM local servido pelo Ollama.

Fica atrás da porta `ModeloDeLinguagem`: trocar de provedor (API, #13) não muda a aplicação.

Cada chamada pode ser entregue a um gancho (`ao_gerar`), com o modelo, o prompt, a saída, os
tokens e o tempo. É assim que o registro no Langfuse fica de fora da aplicação: quem cria o
adaptador decide para onde as chamadas vão.
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChamadaAoLLM:
    """O que aconteceu numa chamada ao LLM: o suficiente para registrar e comparar."""

    modelo: str
    sistema: str
    mensagem: str
    saida: str
    estruturada: bool
    opcoes: dict
    tokens_de_entrada: int | None
    tokens_de_saida: int | None
    segundos: float


class ModeloOllama:
    def __init__(
        self,
        url: str = "http://localhost:11434",
        modelo: str = "qwen2.5:7b",
        temperatura: float = 0.2,
        contexto: int = 8192,
        tempo_limite: float = 1800,
        cliente: Any = None,
        semente: int | None = None,
        saida_maxima: int | None = None,
        pensar: bool | None = False,
        ao_gerar: Callable[[ChamadaAoLLM], None] | None = None,
        relogio: Callable[[], float] = time.perf_counter,
    ):
        if cliente is None:
            import ollama

            cliente = ollama.Client(host=url, timeout=tempo_limite)
        self._cliente = cliente
        self.modelo = modelo
        # o padrão do Ollama é 4096 tokens; cinco receitas longas mais as instruções passam
        # disso, e o Ollama corta o começo do prompt sem avisar
        self._opcoes = {"temperature": temperatura, "num_ctx": contexto}
        if semente is not None:
            # com temperatura 0 e semente fixa, a mesma pergunta gera a mesma resposta,
            # o que permite comparar duas execuções da avaliação
            self._opcoes["seed"] = semente
        if saida_maxima is not None:
            # teto igual para todos os modelos na comparação
            self._opcoes["num_predict"] = saida_maxima
        # modelos com raciocínio (Qwen 3.5) pensam antes de responder; desligado por padrão,
        # para a comparação com modelos sem raciocínio ser justa. None não manda o parâmetro.
        self._pensar = pensar
        self._ao_gerar = ao_gerar
        self._relogio = relogio

    @property
    def opcoes(self) -> dict:
        return dict(self._opcoes)

    def _conversar(self, sistema: str, mensagem: str, formato: Any = None) -> str:
        extras = {} if self._pensar is None else {"think": self._pensar}
        inicio = self._relogio()
        resposta = self._cliente.chat(
            model=self.modelo,
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": mensagem},
            ],
            options=self._opcoes,
            format=formato,
            **extras,
        )
        segundos = self._relogio() - inicio
        texto = resposta["message"]["content"].strip()
        if self._ao_gerar:
            self._entregar(
                ChamadaAoLLM(
                    modelo=self.modelo,
                    sistema=sistema,
                    mensagem=mensagem,
                    saida=texto,
                    estruturada=formato is not None,
                    opcoes=self.opcoes,
                    tokens_de_entrada=_campo(resposta, "prompt_eval_count"),
                    tokens_de_saida=_campo(resposta, "eval_count"),
                    segundos=segundos,
                )
            )
        return texto

    def _entregar(self, chamada: ChamadaAoLLM) -> None:
        """Uma falha no registro não pode mudar a resposta."""
        try:
            self._ao_gerar(chamada)
        except Exception:
            logger.exception("Falha ao registrar a chamada ao LLM")

    def gerar(self, sistema: str, mensagem: str) -> str:
        """Texto livre."""
        return self._conversar(sistema, mensagem)

    def gerar_json(self, sistema: str, mensagem: str, esquema: dict) -> dict:
        """Saída estruturada: o Ollama restringe a geração ao esquema JSON."""
        return json.loads(self._conversar(sistema, mensagem, formato=esquema))


def _campo(resposta: Any, nome: str) -> Any:
    """Campo da resposta do Ollama, que pode vir como objeto ou como dicionário."""
    try:
        return resposta[nome]
    except (KeyError, TypeError):
        return getattr(resposta, nome, None)
