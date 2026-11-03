# Sensibilidade: as conclusões sobrevivem a preços reais?

Gerado por `experimentos/sensibilidade_precos.py` em 03/11/2026.

**Fonte dos preços reais:** Procon Anápolis, Pesquisa Comparativa de Preços, itens da cesta básica, coleta de 2 a 6 de março de 2026. Anápolis fica na mesma Região 1 da cesta DIEESE que o DF, mas **estes não são preços de Brasília**. Só 12 dos 28 alimentos foram pesquisados; os demais seguem com preço de exemplo. Este teste não substitui a coleta do grupo.

## Resultado nos 160 cenários

| Medida | Preços de exemplo | Com preços reais do Procon |
|--------|-------------------|----------------------------|
| Cenários com solução | 109 de 160 | 144 de 160 |
| Dentro do orçamento | 100% | 100% |
| Cumprem as metas | 100% | 100% |
| Respeitam as restrições | 100% | 100% |
| Custo médio por pessoa/dia | R$ 5,77 | R$ 4,89 |
| Custo por 1.000 kcal (cesta) | R$ 2,86 | R$ 2,41 |
| Custo por 1.000 kcal (referência) | R$ 6,72 | R$ 6,38 |
| Custo por g de proteína (cesta) | R$ 0,111 | R$ 0,093 |
| Custo por g de proteína (referência) | R$ 0,181 | R$ 0,172 |
| Economia bruta × referência | 72,5% | 75,4% |
| Economia com a mesma energia | 57,0% | 61,6% |
| Proteína de origem animal | 21,8% | 21,1% |

## A referência comparada ao custo publicado

| Cesta para 1 adulto, 1 mês | Custo |
|---------------------------|-------|
| Brasília, DIEESE/Conab, setembro de 2026 (13 itens, preços reais) | **R$ 773,78** |
| Anápolis, Procon, março de 2026 (média dos supermercados) | R$ 657,24 |
| Nossa referência com preços de exemplo (sem café e manteiga; farinha de mandioca no lugar da de trigo) | R$ 629,69 |
| Nossa referência com preços do Procon nos itens pesquisados | R$ 597,75 |

## Preços de exemplo × preços reais (por kg)

| Produto | Exemplo (média) | Real (média) | Diferença | Variação entre supermercados |
|---------|-----------------|--------------|-----------|------------------------------|
| Arroz tipo 1, 5 kg | R$ 6,02 | R$ 3,15 | +91% | R$ 12,98 a R$ 16,99 (31%) |
| Feijão carioquinha, 1 kg | R$ 7,99 | R$ 7,66 | +4% | R$ 6,79 a R$ 7,99 (18%) |
| Açúcar cristal, 5 kg | R$ 4,70 | R$ 2,98 | +58% | R$ 12,59 a R$ 18,39 (46%) |
| Batata inglesa, kg | R$ 6,82 | R$ 5,52 | +24% | R$ 4,49 a R$ 6,69 (49%) |
| Banana prata, kg | R$ 6,82 | R$ 5,86 | +16% | R$ 3,99 a R$ 7,69 (93%) |
| Tomate, kg | R$ 8,82 | R$ 8,92 | -1% | R$ 7,59 a R$ 10,99 (45%) |
| Ovos brancos, dúzia (600 g, como na base) | R$ 17,18 | R$ 16,87 | +2% | R$ 8,99 a R$ 10,99 (22%) |
| Óleo de soja, 900 mL (828 g, como na base) | R$ 9,65 | R$ 8,83 | +9% | R$ 6,79 a R$ 8,49 (25%) |
| Leite integral, 1 L | R$ 5,52 | R$ 4,68 | +18% | R$ 3,99 a R$ 5,99 (50%) |
| Macarrão espaguete, 500 g | R$ 8,58 | R$ 5,08 | +69% | R$ 2,19 a R$ 3,29 (50%) |
| Pão francês, kg | R$ 16,46 | R$ 17,81 | -8% | R$ 12,99 a R$ 20,99 (62%) |
| Carne de 1ª, coxão mole, kg (aproximação do patinho) | R$ 44,90 | R$ 43,96 | +2% | R$ 37,90 a R$ 47,90 (26%) |
