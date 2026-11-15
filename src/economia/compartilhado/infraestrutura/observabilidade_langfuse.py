"""Registro das chamadas ao LLM no Langfuse Cloud.

Só a infraestrutura conhece o Langfuse. O adaptador do LLM entrega cada chamada a um gancho
(`ModeloOllama(ao_gerar=...)`), e este módulo transforma a chamada numa *geração* do Langfuse:
modelo, prompt (nome e versão), entrada, saída, tokens e tempo.

Num registro (trace), cada etapa é uma observação: a busca no Qdrant, cada chamada ao LLM.
A geração entra como filha da observação aberta no momento (a pergunta em avaliação).

RN30: o cliente mascara e-mail, CPF, telefone, cartão e chave de NFC-e em toda entrada, saída
e metadado antes do envio (`economia.compartilhado.mascaramento`).
"""

from collections.abc import Mapping
from typing import Any

from economia.compartilhado.configuracao import Configuracao
from economia.compartilhado.infraestrutura.llm_ollama import ChamadaAoLLM
from economia.compartilhado.mascaramento import mascarar


def criar_cliente(configuracao: Configuracao, **opcoes: Any) -> Any | None:
    """Cliente do Langfuse, ou `None` sem as chaves (nada é enviado).

    Todo dado passa pelo mascaramento da RN30 antes de sair da máquina. `opcoes` vão direto
    ao construtor do SDK (nos testes, um exportador de spans em memória).
    """
    if not configuracao.langfuse_configurado:
        return None
    from langfuse import Langfuse

    return Langfuse(
        public_key=configuracao.langfuse_public_key,
        secret_key=configuracao.langfuse_secret_key,
        base_url=configuracao.langfuse_base_url,
        environment=configuracao.langfuse_ambiente,
        mask=mascarar,
        **opcoes,
    )


class RegistroDeGeracoes:
    """Gancho do `ModeloOllama`: cada chamada vira uma geração no Langfuse.

    `prompts_do_langfuse` liga o texto de cada prompt do sistema ao prompt lido do Langfuse
    (`PromptsDoLangfuse.prompts_lidos`): a geração fica vinculada ao prompt e à versão, e o
    Langfuse mostra as métricas por versão. Um prompt vindo da cópia local não tem vínculo.
    """

    def __init__(self, cliente: Any, prompts_do_langfuse: Mapping[str, Any] = {}):
        self._cliente = cliente
        self._prompts = prompts_do_langfuse

    def __call__(self, chamada: ChamadaAoLLM) -> None:
        prompt = self._prompts.get(chamada.sistema)
        nome = prompt.name if prompt is not None else None
        versao = str(prompt.version) if prompt is not None else None
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
            version=versao,
            model=chamada.modelo,
            prompt=prompt,
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
