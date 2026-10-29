"""Tópico 11: calcula as métricas do projeto e gera o relatório.

Rodar:
    .venv/bin/python experimentos/metricas.py

Gera docs/semana-7/metricas.md e docs/semana-7/metricas-cenarios.csv.
A precisão de preço usa docs/semana-7/verificacao-gondola.csv, preenchida pelo grupo.
"""

import csv
import statistics as st
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from economia.dados import carregar  # noqa: E402
from economia.metricas import avaliar_cenarios, precisao_de_preco, qualidade_dos_dados  # noqa: E402

SAIDA = RAIZ / "docs" / "semana-7"
ARQ_GONDOLA = SAIDA / "verificacao-gondola.csv"
ARQ_EXPERIMENTO = RAIZ / "docs" / "semana-3" / "resultados-llm-x-rag.csv"


def pct(parte, todo):
    return f"{parte / todo:.0%}" if todo else "—"


def br(v, casas=2):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def criar_planilha_gondola(base):
    """Modelo para o grupo conferir 20 preços no mercado (métrica 6)."""
    if ARQ_GONDOLA.exists():
        return
    amostra = sorted(base.precos, key=lambda p: (p.mercado, p.produto))[::5][:20]
    with open(ARQ_GONDOLA, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["produto_id", "mercado", "preco_app", "preco_gondola", "data_verificacao", "quem"])
        for p in amostra:
            w.writerow([p.produto, p.mercado, p.preco, "", "", ""])


