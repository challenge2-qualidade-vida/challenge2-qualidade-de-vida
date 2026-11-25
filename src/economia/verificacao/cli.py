"""Linha de comando da verificação de alegações (spec 79).

Uso:
    poetry run python -m economia.verificacao.cli avaliar \\
        --casos data/avaliacao/verificacao/casos_v1.json \\
        --saida data/avaliacao/verificacao/resultados_v1.json [--llm gemma3:12b]

Roda Research → Analysis → Validation em cada alegação, com até 2 retornos, grava o resultado
e imprime a tabela em Markdown. Com as chaves do Langfuse, cada alegação vira um trace com um
span por agente e as chamadas ao LLM ligadas aos prompts.
"""

import argparse
import json
import os
import platform
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from economia.compartilhado.configuracao import Configuracao, obter_configuracao

AGENTE = "verificacao"
PROMPT_DE_ANALISE = "analise"
PROMPT_DE_VALIDACAO = "validacao"
# na avaliação, a mesma alegação gera a mesma análise
TEMPERATURA_DA_AVALIACAO = 0.0
SEMENTE_DA_AVALIACAO = 42


def descrever_maquina() -> str:
    return f"{platform.system()} {platform.machine()}, {os.cpu_count()} CPUs lógicas"


def criar_pesquisar(configuracao: Configuracao):
    """Research Agent da #75: e5 e a coleção de evidências no Qdrant."""
    from economia.compartilhado.infraestrutura.embeddings_e5 import GeradorE5
    from economia.pesquisa_evidencias.aplicacao.pesquisar_evidencias import (
        PesquisarEvidencias,
    )
    from economia.pesquisa_evidencias.infraestrutura.pesquisador_qdrant import (
        PesquisadorQdrant,
    )
    from economia.pesquisa_evidencias.infraestrutura.repositorio_qdrant import (
        RepositorioQdrant,
    )

    pesquisador = PesquisadorQdrant(
        gerador=GeradorE5(dispositivo=configuracao.dispositivo_embeddings),
        repositorio=RepositorioQdrant.conectar(
            url=configuracao.qdrant_url, colecao=configuracao.colecao_pesquisa_evidencias
        ),
    )
    return PesquisarEvidencias(pesquisador).executar


def criar_llm(configuracao: Configuracao, ao_gerar=None):
    from economia.compartilhado.infraestrutura.llm_ollama import ModeloOllama

    return ModeloOllama(
        url=configuracao.ollama_url,
        modelo=configuracao.ollama_modelo,
        contexto=configuracao.ollama_contexto,
        tempo_limite=configuracao.ollama_tempo_limite,
        saida_maxima=configuracao.ollama_saida_maxima,
        temperatura=TEMPERATURA_DA_AVALIACAO,
        semente=SEMENTE_DA_AVALIACAO,
        ao_gerar=ao_gerar,
    )


def criar_agentes(
    configuracao: Configuracao,
    llm,
    prompts,
    prompt_de_analise: str = PROMPT_DE_ANALISE,
    prompt_de_validacao: str = PROMPT_DE_VALIDACAO,
):
    """Analysis e Validation com os prompts do Langfuse.

    `analise` lê o rótulo `production`; `analise@v2`, outro rótulo.
    """
    from economia.verificacao.aplicacao.analisar_alegacao import AnalisarAlegacao
    from economia.verificacao.aplicacao.validar_analise import ValidarAnalise

    return (
        AnalisarAlegacao(llm, prompts.carregar(AGENTE, prompt_de_analise)),
        ValidarAnalise(
            llm,
            prompts.carregar(AGENTE, prompt_de_validacao),
            configuracao.limiar_confianca_verificacao,
        ),
    )


