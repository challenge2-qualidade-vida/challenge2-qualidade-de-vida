"""Evaluators gerenciados do Langfuse Cloud (LLM como juiz), criados pela API pública (spec 29).

As chamadas usam o cliente da API que vem no SDK do Langfuse (`Langfuse().api`). Os corpos
seguem os nomes dos modelos do SDK (snake_case); o SDK converte para o formato da API.

Dois evaluators, fidelidade e relevância, com os prompts `juiz/fidelidade` e `juiz/relevancia`
do prompt management do Langfuse (rótulo `production`), e
uma regra de avaliação que os aplica à observação raiz de cada pergunta (`miau-ricio.pergunta`),
numa amostra do tráfego real (20%, por conta do custo).

O modelo juiz é o Gemini, pela LLM Connection do projeto. A chave do Gemini é cadastrada por
uma pessoa da equipe na interface do Langfuse e nunca passa pelo repositório.

O comando é idempotente: rodar de novo atualiza o que já existe, pelo nome.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

# adaptadores do Langfuse que servem o Gemini
ADAPTADORES_DO_GEMINI = ("google-ai-studio", "google-vertex-ai")
NOME_DA_REGRA = "miau-ricio: juiz no tráfego real"
OBSERVACAO_AVALIADA = "miau-ricio.pergunta"

# variáveis do prompt → onde estão na observação raiz (ver economia.api.observabilidade)
_ORIGENS = {
    "pergunta": ("input", "$.pergunta"),
    "resposta": ("output", "$.texto"),
    "trechos": ("output", "$.trechos"),
}


@dataclass(frozen=True)
class Avaliador:
    nome: str
    descricao: str
    prompt: str  # prompt `juiz/<prompt>` no Langfuse
    variaveis: tuple[str, ...]


AVALIADORES = (
    Avaliador(
        nome="fidelidade",
        descricao="A resposta só afirma o que está nos trechos recuperados (RN10, RN11)",
        prompt="fidelidade",
        variaveis=("pergunta", "resposta", "trechos"),
    ),
    Avaliador(
        nome="relevancia",
        descricao="A resposta atende ao que a pessoa perguntou",
        prompt="relevancia",
        variaveis=("pergunta", "resposta"),
    ),
)


class SemConexaoDoGemini(RuntimeError):
    """O projeto do Langfuse ainda não tem a LLM Connection do Gemini."""


def provedor_do_gemini(conexoes: Sequence[dict]) -> str:
    """Nome do provedor da LLM Connection do Gemini, para o `modelConfig`."""
    for conexao in conexoes:
        if conexao.get("adapter") in ADAPTADORES_DO_GEMINI:
            return conexao["provider"]
    raise SemConexaoDoGemini(
        "Cadastre a LLM Connection do Gemini no Langfuse (Settings > LLM Connections, "
        "adaptador Google AI Studio) antes de criar os evaluators. "
        "Passo a passo em docs/semana-3/observabilidade.md."
    )


def corpo_do_avaliador(
    avaliador: Avaliador, provedor: str, modelo: str, prompt: str
) -> dict:
    return {
        "name": avaliador.nome,
        "description": avaliador.descricao,
        "type": "llm_as_judge",
        "prompt": prompt,
        "model_config_": {"provider": provedor, "model": modelo},
        "variable_mapping": [
            {
                "variable": variavel,
                "source": _ORIGENS[variavel][0],
                "json_path": _ORIGENS[variavel][1],
            }
            for variavel in avaliador.variaveis
        ],
        "output_definition": {
            "data_type": "NUMERIC",
            "min_value": 0,
            "max_value": 1,
            "score_value_instructions": "Nota de 0 a 1, seguindo os critérios do prompt.",
            "score_reasoning_instructions": "Explique a nota em uma ou duas frases.",
        },
    }


def corpo_da_regra(
    ids_dos_avaliadores: Sequence[str], amostra: float, ambientes: Sequence[str]
) -> dict:
    """Regra sobre a observação raiz de cada pergunta respondida, sem as que deram erro."""
    return {
        "name": NOME_DA_REGRA,
        "enabled": True,
        "sampling": amostra,
        "filter": [
            {
                "type": "stringOptions",
                "column": "name",
                "operator": "any of",
                "value": [OBSERVACAO_AVALIADA],
            },
            {
                "type": "stringOptions",
                "column": "environment",
                "operator": "any of",
                "value": list(ambientes),
            },
            {
                "type": "stringOptions",
                "column": "level",
                "operator": "none of",
                "value": ["ERROR"],
            },
        ],
        "evaluator_assignments": [{"evaluator_id": id} for id in ids_dos_avaliadores],
    }


def _todos(listar) -> list:
    itens, cursor = [], None
    while True:
        pagina = listar(limit=100, cursor=cursor)
        itens.extend(pagina.data)
        cursor = getattr(pagina.meta, "next_cursor", None)
        if not cursor:
            return itens


# ao salvar um evaluator, o Langfuse testa o modelo no provedor: passa do timeout padrão do SDK
_ESCRITA = {"timeout_in_seconds": 120}


class ApiDoLangfuse:
    """Evaluators, regras e LLM Connections pela API do SDK (`Langfuse().api`)."""

    def __init__(self, api: Any):
        self._api = api

    def conexoes(self) -> list[dict]:
        return [
            {"provider": c.provider, "adapter": getattr(c.adapter, "value", c.adapter)}
            for c in self._api.llm_connections.list(limit=100).data
        ]

    def avaliadores(self) -> dict[str, str]:
        return {a.name: a.id for a in _todos(self._api.evaluators.list)}

    def regras(self) -> dict[str, str]:
        return {r.name: r.id for r in _todos(self._api.evaluation_rules.list)}

    def criar_avaliador(self, corpo: dict) -> str:
        from langfuse.api.evaluators.types.create_evaluator_request import (
            CreateEvaluatorRequest_LlmAsJudge,
        )

        pedido = CreateEvaluatorRequest_LlmAsJudge.model_validate(corpo)
        return self._api.evaluators.create(request=pedido, request_options=_ESCRITA).id

    def atualizar_avaliador(self, id: str, corpo: dict) -> str:
        from langfuse.api.evaluators.types.update_llm_as_judge_evaluator_request import (
            UpdateLlmAsJudgeEvaluatorRequest,
        )

        pedido = UpdateLlmAsJudgeEvaluatorRequest.model_validate(corpo)
        return self._api.evaluators.update(
            id, request=pedido, request_options=_ESCRITA
        ).id

    @staticmethod
    def _regra(corpo: dict) -> dict:
        """Filtros e atribuições como modelos do SDK, validados antes do envio."""
        from langfuse.api.evaluation_commons.types.evaluation_rule_filter import (
            EvaluationRuleFilter,
        )
        from langfuse.api.evaluation_rules.types.evaluation_rule_evaluator_assignment_input import (
            EvaluationRuleEvaluatorAssignmentInput,
        )
        from pydantic import TypeAdapter

        filtro = TypeAdapter(EvaluationRuleFilter)
        return {
            **corpo,
            "filter": [filtro.validate_python(f) for f in corpo["filter"]],
            "evaluator_assignments": [
                EvaluationRuleEvaluatorAssignmentInput.model_validate(a)
                for a in corpo["evaluator_assignments"]
            ],
        }

    def criar_regra(self, corpo: dict) -> str:
        return self._api.evaluation_rules.create(
            **self._regra(corpo), request_options=_ESCRITA
        ).id

    def atualizar_regra(self, id: str, corpo: dict) -> str:
        return self._api.evaluation_rules.update(
            id, **self._regra(corpo), request_options=_ESCRITA
        ).id


def criar_avaliadores(
    api: ApiDoLangfuse,
    modelo: str,
    amostra: float,
    ambientes: Sequence[str],
    carregar_prompt: Callable[[str, str], str],
) -> dict[str, str]:
    """Cria ou atualiza os evaluators e a regra. Devolve nome → id, com a regra no fim.

    `carregar_prompt(agente, nome)` lê o prompt do juiz (`PromptsDoLangfuse.carregar`).
    """
    provedor = provedor_do_gemini(api.conexoes())
    existentes = api.avaliadores()
    ids = {}
    for avaliador in AVALIADORES:
        corpo = corpo_do_avaliador(
            avaliador, provedor, modelo, carregar_prompt("juiz", avaliador.prompt)
        )
        if avaliador.nome in existentes:
            ids[avaliador.nome] = api.atualizar_avaliador(
                existentes[avaliador.nome], corpo
            )
        else:
            ids[avaliador.nome] = api.criar_avaliador(corpo)

    regra = corpo_da_regra(list(ids.values()), amostra, ambientes)
    regras = api.regras()
    if NOME_DA_REGRA in regras:
        ids[NOME_DA_REGRA] = api.atualizar_regra(regras[NOME_DA_REGRA], regra)
    else:
        ids[NOME_DA_REGRA] = api.criar_regra(regra)
    return ids
