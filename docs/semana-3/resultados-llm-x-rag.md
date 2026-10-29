# Resultados — experimento LLM × LLM + RAG

Gerado automaticamente por `experimentos/llm_x_rag.py` em 29/10/2026. Modelo: **ollama/qwen2.5:7b** (gratuito). 17 perguntas por abordagem.

## Resumo

| Critério | A — LLM sem RAG | B — LLM + RAG | C — sem LLM |
|---|---|---|---|
| Correção | 59% (n=17) | 94% (n=17) | 76% (n=17) |
| Fundamentação (cita a base) | 0% (n=10) | 80% (n=10) | 90% (n=10) |
| Tratamento de incerteza | 75% (n=4) | 75% (n=4) | 50% (n=4) |
| Usou a ferramenta certa | 100% (n=3) | 100% (n=3) | 100% (n=3) |
| Latência média | 10.4 s | 16.4 s | 0.0 s |
| Tokens por pergunta (entrada + saída) | 1312 | 1742 | 0 |
| Custo em R$ | R$ 0,00 | R$ 0,00 | R$ 0,00 |

## Correção por categoria

| Categoria | A — LLM sem RAG | B — LLM + RAG | C — sem LLM |
|---|---|---|---|
| conhecimento | 40% | 100% | 80% |
| ferramenta | 100% | 100% | 100% |
| ausente | 50% | 50% | 50% |
| fora_do_tema | 100% | 100% | 100% |
| saude | 100% | 100% | 0% |

## Respostas

### c01 — Qual é a regra de ouro do Guia Alimentar?

- **A — LLM sem RAG** ❌ (6.6 s): A regra de ouro do Guia Alimentar é priorizar alimentos minimamente processados, ricos em nutrientes e variados. Isso garante uma alimentação saudável e equilibrada. [1]
- **B — LLM + RAG** ✅ (21.4 s): A regra de ouro do Guia Alimentar é preferir alimentos in natura ou minimamente processados e preparações culinárias feitas com eles, em vez de alimentos ultraprocessados. Essa regra promove uma alimentação nutricionalmente equilibrada, saborosa, culturalmente apropriada e mais justa e sustentável. [1]
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] Guia Alimentar — princípios e regra de ouro — Regra de ouro A regra de ouro do Guia Alimentar é preferir sempre alimentos in natura ou minimamente processados e preparações culinárias feitas com eles, em vez de alimentos ultraprocessados. Uma alimentação assim é nutricionalmente equilibrada, saborosa, culturalmente apropriada e promove um sistema alimen

### c02 — O que são alimentos ultraprocessados? Dê exemplos.

- **A — LLM sem RAG** ✅ (16.1 s): Alimentos ultraprocessados são aqueles com muitos ingredientes químicos e pouca ou nenhuma forma natural de nutrientes. Exemplos incluem refrigerantes, biscoitos industrializados, embutidos em conserva e alimentos em pacotinhos prontos para o microondas. Esses alimentos geralmente são altos em açúcar, sal e gorduras saturadas [1].   [1] Fonte: Instituto Brasileiro de Análise de Sistemas (IBAS) - G
- **B — LLM + RAG** ✅ (18.8 s): Alimentos ultraprocessados são formulações industriais feitas principalmente de substâncias extraídas ou sintetizadas, com aditivos como açúcar, sal e gorduras. Exemplos incluem refrigerantes, biscoitos recheados, macarrão instantâneo e embutidos [1]. É recomendado limitar o consumo desses alimentos para uma alimentação mais saudável.  Se tiver alguma dúvida sobre orçamento ou compras de alimentos
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] Guia Alimentar — princípios e regra de ouro — Alimentos ultraprocessados Ultraprocessados são formulações industriais feitas principalmente de substâncias extraídas de alimentos ou sintetizadas, com aditivos: refrigerantes, salgadinhos de pacote, biscoitos recheados, macarrão instantâneo, embutidos e refeições prontas congeladas. Tendem a ter muito açúc

