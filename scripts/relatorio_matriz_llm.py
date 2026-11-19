"""Gera o relatório em Markdown da matriz de LLMs da #69 (LLM puro x RAG).

Uso: python scripts/relatorio_matriz_llm.py <pasta dos resultados> <arquivo .md>

Lê os JSONs gravados por `avaliar-respostas` e o `estado.jsonl` do scripts/rodar-matriz-llm.sh.
Só formata os números já calculados pelo código da avaliação (RN01).
"""

import json
import sys
from pathlib import Path

ORDEM = ["qwen2.5:7b", "qwen3.5:9b", "gemma3:12b", "qwen3.5:27b", "gemma3:27b"]


def pct(valor):
    return "—" if valor is None else f"{valor * 100:.0f}%"


def num(valor, casas=3):
    return "—" if valor is None else f"{valor:.{casas}f}"


def duracao(segundos):
    if segundos is None:
        return "—"
    horas, resto = divmod(int(segundos), 3600)
    return (
        f"{horas}h{resto // 60:02d}" if horas else f"{resto // 60}min{resto % 60:02d}"
    )


def carregar(pasta: Path):
    execucoes = {}
    for arquivo in sorted(pasta.glob("completo_*.json")):
        dados = json.loads(arquivo.read_text())
        execucoes[(dados["modelo_llm"], dados["modo"])] = dados
    estado = []
    if (pasta / "estado.jsonl").exists():
        estado = [
            json.loads(linha)
            for linha in (pasta / "estado.jsonl").read_text().splitlines()
            if linha.strip()
        ]
    return execucoes, estado


def tempo_total(estado, llm, modo):
    ok = [
        e for e in estado if e["llm"] == llm and e["modo"] == modo and e["codigo"] == 0
    ]
    return ok[-1]["segundos"] if ok else None


