from economia.compartilhado.configuracao import Configuracao
from economia.compartilhado.infraestrutura.llm_ollama import ChamadaAoLLM
from economia.compartilhado.infraestrutura.observabilidade_langfuse import (
    RegistroDeGeracoes,
    criar_cliente,
    versao_do_prompt,
)


class Observacao:
    def __init__(self, **kwargs):
        self.dados = kwargs
        self.encerrada = False

    def end(self):
        self.encerrada = True


class ClienteFalso:
    def __init__(self):
        self.observacoes = []

    def start_observation(self, **kwargs):
        observacao = Observacao(**kwargs)
        self.observacoes.append(observacao)
        return observacao


def chamada(sistema="prompt do sistema"):
    return ChamadaAoLLM(
        modelo="qwen3.5:9b",
        sistema=sistema,
        mensagem="Pergunta: como conservo alface?",
        saida='{"encontrou": true}',
        estruturada=True,
        opcoes={"temperature": 0.0, "num_ctx": 8192, "seed": 42},
        tokens_de_entrada=120,
        tokens_de_saida=30,
        segundos=2.5,
    )


def test_sem_chaves_nao_cria_cliente():
    assert criar_cliente(Configuracao(_env_file=None)) is None
    assert criar_cliente(Configuracao(_env_file=None, langfuse_public_key="pk")) is None


def test_versao_do_prompt_vem_do_nome():
    assert versao_do_prompt("resposta_com_fontes_v2") == "v2"
    assert versao_do_prompt("sem_versao") is None


def test_cada_chamada_vira_uma_geracao_com_modelo_tokens_e_prompt():
    cliente = ClienteFalso()
    registro = RegistroDeGeracoes(
        cliente, {"prompt do sistema": "resposta_sem_base_v1"}
    )
    registro(chamada())
    [geracao] = cliente.observacoes
    dados = geracao.dados
    assert dados["as_type"] == "generation"
    assert dados["name"] == "resposta_sem_base_v1"
    assert dados["version"] == "v1"
    assert dados["model"] == "qwen3.5:9b"
    assert dados["input"] == [
        {"role": "system", "content": "prompt do sistema"},
        {"role": "user", "content": "Pergunta: como conservo alface?"},
    ]
    assert dados["output"] == '{"encontrou": true}'
    assert dados["usage_details"] == {"input": 120, "output": 30}
    assert dados["model_parameters"] == {
        "temperature": 0.0,
        "num_ctx": 8192,
        "seed": 42,
    }
    assert dados["metadata"]["segundos"] == 2.5
    assert dados["metadata"]["estruturada"] is True
    assert geracao.encerrada


def test_prompt_desconhecido_e_tokens_ausentes():
    cliente = ClienteFalso()
    sem_tokens = chamada(sistema="outro")
    sem_tokens = ChamadaAoLLM(
        **{**sem_tokens.__dict__, "tokens_de_entrada": None, "tokens_de_saida": None}
    )
    RegistroDeGeracoes(cliente)(sem_tokens)
    dados = cliente.observacoes[0].dados
    assert dados["name"] == "llm"
    assert dados["version"] is None
    assert dados["usage_details"] is None
