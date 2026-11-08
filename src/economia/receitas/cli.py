"""Linha de comando do RAG de receitas.

Uso:
    poetry run python -m economia.receitas.cli indexar [--modelo e5|qwen3] [--recriar]
    poetry run python -m economia.receitas.cli perguntar "o que faço com arroz e ovo?"
"""

import argparse
import sys
from pathlib import Path

from economia.compartilhado.configuracao import Configuracao, obter_configuracao

PASTA_DE_DADOS = Path("data/raw")
ARQUIVO_AFRODITE = PASTA_DE_DADOS / "receitas/afrodite.json"
ARQUIVO_RECIPENLG = PASTA_DE_DADOS / "receitas/recipenlg_0000.parquet"
ARQUIVO_GUIA = PASTA_DE_DADOS / "orientacao/guia_alimentar_populacao_brasileira_2ed.pdf"


def criar_gerador(configuracao: Configuracao):
    if configuracao.modelo_embeddings == "e5":
        from economia.receitas.infraestrutura.embeddings_e5 import GeradorE5

        return GeradorE5(dispositivo=configuracao.dispositivo_embeddings)
    from economia.receitas.infraestrutura.embeddings_ollama import GeradorOllama

    return GeradorOllama(url=configuracao.ollama_url)


def criar_repositorio(configuracao: Configuracao):
    from economia.receitas.infraestrutura.repositorio_qdrant import RepositorioQdrant

    return RepositorioQdrant.conectar(configuracao.qdrant_url, configuracao.colecao)


def carregar_trechos(quantidade_recipenlg: int, amostra_de_receitas: int | None):
    from economia.receitas.aplicacao.indexar_base import amostra_fixa, montar_trechos
    from economia.receitas.infraestrutura.carregadores import (
        carregar_afrodite,
        carregar_guia_alimentar,
        carregar_recipenlg,
    )
    from economia.receitas.infraestrutura.embeddings_e5 import contador_de_tokens_e5

    receitas = carregar_afrodite(ARQUIVO_AFRODITE) + carregar_recipenlg(
        ARQUIVO_RECIPENLG, quantidade=quantidade_recipenlg
    )
    documentos = [carregar_guia_alimentar(ARQUIVO_GUIA)]
    trechos, descartadas = montar_trechos(
        receitas, documentos, contar=contador_de_tokens_e5()
    )
    if amostra_de_receitas is not None:
        trechos = amostra_fixa(trechos, amostra_de_receitas)
    return trechos, descartadas


def configuracao_com_modelo(modelo: str | None) -> Configuracao:
    configuracao = obter_configuracao()
    if modelo is None:
        return configuracao
    return configuracao.model_copy(update={"modelo_embeddings": modelo})


def comando_indexar(args: argparse.Namespace) -> None:
    from economia.receitas.aplicacao.indexar_base import indexar

    configuracao = configuracao_com_modelo(args.modelo)
    trechos, descartadas = carregar_trechos(args.quantidade_recipenlg, args.amostra)
    print(f"{len(trechos)} trechos ({descartadas} receitas incompletas descartadas)")
    gerador = criar_gerador(configuracao)
    repositorio = criar_repositorio(configuracao)

    def progresso(feitos: int, total: int) -> None:
        print(
            f"\r{configuracao.colecao}: {feitos}/{total}",
            end="",
            file=sys.stderr,
            flush=True,
        )

    resultado = indexar(
        trechos,
        gerador,
        repositorio,
        tamanho_do_lote=args.lote,
        recriar=args.recriar,
        ao_progredir=progresso,
        receitas_descartadas=descartadas,
    )
    print(file=sys.stderr)
    print(
        f"{resultado.trechos} trechos gravados em {configuracao.colecao} "
        f"em {resultado.segundos:.0f} s ({repositorio.contar()} na coleção)"
    )


def criar_responder(configuracao: Configuracao):
    from economia.compartilhado.infraestrutura.llm_ollama import ModeloOllama
    from economia.compartilhado.infraestrutura.prompts import carregar_prompt
    from economia.receitas.aplicacao.responder_pergunta import ResponderPergunta

    return ResponderPergunta(
        criar_gerador(configuracao),
        criar_repositorio(configuracao),
        ModeloOllama(url=configuracao.ollama_url, modelo=configuracao.ollama_modelo),
        prompt_do_sistema=carregar_prompt("miau-ricio", "resposta_com_fontes_v1"),
        limiar=configuracao.limiar_similaridade,
        prompt_de_extracao=carregar_prompt("miau-ricio", "extrair_ingredientes_v1"),
        ingredientes_basicos=configuracao.ingredientes_basicos,
        tolerancia=configuracao.tolerancia_empate,
    )


def comando_perguntar(args: argparse.Namespace) -> None:
    """Mostra a consulta, os trechos recuperados, a resposta e as fontes (demonstração)."""
    import time

    from economia.receitas.aplicacao.responder_pergunta import formatar_fonte

    configuracao = configuracao_com_modelo(args.modelo)
    caso = criar_responder(configuracao)
    print(f"Pergunta: {args.pergunta}")
    print(
        f"Coleção: {configuracao.colecao} | limiar: {configuracao.limiar_similaridade}"
    )

    if args.trechos:
        print("\nTrechos recuperados (acima do limiar):")
        for n, recuperado in enumerate(caso.recuperar(args.pergunta), start=1):
            trecho = recuperado.trecho
            print(
                f"  {n}. [{recuperado.score:.3f}] {trecho.tipo.value}: {trecho.titulo}"
            )

    inicio = time.perf_counter()
    resposta = caso.responder(args.pergunta)
    if resposta.ingredientes_disponiveis:
        print(
            f"\nIngredientes da pergunta: {', '.join(resposta.ingredientes_disponiveis)}"
        )
    print(f"\nResposta ({time.perf_counter() - inicio:.0f} s):\n{resposta.texto}")
    if resposta.trechos:
        print("\nFontes:")
        for n, recuperado in enumerate(resposta.trechos, start=1):
            print(f"  [{n}] {formatar_fonte(recuperado)}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="economia.receitas.cli", description=__doc__)
    comandos = parser.add_subparsers(dest="comando", required=True)

    indexar_parser = comandos.add_parser(
        "indexar", help="indexa a base de conhecimento no Qdrant"
    )
    indexar_parser.add_argument(
        "--modelo", choices=["e5", "qwen3"], help="padrão: MODELO_EMBEDDINGS"
    )
    indexar_parser.add_argument(
        "--recriar", action="store_true", help="apaga a coleção antes"
    )
    indexar_parser.add_argument(
        "--lote", type=int, default=16, help="trechos por lote (padrão: 16)"
    )
    indexar_parser.add_argument("--quantidade-recipenlg", type=int, default=3000)
    indexar_parser.add_argument(
        "--amostra",
        type=int,
        help="indexa só N receitas (metade de cada fonte) e todos os trechos de orientação",
    )
    indexar_parser.set_defaults(funcao=comando_indexar)

    perguntar_parser = comandos.add_parser(
        "perguntar", help="responde uma pergunta com os trechos e as fontes"
    )
    perguntar_parser.add_argument("pergunta")
    perguntar_parser.add_argument(
        "--modelo", choices=["e5", "qwen3"], help="padrão: MODELO_EMBEDDINGS"
    )
    perguntar_parser.add_argument(
        "--sem-trechos",
        dest="trechos",
        action="store_false",
        help="não mostra os trechos recuperados",
    )
    perguntar_parser.set_defaults(funcao=comando_perguntar)

    args = parser.parse_args(argv)
    args.funcao(args)


if __name__ == "__main__":
    main()