def gerar(pasta: Path) -> str:
    execucoes, estado = carregar(pasta)
    modelos = [m for m in ORDEM if any(e["llm"] == m for e in estado)] or ORDEM
    qualquer = next(iter(execucoes.values()), {})
    limiar = next((d["limiar"] for d in execucoes.values() if d.get("limiar")), "—")
    linhas = [
        "# Matriz de LLMs: LLM puro x RAG no PC Linux (#69)",
        "",
        (
            "Execução da matriz da [spec 69](../../specs/69-llm-puro-vs-rag/spec.md) numa máquina só, "
            "uma execução por vez, gerada por `scripts/rodar-matriz-llm.sh`. "
            "Os números saem dos JSONs da avaliação; este arquivo só os formata."
        ),
        "",
        "## Configuração",
        "",
        f"- **Máquina:** {qualquer.get('maquina', '—')}, Radeon RX 9060 XT (16 GB), 60 GB de RAM",
        f"- **Perguntas:** `{qualquer.get('perguntas_arquivo', '—')}` ({qualquer.get('perguntas', '—')} perguntas)",
        f"- **Embeddings:** {qualquer.get('modelo_embeddings', '—')}; limiar {limiar} no RAG",
        (
            f"- **Fixos:** temperatura {qualquer.get('temperatura', '—')}, semente {qualquer.get('semente', '—')}, "
            f"contexto {qualquer.get('contexto', '—')}, saída máxima {qualquer.get('saida_maxima', '—')}, raciocínio desligado"
        ),
        (
            "- **Prompts:** RAG com `resposta_com_fontes@v2` (resposta estruturada e segunda tentativa de citação); "
            "puro com `resposta_sem_base`"
        ),
        f"- **Resultados:** `{pasta}`",
        "",
        "## Resultados por modelo e modo",
        "",
        "| Modelo | Modo | Acurácia | Respondeu | Recusa (RN11) | Aviso de preço (RN04) | Fonte citada (RN10) | Hit@5 | ROUGE-1 | ROUGE-L | Cosseno | Latência média | Latência máx. | Tempo total |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for llm in modelos:
        for modo in ("rag", "puro"):
            d = execucoes.get((llm, modo))
            if not d:
                linhas.append(f"| `{llm}` | {modo} | não concluída |" + " |" * 11)
                continue
            linhas.append(
                f"| `{llm}` | {modo} | {pct(d['acuracia'])} | {pct(d['taxa_de_resposta'])} | "
                f"{pct(d['recusa_correta'])} | {pct(d['aviso_de_preco'])} | {pct(d['fonte_esperada'])} | "
                f"{pct(d['hit'])} | {num(d['rouge_1'])} | {num(d['rouge_l'])} | {num(d['cosseno'])} | "
                f"{num(d['latencia_media'], 1)} s | {num(d['latencia_maxima'], 1)} s | "
                f"{duracao(tempo_total(estado, llm, modo))} |"
            )

    linhas += [
        "",
        "## Ganho do RAG sobre o LLM puro",
        "",
        "Diferença RAG − puro, por modelo (pontos percentuais e pontos de métrica).",
        "",
        "| Modelo | Acurácia | ROUGE-1 | ROUGE-L | Cosseno | Latência média |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for llm in modelos:
        rag, puro = execucoes.get((llm, "rag")), execucoes.get((llm, "puro"))
        if not (rag and puro):
            linhas.append(f"| `{llm}` | — | — | — | — | — |")
            continue

        def dif(chave, casas=3, escala=1, rag=rag, puro=puro):
            a, b = rag.get(chave), puro.get(chave)
            return "—" if a is None or b is None else f"{(a - b) * escala:+.{casas}f}"

        linhas.append(
            f"| `{llm}` | {dif('acuracia', 0, 100)} p.p. | {dif('rouge_1')} | {dif('rouge_l')} | "
            f"{dif('cosseno')} | {dif('latencia_media', 1)} s |"
        )

    linhas += ["", "## Erros de comportamento", ""]
    for llm in modelos:
        for modo in ("rag", "puro"):
            d = execucoes.get((llm, modo))
            if d:
                linhas.append(
                    f"- `{llm}` {modo}: falsas recusas {', '.join(d['falsas_recusas']) or 'nenhuma'}; "
                    f"respostas indevidas {', '.join(d['respostas_indevidas']) or 'nenhuma'}"
                )

    categorias = sorted(
        {c for d in execucoes.values() for c in d.get("por_categoria", {})}
    )
    if categorias:
        linhas += [
            "",
            "## ROUGE-L por categoria",
            "",
            "| Categoria | "
            + " | ".join(f"{m} {modo}" for m in modelos for modo in ("rag", "puro"))
            + " |",
            "| --- |" + " --- |" * (2 * len(modelos)),
        ]
        for cat in categorias:
            celulas = []
            for m in modelos:
                for modo in ("rag", "puro"):
                    d = execucoes.get((m, modo), {})
                    celulas.append(
                        num(d.get("por_categoria", {}).get(cat, {}).get("rouge_l"), 2)
                    )
            linhas.append(f"| {cat} | " + " | ".join(celulas) + " |")

    linhas += ["", "## Execuções e links do Langfuse", ""]
    linhas += [
        "| Modelo | Modo | Tentativa | Início | Fim | Duração | Código de saída |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e in estado:
        linhas.append(
            f"| `{e['llm']}` | {e['modo']} | {e['tentativa']} | {e['inicio']} | {e['fim']} | "
            f"{duracao(e['segundos'])} | {e['codigo']} |"
        )
    linhas.append("")
    for llm in modelos:
        for modo in ("rag", "puro"):
            d = execucoes.get((llm, modo))
            if d and d.get("langfuse_run"):
                linhas.append(f"- `{llm}` {modo} ({d['run']}): {d['langfuse_run']}")

    linhas += [
        "",
        "## Limites",
        "",
        (
            '- As respostas de referência de `perguntas_rag_v3.json` ainda têm o aviso "Revisar antes de rodar a matriz"; '
            "ROUGE e cosseno dependem delas."
        ),
        "- O ROUGE penaliza paráfrase e o cosseno do e5 varia pouco (quase sempre entre 0,7 e 1,0): servem para comparar execuções, não como nota absoluta.",
        "- Nenhuma métrica confere se os números da resposta estão certos.",
        "- Os modelos de 27B não cabem nos 16 GB da placa e dividem a carga com a RAM: a latência deles mede também esse transbordo.",
        "- O juiz (fidelidade e relevância) ainda não avalia os runs da avaliação no Langfuse (tarefa 1.4 do plano).",
        "- Uma máquina só, e perguntas fictícias.",
        "",
    ]
    return "\n".join(linhas)


if __name__ == "__main__":
    pasta, destino = Path(sys.argv[1]), Path(sys.argv[2])
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(gerar(pasta))
    print(f"Relatório gravado em {destino}")
