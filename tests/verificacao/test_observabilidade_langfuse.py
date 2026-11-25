"""Testes do registro da verificação no Langfuse, com um cliente falso."""

from contextlib import contextmanager

from economia.verificacao.infraestrutura.observabilidade_langfuse import (
    NOME_DO_REGISTRO,
    ObservadorLangfuse,
)


class Observacao:
    def __init__(self, registro):
        self._registro = registro

    def update(self, **campos):
        self._registro["atualizacoes"].append(campos)


class ClienteFalso:
    def __init__(self, falhar=False):
        self.registros = []
        self._falhar = falhar

    @contextmanager
    def start_as_current_observation(self, name, as_type, input):
        if self._falhar:
            raise RuntimeError("Langfuse fora do ar")
        registro = {"nome": name, "tipo": as_type, "entrada": input, "atualizacoes": []}
        self.registros.append(registro)
        yield Observacao(registro)


def test_verificacao_avulsa_abre_o_trace_da_alegacao():
    cliente = ClienteFalso()
    entrada = {"alegacao": "Ovo aumenta o colesterol?", "perfil": "consumidor_geral"}

    with ObservadorLangfuse(cliente).verificacao(entrada) as registrar:
        registrar({"retornos": 0})

    assert cliente.registros == [
        {
            "nome": NOME_DO_REGISTRO,
            "tipo": "chain",
            "entrada": entrada,
            "atualizacoes": [{"output": {"retornos": 0}}],
        }
    ]


def test_validacao_reprovada_leva_os_motivos_e_o_destino_no_metadado():
    cliente = ClienteFalso()
    saida = {
        "aprovado": False,
        "motivos": ["Confiança baixa."],
        "retornar_para": "research",
    }

    with ObservadorLangfuse(cliente).etapa("validation", {}) as registrar:
        registrar(saida)

    registro = cliente.registros[0]
    assert (registro["nome"], registro["tipo"]) == ("verificacao.validation", "agent")
    assert registro["atualizacoes"] == [
        {
            "output": saida,
            "metadata": {"motivos": ["Confiança baixa."], "retornar_para": "research"},
        }
    ]


def test_validacao_aprovada_e_outras_etapas_vao_sem_metadado():
    cliente = ClienteFalso()
    observador = ObservadorLangfuse(cliente)

    with observador.etapa("validation", {}) as registrar:
        registrar({"aprovado": True, "motivos": [], "retornar_para": None})
    with observador.etapa("research", {"limite": 5}) as registrar:
        registrar({"evidencias": []})

    assert [r["atualizacoes"][0].keys() for r in cliente.registros] == [
        {"output"},
        {"output"},
    ]
    assert cliente.registros[1]["tipo"] == "retriever"


def test_falha_do_langfuse_nao_interrompe_a_verificacao():
    with ObservadorLangfuse(ClienteFalso(falhar=True)).verificacao({}) as registrar:
        registrar({"retornos": 0})
