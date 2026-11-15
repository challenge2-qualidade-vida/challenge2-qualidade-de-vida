"""Prompts no prompt management do Langfuse (#28).

Os arquivos em `prompts/<agente>/<nome>_v<versao>.md` continuam sendo a fonte da verdade.
`sincronizar_prompts` publica cada arquivo no Langfuse como o prompt `<agente>/<nome>`, com o
rótulo `v<versao>`; o prompt em uso pela configuração recebe também o rótulo `production`.

Em execução, `PromptsDoLangfuse.carregar` lê o prompt do Langfuse pelo rótulo da versão
configurada e usa o arquivo local quando o Langfuse não responde. O prompt lido fica guardado
para a geração do LLM ser vinculada a ele (`RegistroDeGeracoes`).
"""

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from economia.compartilhado.infraestrutura.prompts import (
    PASTA_DOS_PROMPTS,
    carregar_prompt,
)

logger = logging.getLogger(__name__)

PRODUCAO = "production"
_NOME_COM_VERSAO = re.compile(r"^(?P<base>.+)_(?P<versao>v\d+)$")
# o prompt muda pouco: o SDK guarda em memória e confere de novo em segundo plano
CACHE_EM_SEGUNDOS = 300


def nome_no_langfuse(agente: str, nome: str) -> tuple[str, str]:
    """Nome do prompt no Langfuse e rótulo da versão (resposta_com_fontes_v2 → v2)."""
    encontrado = _NOME_COM_VERSAO.match(nome)
    if not encontrado:
        raise ValueError(f"Prompt sem versão no nome: {agente}/{nome}")
    return f"{agente}/{encontrado['base']}", encontrado["versao"]


@dataclass(frozen=True)
class PromptSincronizado:
    arquivo: str
    nome: str
    rotulo: str
    versao: int
    criado: bool
    em_producao: bool


def _buscar(cliente: Any, nome: str, rotulo: str) -> Any | None:
    try:
        return cliente.get_prompt(
            nome, label=rotulo, cache_ttl_seconds=0, max_retries=0
        )
    except Exception:  # o SDK levanta NotFoundError quando o rótulo não existe
        logger.debug("Prompt %s sem o rótulo %s", nome, rotulo, exc_info=True)
        return None


def sincronizar_prompts(
    cliente: Any,
    em_producao: Iterable[str],
    pasta: Path = PASTA_DOS_PROMPTS,
) -> list[PromptSincronizado]:
    """Publica os arquivos de prompt no Langfuse. Sem mudança no arquivo, nada é criado.

    `em_producao` são os arquivos em uso pela configuração (ex.: "miau-ricio/resposta_com_fontes_v1").
    """
    em_producao = set(em_producao)
    resultado = []
    for caminho in sorted(pasta.glob("*/*.md")):
        agente, arquivo = caminho.parent.name, caminho.stem
        nome, rotulo = nome_no_langfuse(agente, arquivo)
        texto = carregar_prompt(agente, arquivo, pasta)
        producao = f"{agente}/{arquivo}" in em_producao
        rotulos = [rotulo, PRODUCAO] if producao else [rotulo]

        atual = _buscar(cliente, nome, rotulo)
        criado = atual is None or atual.prompt != texto
        if criado:
            atual = cliente.create_prompt(
                name=nome,
                prompt=texto,
                labels=rotulos,
                type="text",
                commit_message=f"Sincronizado de prompts/{agente}/{arquivo}.md",
            )
        elif producao and PRODUCAO not in (atual.labels or []):
            cliente.update_prompt(name=nome, version=atual.version, new_labels=rotulos)
        resultado.append(
            PromptSincronizado(
                arquivo=f"{agente}/{arquivo}",
                nome=nome,
                rotulo=rotulo,
                versao=atual.version,
                criado=criado,
                em_producao=producao,
            )
        )
    return resultado


class PromptsDoLangfuse:
    """Carrega os prompts do Langfuse, com o arquivo local como alternativa.

    `prompts_lidos` liga o texto de cada prompt ao prompt do Langfuse, para o
    `RegistroDeGeracoes` vincular cada geração à versão usada.
    """

    def __init__(self, cliente: Any, pasta: Path = PASTA_DOS_PROMPTS):
        self._cliente = cliente
        self._pasta = pasta
        self.prompts_lidos: dict[str, Any] = {}

    def carregar(self, agente: str, nome: str) -> str:
        local = carregar_prompt(agente, nome, self._pasta)
        nome_remoto, rotulo = nome_no_langfuse(agente, nome)
        try:
            prompt = self._cliente.get_prompt(
                nome_remoto,
                label=rotulo,
                fallback=local,
                cache_ttl_seconds=CACHE_EM_SEGUNDOS,
            )
        except Exception:
            logger.warning(
                "Prompt %s lido do arquivo: Langfuse indisponível", nome, exc_info=True
            )
            return local
        if getattr(prompt, "is_fallback", False):
            return local
        self.prompts_lidos[prompt.prompt] = prompt
        return prompt.prompt
