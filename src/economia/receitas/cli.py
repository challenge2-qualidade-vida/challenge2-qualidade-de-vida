"""Linha de comando do RAG de receitas.

Uso:
    poetry run python -m economia.receitas.cli indexar [--modelo e5|qwen3] [--recriar] [--amostra 400]
    poetry run python -m economia.receitas.cli perguntar "o que faço com arroz e ovo?"
    poetry run python -m economia.receitas.cli comparar [--amostra 400]
"""

import argparse
import sys
from pathlib import Path

from economia.compartilhado.configuracao import Configuracao, obter_configuracao

PASTA_DE_DADOS = Path("data/raw")
ARQUIVO_AFRODITE = PASTA_DE_DADOS / "receitas/afrodite.json"
ARQUIVO_RECIPENLG = PASTA_DE_DADOS / "receitas/recipenlg_0000.parquet"
PASTA_DE_ORIENTACAO = PASTA_DE_DADOS / "orientacao"
PASTA_DE_AVALIACAO = Path("data/avaliacao")
ARQUIVO_DE_PERGUNTAS = PASTA_DE_AVALIACAO / "perguntas_rag_v1.json"
ARQUIVO_GUIA = PASTA_DE_ORIENTACAO / "guia_alimentar_populacao_brasileira_2ed.pdf"


def criar_gerador(configuracao: Configuracao):
    if configuracao.modelo_embeddings == "e5":
        from economia.receitas.infraestrutura.embeddings_e5 import GeradorE5

        return GeradorE5(dispositivo=configuracao.dispositivo_embeddings)
    from economia.receitas.infraestrutura.embeddings_ollama import GeradorOllama

    return GeradorOllama(url=configuracao.ollama_url)


def criar_repositorio(configuracao: Configuracao, amostra: int | None = None):
    from economia.receitas.infraestrutura.repositorio_qdrant import RepositorioQdrant

    return RepositorioQdrant.conectar(
        configuracao.qdrant_url, configuracao.colecao_da_amostra(amostra)
    )


def descrever_maquina() -> str:
    import os
    import platform

    return f"{platform.system()} {platform.machine()}, {os.cpu_count()} CPUs lógicas"


def carregar_documentos():
    """Guia Alimentar e os PDFs do catálogo. Arquivo que falta é avisado e fica de fora."""
    from economia.receitas.infraestrutura.carregadores import (
        DOCUMENTOS_DE_ORIENTACAO,
        carregar_documento_de_orientacao,
        carregar_guia_alimentar,
    )

    documentos = [carregar_guia_alimentar(ARQUIVO_GUIA)]
    for especificacao in DOCUMENTOS_DE_ORIENTACAO:
        if (PASTA_DE_ORIENTACAO / especificacao.arquivo).is_file():
            documentos.append(
                carregar_documento_de_orientacao(PASTA_DE_ORIENTACAO, especificacao)
            )
        else:
            print(
                f"Aviso: {especificacao.arquivo} não encontrado, fica fora",
                file=sys.stderr,
            )
    return documentos


