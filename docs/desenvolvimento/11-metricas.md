# Tópico 11 — Métricas e testes finais

**Status:** ✅ concluído em 29/10/2026 (métricas 6 e 8 dependem de trabalho de campo do grupo)

## O que foi feito

O cálculo automático das **8 métricas do README** sobre uma grade de **160 cenários**, o relatório gerado e as **correções que as métricas motivaram**.

| Arquivo | Conteúdo |
|---------|----------|
| [src/economia/metricas.py](../../src/economia/metricas.py) | Cesta de referência, cenários e cálculo de cada métrica |
| [data/experimento/cesta_referencia.json](../../data/experimento/cesta_referencia.json) | Cesta de referência no estilo DIEESE (quantidades por pessoa por mês) |
| [experimentos/metricas.py](../../experimentos/metricas.py) | Roda tudo e gera o relatório |
| [docs/semana-7/metricas.md](../semana-7/metricas.md) | **Relatório gerado** |
| [docs/semana-7/metricas-cenarios.csv](../semana-7/metricas-cenarios.csv) | Resultado de cada um dos 160 cenários |
| [docs/semana-7/verificacao-gondola.csv](../semana-7/verificacao-gondola.csv) | Planilha para o grupo conferir 20 preços no mercado (métrica 6) |

```bash
.venv/bin/python experimentos/metricas.py      # ~1 min
```

## Os cenários

1, 2, 4 e 6 pessoas × semana e mês × orçamento de **R$ 5, 6, 8 e 12 por pessoa por dia** × 5 perfis (sem restrição, vegetariano, sem lactose, sem porco, sem glúten), com R$ 10 de deslocamento para um 2º mercado. São 160 combinações.

## A cesta de referência

O README pede comparar com a **cesta básica do DIEESE de Brasília**. O DIEESE publica o **custo** dessa cesta com os preços que ele coleta. Comparar esse custo com o da nossa base seria misturar duas fontes de preço. Por isso montamos a cesta **com as quantidades do DIEESE** (Decreto-Lei nº 399/1938, Região 1, que inclui o DF) e a precificamos **com a mesma base de preços** da EconoMIA, pelo menor preço por kg. Assim a diferença vem só da **escolha dos alimentos**.

Adaptações: farinha de trigo → farinha de mandioca; 90 bananas ≈ 9 kg; café e manteiga ficaram de fora (não estão na base), o que deixa a referência mais barata e torna a comparação **conservadora**. As quantidades precisam ser conferidas na metodologia oficial do DIEESE.

**A referência não tem a mesma energia:** dá cerca de **3.100 kcal por pessoa por dia** (155% da meta de 2.000). Por isso o relatório traz duas economias: a **bruta** e a **com a mesma energia** (a referência reduzida proporcionalmente à meta de kcal).

## Resultados (29/10/2026, preços de exemplo)

> ⚠️ Os preços são de exemplo. Os valores mostram **como as métricas funcionam**; a economia real só pode ser medida depois da coleta.

| # | Métrica | Resultado |
|---|---------|-----------|
| 1 | Economia × cesta de referência | **72,5%** bruta; **57,2%** com a mesma energia |
| 2 | Aderência ao orçamento | **100%** das cestas dentro do orçamento (incluindo o deslocamento); 68% dos cenários têm solução |
| 3 | Adequação nutricional | **100%** cumprem as 4 metas; **100%** respeitam as restrições; **100%** têm ≥ 3 frutas/hortaliças; 5 a 8 grupos de alimentos por cesta |
| 4 | Custo por 1.000 kcal / por g de proteína | **R$ 2,86 / R$ 0,111** (referência: R$ 6,75 / R$ 0,181) |
| 5 | Qualidade dos dados | 100% dos preços com data e fonte; 100% com até 30 dias; cobertura de 98% (produto × mercado); **100% de fonte "exemplo"** |
| 6 | Precisão de preço (±5% na gôndola) | **pendente**: trabalho de campo |
| 7 | Qualidade das respostas | A 59% · B 94% · C 82% · **D 94%** (tópicos 8 e 9) |
| 8 | Utilidade percebida | **pendente**: teste com usuários |

**Cenários sem solução:** todos ficam nas faixas de **R$ 5 e R$ 6 por pessoa por dia**. Para eles, o app informa o mínimo necessário (em média R$ 5,81 e R$ 6,20 por pessoa por dia). Nas faixas de R$ 8 e R$ 12, **todos** os cenários têm solução.

### Por que a economia é tão grande, e por que isso não é mérito só do app

