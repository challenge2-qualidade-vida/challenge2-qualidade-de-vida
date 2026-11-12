"""Registro das chamadas ao LLM no Langfuse Cloud.

Só a infraestrutura conhece o Langfuse. O adaptador do LLM entrega cada chamada a um gancho
(`ModeloOllama(ao_gerar=...)`), e este módulo transforma a chamada numa *geração* do Langfuse:
modelo, prompt (nome e versão), entrada, saída, tokens e tempo.

Num registro (trace), cada etapa é uma observação: a busca no Qdrant, cada chamada ao LLM.
A geração entra como filha da observação aberta no momento (a pergunta em avaliação).

RN30: só o conjunto de avaliação, com perguntas fictícias, é registrado. As perguntas reais
das pessoas não passam por aqui.
"""

import re
from collections.abc import Mapping
from typing import Any

from economia.compartilhado.configuracao import Configuracao
from economia.compartilhado.infraestrutura.llm_ollama import ChamadaAoLLM

_VERSAO = re.compile(r"_(v\d+)$")


def criar_cliente(configuracao: Configuracao) -> Any | None:
    """Cliente do Langfuse, ou `None` sem as chaves (nada é enviado)."""
    if not configuracao.langfuse_configurado:
        return None
    from langfuse import Langfuse

    return Langfuse(
        public_key=configuracao.langfuse_public_key,
        secret_key=configuracao.langfuse_secret_key,
        base_url=configuracao.langfuse_base_url,
    )


def versao_do_prompt(nome: str) -> str | None:
    """Versão no fim do nome do arquivo do prompt (ex.: resposta_com_fontes_v2 → v2)."""
    encontrada = _VERSAO.search(nome)
    return encontrada.group(1) if encontrada else None


class RegistroDeGeracoes:
    """Gancho do `ModeloOllama`: cada chamada vira uma geração no Langfuse.

    `nomes_dos_prompts` liga o texto de cada prompt do sistema ao nome do arquivo, para o
    registro dizer qual prompt, e qual versão, gerou cada resposta.
    """

    def __init__(self, cliente: Any, nomes_dos_prompts: Mapping[str, str] = {}):
        self._cliente = cliente
        self._nomes = dict(nomes_dos_prompts)

    def __call__(self, chamada: ChamadaAoLLM) -> None:
        nome = self._nomes.get(chamada.sistema)
        tokens = (
            {"input": chamada.tokens_de_entrada, "output": chamada.tokens_de_saida}
            if chamada.tokens_de_entrada is not None
            and chamada.tokens_de_saida is not None
            else None
        )
        # o Ollama já respondeu quando o gancho é chamado: a duração real vai no metadado
        geracao = self._cliente.start_observation(
            as_type="generation",
            name=nome or "llm",
            version=versao_do_prompt(nome) if nome else None,
            model=chamada.modelo,
            input=[
                {"role": "system", "content": chamada.sistema},
                {"role": "user", "content": chamada.mensagem},
            ],
            output=chamada.saida,
            model_parameters=chamada.opcoes,
            usage_details=tokens,
            metadata={
                "segundos": round(chamada.segundos, 3),
                "estruturada": chamada.estruturada,
            },
        )
        geracao.end()
