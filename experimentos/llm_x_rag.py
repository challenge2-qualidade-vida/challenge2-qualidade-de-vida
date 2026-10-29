"""Experimento do tópico 8: LLM sem RAG × LLM + RAG × sem LLM (+ agentes, tópico 9).

Rodar (com o Ollama ligado):
    .venv/bin/python experimentos/llm_x_rag.py            # todas as abordagens
    .venv/bin/python experimentos/llm_x_rag.py C D        # só C e D; as outras vêm do CSV anterior
    LLM_MODELO=qwen2.5:3b .venv/bin/python experimentos/llm_x_rag.py

Gera docs/semana-3/resultados-llm-x-rag.md e docs/semana-3/resultados-llm-x-rag.csv.
"""

import csv
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from economia.agentes import Orquestrador  # noqa: E402
from economia.assistente import Assistente  # noqa: E402
from economia.avaliacao import avaliar, carregar_perguntas  # noqa: E402
from economia.dados import carregar  # noqa: E402
from economia.llm import cliente_do_ambiente  # noqa: E402
from economia.rag import BaseConhecimento  # noqa: E402

SAIDA = RAIZ / "docs" / "semana-3"
CRITERIOS = ["correcao", "fundamentacao", "incerteza", "ferramenta"]
NOMES_CRITERIOS = {
    "correcao": "Correção",
    "fundamentacao": "Fundamentação (cita a base)",
    "incerteza": "Tratamento de incerteza",
    "ferramenta": "Usou a ferramenta certa",
}


def rodar(nome, assistente, perguntas):
    linhas = []
    cliente = assistente.cliente
    for p in perguntas:
        antes = (cliente.tokens_entrada, cliente.tokens_saida) if cliente else (0, 0)
        inicio = time.perf_counter()
        r = assistente.responder(p["pergunta"])
        segundos = time.perf_counter() - inicio
        depois = (cliente.tokens_entrada, cliente.tokens_saida) if cliente else (0, 0)
        notas = avaliar(p, r.resposta, r.ferramentas_usadas, r.fontes)
        linhas.append({
            "abordagem": nome, "id": p["id"], "categoria": p["categoria"], "pergunta": p["pergunta"],
            **notas, "segundos": round(segundos, 1),
            "tokens_entrada": depois[0] - antes[0], "tokens_saida": depois[1] - antes[1],
            "modo": r.modo, "ferramentas": ",".join(r.ferramentas_usadas), "resposta": r.resposta.replace("\n", " "),
        })
        print(f"[{nome}] {p['id']} correção={notas['correcao']} {segundos:.1f}s", flush=True)
    return linhas


def media(linhas, campo):
    valores = [l[campo] for l in linhas if l[campo] is not None]
    return (sum(valores) / len(valores), len(valores)) if valores else (None, 0)


def pct(v):
    return "—" if v is None else f"{v:.0%}"


def relatorio(linhas, abordagens, modelo):
    md = [
        "# Resultados — experimento LLM × LLM + RAG",
        "",
        f"Gerado automaticamente por `experimentos/llm_x_rag.py` em {date.today().strftime('%d/%m/%Y')}. Modelo: **{modelo}** (gratuito). "
        f"{len({l['id'] for l in linhas})} perguntas por abordagem.",
        "",
        "## Resumo",
        "",
        "| Critério | " + " | ".join(abordagens) + " |",
        "|---|" + "---|" * len(abordagens),
    ]
    por = {a: [l for l in linhas if l["abordagem"] == a] for a in abordagens}
    for c in CRITERIOS:
        celulas = []
        for a in abordagens:
            v, n = media(por[a], c)
            celulas.append(f"{pct(v)} (n={n})")
        md.append(f"| {NOMES_CRITERIOS[c]} | " + " | ".join(celulas) + " |")
    md.append("| Latência média | " + " | ".join(f"{sum(l['segundos'] for l in por[a]) / len(por[a]):.1f} s" for a in abordagens) + " |")
    md.append("| Tokens por pergunta (entrada + saída) | " + " | ".join(
        f"{sum(l['tokens_entrada'] + l['tokens_saida'] for l in por[a]) / len(por[a]):.0f}" for a in abordagens) + " |")
    md.append("| Custo em R$ | " + " | ".join("R$ 0,00" for _ in abordagens) + " |")

    md += ["", "## Correção por categoria", "", "| Categoria | " + " | ".join(abordagens) + " |", "|---|" + "---|" * len(abordagens)]
    for cat in dict.fromkeys(l["categoria"] for l in linhas):
        md.append(f"| {cat} | " + " | ".join(pct(media([l for l in por[a] if l["categoria"] == cat], "correcao")[0]) for a in abordagens) + " |")

    md += ["", "## Respostas", ""]
    for pid in dict.fromkeys(l["id"] for l in linhas):
        da_pergunta = [l for l in linhas if l["id"] == pid]
        md += [f"### {pid} — {da_pergunta[0]['pergunta']}", ""]
        for l in da_pergunta:
            marca = "✅" if l["correcao"] else "❌"
            md.append(f"- **{l['abordagem']}** {marca} ({l['segundos']} s): {l['resposta'][:400]}")
        md.append("")
    return "\n".join(md)


def main():
    base = carregar()
    bc = BaseConhecimento(base)
    perguntas = carregar_perguntas()

    clientes = [cliente_do_ambiente() for _ in range(3)]
    if clientes[0] is None:
        sys.exit("Nenhum LLM configurado. Ligue o Ollama ou defina LLM_PROVEDOR e LLM_API_KEY.")
    for c in clientes:
        c.temperatura = 0  # mais reprodutível

    abordagens = {
        "A — LLM sem RAG": Assistente(base, bc, clientes[0], usar_rag=False),
        "B — LLM + RAG": Assistente(base, bc, clientes[1], usar_rag=True),
        "C — sem LLM": Assistente(base, bc, None),
        "D — agentes (orquestrador + Mia)": Orquestrador(base, bc, clientes[2]),
    }
    escolhidas = {a.upper() for a in sys.argv[1:]} or {n[0] for n in abordagens}

    anteriores = []
    arquivo_csv = SAIDA / "resultados-llm-x-rag.csv"
    if arquivo_csv.exists() and len(escolhidas) < len(abordagens):
        with open(arquivo_csv, encoding="utf-8") as f:
            for l in csv.DictReader(f):
                if l["abordagem"][0] not in escolhidas:
                    for k in CRITERIOS:
                        l[k] = None if l[k] == "" else int(l[k])
                    for k in ("segundos",):
                        l[k] = float(l[k])
                    for k in ("tokens_entrada", "tokens_saida"):
                        l[k] = int(l[k])
                    anteriores.append(l)

    linhas = []
    for nome, assistente in abordagens.items():
        if nome[0] in escolhidas:
            linhas += rodar(nome, assistente, perguntas)
        else:
            linhas += [l for l in anteriores if l["abordagem"] == nome]
    linhas.sort(key=lambda l: l["abordagem"])
    abordagens = {n: a for n, a in abordagens.items() if any(l["abordagem"] == n for l in linhas)}

    SAIDA.mkdir(parents=True, exist_ok=True)
    with open(SAIDA / "resultados-llm-x-rag.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    (SAIDA / "resultados-llm-x-rag.md").write_text(relatorio(linhas, list(abordagens), f"{clientes[0].provedor}/{clientes[0].modelo}"), encoding="utf-8")
    print("Resultados em", SAIDA)


if __name__ == "__main__":
    main()
