from types import SimpleNamespace

import pytest

from economia.receitas.aplicacao.avaliacao import (
    NAO_ENCONTRAR,
    RESPONDER,
    Esperado,
    PerguntaDeAvaliacao,
)
from economia.receitas.aplicacao.avaliacao_respostas import ResultadoDaResposta
from economia.receitas.dominio.modelos import TrechoRecuperado
from economia.receitas.infraestrutura.experimento_langfuse import (
    RepositorioObservado,
    avaliacoes_do_resultado,
    rodar_experimento,
    sincronizar_dataset,
)


class Observacao:
    def __init__(self, registro, **kwargs):
        self.registro = registro
        self.dados = kwargs

    def __enter__(self):
        return self

    def __exit__(self, *erro):
        return False

    def update(self, **kwargs):
        self.dados.update(kwargs)


class ClienteFalso:
    def __init__(self):
        self.observacoes = []
        self.datasets = []
        self.itens = []
        self.dataset = None

    def start_as_current_observation(self, **kwargs):
        observacao = Observacao(self, **kwargs)
        self.observacoes.append(observacao)
        return observacao

    def create_dataset(self, **kwargs):
        self.datasets.append(kwargs)

    def create_dataset_item(self, **kwargs):
        self.itens.append(kwargs)

    def get_dataset(self, nome):
        return self.dataset


class RepositorioFalso:
    def __init__(self, trecho):
        self.trecho = trecho

    def buscar(self, vetor, limite, tipo=None):
        return [TrechoRecuperado(self.trecho("alface"), 0.91)]

    def contar(self):
        return 7


def test_busca_observada_registra_os_trechos_e_os_scores(trecho):
    cliente = ClienteFalso()
    repositorio = RepositorioObservado(RepositorioFalso(trecho), cliente)
    [recuperado] = repositorio.buscar([0.1, 0.2], 5)
    assert recuperado.score == 0.91
    [busca] = cliente.observacoes
    assert busca.dados["as_type"] == "retriever"
    assert busca.dados["input"] == {"limite": 5, "tipo": None}
    assert busca.dados["output"] == [
        {
            "titulo": "Título alface",
            "documento_id": "alface",
            "tipo": "receita",
            "score": 0.91,
        }
    ]
    # o resto do repositório passa direto
    assert repositorio.contar() == 7


PERGUNTAS = [
    PerguntaDeAvaliacao(
        "c1",
        "como conservo alface?",
        "conservacao",
        (Esperado("alface"),),
        resposta_referencia="Guarde seca.",
    ),
    PerguntaDeAvaliacao("s1", "pneu?", "sem_resposta"),
]


def test_sincronizar_dataset_cria_um_item_por_pergunta():
    cliente = ClienteFalso()
    sincronizar_dataset(cliente, "miau-ricio-v3", PERGUNTAS)
    assert cliente.datasets[0]["name"] == "miau-ricio-v3"
    primeiro, segundo = cliente.itens
    assert primeiro == {
        "dataset_name": "miau-ricio-v3",
        "id": "miau-ricio-v3:c1",
        "input": {"pergunta": "como conservo alface?"},
        "expected_output": "Guarde seca.",
        "metadata": {
            "id": "c1",
            "categoria": "conservacao",
            "comportamento": RESPONDER,
        },
    }
    assert segundo["expected_output"] is None
    assert segundo["metadata"]["comportamento"] == NAO_ENCONTRAR


def resultado(**kwargs):
    base = {
        "id": "c1",
        "categoria": "conservacao",
        "esperado": RESPONDER,
        "obtido": RESPONDER,
        "fonte_esperada": True,
        "segundos": 2.5,
    }
    return ResultadoDaResposta(**{**base, **kwargs})


def test_metricas_viram_avaliacoes_e_as_vazias_ficam_de_fora():
    saida = {
        "comportamento_correto": True,
        "fonte_esperada": None,
        "rouge_1": 0.5,
        "rouge_l": 0.4,
        "cosseno": None,
        "hit": 1,
        "segundos": 2.5,
    }
    avaliacoes = {a.name: a.value for a in avaliacoes_do_resultado(saida)}
    assert avaliacoes == {
        "comportamento_correto": 1.0,
        "rouge_1": 0.5,
        "rouge_l": 0.4,
        "hit@k": 1.0,
        "latencia_s": 2.5,
    }


class DatasetFalso:
    def __init__(self, ids, falhar=()):
        self.items = [SimpleNamespace(metadata={"id": i}) for i in ids]
        self.falhar = set(falhar)
        self.argumentos = None

    def run_experiment(self, **kwargs):
        self.argumentos = kwargs
        for item in self.items:
            if item.metadata["id"] in self.falhar:
                continue
            saida = kwargs["task"](item=item)
            for avaliador in kwargs["evaluators"]:
                avaliador(input=None, output=saida, expected_output=None, metadata={})
        return SimpleNamespace(dataset_run_url="https://langfuse/run")


def test_rodar_experimento_avalia_cada_item_e_devolve_na_ordem_das_perguntas():
    cliente = ClienteFalso()
    cliente.dataset = DatasetFalso(["s1", "c1"])
    vistos = []

    def avaliar(pergunta):
        return resultado(id=pergunta.id)

    resultados, url = rodar_experimento(
        cliente,
        "miau-ricio-v3",
        "rag-qwen3.5:9b",
        PERGUNTAS,
        avaliar,
        metadata={"modo": "rag"},
        ao_progredir=lambda n, total, r: vistos.append((n, total, r.id)),
    )
    assert [r.id for r in resultados] == ["c1", "s1"]
    assert url == "https://langfuse/run"
    assert vistos == [(1, 2, "s1"), (2, 2, "c1")]
    argumentos = cliente.dataset.argumentos
    assert argumentos["run_name"] == "rag-qwen3.5:9b"
    assert argumentos["max_concurrency"] == 1
    assert argumentos["metadata"] == {"modo": "rag"}


def test_rodar_experimento_avisa_quando_falta_resultado():
    cliente = ClienteFalso()
    cliente.dataset = DatasetFalso(["c1", "s1"], falhar=["s1"])
    with pytest.raises(RuntimeError, match="s1"):
        rodar_experimento(
            cliente,
            "d",
            "r",
            PERGUNTAS,
            lambda p: resultado(id=p.id),
            metadata={},
        )
