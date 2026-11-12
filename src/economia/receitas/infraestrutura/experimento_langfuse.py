"""Avaliação do Miau-ricio como experimento no Langfuse.

- `RepositorioObservado`: cada busca no Qdrant vira uma observação do tipo *retriever*, com os
  trechos e os scores.
- `sincronizar_dataset`: o conjunto de perguntas vira um *dataset*, com a resposta de
  referência como saída esperada.
- `rodar_experimento`: cada execução (modo e LLM) vira um *run* do dataset. Cada pergunta é
  um registro (trace) com a busca e as chamadas ao LLM dentro, e as métricas da avaliação
  entram como pontuações (scores). Na interface, os runs ficam lado a lado.

As métricas são calculadas pela aplicação (`avaliar_pergunta`), como sem o Langfuse: aqui elas
só são enviadas (RN01).
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from typing import Any

from economia.receitas.aplicacao.avaliacao import PerguntaDeAvaliacao
from economia.receitas.aplicacao.avaliacao_respostas import ResultadoDaResposta
from economia.receitas.dominio.modelos import TrechoRecuperado

# nome da pontuação no Langfuse → campo da saída da tarefa
PONTUACOES = {
    "comportamento_correto": "comportamento_correto",
    "fonte_esperada": "fonte_esperada",
    "rouge_1": "rouge_1",
    "rouge_l": "rouge_l",
    "cosseno": "cosseno",
    "hit@k": "hit",
    "latencia_s": "segundos",
}


class RepositorioObservado:
    """Repositório que registra cada busca. O resto passa direto para o repositório real."""

    def __init__(self, repositorio: Any, cliente: Any):
        self._repositorio = repositorio
        self._cliente = cliente

    def buscar(self, vetor, limite, tipo=None) -> list[TrechoRecuperado]:
        with self._cliente.start_as_current_observation(
            as_type="retriever",
            name="busca no Qdrant",
            input={"limite": limite, "tipo": tipo.value if tipo else None},
        ) as busca:
            recuperados = self._repositorio.buscar(vetor, limite, tipo)
            busca.update(
                output=[
                    {
                        "titulo": r.trecho.titulo,
                        "documento_id": r.trecho.documento_id,
                        "tipo": r.trecho.tipo.value,
                        "score": round(r.score, 4),
                    }
                    for r in recuperados
                ]
            )
            return recuperados

    def __getattr__(self, nome: str) -> Any:
        return getattr(self._repositorio, nome)


def sincronizar_dataset(
    cliente: Any, nome: str, perguntas: Sequence[PerguntaDeAvaliacao]
) -> None:
    """Cria (ou atualiza) o dataset com um item por pergunta. O id do item é fixo."""
    cliente.create_dataset(
        name=nome, description="Perguntas de avaliação do Miau-ricio (fictícias)"
    )
    for pergunta in perguntas:
        cliente.create_dataset_item(
            dataset_name=nome,
            id=f"{nome}:{pergunta.id}",
            input={"pergunta": pergunta.pergunta},
            expected_output=pergunta.resposta_referencia,
            metadata={
                "id": pergunta.id,
                "categoria": pergunta.categoria,
                "comportamento": pergunta.comportamento_esperado,
            },
        )


def saida_da_tarefa(resultado: ResultadoDaResposta) -> dict:
    """O que aparece como saída de cada item no Langfuse: a resposta e as métricas."""
    return {**asdict(resultado), "comportamento_correto": resultado.acertou}


def avaliacoes_do_resultado(saida: Mapping) -> list:
    """Uma pontuação por métrica presente. Booleanos viram 1 ou 0, para a média funcionar."""
    from langfuse import Evaluation

    avaliacoes = []
    for nome, campo in PONTUACOES.items():
        valor = saida.get(campo)
        if valor is None:
            continue
        avaliacoes.append(
            Evaluation(name=nome, value=float(valor), data_type="NUMERIC")
        )
    return avaliacoes


def rodar_experimento(
    cliente: Any,
    nome_do_dataset: str,
    nome_do_run: str,
    perguntas: Sequence[PerguntaDeAvaliacao],
    avaliar: Callable[[PerguntaDeAvaliacao], ResultadoDaResposta],
    metadata: Mapping[str, Any],
    ao_progredir: Callable[[int, int, ResultadoDaResposta], None] | None = None,
) -> tuple[list[ResultadoDaResposta], str | None]:
    """Roda a avaliação como um run do dataset. Devolve os resultados e o link do run.

    Uma pergunta por vez (`max_concurrency=1`): o Ollama atende um pedido de cada vez, e a
    ordem fixa mantém a execução reproduzível.
    """
    por_id = {p.id: p for p in perguntas}
    resultados: dict[str, ResultadoDaResposta] = {}

    def tarefa(*, item, **_):
        pergunta = por_id[item.metadata["id"]]
        resultado = avaliar(pergunta)
        resultados[pergunta.id] = resultado
        if ao_progredir:
            ao_progredir(len(resultados), len(perguntas), resultado)
        return saida_da_tarefa(resultado)

    def avaliador(*, output, **_):
        return avaliacoes_do_resultado(output or {})

    dataset = cliente.get_dataset(nome_do_dataset)
    execucao = dataset.run_experiment(
        name=nome_do_run,
        run_name=nome_do_run,
        description="Avaliação do Miau-ricio (LLM puro ou com RAG)",
        task=tarefa,
        evaluators=[avaliador],
        max_concurrency=1,
        metadata=dict(metadata),
    )
    faltando = [p.id for p in perguntas if p.id not in resultados]
    if faltando:
        # o SDK registra a exceção da tarefa e segue; sem o resultado, o resumo ficaria errado
        raise RuntimeError(
            f"Perguntas sem resultado no experimento: {', '.join(faltando)}"
        )
    return [resultados[p.id] for p in perguntas], getattr(
        execucao, "dataset_run_url", None
    )
