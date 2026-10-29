# Tópico 2 — Otimizador da cesta

**Status:** ✅ concluído em 29/10/2026

## O que foi feito

O coração do app: dado o orçamento, o número de pessoas, o período e as restrições, o otimizador escolhe **quantas embalagens de cada produto comprar** para ter a **cesta mais barata que ainda cumpre as metas nutricionais e de variedade**.

| Arquivo | Conteúdo |
|---------|----------|
| [src/economia/metas.py](../../src/economia/metas.py) | Metas nutricionais, limites de variedade e restrições alimentares |
| [src/economia/otimizador.py](../../src/economia/otimizador.py) | `Pedido`, `Cesta` e a função `montar_cesta()` |
| [tests/test_otimizador.py](../../tests/test_otimizador.py) | 14 testes |

## Por que um otimizador, e não o LLM?

Um LLM pode inventar preço, errar soma e "esquecer" uma meta nutricional. O otimizador é **determinístico** (a mesma entrada sempre dá a mesma cesta), **auditável** (cada restrição está no código) e **garante** que todas as metas são cumpridas ou avisa que não dá. O LLM entra depois (tópico 7) só para conversar e explicar.

## Como funciona

É um problema de **programação linear inteira**, resolvido com a função `milp` do SciPy (gratuito, usa o solver HiGHS).

**Variável:** `x[j]` = número de embalagens da oferta `j` (um produto em um mercado). É inteiro, porque não dá para comprar meia embalagem.

**Objetivo:** minimizar `Σ preço[j] × x[j]`.

**Restrições:**

| Restrição | Regra | Fonte |
|-----------|-------|-------|
| Energia | ≥ 2.000 kcal × pessoas × dias | VD da ANVISA, IN nº 75/2020 |
| Proteína | ≥ 50 g × pessoas × dias | VD da ANVISA, IN nº 75/2020 |
| Fibra | ≥ 25 g × pessoas × dias | VD da ANVISA, IN nº 75/2020 |
| Frutas, legumes e verduras | ≥ 400 g × pessoas × dias | OMS |
| Variedade (energia) | nenhum alimento passa de 25% das kcal | parâmetro do grupo |
| Variedade (FLV) | nenhuma fruta ou hortaliça passa de 40% da meta de FLV, o que obriga pelo menos 3 tipos | parâmetro do grupo |
| Proteína de origem animal | ≥ 20% da proteína vem de carnes, ovos, peixe, leite ou queijo (se as restrições permitirem algum) | parâmetro do grupo, **acrescentado no tópico 11** |
| Açúcar | ≤ 10% das kcal | OMS (açúcares livres) |
| Óleos | ≤ 10% das kcal | parâmetro do grupo (o Guia Alimentar pede "pequenas quantidades") |
| Restrições alimentares | alimentos com a tag da restrição ficam fora | escolha do usuário |
| Orçamento | `Σ preço × x ≤ orçamento` | informado pelo usuário |

Os limites de variedade nunca ficam abaixo de uma embalagem. Sem essa regra, uma cesta para 1 pessoa por 1 semana seria impossível: 25% da energia da semana é menos do que um pacote de arroz de 1 kg.

Os números ficam todos em `metas.py`, num lugar só, para o grupo ajustar sem mexer no algoritmo.

### Passo a passo dentro de `montar_cesta()`

1. Calcula as metas totais (`metas_totais`: meta diária × pessoas × dias).
2. Monta a lista de ofertas: os preços dos mercados pedidos, sem os alimentos proibidos pelas restrições.
3. Para cada oferta, calcula kcal, proteína, fibra e gramas de FLV da embalagem inteira.
4. Escreve cada restrição como uma linha de uma matriz (`LinearConstraint`).
5. Chama `milp(...)` com variáveis inteiras entre 0 e 1000 e um limite de 20 s.
6. Se não houver solução (por exemplo, orçamento baixo demais), devolve `None`.
7. Se houver, devolve uma `Cesta` com os itens (produto, mercado, quantidade, preço, preço por kg, data e fonte do preço), o custo total, o custo por mercado, o que foi obtido e as metas.

## Exemplo

```python
from economia.dados import carregar
from economia.otimizador import Pedido, montar_cesta

base = carregar()
cesta = montar_cesta(base, Pedido(orcamento=800, pessoas=4, periodo="mes"), ("C",))
cesta.custo_total            # 708.31
cesta.custo_por_1000_kcal    # ≈ 2,95
```

Com os preços de exemplo, a cesta de 4 pessoas por um mês custa **R$ 739,49 no Mercado A, R$ 711,42 no B e R$ 708,31 no C** (antes da meta de proteína animal do tópico 11, eram R$ 664,16, R$ 639,15 e R$ 631,72). Cada solução leva menos de 0,1 s.

## Limitações conhecidas

- **Todas as pessoas contam como adultos** (2.000 kcal). Crianças e idosos têm necessidades diferentes. A explicação do app deixa isso claro, e o tema de "dieta individual" está fora do MVP.
- **Só três nutrientes** (energia, proteína, fibra), mais frutas e hortaliças. Ferro, cálcio e vitaminas podem entrar depois, já que a TACO tem esses dados.
- ~~**O menor custo pode ser "monótono"**~~ **Resolvido no tópico 11:** as métricas mostraram que **100% das cestas saíam sem nenhuma proteína animal**, porque feijão e grãos cumprem energia, proteína e fibra mais barato. Isso deixa a cesta sem as principais fontes de vitamina B12 e cálcio, que o modelo não mede. Entrou a meta de ≥ 20% de proteína de origem animal, e a cesta ficou cerca de R$ 0,50 mais cara por pessoa por dia.
- **Os valores nutricionais são do alimento cru** (TACO). É o certo para uma lista de compras, mas não reflete perdas no preparo.

## Testes

```bash
pytest tests/test_otimizador.py -v
```

Os testes conferem que a cesta: cumpre todas as metas; respeita o orçamento; não existe quando o orçamento é impossível (R$ 50 para 4 pessoas); tem custo igual à soma dos itens; respeita **cada uma** das 6 restrições; tem pelo menos 3 frutas ou hortaliças; é viável para 1 pessoa por 1 semana; compra só nos mercados pedidos; e que uma restrição desconhecida gera erro.

**Resultado em 29/10/2026:** 20 testes passando no projeto (6 de dados + 14 do otimizador).