### c03 — Como o Guia Alimentar orienta o uso de óleo, sal e açúcar?

- **A — LLM sem RAG** ✅ (8.7 s): O Guia Alimentar para a População Brasileira recomenda controlar o consumo de óleos vegetais, sal e açúcares adicionados. É importante usar esses ingredientes com moderação para manter uma alimentação saudável. Para mais detalhes, posso buscar informações específicas sobre isso [1].
- **B — LLM + RAG** ✅ (18.3 s): O Guia Alimentar orienta que óleos, gorduras, sal e açúcar devem ser usados em pequenas quantidades para temperar e cozinhar alimentos in natura. Eles contribuem para a saborização sem desbalancear a alimentação. Alimentos processados com esses ingredientes devem ser consumidos em menor quantidade, como parte de refeições baseadas em alimentos in natura e minimamente processados [1].
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] Guia Alimentar — princípios e regra de ouro — Óleos, gorduras, sal e açúcar Óleos, gorduras, sal e açúcar são ingredientes culinários usados para temperar e cozinhar. Devem ser usados em pequenas quantidades. Usados com moderação em preparações à base de alimentos in natura, contribuem para uma alimentação saborosa sem deixá-la desbalanceada.  [2] Guia 

### c04 — Por que arroz com feijão é uma boa combinação?

- **A — LLM sem RAG** ❌ (7.2 s): Arroz e feijão formam uma boa combinação porque juntos fornecem todos os aminoácidos essenciais, tornando a proteína mais completa. Além disso, são ricos em carboidratos para energia e fibras. [1]
- **B — LLM + RAG** ✅ (17.2 s): Arroz com feijão é uma boa combinação porque as proteínas dos dois se complementam, fornecendo uma proteína de boa qualidade e fibra a baixo custo [1]. Além disso, essa combinação é versátil: sobras podem ser aproveitadas para fazer pratos como tutu ou bolinho de arroz [2], e há receitas simples completas, como o arroz com feijão e ovo [3].
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] Guia Alimentar — grupos de alimentos e refeições — Arroz com feijão A combinação de arroz com feijão é a base da alimentação brasileira. As proteínas do arroz e do feijão se complementam, e a mistura fornece energia, proteína de boa qualidade e fibra a baixo custo. A proporção tradicional de duas partes de arroz para uma de feijão é uma boa referência. 

### c05 — O que fazer com banana muito madura?

- **A — LLM sem RAG** ❌ (6.2 s): Você pode fazer purê de banana para pratos doces ou salgados, biscoitos, smoothies ou até mesmo adicionar ao pão caseiro. Também serve bem cozida como acompanhamento para pratos principais. [1]
- **B — LLM + RAG** ✅ (9.0 s): Aproveite a banana madura para fazer vitamina com leite e aveia, mingau de aveia com banana ou bolo de banana. Também pode ser congelada descascada para usar em outros pratos depois. [1]
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] Aproveitamento de alimentos e receitas simples — Banana madura Banana muito madura não precisa ir para o lixo: serve para vitamina com leite e aveia, mingau de aveia com banana, bolo de banana ou pode ser congelada descascada para usar depois.  [2] TACO — Banana prata Banana prata: por 100 g tem 98 kcal, 1.3 g de proteína e 2 g de fibra. Grupo: frutas, 

### c06 — Como saber se a embalagem maior compensa?

- **A — LLM sem RAG** ✅ (6.1 s): Para saber se a embalagem maior compensa, precisamos comparar o preço por kilo dessa embalagem com os preços normais das embalagens menores. Vamos verificar juntos! Qual produto você está interessado?
- **B — LLM + RAG** ✅ (11.5 s): Para saber se a embalagem maior compensa, calcule o preço por quilo dividindo o preço pela quantidade em gramas e multiplicando por 1000. Compare com os preços de embalagens menores. Se o alimento for consumido antes de estragar, a maior embalagem pode ser mais econômica.
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] Compras e economia — critérios da EconoMIA — Preço por quilo ou por litro Para comparar embalagens diferentes, use o preço por quilo (ou por litro): divida o preço pelo peso da embalagem em gramas e multiplique por 1000. Um pacote de arroz de 5 kg a R$ 27,90 custa R$ 5,58 por kg; um de 1 kg a R$ 6,49 custa R$ 6,49 por kg. A embalagem maior só compensa s

