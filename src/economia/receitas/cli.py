"""Linha de comando do RAG de receitas.

Uso:
    poetry run python -m economia.receitas.cli indexar [--modelo e5|qwen3] [--recriar] [--amostra 400]
    poetry run python -m economia.receitas.cli perguntar "o que faço com arroz e ovo?"
    poetry run python -m economia.receitas.cli comparar [--amostra 400] [--saida arquivo.json]
    poetry run python -m economia.receitas.cli avaliar-respostas --saida arquivo.json [--modo rag|puro] [--llm gemma3:12b]
    poetry run python -m economia.receitas.cli comparar-execucoes ANTES.json DEPOIS.json
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
ARQUIVO_DE_PERGUNTAS = PASTA_DE_AVALIACAO / "perguntas_rag_v2.json"
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


# A avaliação das respostas usa o LLM sem aleatoriedade, para que duas execuções sejam comparáveis.
TEMPERATURA_DA_AVALIACAO = 0.0
SEMENTE_DA_AVALIACAO = 42


PROMPT_SEM_BASE = "resposta_sem_base_v1"
MODOS = ("rag", "puro")


def criar_llm(configuracao: Configuracao, deterministico: bool = False, ao_gerar=None):
    """LLM do Ollama com a configuração. Na avaliação, temperatura 0 e semente fixa."""
    from economia.compartilhado.infraestrutura.llm_ollama import ModeloOllama

    return ModeloOllama(
        url=configuracao.ollama_url,
        modelo=configuracao.ollama_modelo,
        contexto=configuracao.ollama_contexto,
        tempo_limite=configuracao.ollama_tempo_limite,
        saida_maxima=configuracao.ollama_saida_maxima,
        ao_gerar=ao_gerar,
        **(
            {
                "temperatura": TEMPERATURA_DA_AVALIACAO,
                "semente": SEMENTE_DA_AVALIACAO,
            }
            if deterministico
            else {}
        ),
    )


def criar_responder(
    configuracao: Configuracao,
    amostra: int | None = None,
    deterministico: bool = False,
    llm=None,
    repositorio=None,
    gerador=None,
):
    from economia.compartilhado.infraestrutura.prompts import carregar_prompt
    from economia.receitas.aplicacao.responder_pergunta import ResponderPergunta

    return ResponderPergunta(
        gerador or criar_gerador(configuracao),
        repositorio or criar_repositorio(configuracao, amostra),
        llm or criar_llm(configuracao, deterministico),
        prompt_do_sistema=carregar_prompt(
            "miau-ricio", configuracao.prompt_de_resposta
        ),
        limiar=configuracao.limiar_similaridade,
        prompt_de_extracao=carregar_prompt("miau-ricio", "extrair_ingredientes_v1"),
        ingredientes_basicos=configuracao.ingredientes_basicos,
        tolerancia=configuracao.tolerancia_empate,
        resposta_estruturada=configuracao.resposta_estruturada,
        pedido_de_citacao=carregar_prompt("miau-ricio", "pedido_de_citacao_v1")
        if configuracao.segunda_tentativa_de_citacao
        else None,
    )


def criar_caso_de_avaliacao(
    configuracao: Configuracao,
    modo: str,
    llm,
    amostra: int | None = None,
    repositorio=None,
    gerador=None,
):
    """Caso de uso avaliado: o RAG completo ou o LLM puro, com o mesmo LLM."""
    if modo == "puro":
        from economia.compartilhado.infraestrutura.prompts import carregar_prompt
        from economia.receitas.aplicacao.responder_sem_base import ResponderSemBase

        return ResponderSemBase(llm, carregar_prompt("miau-ricio", PROMPT_SEM_BASE))
    return criar_responder(
        configuracao, amostra, llm=llm, repositorio=repositorio, gerador=gerador
    )


def nomes_dos_prompts(configuracao: Configuracao) -> dict[str, str]:
    """Texto de cada prompt → nome do arquivo, para o registro dizer qual prompt foi usado."""
    from economia.compartilhado.infraestrutura.prompts import carregar_prompt

    nomes = {
        PROMPT_SEM_BASE,
        configuracao.prompt_de_resposta,
        "extrair_ingredientes_v1",
        "pedido_de_citacao_v1",
    }
    return {carregar_prompt("miau-ricio", nome): nome for nome in nomes}


def nome_do_run(configuracao: Configuracao, modo: str) -> str:
    """Nome da execução: modo, LLM, prompt e, no RAG, o modelo de embeddings."""
    if modo == "puro":
        return f"puro-{configuracao.ollama_modelo}-{PROMPT_SEM_BASE}"
    return (
        f"rag-{configuracao.ollama_modelo}-{configuracao.prompt_de_resposta}"
        f"-{configuracao.modelo_embeddings}"
    )


def nome_do_dataset(arquivo: Path, avaliadas: int, total: int) -> str:
    """Um dataset por conjunto de perguntas; um piloto (subconjunto) tem o seu."""
    nome = f"miau-ricio-{arquivo.stem}"
    return nome if avaliadas == total else f"{nome}-{avaliadas}de{total}"


def descrever_llm(configuracao: Configuracao) -> dict:
    """Digest, quantização e tamanho do modelo no Ollama, para a execução ser reproduzível."""
    import ollama

    cliente = ollama.Client(host=configuracao.ollama_url)
    try:
        detalhes = cliente.show(configuracao.ollama_modelo)["details"]
        digest = next(
            (
                m["digest"]
                for m in cliente.list()["models"]
                if m["model"] == configuracao.ollama_modelo
            ),
            None,
        )
    # Ollama fora do ar ou modelo não baixado: a execução falha depois, na 1ª pergunta
    except (ConnectionError, ollama.ResponseError) as erro:
        return {"erro": str(erro)}
    return {
        "digest": digest,
        "quantizacao": detalhes["quantization_level"],
        "parametros": detalhes["parameter_size"],
        "familia": detalhes["family"],
    }


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

    from economia.receitas.aplicacao.avaliacao import (
        avaliar,
        carregar_perguntas,
        por_categoria,
    )

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
                "por_categoria": por_categoria(resumo.resultados),
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

    for r in resumos:
        print(f"\n{r['colecao']}: por categoria")
        print(
            f"  {'categoria':<24} {'perguntas':>9} {'Recall@k':>8} {'MRR':>6} {'maior score':>11}"
        )
        for categoria, m in r["por_categoria"].items():
            recall = "—" if m["recall"] is None else f"{m['recall']:.2f}"
            mrr = "—" if m["mrr"] is None else f"{m['mrr']:.2f}"
            print(
                f"  {categoria:<24} {m['perguntas']:>9} {recall:>8} {mrr:>6} {m['maior_score']:>11.3f}"
            )

    sufixo = f"_amostra{args.amostra}" if args.amostra else ""
    saida = args.saida or PASTA_DE_AVALIACAO / f"resultados_v1{sufixo}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(
        json.dumps(
            {
                "maquina": descrever_maquina(),
                "data": _agora(),
                "perguntas": str(args.perguntas),
                "k": args.k,
                "modelos": resumos,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nResultado gravado em {saida}")


def _agora() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


def comando_avaliar_respostas(args: argparse.Namespace) -> None:
    """Roda o caso de uso (RAG ou LLM puro) em cada pergunta e grava o resultado.

    Com as chaves do Langfuse, a execução vira um run do dataset das perguntas, com a busca e
    as chamadas ao LLM registradas e as métricas como pontuações. Sem as chaves, nada é enviado.
    """
    import json
    from dataclasses import asdict
    from functools import partial

    from economia.receitas.aplicacao.avaliacao import carregar_perguntas
    from economia.receitas.aplicacao.avaliacao_respostas import (
        avaliar_pergunta,
        avaliar_respostas,
        resumir_respostas,
    )

    configuracao = configuracao_com_modelo(args.modelo)
    ajustes = {
        chave: valor
        for chave, valor in (
            ("prompt_de_resposta", args.prompt),
            ("resposta_estruturada", args.estruturada),
            ("segunda_tentativa_de_citacao", args.segunda_tentativa),
            ("ollama_modelo", args.llm),
        )
        if valor is not None
    }
    configuracao = configuracao.model_copy(update=ajustes)
    todas = carregar_perguntas(args.perguntas)
    perguntas = todas
    if args.categorias:
        perguntas = [p for p in perguntas if p.categoria in args.categorias]
    if args.limite:
        perguntas = perguntas[: args.limite]

    from economia.compartilhado.infraestrutura.observabilidade_langfuse import (
        RegistroDeGeracoes,
        criar_cliente,
    )

    langfuse = criar_cliente(configuracao)
    registro = (
        RegistroDeGeracoes(langfuse, nomes_dos_prompts(configuracao))
        if langfuse
        else None
    )
    llm = criar_llm(configuracao, deterministico=True, ao_gerar=registro)
    # o e5 calcula o cosseno nos dois modos; no RAG, é o mesmo gerador da busca
    gerador = criar_gerador(configuracao)
    repositorio = None
    if args.modo == "rag":
        repositorio = criar_repositorio(configuracao, args.amostra)
        if langfuse:
            from economia.receitas.infraestrutura.experimento_langfuse import (
                RepositorioObservado,
            )

            repositorio = RepositorioObservado(repositorio, langfuse)
    caso = criar_caso_de_avaliacao(
        configuracao, args.modo, llm, args.amostra, repositorio, gerador
    )
    colecao = (
        configuracao.colecao_da_amostra(args.amostra) if args.modo == "rag" else None
    )
    run = nome_do_run(configuracao, args.modo)
    execucao = {
        "modo": args.modo,
        "run": run,
        "maquina": descrever_maquina(),
        "data": _agora(),
        "perguntas_arquivo": str(args.perguntas),
        "colecao": colecao,
        "modelo_embeddings": configuracao.modelo_embeddings,
        "modelo_llm": configuracao.ollama_modelo,
        "llm": descrever_llm(configuracao),
        "limiar": configuracao.limiar_similaridade if args.modo == "rag" else None,
        "prompt_de_resposta": configuracao.prompt_de_resposta
        if args.modo == "rag"
        else PROMPT_SEM_BASE,
        "resposta_estruturada": configuracao.resposta_estruturada
        if args.modo == "rag"
        else True,
        "segunda_tentativa_de_citacao": configuracao.segunda_tentativa_de_citacao
        if args.modo == "rag"
        else False,
        "temperatura": TEMPERATURA_DA_AVALIACAO,
        "semente": SEMENTE_DA_AVALIACAO,
        "contexto": configuracao.ollama_contexto,
        "saida_maxima": configuracao.ollama_saida_maxima,
        "raciocinio": False,
    }
    print(f"Execução {run} | {len(perguntas)} perguntas", flush=True)

    def progresso(n, total, r) -> None:
        marca = "ok " if r.acertou else "ERR"
        fonte = {True: "fonte ok", False: "fonte errada", None: ""}[r.fonte_esperada]
        rouge = "" if r.rouge_l is None else f"ROUGE-L {r.rouge_l:.2f}"
        print(
            f"[{n:>3}/{total}] {marca} {r.id:<5} esperado={r.esperado:<15} "
            f"obtido={r.obtido:<15} {r.segundos:6.1f} s {fonte} {rouge}",
            flush=True,
        )

    avaliar = partial(avaliar_pergunta, responder=caso.responder, gerador=gerador)
    url_do_run = None
    if langfuse:
        from economia.receitas.infraestrutura.experimento_langfuse import (
            rodar_experimento,
            sincronizar_dataset,
        )

        dataset = nome_do_dataset(args.perguntas, len(perguntas), len(todas))
        sincronizar_dataset(langfuse, dataset, perguntas)
        resultados, url_do_run = rodar_experimento(
            langfuse,
            dataset,
            run,
            perguntas,
            avaliar,
            metadata={k: v for k, v in execucao.items() if k != "llm"},
            ao_progredir=progresso,
        )
        langfuse.flush()
        resumo = resumir_respostas(resultados)
    else:
        resumo = avaliar_respostas(
            perguntas, caso.responder, ao_progredir=progresso, gerador=gerador
        )
    dados = {**execucao, "langfuse_run": url_do_run, **asdict(resumo)}

    def taxa(valor) -> str:
        return "—" if valor is None else f"{valor:.0%}"

    def numero(valor) -> str:
        return "—" if valor is None else f"{valor:.3f}"

    print(f"\n{resumo.perguntas} perguntas | {run}")
    for rotulo, chave in (
        ("Acurácia do comportamento", "acuracia"),
        ("Taxa de resposta", "taxa_de_resposta"),
        ("Recusa correta (RN11)", "recusa_correta"),
        ("Aviso de preço (RN04)", "aviso_de_preco"),
        ("Fonte esperada citada", "fonte_esperada"),
        ("Hit@5", "hit"),
    ):
        print(f"  {rotulo:<28} {taxa(dados[chave]):>6}")
    for rotulo, chave in (
        ("ROUGE-1 F1", "rouge_1"),
        ("ROUGE-L F1", "rouge_l"),
        ("Cosseno com a referência", "cosseno"),
    ):
        print(f"  {rotulo:<28} {numero(dados[chave]):>6}")
    print(
        f"  {'Latência média / máxima':<28} {resumo.latencia_media:5.1f} s / {resumo.latencia_maxima:.1f} s"
    )
    if resumo.falsas_recusas:
        print(f"  Falsas recusas: {', '.join(resumo.falsas_recusas)}")
    if resumo.respostas_indevidas:
        print(f"  Respostas indevidas: {', '.join(resumo.respostas_indevidas)}")

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nResultado gravado em {args.saida}")
    if url_do_run:
        print(f"Run no Langfuse: {url_do_run}")


def comando_comparar_execucoes(args: argparse.Namespace) -> None:
    """Mostra a diferença de cada métrica entre duas execuções da avaliação."""
    import json

    from economia.receitas.aplicacao.comparacao_de_avaliacoes import (
        comparar_categorias,
        comparar_execucoes,
        formatar_delta,
        tipo_da_execucao,
    )

    antes = json.loads(args.antes.read_text(encoding="utf-8"))
    depois = json.loads(args.depois.read_text(encoding="utf-8"))

    def valor(v) -> str:
        return "—" if v is None else f"{v:.3f}"

    print(
        f"Comparação ({tipo_da_execucao(antes)}): {args.antes.name} → {args.depois.name}\n"
    )
    print(f"{'métrica':<26} {'antes':>8} {'depois':>8} {'diferença':>9}")
    for d in comparar_execucoes(antes, depois):
        print(
            f"{d.metrica:<26} {valor(d.antes):>8} {valor(d.depois):>8} {formatar_delta(d.delta):>9}"
        )
    print("\nPor categoria:")
    for categoria, diferencas in comparar_categorias(antes, depois).items():
        partes = [
            f"{d.metrica} {valor(d.antes)} → {valor(d.depois)} ({formatar_delta(d.delta)})"
            for d in diferencas
        ]
        print(f"  {categoria:<24} " + " | ".join(partes))


def criar_parser() -> argparse.ArgumentParser:
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
    comparar_parser.add_argument(
        "--saida",
        type=Path,
        help="arquivo do resultado (padrão: data/avaliacao/resultados_v1.json)",
    )
    comparar_parser.set_defaults(funcao=comando_comparar)

    respostas_parser = comandos.add_parser(
        "avaliar-respostas",
        help="roda o caso de uso completo em cada pergunta e confere o comportamento",
    )
    respostas_parser.add_argument("--saida", type=Path, required=True)
    respostas_parser.add_argument(
        "--modo",
        choices=MODOS,
        default="rag",
        help="rag (busca, limiar e fontes) ou puro (só o LLM, sem a base)",
    )
    respostas_parser.add_argument(
        "--llm", help="modelo do Ollama (padrão: OLLAMA_MODELO, ex.: gemma3:12b)"
    )
    respostas_parser.add_argument(
        "--perguntas", type=Path, default=ARQUIVO_DE_PERGUNTAS
    )
    respostas_parser.add_argument(
        "--modelo", choices=["e5", "qwen3"], help="padrão: MODELO_EMBEDDINGS"
    )
    respostas_parser.add_argument(
        "--amostra", type=int, help="usa a coleção da amostra"
    )
    respostas_parser.add_argument(
        "--categorias", nargs="+", help="avalia só estas categorias"
    )
    respostas_parser.add_argument("--limite", type=int, help="avalia só as N primeiras")
    respostas_parser.add_argument(
        "--prompt",
        help="prompt da resposta (padrão: PROMPT_DE_RESPOSTA, ex.: resposta_com_fontes_v2)",
    )
    respostas_parser.add_argument(
        "--estruturada",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="pede ao LLM um JSON com a resposta e os trechos usados",
    )
    respostas_parser.add_argument(
        "--segunda-tentativa",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="pede ao LLM que reescreva citando quando a resposta vier sem citação",
    )
    respostas_parser.set_defaults(funcao=comando_avaliar_respostas)

    execucoes_parser = comandos.add_parser(
        "comparar-execucoes", help="diferença entre duas execuções da avaliação"
    )
    execucoes_parser.add_argument("antes", type=Path)
    execucoes_parser.add_argument("depois", type=Path)
    execucoes_parser.set_defaults(funcao=comando_comparar_execucoes)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = criar_parser().parse_args(argv)
    args.funcao(args)


if __name__ == "__main__":
    main()
