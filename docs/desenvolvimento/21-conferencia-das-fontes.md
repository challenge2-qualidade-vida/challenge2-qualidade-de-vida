# Tópico 21 — Conferência dos dados com as fontes oficiais

**Status:** ✅ concluído em 03/11/2026

Vários arquivos diziam "conferir no original". Esta conferência foi feita com os documentos oficiais, e o que não batia foi corrigido.

## O que foi conferido

| Dado | Como | Resultado |
|------|------|-----------|
| 28 alimentos × Tabela TACO, 4ª ed. | Comparação com a linha da tabela original (kcal, proteína, fibra) | **27 iguais.** O leite não tem valor na TACO |
| Cesta de referência × metodologia do DIEESE | Tabela do Decreto-Lei nº 399/1938, Região 1 (inclui o DF) | Quantidades corretas. Óleo ajustado de 690 g para os **750 g** da tabela |
| Resumos do Guia Alimentar × PDF de 2014 | Busca de cada afirmação no texto original | Regra de ouro, dez passos e grupos conferem. **4 frases corrigidas** (abaixo) |

## O que foi corrigido

| Problema | Correção |
|----------|----------|
| **Leite atribuído à TACO**, que traz o aviso de que as análises estão sendo reavaliadas | O alimento declara a própria fonte (`fonte_nutricao`), e o RAG deixa de citá-lo como TACO |
| "Feiras e sacolões costumam ter hortaliças mais baratas" | O Guia não diz isso. Agora: preferir os da estação e cultivados localmente |
| "Frutas da estação costumam ser mais baratas e saborosas" | Idem |
| "O ovo é uma das fontes de proteína mais baratas" | O Guia diz que são acessíveis e relativamente baratos. Texto ajustado também na dica do app |
| "Comprar com fome aumenta o gasto" | Sem fonte: removido |
| Link do Guia Alimentar exigia login em gov.br | Trocado pelo da Biblioteca Virtual em Saúde |
| O app mostrava "revisar antes da entrega" como fonte das receitas | Agora: "Texto do grupo, sem fonte externa" |

## Teste com preços reais

Os preços de Brasília ainda dependem da coleta do grupo. Para não esperar, testamos a pergunta que a banca fará: **as conclusões valem com preços reais?**

O [Procon de Anápolis](https://www.anapolis.go.gov.br/wp-content/uploads/2026/03/plan-e-rel-cesta-basica-26..pdf) publicou preços de 6 supermercados, na mesma Região 1 da cesta DIEESE. O script troca os preços de exemplo pelas médias reais nos 12 alimentos pesquisados e refaz os 160 cenários.

**Resultado:** [sensibilidade-precos.md](../semana-7/sensibilidade-precos.md).

- Aderência ao orçamento, metas e restrições **continuam em 100%**.
- Os cenários com solução sobem de 109 para **144** de 160, porque os preços de exemplo estavam altos em arroz (+91%), macarrão (+69%) e açúcar (+58%).
- O custo por 1.000 kcal fica em **R$ 2,41**, contra R$ 6,38 da referência.

**Limites:** Anápolis não é Brasília, e 16 alimentos seguem com preço de exemplo, inclusive várias hortaliças. Esses preços **não aparecem no app**. O teste reforça o método, mas não substitui a coleta nem permite prometer um percentual de economia.

## Referência real

O DIEESE/Conab publicou **R$ 773,78** para a cesta de Brasília em setembro de 2026. Nossa referência, sem café e manteiga e com farinha de mandioca, dá R$ 629,69 com preços de exemplo e R$ 597,75 com os preços do Procon. A ordem de grandeza é coerente, e a diferença é esperada por causa dos itens que ficaram de fora.

## O que continua pendente

- **Preços de Brasília:** a coleta em campo.
- **Leite:** conferir o valor na Tabela TBCA (USP). A página exige busca interativa, então usamos faixas de rótulos e de tabelas secundárias.
- **DF na PNAD:** o informativo do IBGE traz só as grandes regiões. O número do DF veio de reportagem, e as reportagens divergem sobre 2023.
- **Receitas:** revisão do grupo.