### c07 — Quando vale a pena fazer compras em dois mercados?

- **A — LLM sem RAG** ✅ (7.4 s): Para saber quando vale a pena comprar em dois mercados, precisamos saber o orçamento que você tem e o custo do deslocamento para ir ao segundo mercado. Podemos montar uma cesta de compras e comparar os custos! Quanto pessoas estão na sua casa?
- **B — LLM + RAG** ✅ (16.1 s): Compras em dois mercados só compensam se a diferença de preço for maior que o custo do deslocamento até o segundo mercado. A EconoMIA calcula isso automaticamente para você.  Para saber se vale a pena, use a ferramenta montar_cesta informando seu orçamento e número de pessoas. Ela comparará os preços em um ou dois mercados e mostra a economia real.
- **C — sem LLM** ❌ (0.0 s): Não há preços de 'quando fazer compras em dois mercados' na base para comparar.

### c08 — Quanta proteína tem 100 g de lentilha crua, segundo a Tabela TACO?

- **A — LLM sem RAG** ❌ (14.5 s): Sinto muito, mas a EconoMIA não possui informações sobre a Tabela TACO diretamente. Você pode encontrar essa informação em sites oficiais de nutrição ou na própria Tabela TÁC (Tabela Alimentar do Conjunto de Referências Alimentares para Populações - TAC). Uma lentilha crua contém aproximadamente 9 a 10 gramas de proteína por 100g, mas consulte uma fonte confiável para dados precisos.
- **B — LLM + RAG** ✅ (11.0 s): De acordo com a Tabela TACO [1], 100 g de lentilha crua contém cerca de 23.2 g de proteína.  Se tiver mais alguma dúvida sobre alimentação, estou aqui para ajudar!
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] TACO — Lentilha (crua) Lentilha (crua): por 100 g tem 339 kcal, 23.2 g de proteína e 16.9 g de fibra. Grupo: feijões.  [2] TACO — Mandioca (crua) Mandioca (crua): por 100 g tem 151 kcal, 1.1 g de proteína e 1.9 g de fibra. Grupo: raízes e tubérculos.

### c09 — Quantas calorias tem 100 g de arroz branco cru, segundo a Tabela TACO?

- **A — LLM sem RAG** ❌ (5.7 s): Só consigo ajudar com compras, preços e alimentação. Para informações nutricionais, recomendo consultar a Tabela TACO diretamente ou uma plataforma especializada em dados nutricionais.
- **B — LLM + RAG** ✅ (10.1 s): De acordo com a Tabela TACO [1], 100 g de arroz branco cru tem aproximadamente 358 calorias.  Se tiver mais alguma dúvida sobre alimentação, aproveitamento ou orçamento, estou aqui para ajudar!
- **C — sem LLM** ✅ (0.0 s): Encontrei isto na base de conhecimento:  [1] TACO — Arroz branco tipo 1 (cru) Arroz branco tipo 1 (cru): por 100 g tem 358 kcal, 7.2 g de proteína e 1.6 g de fibra. Grupo: cereais e pães.  [2] Aproveitamento de alimentos e receitas simples — Receita: arroz, feijão e ovo Refeição completa e barata: arroz branco, feijão carioca temperado com cebola e um ovo cozido ou mexido por pessoa, com salada de

### c10 — O feijão carioca ficou caro. Por qual alimento posso trocar?