def qualidade_respostas():
    if not ARQ_EXPERIMENTO.exists():
        return None
    with open(ARQ_EXPERIMENTO, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    resumo = {}
    for l in linhas:
        r = resumo.setdefault(l["abordagem"], [0, 0])
        r[0] += int(l["correcao"])
        r[1] += 1
    return resumo


def main():
    base = carregar()
    SAIDA.mkdir(parents=True, exist_ok=True)
    criar_planilha_gondola(base)
    linhas = avaliar_cenarios(base)
    with open(SAIDA / "metricas-cenarios.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for l in linhas for k in l}))
        w.writeheader()
        w.writerows(linhas)

    viaveis = [l for l in linhas if l["viavel"]]
    n = len(viaveis)
    dados = qualidade_dos_dados(base)
    gondola = precisao_de_preco(ARQ_GONDOLA)
    respostas = qualidade_respostas()
    aviso = "⚠️ **Todos os preços são de exemplo**: os valores de economia mostram como a métrica funciona, não a economia real. Recalcular depois da coleta." if dados["por_fonte"].get("exemplo") else ""

    md = [
        "# Métricas da EconoMIA",
        "",
        f"Gerado por `experimentos/metricas.py` em {date.today().strftime('%d/%m/%Y')}. "
        f"{len(linhas)} cenários: 1, 2, 4 e 6 pessoas × semana e mês × orçamento de R$ 5, 6, 8 e 12 por pessoa por dia × "
        "5 perfis (sem restrição, vegetariano, sem lactose, sem porco, sem glúten). Deslocamento de R$ 10 para um 2º mercado.",
        "",
        aviso,
        "",
        "## Resumo",
        "",
        "| # | Métrica | Resultado |",
        "|---|---------|-----------|",
        f"| 1 | Economia média × cesta de referência (estilo DIEESE) | **{br(st.mean(l['economia_pct'] for l in viaveis), 1)}%** bruta; **{br(st.mean(l['economia_ajustada_pct'] for l in viaveis), 1)}%** com a mesma energia |",
        f"| 2 | Aderência ao orçamento | **{pct(sum(l['dentro_orcamento'] for l in viaveis), n)}** das cestas dentro do orçamento; {pct(n, len(linhas))} dos cenários têm solução |",
        f"| 3 | Adequação nutricional | **{pct(sum(l['cumpre_metas'] for l in viaveis), n)}** cumprem as 4 metas; {pct(sum(l['respeita_restricoes'] for l in viaveis), n)} respeitam as restrições; {pct(sum(l['flv_diferentes'] >= 3 for l in viaveis), n)} têm ≥ 3 frutas/hortaliças |",
        f"| 4 | Custo por 1.000 kcal / por g de proteína | **R$ {br(st.mean(l['custo_1000kcal'] for l in viaveis))}** / R$ {br(st.mean(l['custo_g_proteina'] for l in viaveis), 3)} (referência: R$ {br(st.mean(l['ref_custo_1000kcal'] for l in viaveis))} / R$ {br(st.mean(l['ref_custo_g_proteina'] for l in viaveis), 3)}) |",
        f"| 5 | Qualidade dos dados | {dados['com_data_e_fonte_pct']:.0f}% dos preços com data e fonte; {dados['ate_30_dias_pct']:.0f}% com até 30 dias; cobertura de {dados['cobertura_pct']:.0f}% (produto × mercado); fontes: {dados['por_fonte']} |",
        f"| 6 | Precisão de preço (gôndola, ±5%) | " + (f"**{gondola['dentro_da_margem_pct']:.0f}%** de {gondola['itens_verificados']} itens" if gondola else "**pendente**: o grupo preenche `verificacao-gondola.csv` no mercado") + " |",
        "| 7 | Qualidade das respostas (experimento) | " + ("; ".join(f"{a}: {pct(c, t)}" for a, (c, t) in respostas.items()) if respostas else "rodar `experimentos/llm_x_rag.py`") + " |",
        "| 8 | Utilidade percebida | **pendente**: teste com usuários (roteiro em `docs/desenvolvimento/11-metricas.md`) |",
        "",
        "## Detalhes",
        "",
        "### Cenários sem solução",
        "",
    ]
    sem = [l for l in linhas if not l["viavel"]]
    if sem:
        faixas = {}
        for l in sem:
            dias = 7 if l["periodo"] == "semana" else 30
            faixas.setdefault(round(l["orcamento"] / l["pessoas"] / dias, 2), []).append(l)
        for por_dia, ls in sorted(faixas.items()):
            minimos = [l["minimo_necessario"] / l["pessoas"] / (7 if l["periodo"] == "semana" else 30) for l in ls if l["minimo_necessario"]]
            md.append(f"- R$ {br(por_dia)} por pessoa/dia: {len(ls)} cenários sem solução. O app informa o mínimo necessário (em média R$ {br(st.mean(minimos))} por pessoa/dia).")
    else:
        md.append("- Todos os cenários têm solução.")

    md += [
        "",
        "### Economia por perfil de restrição",
        "",
        "| Perfil | Cenários viáveis | Custo médio por pessoa/dia | Economia bruta | Economia com a mesma energia | Proteína de origem animal |",
        "|---|---|---|---|---|---|",
    ]
    for perfil in dict.fromkeys(l["restricoes"] for l in linhas):
        ls = [l for l in viaveis if l["restricoes"] == perfil]
        if not ls:
            continue
        por_dia = st.mean(l["custo"] / l["pessoas"] / (7 if l["periodo"] == "semana" else 30) for l in ls)
        md.append(f"| {perfil} | {len(ls)} | R$ {br(por_dia)} | {br(st.mean(l['economia_pct'] for l in ls), 1)}% | {br(st.mean(l['economia_ajustada_pct'] for l in ls), 1)}% | {br(st.mean(l['proteina_animal_pct'] for l in ls), 1)}% |")

    md += [
        "",
        "### Variedade",
        "",
        f"- Grupos de alimentos por cesta: média {br(st.mean(l['grupos'] for l in viaveis), 1)} (mín. {min(l['grupos'] for l in viaveis)}, máx. {max(l['grupos'] for l in viaveis)}).",
        f"- Frutas e hortaliças diferentes: média {br(st.mean(l['flv_diferentes'] for l in viaveis), 1)} (mín. {min(l['flv_diferentes'] for l in viaveis)}).",
        f"- Proteína de origem animal: média {br(st.mean(l['proteina_animal_pct'] for l in viaveis), 1)}% da proteína da cesta.",
        "",
        "Dados por cenário: [metricas-cenarios.csv](metricas-cenarios.csv).",
    ]
    (SAIDA / "metricas.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:24]))


if __name__ == "__main__":
    main()
