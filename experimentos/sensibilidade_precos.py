"""Tópico 21: as conclusões sobrevivem a preços reais?

Troca os preços de exemplo pelas médias reais do Procon Anápolis nos alimentos
pesquisados, mantendo a diferença entre mercados e entre embalagens, e recalcula
os 160 cenários. Os demais alimentos continuam com preço de exemplo.

Rodar:  .venv/bin/python experimentos/sensibilidade_precos.py   (~2 min)
Gera:   docs/semana-7/sensibilidade-precos.md
"""

import json
import statistics as st
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from economia.dados import Base, carregar, preco_por_kg  # noqa: E402
from economia.metricas import avaliar_cenarios, cesta_referencia  # noqa: E402

ARQ_REAIS = RAIZ / "data" / "experimento" / "precos_procon_anapolis.json"
SAIDA = RAIZ / "docs" / "semana-7" / "sensibilidade-precos.md"
ARQ_REFERENCIA = RAIZ / "data" / "experimento" / "cesta_referencia.json"


def media_kg(base: Base, alimento: str) -> float:
    return st.mean(preco_por_kg(base.produtos[p.produto], p) for p in base.precos if base.produtos[p.produto].alimento == alimento)


def com_precos_reais(base: Base, itens: list[dict]) -> Base:
    reais_kg = {i["alimento"]: i["preco_medio"] / i["gramas"] * 1000 for i in itens}
    medias = {a: media_kg(base, a) for a in reais_kg}
    novos = []
    for p in base.precos:
        alimento = base.produtos[p.produto].alimento
        if alimento in reais_kg:
            p = replace(p, preco=round(p.preco * reais_kg[alimento] / medias[alimento], 2), fonte="procon_anapolis")
        novos.append(p)
    return replace(base, precos=novos)


def resumo(linhas: list[dict]) -> dict:
    v = [l for l in linhas if l["viavel"]]
    return {
        "viaveis": len(v), "total": len(linhas),
        "dentro": sum(l["dentro_orcamento"] for l in v) / len(v),
        "metas": sum(l["cumpre_metas"] for l in v) / len(v),
        "restricoes": sum(l["respeita_restricoes"] for l in v) / len(v),
        "economia": st.mean(l["economia_pct"] for l in v),
        "economia_aj": st.mean(l["economia_ajustada_pct"] for l in v),
        "kcal": st.mean(l["custo_1000kcal"] for l in v),
        "ref_kcal": st.mean(l["ref_custo_1000kcal"] for l in v),
        "prot": st.mean(l["custo_g_proteina"] for l in v),
        "ref_prot": st.mean(l["ref_custo_g_proteina"] for l in v),
        "dia": st.mean(l["custo"] / l["pessoas"] / (7 if l["periodo"] == "semana" else 30) for l in v),
        "animal": st.mean(l["proteina_animal_pct"] for l in v),
    }


def br(v, casas=2):
    return f"{v:.{casas}f}".replace(".", ",")


def main():
    dados = json.loads(ARQ_REAIS.read_text(encoding="utf-8"))
    base = carregar()
    real = com_precos_reais(base, dados["itens"])
    a, b = resumo(avaliar_cenarios(base)), resumo(avaliar_cenarios(real))
    ref_a, ref_b = cesta_referencia(base, 1, 30), cesta_referencia(real, 1, 30)
    publicado = json.loads(ARQ_REFERENCIA.read_text(encoding="utf-8"))["custo_publicado"]

    linhas_itens = []
    for i in dados["itens"]:
        ex, re_ = media_kg(base, i["alimento"]), i["preco_medio"] / i["gramas"] * 1000
        linhas_itens.append(f"| {i['produto_pesquisado']} | R$ {br(ex)} | R$ {br(re_)} | {(ex / re_ - 1) * 100:+.0f}% | R$ {br(i['menor'])} a R$ {br(i['maior'])} ({(i['maior'] / i['menor'] - 1) * 100:.0f}%) |".replace(".", ",", 0))

    def linha(nome, f):
        return f"| {nome} | {f(a)} | {f(b)} |"

    md = [
        "# Sensibilidade: as conclusões sobrevivem a preços reais?",
        "",
        f"Gerado por `experimentos/sensibilidade_precos.py` em {date.today().strftime('%d/%m/%Y')}.",
        "",
        f"**Fonte dos preços reais:** {dados['fonte']}. Anápolis fica na mesma Região 1 da cesta DIEESE que o DF, mas **estes não são preços de Brasília**. "
        f"Só {len(dados['itens'])} dos {len(base.alimentos)} alimentos foram pesquisados; os demais seguem com preço de exemplo. Este teste não substitui a coleta do grupo.",
        "",
        "## Resultado nos 160 cenários",
        "",
        "| Medida | Preços de exemplo | Com preços reais do Procon |",
        "|--------|-------------------|----------------------------|",
        linha("Cenários com solução", lambda r: f"{r['viaveis']} de {r['total']}"),
        linha("Dentro do orçamento", lambda r: f"{r['dentro']:.0%}"),
        linha("Cumprem as metas", lambda r: f"{r['metas']:.0%}"),
        linha("Respeitam as restrições", lambda r: f"{r['restricoes']:.0%}"),
        linha("Custo médio por pessoa/dia", lambda r: f"R$ {br(r['dia'])}"),
        linha("Custo por 1.000 kcal (cesta)", lambda r: f"R$ {br(r['kcal'])}"),
        linha("Custo por 1.000 kcal (referência)", lambda r: f"R$ {br(r['ref_kcal'])}"),
        linha("Custo por g de proteína (cesta)", lambda r: f"R$ {br(r['prot'], 3)}"),
        linha("Custo por g de proteína (referência)", lambda r: f"R$ {br(r['ref_prot'], 3)}"),
        linha("Economia bruta × referência", lambda r: f"{br(r['economia'], 1)}%"),
        linha("Economia com a mesma energia", lambda r: f"{br(r['economia_aj'], 1)}%"),
        linha("Proteína de origem animal", lambda r: f"{br(r['animal'], 1)}%"),
        "",
        "## A referência comparada ao custo publicado",
        "",
        "| Cesta para 1 adulto, 1 mês | Custo |",
        "|---------------------------|-------|",
        f"| {publicado['capital']}, DIEESE/Conab, {publicado['mes']} (13 itens, preços reais) | **R$ {br(publicado['valor'])}** |",
        f"| Anápolis, Procon, março de 2026 (média dos supermercados) | R$ {br(dados['cesta_individual_media'])} |",
        f"| Nossa referência com preços de exemplo (sem café e manteiga; farinha de mandioca no lugar da de trigo) | R$ {br(ref_a.custo)} |",
        f"| Nossa referência com preços do Procon nos itens pesquisados | R$ {br(ref_b.custo)} |",
        "",
        "## Preços de exemplo × preços reais (por kg)",
        "",
        "| Produto | Exemplo (média) | Real (média) | Diferença | Variação entre supermercados |",
        "|---------|-----------------|--------------|-----------|------------------------------|",
        *linhas_itens,
    ]
    SAIDA.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