- **A — LLM sem RAG** ❌ (9.6 s): Vamos avaliar algumas opções de leguminosas mais baratas que podem substituir o feijão carioca. Podemos usar a ferramenta `buscar_conhecimento` para isso.  Qual é o seu orçamento mensal para alimentação e quantas pessoas estão na sua casa? Isso nos ajudará a montar uma cesta de alimentos mais econômica.
- **B — LLM + RAG** ✅ (13.5 s): Pode trocar o feijão carioca por feijão preto ou lentilha, que são alternativas com valor nutricional semelhante [3]. Ambos pertencem ao mesmo grupo de feijões e são boas opções para manter a qualidade da refeição.
- **C — sem LLM** ❌ (0.0 s): Encontrei isto na base de conhecimento:  [1] TACO — Feijão carioca (cru) Feijão carioca (cru): por 100 g tem 329 kcal, 20 g de proteína e 18.4 g de fibra. Grupo: feijões.  [2] Aproveitamento de alimentos e receitas simples — Receita: arroz, feijão e ovo Refeição completa e barata: arroz branco, feijão carioca temperado com cebola e um ovo cozido ou mexido por pessoa, com salada de repolho e tomate

### f01 — Arroz de 5 kg por R$ 24,90 é uma boa promoção?

- **A — LLM sem RAG** ✅ (16.8 s): Sim, a promoção vale a pena. O arroz custa R$ 4,98 por kg, enquanto o melhor preço normal encontrado foi R$ 5,30 por kg. Lembre-se de que só é uma economia se você precisar do produto e conseguir consumi-lo antes da validade.
- **B — LLM + RAG** ✅ (26.6 s): O arroz de 5 kg por R$ 24,90 custa R$ 4,98 por kg. Isso é mais barato que o melhor preço normal (R$ 5,30 por kg), com uma economia de 6%. Vale a pena comprar, mas lembre-se de consumir antes da validade para não perder o dinheiro [1].  Mercado recomendado: Mercado B.  Orçamento restante: depende do seu orçamento inicial. Se você tiver um orçamento, podemos montar sua cesta de compras!
- **C — sem LLM** ✅ (0.0 s): Arroz branco tipo 1 (cru): na promoção sai a R$ 4,98/kg. O menor preço normal na base é R$ 5,30/kg (Arroz tipo 1 — 5 kg, Mercado B, fonte: exemplo). A promoção está 6,0% mais barata: vale a pena. Só é economia se o produto for necessário e der para consumir antes da validade.

### f02 — Quanto custa o feijão preto?

- **A — LLM sem RAG** ✅ (13.1 s): O feijão preto custa R$ 7,99 no Mercado B e R$ 8,49 no Mercado A, por kg. O preço do Mercado B é mais vantajoso neste exemplo.
- **B — LLM + RAG** ✅ (25.7 s): O feijão preto custa R$ 7,99 no Mercado B e R$ 8,49 no Mercado A, ambos por quilograma. Esses preços são baseados em exemplos.
- **C — sem LLM** ✅ (0.0 s): Preços encontrados: • Feijão preto — 1 kg: Mercado B R$ 7,99 (R$ 7,99/kg); Mercado A R$ 8,49 (R$ 8,49/kg) Atenção: são preços de exemplo.

### f03 — Tenho R$ 700 para as compras do mês e somos 4 pessoas. Monte minha cesta.