def comando_avaliar(args: argparse.Namespace) -> None:
    from economia.compartilhado.infraestrutura.observabilidade_langfuse import (
        RegistroDeGeracoes,
        criar_cliente,
    )
    from economia.compartilhado.infraestrutura.prompts_langfuse import (
        PromptsDoLangfuse,
    )
    from economia.verificacao.aplicacao.avaliacao import (
        avaliar,
        carregar_casos,
        tabela_markdown,
    )

    configuracao = obter_configuracao()
    if args.llm:
        configuracao = configuracao.model_copy(update={"ollama_modelo": args.llm})
    casos = carregar_casos(args.casos)
    if args.limite_de_casos:
        casos = casos[: args.limite_de_casos]

    langfuse = criar_cliente(configuracao)
    prompts = PromptsDoLangfuse(langfuse)
    registro = RegistroDeGeracoes(langfuse, prompts.prompts_lidos) if langfuse else None
    llm = criar_llm(configuracao, ao_gerar=registro)
    analisar, validar = criar_agentes(
        configuracao, llm, prompts, args.prompt_analise, args.prompt_validacao
    )
    observador = None
    if langfuse:
        from economia.verificacao.infraestrutura.observabilidade_langfuse import (
            ObservadorLangfuse,
        )

        observador = ObservadorLangfuse(langfuse, tags=("verificacao", "avaliacao"))

    print(f"{len(casos)} alegações | LLM {configuracao.ollama_modelo}", flush=True)

    def progresso(n, total, r) -> None:
        marca = "ok " if r.acertou else "ERR"
        retornos = (
            f"{r.retornos} retorno(s) {','.join(r.destinos)}" if r.retornos else ""
        )
        print(
            f"[{n:>2}/{total}] {marca} {r.id:<5} esperada={r.esperada:<9} "
            f"obtida={r.obtida!s:<11} {'aprovada' if r.aprovado else 'reprovada'} "
            f"{r.segundos:6.1f} s {retornos}",
            flush=True,
        )

    resumo = avaliar(
        casos,
        criar_pesquisar(configuracao),
        analisar,
        validar,
        limite=args.limite,
        maximo_de_retornos=args.retornos,
        limite_maximo=args.limite_maximo,
        observador=observador,
        ao_progredir=progresso,
    )
    if langfuse:
        langfuse.flush()

    dados = {
        "data": datetime.now(UTC).isoformat(timespec="seconds"),
        "maquina": descrever_maquina(),
        "casos_arquivo": str(args.casos),
        "modelo_llm": configuracao.ollama_modelo,
        "modelo_embeddings": configuracao.modelo_embeddings,
        "colecao": configuracao.colecao_verificacao,
        "limiar_confianca": configuracao.limiar_confianca_verificacao,
        "limite_inicial": args.limite,
        "maximo_de_retornos": args.retornos,
        "limite_maximo": args.limite_maximo,
        "prompt_de_analise": args.prompt_analise,
        "prompt_de_validacao": args.prompt_validacao,
        "temperatura": TEMPERATURA_DA_AVALIACAO,
        "semente": SEMENTE_DA_AVALIACAO,
        "versoes_dos_prompts": dict(prompts.versoes),
        **asdict(resumo),
    }
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("\n" + tabela_markdown(resumo))
    print(f"\nResultado gravado em {args.saida}")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="economia.verificacao.cli")
    comandos = parser.add_subparsers(required=True)

    avaliar = comandos.add_parser(
        "avaliar",
        help="Roda Research → Analysis → Validation num conjunto de alegações",
    )
    avaliar.add_argument("--casos", type=Path, required=True)
    avaliar.add_argument("--saida", type=Path, required=True)
    avaliar.add_argument("--llm", help="Modelo do Ollama (padrão: OLLAMA_MODELO)")
    avaliar.add_argument(
        "--limite", type=int, default=5, help="Evidências na primeira busca (padrão 5)"
    )
    avaliar.add_argument(
        "--retornos", type=int, default=2, help="Limite de retornos por caso (padrão 2)"
    )
    avaliar.add_argument(
        "--limite-maximo",
        type=int,
        default=20,
        help="Teto da busca nos retornos ao Research, que dobram o limite (padrão 20)",
    )
    avaliar.add_argument(
        "--prompt-analise",
        default=PROMPT_DE_ANALISE,
        help="Prompt do Analysis no Langfuse: analise (production) ou analise@<rótulo>",
    )
    avaliar.add_argument(
        "--prompt-validacao",
        default=PROMPT_DE_VALIDACAO,
        help="Prompt do Validation no Langfuse: validacao (production) ou validacao@<rótulo>",
    )
    avaliar.add_argument(
        "--limite-de-casos", type=int, help="Roda só os primeiros N casos (piloto)"
    )
    avaliar.set_defaults(funcao=comando_avaliar)
    return parser


def main(argv: list[str] | None = None) -> None:
    from economia.compartilhado.infraestrutura.prompts_langfuse import (
        PromptIndisponivel,
    )

    args = criar_parser().parse_args(argv)
    try:
        args.funcao(args)
    except PromptIndisponivel as erro:
        raise SystemExit(str(erro)) from erro


if __name__ == "__main__":
    main()