A cesta da EconoMIA é mais barata principalmente porque **troca parte da carne** (6 kg por pessoa por mês na referência) por feijão, ovos, frango e grãos, que dão proteína mais barata, como recomenda o Guia Alimentar. A referência DIEESE também não tem metas de fibra nem de frutas e hortaliças. **Os números são de preço de exemplo e de uma comparação que favorece o app.** Na apresentação, a métrica mais honesta é a **4 (custo por 1.000 kcal e por grama de proteína)**, que compara as cestas na mesma unidade.

## O que as métricas revelaram, e o que foi corrigido

A primeira rodada das métricas encontrou **três problemas reais**. Para isso servem as métricas:

| # | Problema encontrado | Causa | Correção |
|---|---------------------|-------|----------|
| 1 | **Aderência ao orçamento de 87%**, não 100% | Na opção de dois mercados, a comida cabia no orçamento, mas comida + deslocamento passava dele | O deslocamento agora sai do orçamento (`planejador.py`) |
| 2 | **0% de proteína animal** em todas as cestas, e os 5 perfis davam a mesma cesta | Feijão e grãos cumprem energia, proteína e fibra mais barato. A cesta ficava sem as principais fontes de **vitamina B12 e cálcio**, que o modelo não mede: exatamente o risco de "otimização enganosa" do README | Nova meta: **≥ 20% da proteína de origem animal** (carnes, ovos, peixe, leite ou queijo), quando as restrições permitem (`metas.py`, `otimizador.py`) |
| 3 | "Mínimo necessário" **menor** que o orçamento informado | Era calculado juntando os 3 mercados, sem deslocamento | Agora é o menor custo entre um mercado só e dois mercados mais o deslocamento |

**Efeito das correções:** aderência de 87% → **100%**; proteína animal de 0% → **22%**; grupos de alimentos por cesta de 4,9 → **6,2**. Em troca, a cesta ficou cerca de **R$ 0,57 mais cara por pessoa por dia** (R$ 5,13 → R$ 5,70) e menos cenários de orçamento apertado têm solução (90% → 68%). É o preço de não economizar à custa da qualidade, a métrica principal do projeto.

Como os valores das cestas mudaram, os exemplos dos docs 02 a 05 e o gabarito do experimento foram atualizados.

## O que falta: trabalho de campo do grupo

### Métrica 6: precisão de preço

1. Abrir [verificacao-gondola.csv](../semana-7/verificacao-gondola.csv): 20 produtos já sorteados, com o preço que o app mostra.
2. Ir ao mercado e anotar o preço na gôndola, a data e quem conferiu.
3. Rodar `experimentos/metricas.py`: a métrica 6 é calculada sozinha (% dentro de ±5%).

> Só faz sentido **depois da coleta real**: com os preços de exemplo, a precisão seria perto de 0%.

### Métrica 8: utilidade percebida (roteiro de teste com usuários)

**Quem:** 5 a 8 pessoas fora do grupo, de rendas e tamanhos de família diferentes, com pelo menos uma pessoa pouco familiarizada com tecnologia.

**Tarefas** (a pessoa usa o site sozinha, e o grupo só observa e anota):

1. "Monte uma cesta para a sua casa com o dinheiro que você costuma gastar no mês."
2. "Descubra se compensa ir a dois mercados."
3. "Pergunte à EconoMIA se uma promoção que você viu vale a pena."
4. "Peça um cardápio com a sua cesta."

**Perguntas no fim** (de 1 a 5):

1. As recomendações foram úteis para a sua realidade?
2. Você entendeu por que a cesta foi montada assim?
3. Você confiaria nos preços mostrados?
4. Você usaria o app nas suas compras?
5. (aberta) O que faltou ou atrapalhou?

**Métrica:** % de pessoas que deram 4 ou 5 na pergunta 1 e concluíram a tarefa 1 sozinhas.

> **Privacidade:** não anotar nome nem renda exata das pessoas, só faixas (LGPD).

## Testes automatizados (resumo final)

```bash
pytest
```

**127 testes passando** em 29/10/2026, cobrindo todos os tópicos:

| Arquivo | Testes | O que cobre |
|---------|--------|-------------|
| test_dados.py | 6 | integridade das bases |
| test_otimizador.py | 16 | metas, orçamento, restrições, variedade, proteína animal |
| test_planejador.py | 10 | 1 × 2 mercados, deslocamento no orçamento, mínimo necessário, explicação |
| test_api.py | 18 | endpoints, validação, chat, cardápio, NFC-e |
| test_rag.py | 13 | busca na base, limiar de "não sei" |
| test_assistente.py | 20 | chat, ferramentas, modo sem LLM, LLM falso |
| test_avaliacao.py | 6 | critérios do experimento |
| test_agentes.py | 23 | orquestrador, Mia, cardápio |
| test_nfce.py | 15 | QR code, segurança (SSRF), leitura da nota, contribuição |

Nenhum teste chama um LLM de verdade nem a internet: são rápidos (~8 s), gratuitos e sempre dão o mesmo resultado.
