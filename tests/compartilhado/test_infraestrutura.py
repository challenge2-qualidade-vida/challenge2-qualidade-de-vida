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
    def __init__(self, conteudo: str):
        self.conteudo = conteudo
        self.chamadas = []

    def chat(self, **kwargs):
        self.chamadas.append(kwargs)
        return {"message": {"content": self.conteudo}}


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
