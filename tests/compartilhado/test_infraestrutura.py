import pytest

from economia.compartilhado.infraestrutura.llm_ollama import ModeloOllama
from economia.compartilhado.infraestrutura.prompts import carregar_prompt


def test_carrega_o_prompt_versionado_do_repositorio():
    prompt = carregar_prompt("miau-ricio", "resposta_com_fontes_v1")
    assert "NAO_ENCONTRADO" in prompt
    assert prompt == prompt.strip()


def test_prompt_inexistente_falha_com_o_caminho(tmp_path):
    with pytest.raises(FileNotFoundError, match="nenhum_v1"):
        carregar_prompt("miau-ricio", "nenhum_v1", pasta=tmp_path)


class ClienteFalso:
    def __init__(self, conteudo: str, tokens: tuple[int, int] | None = None):
        self.conteudo = conteudo
        self.tokens = tokens
        self.chamadas = []

    def chat(self, **kwargs):
        self.chamadas.append(kwargs)
        resposta = {"message": {"content": self.conteudo}}
        if self.tokens:
            resposta["prompt_eval_count"], resposta["eval_count"] = self.tokens
        return resposta


def test_gerar_manda_sistema_e_mensagem_com_a_temperatura():
    cliente = ClienteFalso("  resposta  ")
    llm = ModeloOllama(modelo="qwen2.5:7b", temperatura=0.1, cliente=cliente)
    assert llm.gerar("instruções", "pergunta") == "resposta"
    [chamada] = cliente.chamadas
    assert chamada["model"] == "qwen2.5:7b"
    assert chamada["messages"] == [
        {"role": "system", "content": "instruções"},
        {"role": "user", "content": "pergunta"},
    ]
    assert chamada["options"] == {"temperature": 0.1, "num_ctx": 8192}
    assert chamada["format"] is None


def test_gerar_json_restringe_ao_esquema_e_decodifica():
    cliente = ClienteFalso('{"ingredientes": ["ovo"]}')
    esquema = {"type": "object"}
    resultado = ModeloOllama(cliente=cliente).gerar_json("s", "m", esquema)
    assert resultado == {"ingredientes": ["ovo"]}
    assert cliente.chamadas[0]["format"] == esquema


def test_tempo_limite_vai_para_o_cliente_do_ollama(monkeypatch):
    import ollama

    criados = []
    monkeypatch.setattr(ollama, "Client", lambda **kwargs: criados.append(kwargs))
    ModeloOllama(url="http://ollama:11434", tempo_limite=42)
    assert criados == [{"host": "http://ollama:11434", "timeout": 42}]


def test_semente_fixa_vai_nas_opcoes():
    cliente = ClienteFalso("ok")
    llm = ModeloOllama(temperatura=0.0, semente=42, cliente=cliente)
    llm.gerar("instruções", "pergunta")
    assert cliente.chamadas[0]["options"] == {
        "temperature": 0.0,
        "num_ctx": 8192,
        "seed": 42,
    }


def test_raciocinio_desligado_por_padrao():
    # o Qwen 3.5 pensa antes de responder; desligado, a comparação com o Gemma é justa
    cliente = ClienteFalso("ok")
    ModeloOllama(cliente=cliente).gerar("s", "m")
    assert cliente.chamadas[0]["think"] is False


def test_raciocinio_sem_valor_nao_vai_na_chamada():
    cliente = ClienteFalso("ok")
    ModeloOllama(cliente=cliente, pensar=None).gerar("s", "m")
    assert "think" not in cliente.chamadas[0]


def test_saida_maxima_vai_nas_opcoes():
    cliente = ClienteFalso("ok")
    ModeloOllama(cliente=cliente, saida_maxima=512).gerar("s", "m")
    assert cliente.chamadas[0]["options"]["num_predict"] == 512


def test_gancho_recebe_cada_chamada_com_tokens_e_segundos():
    chamadas = []
    tempos = iter([10.0, 12.5])
    llm = ModeloOllama(
        modelo="qwen3.5:9b",
        cliente=ClienteFalso('{"a": 1}', tokens=(120, 30)),
        ao_gerar=chamadas.append,
        relogio=lambda: next(tempos),
    )
    llm.gerar_json("instruções", "pergunta", {"type": "object"})
    [chamada] = chamadas
    assert chamada.modelo == "qwen3.5:9b"
    assert chamada.sistema == "instruções"
    assert chamada.mensagem == "pergunta"
    assert chamada.saida == '{"a": 1}'
    assert chamada.estruturada is True
    assert (chamada.tokens_de_entrada, chamada.tokens_de_saida) == (120, 30)
    assert chamada.segundos == 2.5
    assert chamada.opcoes["temperature"] == 0.2


def test_falha_no_gancho_nao_muda_a_resposta():
    def quebrado(chamada):
        raise RuntimeError("Langfuse fora do ar")

    llm = ModeloOllama(cliente=ClienteFalso("resposta"), ao_gerar=quebrado)
    assert llm.gerar("s", "m") == "resposta"