def carregar_trechos(
    quantidade_recipenlg: int,
    amostra_de_receitas: int | None,
    so_orientacao: bool = False,
):
    from economia.receitas.aplicacao.indexar_base import amostra_fixa, montar_trechos
    from economia.receitas.infraestrutura.carregadores import (
        carregar_afrodite,
        carregar_recipenlg,
    )
    from economia.receitas.infraestrutura.embeddings_e5 import contador_de_tokens_e5

    receitas = []
    if not so_orientacao:
        receitas = carregar_afrodite(ARQUIVO_AFRODITE) + carregar_recipenlg(
            ARQUIVO_RECIPENLG, quantidade=quantidade_recipenlg
        )
    documentos = carregar_documentos()
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
    trechos, descartadas = carregar_trechos(
        args.quantidade_recipenlg, args.amostra, args.so_orientacao
    )
    print(f"{len(trechos)} trechos ({descartadas} receitas incompletas descartadas)")
    gerador = criar_gerador(configuracao)
    repositorio = criar_repositorio(configuracao, args.amostra)
    colecao = repositorio.colecao

    def progresso(feitos: int, total: int) -> None:
        print(
            f"\r{colecao}: {feitos}/{total}",
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
        f"{resultado.trechos} trechos gravados em {colecao} "
        f"em {resultado.segundos:.0f} s ({repositorio.contar()} na coleção)"
    )
    if not args.so_orientacao:
        import json

        PASTA_DE_AVALIACAO.mkdir(parents=True, exist_ok=True)
        registro = {
            "colecao": colecao,
            "modelo": gerador.nome,
            "trechos": resultado.trechos,
            "segundos": round(resultado.segundos, 1),
            "trechos_por_segundo": round(resultado.trechos / resultado.segundos, 2),
            "maquina": descrever_maquina(),
        }
        (PASTA_DE_AVALIACAO / f"indexacao_{colecao}.json").write_text(
            json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def criar_responder(configuracao: Configuracao, amostra: int | None = None):
    from economia.compartilhado.infraestrutura.llm_ollama import ModeloOllama
    from economia.compartilhado.infraestrutura.prompts import carregar_prompt
    from economia.receitas.aplicacao.responder_pergunta import ResponderPergunta

    return ResponderPergunta(
        criar_gerador(configuracao),
        criar_repositorio(configuracao, amostra),
        ModeloOllama(
            url=configuracao.ollama_url,
            modelo=configuracao.ollama_modelo,
            contexto=configuracao.ollama_contexto,
        ),
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
    caso = criar_responder(configuracao, args.amostra)
    colecao = configuracao.colecao_da_amostra(args.amostra)
    print(f"Pergunta: {args.pergunta}")
    print(f"Coleção: {colecao} | limiar: {configuracao.limiar_similaridade}")

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


def comando_comparar(args: argparse.Namespace) -> None:
    """Avalia cada modelo no conjunto de perguntas e grava o resultado em data/avaliacao/."""
    import json
    from dataclasses import asdict

    from economia.receitas.aplicacao.avaliacao import avaliar, carregar_perguntas

    perguntas = carregar_perguntas(args.perguntas)
    resumos = []
    for modelo in args.modelos:
        configuracao = configuracao_com_modelo(modelo)
        repositorio = criar_repositorio(configuracao, args.amostra)
        if repositorio.contar() == 0:
            print(
                f"{repositorio.colecao}: coleção vazia; rode indexar --modelo {modelo} antes"
            )
            continue
        resumo = avaliar(perguntas, criar_gerador(configuracao), repositorio, k=args.k)
        indexacao = PASTA_DE_AVALIACAO / f"indexacao_{repositorio.colecao}.json"
        resumos.append(
            {
                "colecao": repositorio.colecao,
                "trechos_na_colecao": repositorio.contar(),
                "indexacao": json.loads(indexacao.read_text())
                if indexacao.is_file()
                else None,
                **asdict(resumo),
                "separacao": round(resumo.separacao, 4),
                "limiar_sugerido": resumo.limiar_sugerido,
            }
        )

    print(f"\n{len(perguntas)} perguntas, top-{args.k} | {descrever_maquina()}\n")
    cabecalho = (
        f"{'coleção':<38} {'Recall@k':>8} {'MRR':>6} {'score c/':>8} {'score s/':>8} "
        f"{'separação':>9} {'limiar':>6} {'s/consulta':>10}"
    )
    print(cabecalho)
    for r in resumos:
        print(
            f"{r['colecao']:<38} {r['recall']:>8.2f} {r['mrr']:>6.2f} "
            f"{r['score_medio_com_resposta']:>8.3f} {r['score_medio_sem_resposta']:>8.3f} "
            f"{r['separacao']:>9.3f} {r['limiar_sugerido']:>6.3f} {r['latencia_media']:>10.3f}"
        )
    for r in resumos:
        erros = [
            p for p in r["resultados"] if p["tem_resposta"] and p["posicao"] is None
        ]
        if erros:
            print(f"\n{r['colecao']}: perguntas sem acerto no top-{args.k}:")
            for p in erros:
                print(f"  {p['id']} ({p['categoria']}): {' | '.join(p['titulos'][:3])}")

    sufixo = f"_amostra{args.amostra}" if args.amostra else ""
    saida = PASTA_DE_AVALIACAO / f"resultados_v1{sufixo}.json"
    saida.write_text(
        json.dumps(
            {"maquina": descrever_maquina(), "k": args.k, "modelos": resumos},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nResultado gravado em {saida}")


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
        help="indexa só N receitas (metade de cada fonte) e todos os trechos de orientação, "
        "numa coleção própria (ex.: base_conhecimento_e5_amostra400)",
    )
    indexar_parser.add_argument(
        "--so-orientacao",
        action="store_true",
        help="indexa só os textos de orientação (as receitas já gravadas ficam)",
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
    perguntar_parser.add_argument(
        "--amostra", type=int, help="usa a coleção da amostra (ex.: 400)"
    )
    perguntar_parser.set_defaults(funcao=comando_perguntar)

    comparar_parser = comandos.add_parser(
        "comparar", help="compara os modelos de embeddings no conjunto de avaliação"
    )
    comparar_parser.add_argument(
        "--modelos", nargs="+", choices=["e5", "qwen3"], default=["e5", "qwen3"]
    )
    comparar_parser.add_argument(
        "--amostra", type=int, help="usa as coleções da amostra (ex.: 400)"
    )
    comparar_parser.add_argument("--k", type=int, default=5)
    comparar_parser.add_argument("--perguntas", type=Path, default=ARQUIVO_DE_PERGUNTAS)
    comparar_parser.set_defaults(funcao=comando_comparar)

    args = parser.parse_args(argv)
    args.funcao(args)


if __name__ == "__main__":
    main()