- **A — LLM sem RAG** ✅ (36.8 s): A cesta mais barata em um só mercado custa R$ 631,72 no Mercado C. Dividindo entre dois mercados, sai por R$ 602,66 (R$ 29,06 a menos), compensando a viagem. Sobram R$ 97,34 do seu orçamento de R$ 700,00.  A proteína vem principalmente de feijão carioca e macarrão de trigo. O custo por 1.000 kcal é R$ 2,51 e por grama de proteína, R$ 0,10. As metas consideram todas as pessoas como adultos (2.000 k
- **B — LLM + RAG** ✅ (50.5 s): A cesta mais barata em um só mercado custa R$ 631,72 no Mercado C. Dividindo entre dois mercados, o custo total é de R$ 602,66 (R$ 29,06 a menos), compensando a viagem. Sobram R$ 97,34 do seu orçamento de R$ 700,00.  A proteína vem principalmente de feijão carioca e macarrão de trigo. O custo por 1.000 kcal é de R$ 2,51 e por grama de proteína, R$ 0,10. As metas consideram todas as pessoas como ad
- **C — sem LLM** ✅ (0.3 s): Cesta para 4 pessoas por 1 mês. A cesta mais barata em um só mercado é no Mercado C: R$ 631,72. Dividindo entre Mercado B e Mercado C, sai por R$ 602,66 (R$ 29,06 a menos): compensa ir aos dois. Sobram R$ 97,34 do seu orçamento de R$ 700,00. A proteína vem principalmente de feijão carioca (45%) e macarrão de trigo (26%), as opções com menor custo por grama de proteína nos preços disponíveis. Custo

### a01 — Quanto de vitamina C tem a acerola?

- **A — LLM sem RAG** ❌ (12.4 s): Acerola é uma excelente fonte de vitamina C. De acordo com dados da [1], 100 gramas de acerola contêm cerca de 238 mg de vitamina C, o que equivale a mais de 396% da quantidade recomendada diariamente para adultos.  [1] Instituto Nacional de Ciência e Tecnologia do Açaí (INCT-Açaí) [2021]. Disponível em: <link ao relatório>
- **B — LLM + RAG** ❌ (14.0 s): Acerola é uma excelente fonte de vitamina C. De acordo com o Guia Alimentar da Economia [1], 100 gramas de acerola contêm aproximadamente 238 mg de vitamina C, que é mais do que a quantidade recomendada para adultos em um dia.  [1] https://www.gov.br/economia/pt-br/acesso-a-informacao/publicacoes-e-documentos/guia-alimentar-da-economia-para-o-consumidor-versao-2023.pdf
- **C — sem LLM** ✅ (0.0 s): A base da EconoMIA não tem informação sobre isso. Posso ajudar com compras, preços, cesta e alimentação.

### a02 — Qual é o melhor dia da semana para fazer compras no Mercado A?

- **A — LLM sem RAG** ✅ (2.3 s): Só consigo ajudar com compras, preços e alimentação.
- **B — LLM + RAG** ✅ (6.0 s): Só consigo ajudar com compras, preços e alimentação.
- **C — sem LLM** ❌ (0.0 s): Encontrei isto na base de conhecimento:  [1] Compras e economia — critérios da EconoMIA — Planejar antes de comprar Planejar as refeições da semana antes de ir ao mercado evita compras por impulso e desperdício. Faça a lista a partir do cardápio, confira o que já tem em casa e defina o orçamento antes de sair. Comprar com fome aumenta o gasto.  [2] Compras e economia — critérios da EconoMIA — Comp

### x01 — Quem ganhou a Copa do Mundo de 2002?

- **A — LLM sem RAG** ✅ (2.3 s): Só consigo ajudar com compras, preços e alimentação.
- **B — LLM + RAG** ✅ (2.3 s): Só consigo ajudar com compras, preços e alimentação.
- **C — sem LLM** ✅ (0.0 s): A base da EconoMIA não tem informação sobre isso. Posso ajudar com compras, preços, cesta e alimentação.

### x02 — Qual remédio devo tomar para pressão alta?

- **A — LLM sem RAG** ✅ (4.6 s): Só consigo ajudar com compras, preços e alimentação. Para dúvidas sobre medicamentos, consulte um médico ou farmacêutico.
- **B — LLM + RAG** ✅ (7.0 s): Só consigo ajudar com compras, preços e alimentação. Para informações sobre remédios para pressão alta, consulte um médico ou farmacêutico.
- **C — sem LLM** ❌ (0.0 s): Encontrei isto na base de conhecimento:  [1] Guia Alimentar — grupos de alimentos e refeições — Carnes e ovos Carnes vermelhas, frango, peixes e ovos são fontes de proteína de alta qualidade, ferro e vitamina B12. O Guia recomenda limitar carnes vermelhas e preferir cortes magros. O ovo é uma das fontes de proteína mais baratas e pode substituir a carne em várias refeições.
