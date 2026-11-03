# Métricas da EconoMIA

Gerado por `experimentos/metricas.py` em 03/11/2026. 160 cenários: 1, 2, 4 e 6 pessoas × semana e mês × orçamento de R$ 5, 6, 8 e 12 por pessoa por dia × 5 perfis (sem restrição, vegetariano, sem lactose, sem porco, sem glúten). Deslocamento de R$ 10 para um 2º mercado.

⚠️ **Todos os preços são de exemplo**: os valores de economia mostram como a métrica funciona, não a economia real. Recalcular depois da coleta.

## Resumo

| # | Métrica | Resultado |
|---|---------|-----------|
| 1 | Economia média × cesta de referência (estilo DIEESE) | **72,5%** bruta; **57,0%** com a mesma energia |
| 2 | Aderência ao orçamento | **100%** das cestas dentro do orçamento; 68% dos cenários têm solução |
| 3 | Adequação nutricional | **100%** cumprem as 4 metas; 100% respeitam as restrições; 100% têm ≥ 3 frutas/hortaliças |
| 4 | Custo por 1.000 kcal / por g de proteína | **R$ 2,86** / R$ 0,111 (referência: R$ 6,72 / R$ 0,181) |
| 5 | Qualidade dos dados | 100% dos preços com data e fonte; 100% com até 30 dias; cobertura de 98% (produto × mercado); fontes: {'exemplo': 91} |
| 6 | Precisão de preço (gôndola, ±5%) | **pendente**: o grupo preenche `verificacao-gondola.csv` no mercado |
| 7 | Qualidade das respostas (experimento) | A — LLM sem RAG: 59%; B — LLM + RAG: 94%; C — sem LLM: 82%; D — agentes (orquestrador + Mia): 94% |
| 8 | Utilidade percebida | **pendente**: teste com usuários (roteiro em `docs/desenvolvimento/11-metricas.md`) |

## Detalhes

### Cenários sem solução

- R$ 5,00 por pessoa/dia: 40 cenários sem solução. O app informa o mínimo necessário (em média R$ 5,81 por pessoa/dia).
- R$ 6,00 por pessoa/dia: 11 cenários sem solução. O app informa o mínimo necessário (em média R$ 6,20 por pessoa/dia).

### Economia por perfil de restrição

| Perfil | Cenários viáveis | Custo médio por pessoa/dia | Economia bruta | Economia com a mesma energia | Proteína de origem animal |
|---|---|---|---|---|---|
| nenhuma | 23 | R$ 5,70 | 72,8% | 57,6% | 22,0% |
| vegetariano | 17 | R$ 6,08 | 71,0% | 54,8% | 20,8% |
| sem_lactose | 23 | R$ 5,70 | 72,8% | 57,5% | 22,0% |
| sem_porco | 23 | R$ 5,70 | 72,8% | 57,6% | 22,0% |
| sem_gluten | 23 | R$ 5,75 | 72,6% | 57,2% | 21,7% |

### Variedade

- Grupos de alimentos por cesta: média 6,2 (mín. 5, máx. 8).
- Frutas e hortaliças diferentes: média 3,4 (mín. 3).
- Proteína de origem animal: média 21,8% da proteína da cesta.

Dados por cenário: [metricas-cenarios.csv](metricas-cenarios.csv).