from dataclasses import dataclass, field

import pytest

from economia.compartilhado.infraestrutura.prompts_langfuse import (
    PRODUCAO,
    PromptsDoLangfuse,
    nome_no_langfuse,
    sincronizar_prompts,
)


@dataclass
class PromptFalso:
    name: str
    prompt: str
    version: int
    labels: list[str] = field(default_factory=list)
    is_fallback: bool = False


class LangfuseDePrompts:
    """Guarda as versões criadas, como o prompt management do Langfuse."""

    def __init__(self):
        self.versoes: dict[str, list[PromptFalso]] = {}
        self.criados = 0
        self.indisponivel = False

    def create_prompt(self, *, name, prompt, labels, **_):
        versoes = self.versoes.setdefault(name, [])
        for antigo in versoes:  # cada rótulo aponta para uma versão só
            antigo.labels = [r for r in antigo.labels if r not in labels]
        novo = PromptFalso(name, prompt, len(versoes) + 1, list(labels))
        versoes.append(novo)
        self.criados += 1
        return novo

    def update_prompt(self, *, name, version, new_labels):
        for p in self.versoes[name]:
            if p.version == version:
                p.labels = sorted(set(p.labels) | set(new_labels))

    def get_prompt(self, name, *, label, fallback=None, **_):
        if self.indisponivel:
            if fallback is not None:
                return PromptFalso(name, fallback, 0, is_fallback=True)
            raise ConnectionError("Langfuse fora do ar")
        for p in reversed(self.versoes.get(name, [])):
            if label in p.labels:
                return p
        raise LookupError("rótulo não encontrado")


@pytest.fixture
def pasta(tmp_path):
    (tmp_path / "miau-ricio").mkdir()
    (tmp_path / "miau-ricio" / "resposta_com_fontes_v1.md").write_text("Prompt v1")
    (tmp_path / "miau-ricio" / "resposta_com_fontes_v2.md").write_text("Prompt v2")
    return tmp_path


def test_nome_no_langfuse_separa_a_versao():
    assert nome_no_langfuse("miau-ricio", "resposta_com_fontes_v2") == (
        "miau-ricio/resposta_com_fontes",
        "v2",
    )
    with pytest.raises(ValueError):
        nome_no_langfuse("miau-ricio", "sem_versao")


def test_sincronizar_publica_cada_arquivo_com_o_rotulo_da_versao(pasta):
    langfuse = LangfuseDePrompts()
    sincronizados = sincronizar_prompts(
        langfuse, {"miau-ricio/resposta_com_fontes_v2"}, pasta
    )

    assert [(s.rotulo, s.em_producao) for s in sincronizados] == [
        ("v1", False),
        ("v2", True),
    ]
    v2 = langfuse.get_prompt("miau-ricio/resposta_com_fontes", label="v2")
    assert v2.prompt == "Prompt v2"
    assert PRODUCAO in v2.labels


def test_sincronizar_de_novo_sem_mudanca_nao_cria_versao(pasta):
    langfuse = LangfuseDePrompts()
    sincronizar_prompts(langfuse, set(), pasta)
    criados = langfuse.criados

    segunda = sincronizar_prompts(langfuse, set(), pasta)

    assert langfuse.criados == criados
    assert not any(s.criado for s in segunda)


def test_trocar_o_prompt_em_uso_move_o_rotulo_production(pasta):
    langfuse = LangfuseDePrompts()
    sincronizar_prompts(langfuse, set(), pasta)

    sincronizar_prompts(langfuse, {"miau-ricio/resposta_com_fontes_v1"}, pasta)

    v1 = langfuse.get_prompt("miau-ricio/resposta_com_fontes", label="v1")
    assert PRODUCAO in v1.labels


def test_arquivo_alterado_cria_versao_nova(pasta):
    langfuse = LangfuseDePrompts()
    sincronizar_prompts(langfuse, set(), pasta)
    (pasta / "miau-ricio" / "resposta_com_fontes_v1.md").write_text("Prompt v1 revisto")

    sincronizar_prompts(langfuse, set(), pasta)

    v1 = langfuse.get_prompt("miau-ricio/resposta_com_fontes", label="v1")
    assert (v1.prompt, v1.version) == ("Prompt v1 revisto", 3)


def test_carregar_le_do_langfuse_e_guarda_o_prompt(pasta):
    langfuse = LangfuseDePrompts()
    langfuse.create_prompt(
        name="miau-ricio/resposta_com_fontes",
        prompt="Prompt do Langfuse",
        labels=["v1"],
    )
    prompts = PromptsDoLangfuse(langfuse, pasta)

    texto = prompts.carregar("miau-ricio", "resposta_com_fontes_v1")

    assert texto == "Prompt do Langfuse"
    assert prompts.prompts_lidos[texto].version == 1


@pytest.mark.parametrize("falha", ["fallback", "excecao"])
def test_sem_o_langfuse_o_prompt_vem_do_arquivo(pasta, falha):
    langfuse = LangfuseDePrompts()
    langfuse.indisponivel = True
    prompts = PromptsDoLangfuse(langfuse, pasta)
    if falha == "excecao":
        langfuse.get_prompt = lambda *a, **k: (_ for _ in ()).throw(TimeoutError())

    assert prompts.carregar("miau-ricio", "resposta_com_fontes_v1") == "Prompt v1"
    assert prompts.prompts_lidos == {}
