import json
from dataclasses import dataclass, field

import pytest

from economia.compartilhado.infraestrutura.prompts_langfuse import (
    PRODUCAO,
    PromptIndisponivel,
    PromptsDoLangfuse,
    resolver,
)


@dataclass
class PromptFalso:
    name: str
    prompt: str
    version: int
    labels: list[str] = field(default_factory=list)


class LangfuseDePrompts:
    """Prompt management em memória: cada rótulo aponta para uma versão."""

    def __init__(self, *prompts: PromptFalso):
        self.prompts = list(prompts)
        self.fora_do_ar = False

    def get_prompt(self, name, *, label, **_):
        if self.fora_do_ar:
            raise ConnectionError("Langfuse fora do ar")
        for p in self.prompts:
            if p.name == name and label in p.labels:
                return p
        raise LookupError(f"{name}@{label}")


V1 = PromptFalso("miau-ricio/resposta_com_fontes", "Prompt v1", 1, ["v1", PRODUCAO])
V2 = PromptFalso("miau-ricio/resposta_com_fontes", "Prompt v2", 2, ["v2", "latest"])


@pytest.mark.parametrize(
    ("referencia", "esperado"),
    [
        ("resposta_com_fontes", ("miau-ricio/resposta_com_fontes", PRODUCAO)),
        ("resposta_com_fontes@v2", ("miau-ricio/resposta_com_fontes", "v2")),
        ("resposta_com_fontes@latest", ("miau-ricio/resposta_com_fontes", "latest")),
        ("resposta_com_fontes_v2", ("miau-ricio/resposta_com_fontes", "v2")),
    ],
)
def test_referencia_vira_nome_e_rotulo(referencia, esperado):
    assert resolver("miau-ricio", referencia) == esperado


def test_le_o_rotulo_production_e_guarda_o_prompt(tmp_path):
    prompts = PromptsDoLangfuse(LangfuseDePrompts(V1, V2), tmp_path)

    texto = prompts.carregar("miau-ricio", "resposta_com_fontes")

    assert texto == "Prompt v1"
    assert prompts.prompts_lidos[texto] is V1
    assert prompts.versoes == {"miau-ricio/resposta_com_fontes": 1}


def test_outro_rotulo_le_outra_versao(tmp_path):
    prompts = PromptsDoLangfuse(LangfuseDePrompts(V1, V2), tmp_path)
    assert prompts.carregar("miau-ricio", "resposta_com_fontes@v2") == "Prompt v2"


def test_cada_leitura_atualiza_a_copia_local(tmp_path):
    PromptsDoLangfuse(LangfuseDePrompts(V1), tmp_path).carregar(
        "miau-ricio", "resposta_com_fontes"
    )

    copia = json.loads(
        (tmp_path / "miau-ricio" / "resposta_com_fontes@production.json").read_text()
    )
    assert (copia["texto"], copia["versao"]) == ("Prompt v1", 1)


@pytest.mark.parametrize("cliente", ["fora_do_ar", "sem_chaves"])
def test_sem_o_langfuse_o_prompt_vem_da_copia_local(tmp_path, cliente):
    langfuse = LangfuseDePrompts(V1)
    PromptsDoLangfuse(langfuse, tmp_path).carregar("miau-ricio", "resposta_com_fontes")
    langfuse.fora_do_ar = True

    prompts = PromptsDoLangfuse(langfuse if cliente == "fora_do_ar" else None, tmp_path)

    assert prompts.carregar("miau-ricio", "resposta_com_fontes") == "Prompt v1"
    assert prompts.prompts_lidos == {}  # da cópia, a geração fica sem vínculo


def test_sem_o_langfuse_e_sem_copia_o_prompt_esta_indisponivel(tmp_path):
    langfuse = LangfuseDePrompts(V1)
    langfuse.fora_do_ar = True

    with pytest.raises(PromptIndisponivel, match="LANGFUSE_PUBLIC_KEY"):
        PromptsDoLangfuse(langfuse, tmp_path).carregar(
            "miau-ricio", "resposta_com_fontes"
        )


def test_rotulo_inexistente_sem_copia_esta_indisponivel(tmp_path):
    with pytest.raises(PromptIndisponivel, match="resposta_com_fontes@v9"):
        PromptsDoLangfuse(LangfuseDePrompts(V1), tmp_path).carregar(
            "miau-ricio", "resposta_com_fontes@v9"
        )
