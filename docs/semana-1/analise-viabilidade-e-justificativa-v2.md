# EconoMIA: análise de viabilidade, concorrentes e justificativa (v2)

> **Versão 2.** Mudanças em relação à [v1](analise-viabilidade-e-justificativa-v1.md): os dados de preço unitário da Austrália e do Reino Unido (seção 1.4) foram trocados por dados do Brasil (Idec, Lei 13.175/2015, Procon Maceió), e a pesquisa do Procon de Lages entrou na seção 1.3. Na seção 1.7, entrou o levantamento ObservaDF (UnB, 2026) e a evidência da PNAD 2024 foi reescrita. Na seção 1.8, o estudo francês (Ducrot, 2017) foi trocado por dados do Brasil (Santos et al., 2019, e UNICEF, 2021). A seção 3.4 passou a ser "em decisão", com as opções de modelo, ferramentas de LLMOps e deploy em lista. As referências foram numeradas ([1] a [55]) e passaram a listar só as fontes citadas no texto; a reportagem da Itatiaia (que trazia o valor de junho, não de julho) saiu da seção 1.1, e a evidência sobre ultraprocessados (seção 1.6) foi corrigida com os números da fonte.

> Documento da Semana 1 (27/10 a 02/11/2026). Ele dá base às seções **2. Problema**, **5. Riscos** e **7. Fontes** de [definicoes-do-projeto.md](definicoes-do-projeto.md).
> Pesquisa feita em 29/10/2026. Os itens marcados com ⚠️ vieram de fonte secundária ou não tiveram o documento original conferido. 

---

## 0. Resumo executivo

| Pergunta | Resposta curta |
| --- | --- |
| **O problema existe e é relevante?** | **Sim.** Em Brasília, a cesta básica consome cerca de 50% do salário mínimo líquido [1] [2]. 82% das famílias brasileiras estão endividadas [5] [7], e 27% dos domicílios do DF vivem com algum grau de insegurança alimentar [28] [29]. Cada família desperdiça cerca de 128 kg de comida por ano [21] [22], e os ultraprocessados já custam o mesmo que a comida in natura [24] [25]. |
| **Já existe solução pronta?** | **Só em partes.** Há apps de preço (Menor Preço Brasil), de lista (Listonic, Bring!), de receitas (Supercook, Samsung Food), de finanças (Mobills) e de leitura de nota (Grocery AI). **Nenhum combina** preço local real, orçamento, receitas e leitura de nota com explicação dos critérios, em português e para o contexto do DF. |
| **É tecnicamente viável em 7 semanas?** | **Sim, com recorte.** LLM, RAG, multiagente e leitura de imagem são tecnologias maduras. **O gargalo é o dado de preço**, não a IA. |
| **Recorte recomendado** | **Gama (RA II do DF)** no MVP, com o modelo de dados já preparado para outras RAs (campo `regiao`). |
| **Maior risco** | Base de preços pequena ou desatualizada. **Mitigação:** coleta própria em 4 a 6 mercados do Gama, mais notas fiscais (NFC-e) da própria equipe e de voluntários, deixando sempre explícita a data e a origem de cada preço. |

---

## 1. Justificativa: evidências do problema

Cada bloco liga uma evidência a uma funcionalidade do EconoMIA. Esse é o argumento que os avaliadores querem ver.

### 1.1 Comida pesa no orçamento, e pesa mais para quem ganha menos

| Evidência | Fonte | Liga com |
| --- | --- | --- |
| Em julho/2026, a cesta básica de **Brasília custou R$ 747,10**: **49,83% do salário mínimo líquido**, ou **101h24min de trabalho**.  | DIEESE, via [Sou Brasília](https://soubrasilia.com/cesta-basica-brasilia-julho-2026-747-reais-dieese-queda-26-capitais/) [1]. Original: [DIEESE, análise jul/2026](https://www.dieese.org.br/analisecestabasica/2026/202607cestabasica.pdf) [2] | 4.1 Planejamento com orçamento |
| O salário mínimo necessário para uma família de 4 seria **R$ 7.687,01** (4,74× o mínimo de R$ 1.621). | [DIEESE jul/2026](https://www.dieese.org.br/analisecestabasica/2026/202607cestabasica.pdf) [2] | Contexto |
| Famílias com até 2 salários mínimos gastam **22% do orçamento com alimentação**. As que ganham mais de 25 SM gastam **7,6%**. | IBGE, POF 2017-2018 ([Agência IBGE](https://agenciadenoticias.ibge.gov.br/agencia-noticias/25606-familias-com-ate-dois-salarios-gastam-61-do-orcamento-com-alimentos-e-habitacao.html) [3]) | Público-alvo de renda média e baixa |
| A alimentação no domicílio subiu **3,03% em 12 meses** (até jun/2026). | IBGE/IPCA, via [CNA](https://cnabrasil.org.br/storage/arquivos/files/Ed.11-CT-CNA-IPCA-16jul2026.pdf) [4] | 4.3 Histórico de preços |

### 1.2 As famílias estão sob pressão financeira e já mudaram o jeito de comprar

| Evidência | Fonte | Liga com |
| --- | --- | --- |
| **~82% das famílias endividadas** em mai/2026, recorde da série. | CNC/PEIC, via [Folha PE](https://www.folhape.com.br/economia/endividamento-das-familias-atinge-maior-nivel-da-serie-historica/505078/) [5] e [Poder360](https://www.poder360.com.br/poder-economia/apos-5-meses-de-alta-endividamento-das-familias-fica-estavel/) [6]. Original: [PEIC maio/2026](https://static.poder360.com.br/2026/06/endividamento-cnc-peic-maio2026.pdf) [7] | Orçamento |
| **70% dos lares** brasileiros vivem com algum grau de restrição orçamentária em 2026. As compras em promoção cresceram **35% em valor** no 2º tri/2026 frente ao 2º tri/2025, e as marcas próprias, 10%. | Worldpanel by Numerator, *Consumer Insights 2026*, via [SuperHiper/Abras, 17/09/2026](https://www.superhiper.com.br/consumidor-muda-habito-de-compra-menos-visitas-carrinhos-maiores-e-mais-promocoes/) [8] | 4.3 Oportunidades |
| **90%** dos brasileiros adotaram ao menos uma estratégia de economia nos últimos 3 meses (trocar de marca, buscar promoção). | McKinsey 2026, via [ABC da Comunicação](https://www.abcdacomunicacao.com.br/brasileiro-pesquisa-mais-compara-mais-e-continua-fiel-as-marcas-que-entregam-valor/) [9] | Comparação de preços |
| **62%** dos cariocas pesquisam mais promoções, trocam de marca e **dividem as compras entre mercados** (RJ, jul/2025; amostra e período não divulgados). | Asserj, via [Diário do Rio, 08/07/2025](https://diariodorio.com/cariocas-recorrem-a-promocoes-e-mercados-alternativos-para-driblar-alta-dos-precos) [10] | Comparação entre lojas |

**Argumento:** as pessoas já tentam economizar, mas fazem isso de forma manual e fragmentada. O EconoMIA não cria um comportamento novo. Ele reduz o esforço de um comportamento que já existe.

### 1.3 Os preços variam muito entre mercados, e é difícil saber onde está mais barato

| Evidência | Fonte | Liga com |
| --- | --- | --- |
| Em Goiânia (região vizinha ao DF), o Procon encontrou **variação de mais de 250%** no preço do mesmo item da cesta (banana) entre supermercados. | [Mais Goiás / Procon Goiânia](https://www.maisgoias.com.br/cidades/procon-encontra-variacao-de-mais-de-250-no-preco-de-itens-da-cesta-basica-em-goiania/) [11] | 4.2 Comparação de preços |
| Em Dourados (MS), houve diferenças de **mais de 100%** em itens básicos entre 12 supermercados (out/2026). | [A Crítica / Procon](https://acritica.net/economia/erva-mate-tem-diferenca-de-344-entre-supermercados-de-dourados-aponta-procon/) [12] | 4.2 |
| Em Lages (SC), o Procon encontrou o quilo da laranja-pera entre **R$ 1,99 e R$ 16,90** (variação de **749%**) em 9 mercados. O total da cesta variou de **R$ 388,53 a R$ 784,58**, uma diferença de R$ 396 para a mesma lista. | [ND Mais, 03/09/2026](https://ndmais.com.br/economia/pesquisa-do-procon-encontra-variacao-de-ate-749-nos-precos-de-supermercados-e-cesta-basica-tem-diferenca-de-r-396/) [13] | 4.2 e "Como reorganizar minhas compras para gastar menos?" |
| **Não encontramos uma pesquisa de preços recente e pública do Procon-DF.** | Busca em 29/10/2026 | **Oportunidade:** a coleta própria da equipe no Gama vira, ao mesmo tempo, dado do app e evidência do problema. |

### 1.4 Promoção não é sinônimo de economia (preço unitário e reduflação)

| Evidência | Fonte | Liga com |
| --- | --- | --- |
| O Idec pesquisou **177 produtos de 70 marcas** e encontrou diferenças de **até 215%** no preço por unidade de medida entre embalagens da mesma marca. **Nem sempre a embalagem maior é a mais barata**: num iogurte, o pote de 400 g saía a R$ 10,23/kg e o de 170 g a R$ 7,29/kg. (pesquisa antiga, de 2009) | Idec, via [InfoMoney, 24/06/2009](https://www.infomoney.com.br/mercados/dependendo-do-tamanho-da-embalagem-preco-de-produto-pode-triplicar/) [14] | "Qual embalagem compensa mais?" |
| Informar o preço por quilo, litro ou unidade é **obrigatório desde 2015** (Lei 13.175/2015, que alterou a Lei 10.962/2004) [15], mas a regra ainda é descumprida. Em fev/2025, o Procon de Maceió **autuou 8 supermercados**, entre outros motivos pela **ausência de preço por unidade de medida**. | [Cada Minuto, 20/02/2025](https://www.cadaminuto.com.br/noticia/2025/02/20/procon-autua-supermercados-por-praticas-abusivas-em-maceio) [16]; [Tribuna de Jundiaí](https://tribunadejundiai.com.br/mais/brasil/supermercados-novas-regras-2026-direitos/) [17] | Preço por kg/L calculado pelo sistema, sem depender da etiqueta |
| **Reduflação:** a Portaria MJ nº 392/2021 [18] obriga avisar na embalagem quando a quantidade diminui. Fiscalizações encontraram descumprimento e avisos difíceis de ver. | [Idec](https://idec.org.br/dicas-e-direitos/reduflacao-pode-um-produto-diferente-ou-menor-com-embalagem-igual) [19]; [Diário do Nordeste](https://diariodonordeste.verdesmares.com.br/negocios/reduflacao-de-produtos-nao-segue-lei-e-consumidores-denunciam-embalagens-enganosas-veja-direitos-1.3293136) [20] | Histórico de compras (Recibaldo detecta embalagem menor pelo mesmo preço) |

### 1.5 Desperdício de alimentos

| Evidência | Fonte | Liga com |
| --- | --- | --- |
| Cada família brasileira desperdiça em média **128 kg de alimentos por ano** (41 kg por pessoa). Os mais desperdiçados são arroz, carne, feijão e frango. | Embrapa/FGV 2018, Porpino et al. ([Hoje em Dia](https://www.hojeemdia.com.br/economiaefinancas/desperdicio-de-alimentos-chega-a-r-1-mil-por-familia-por-ano-diz-embrapa-1.717638) [21]; [tese de Porpino](https://bdjur.stj.jus.br/jspui/bitstream/2011/155327/Gustavo_Porpino.pdf) [22]) | 4.5 Receitas e aproveitamento |
| Isso equivale a **mais de R$ 1.000 por ano** para uma família de 3 pessoas (valores de 2018). | Embrapa/FGV 2018 [21] [22] | Argumento financeiro |
| O PNUMA estima o índice de desperdício de alimentos em **94 kg per capita** na etapa de consumo falimiar no Brasil.| UNEP Food Waste Index 2024 ([O Presente Rural](https://opresenterural.com.br/mundo-joga-fora-mais-de-um-bilhao-de-refeicoes-por-dia-diz-onu/) [23]) | Idem |

### 1.6 Comprar barato e comer bem estão se tornando objetivos opostos

| Evidência | Fonte | Liga com |
| --- | --- | --- |
| O preço médio dos **ultraprocessados caiu cerca de 16%** entre 2018 e 2024 (de R$ 22,20 para R$ 18,80), enquanto o dos in natura e minimamente processados subiu até R$ 21,30 em 2021 e fechou 2024 em R$ 18,60. Em 2024 os dois grupos **convergiram**, e a projeção para 2026 é de R$ 17,90/kg para ultraprocessados contra R$ 19,60/kg para in natura. | UFMG/Idec 2025 ([Idec](https://idec.org.br/node/31258) [24]; [Gazeta SP](https://www.gazetasp.com.br/economia/arroz-feijao-e-frutas-devem-ficar-mais-caros-ate-2026-veja-precos/) [25]) | Agente Miau-ricio (nutrição) |
| O Guia Alimentar recomenda basear a alimentação em alimentos in natura e minimamente processados, preferir os da estação e **planejar o tempo e as compras**. | Ministério da Saúde, *Guia Alimentar para a População Brasileira* (2014) [26] ([10 passos, CFN](https://cfn.org.br/onu-e-governo-brasileiro-ensinam-10-passos-simples-para-uma-alimentacao-saudavel/) [27]) | Base do RAG (fonte oficial e gratuita) |

### 1.7 Insegurança alimentar no DF

| Evidência | Fonte |
| --- | --- |
| Em 2026, **38,5% dos entrevistados no DF** relataram que alguém da casa passou por algum grau de insegurança alimentar (escala Ebia). Houve melhora desde 2021 (a segurança alimentar subiu de 50,1% para 61,5%), mas a **insegurança grave não caiu de forma estatisticamente significativa**: 9,7% dos adultos e 6,3% das crianças sentiram fome e não comeram. O problema é mais forte nas casas de **menor renda** (52,7% até 1,5 salário mínimo per capita, contra 33,1% nas de renda maior) e nas **chefiadas por mulheres** (46,7%, contra 34,9% nas chefiadas por homens). (a reportagem não informa o tamanho da amostra) | ObservaDF (UnB), via [Jornal de Brasília, 17/06/2026](https://jornaldebrasilia.com.br/brasilia/inseguranca-alimentar-grave-persiste-no-df-aponta-levantamento/) [28] |
| Pelo dado oficial, **27,0% dos domicílios do DF** estavam em insegurança alimentar em 2024, contra 26,5% em 2023. O DF foi **uma das 4 UFs que pioraram**, enquanto a média do Brasil caiu de 27,6% para 24,2%. Só **73,0%** dos lares do DF têm segurança alimentar (13º lugar entre as 27 UFs, abaixo da média nacional de 75,8%), e a **insegurança grave no DF é de 4,2%**, acima da média do Brasil (3,2%), apesar de o DF ter o maior PIB per capita do país. | IBGE, PNAD Contínua: Segurança Alimentar 2024 ([Correio Braziliense](https://www.correiobraziliense.com.br/cidades-df/2025/10/7268826-na-contramao-do-brasil-df-tem-aumento-na-inseguranca-alimentar.html) [29]; [Jornal de Brasília](https://jornaldebrasilia.com.br/brasilia/inseguranca-alimentar-grave-persiste-no-df-aponta-levantamento/) [28]) |

**Argumento:** a **insegurança alimentar leve** se caracteriza justamente pela preocupação com a falta de comida e pelo ajuste da qualidade da alimentação para fazer o dinheiro render. É exatamente o espaço em que um planejador de compras atua. O EconoMIA **não resolve a fome**, e o relatório deve deixar isso explícito como limitação.

### 1.8 Falta de tempo (trabalho doméstico invisível)

| Evidência | Fonte | Liga com |
| --- | --- | --- |
| Mulheres dedicam **cerca de 21 h por semana** a afazeres domésticos e cuidados, contra cerca de 11 h dos homens. (o ano de referência varia entre as fontes) | IBGE, PNAD Contínua, Outras Formas de Trabalho ([Monitor Mercantil](https://monitormercantil.com.br/mulheres-dedicam-o-dobro-de-horas-dos-homens-a-afazeres-domesticos/) [30]) | "Economizar tempo na organização das compras" |
| Num estudo com 877 adultos de Cambé (PR), a principal barreira para comer frutas e verduras foi **o custo pesar no orçamento da família** (57,7% para frutas e 49,9% para verduras e legumes). A **falta de tempo para ir ao mercado ou à feira** foi citada por 8,0% (frutas) e 7,6% (verduras), e foi mais comum entre **mulheres** (OR 1,79) e pessoas sem companheiro (OR 1,92). O estudo é transversal, então mostra associação, não causa. | Santos et al., 2019, *Ciência & Saúde Coletiva* 24(7) ([SciELO](http://www.scielo.br/j/csc/a/LSm9mRVdJnBCpF7zvPXxsSP/?lang=pt) [31]) | 4.1 Planejamento com orçamento + 4.4 Lista |
| Em famílias do Bolsa Família com crianças de até 6 anos, os motivos mais citados para comprar ultraprocessados foram **sabor (46%), preço (24%) e praticidade (17%)**. Cerca de 80% das famílias disseram que as crianças tinham comido ultraprocessados no dia anterior. | UNICEF, 2021: 1.343 entrevistados em 21 estados ([comunicado, 16/12/2021](https://www.unicef.org/brazil/comunicados-de-imprensa/estudo-inedito-do-unicef-aponta-alto-consumo-de-alimentos-ultraprocessados-em-lares-atendidos-pelo-bolsa-familia) [32]) | 4.5 Receitas práticas e baratas (Miau-ricio) |

### 1.9 Deslocamento e acesso (o ponto que vocês levantaram: carro, a pé, ônibus)

| Evidência | Fonte |
| --- | --- |
| Na SCIA-Estrutural (DF), um estudo da UnB encontrou **desertos e/ou pântanos alimentares em todos os setores analisados**. | Galvão & Diniz ([Cadernos de Agroecologia](https://cadernos.aba-agroecologia.org.br/cadernos/article/download/8993/6657/33730) [33]) |
| O MDS e a USP mapearam desertos e pântanos alimentares no Brasil (2024), com a plataforma **Alimenta Cidades**. | [Relatório MDS/USP](https://cms.revistaforum.com.br/u/archivos/2025/1/28/Relatório%20-%20Desertos%20e%20Pântanos%20Alimentares.pdf) [34]; [Rev. Saúde Pública](https://scielo.br/j/rsp/a/jYmdChpKNPgyFr8SDwQCHmF/?lang=en) [35] |
| No DF, quem tem renda maior frequenta mais estabelecimentos comerciais. | IPEDF, via [Jornal de Brasília](https://jornaldebrasilia.com.br/blogs-e-colunas/do-alto-da-torre/mais-ricos-frequentam-mais-lojas-e-fazem-mais-esporte/) [36] |

**Implicação de produto:** uma economia de R$ 8 em outro mercado **não vale a pena** para quem vai de ônibus (passagem de ida e volta) ou a pé com sacolas. Isso justifica o item da proposta "custo estimado de deslocamento" e torna o **meio de transporte uma variável obrigatória do perfil do usuário** (ver seção 5).

### 1.10 O público está pronto para IA? (e onde não está)

| Evidência | Fonte |
| --- | --- |
| **32%** dos usuários de internet no Brasil (cerca de 50 milhões) já usam IA generativa. | Cetic.br, TIC Domicílios 2025 ([Teletime](https://teletime.com.br/09/12/2025/tic-domicilios-2025-aponta-que-50-milhoes-de-brasileiros-ja-usam-ia/) [37]; [resumo executivo](https://www.cetic.br/media/docs/publicacoes/2/pt-br/20260511173151/tic_domicilios_2025_resumoexecutivo%20pt.pdf) [38]) |
| O uso é muito desigual: **69% na classe A contra 16% nas classes D e E**. Entre quem não usa, os motivos são falta de interesse (76%), preocupação com privacidade (63%) e falta de habilidade (58%). | Cetic.br, TIC Domicílios 2025, via [Mobile Time](https://www.mobiletime.com.br/noticias/09/12/2025/50-mi-ia-generativa-tic-domicilios-2025/) [39]; [Canaltech](https://canaltech.com.br/inteligencia-artificial/um-a-cada-tres-brasileiros-ja-usa-ia-generativa-aponta-pesquisa/) [40] |

**Implicação:** o público que **mais precisa** (renda mais baixa) é o que **menos usa IA**. A interface precisa ser simples, sem cara de "chat de IA". Vale avaliar um canal pelo WhatsApp, que apareceu como ideia no Miro, e a privacidade precisa ser comunicada logo no início.

---

## 2. Mapa de concorrentes e soluções semelhantes

### 2.1 Tabela comparativa

Legenda: ✅ faz bem · 🟡 parcial · ❌ não faz

| App / solução | Preço local real | Orçamento | Lista | Receitas e aproveitamento | Lê nota ou encarte | Nutrição | Explica o "porquê" | Observação |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Menor Preço Brasil** (Sefaz-RS/Confaz) | ✅ via NFC-e | ❌ | 🟡 | ❌ | 🟡 código de barras | ❌ | ❌ | **Principal concorrente em preço.** O DF assinou o convênio em 2019 ([Convênio ICMS 03/2019](https://www.legisweb.com.br/legislacao/?id=382945) [41]). É gratuito, mas não tem API pública. **Tarefa: testar o app no Gama.** |
| **Nota Paraná / Menor Preço PR** | ✅ | ❌ | 🟡 (exige cadastro) | ❌ | ❌ | ❌ | ❌ | Origem do modelo. Mostra que dados de NFC-e funcionam para comparar preços ([Bem Paraná](https://www.bemparana.com.br/consumidor/aplicativo-que-permite-pesquisa-de-29-milhoes-de-precos-ajuda-a-economizar-na-black-friday/) [42]) |
| **LudiiPrice** (TCC, UFS) | 🟡 colaborativo | ❌ | ❌ | ❌ | ✅ QR code da NFC-e | ❌ | ❌ | **Prova acadêmica** de que dá para ler o QR code e montar uma base de preços ([PDF](https://ri.ufs.br/bitstream/riufs/15903/2/Adan_Cordeiro_Araujo.pdf) [43]) |
| **Listonic / Bring! / AnyList / SoftList** | ❌ | 🟡 soma manual | ✅ | 🟡 (AnyList) | ❌ | ❌ | ❌ | Ótimos em lista compartilhada pela família ([Mobills](https://www.mobills.com.br/blog/aplicativo-de-lista-de-compras/) [44]; [Meu Tudo](https://meutudo.com.br/blog/aplicativo-lista-de-compras/) [45]) |
| **Mobills / Organizze** | ❌ | ✅ | 🟡 | ❌ | ❌ | ❌ | ❌ | Finanças gerais, não pensados para mercado |
| **Supercook** | ❌ | ❌ | ❌ | ✅ "o que tenho em casa" | ❌ | ❌ | ❌ | Sem nutrição, em inglês ([review](https://grate-six.vercel.app/blog/best-recipe-app) [46]) |
| **Samsung Food** (ex-Whisk) | ❌ | ❌ | ✅ | ✅ | ❌ | 🟡 | ❌ | Tem IA, mas é voltado aos EUA e Europa e ao ecossistema Samsung ([9to5Google](https://9to5google.com/2023/08/30/whisk-samsung-food-app-rebrand/) [47]) |
| **Grocery AI** (Pocket Labs) | ❌ | 🟡 | ✅ | ✅ IA | ✅ recibo | ❌ | ❌ | **O mais parecido em funcionalidades**, mas é dos EUA, em inglês e sem preços do Brasil ([App Store](https://apps.apple.com/ca/app/grocery-ai/id1544118181) [48]) |
| **EasyGrocery** (Grocery List: Budget App) | ❌ | ✅ | ✅ | 🟡 | ✅ recibo | ❌ | ❌ | Validade e lista compartilhada ([App Store](https://apps.apple.com/app/id6741698303) [49]) |
| **Apps das redes** (Meu Assaí, Atacadão, Pão de Açúcar etc.) | ✅ só da própria rede | ❌ | 🟡 | ❌ | ❌ | ❌ | ❌ | Por definição, não comparam com a concorrência ([Canaltech](https://canaltech.com.br/apps/aplicativos-para-economizar-no-mercado/) [50]) |
| **Encartes digitais** (Tiendeo, sites de folhetos) ⚠️ | 🟡 só promoções | ❌ | ❌ | ❌ | é o próprio encarte | ❌ | ❌ | Mostram a oferta, mas não dizem se ela compensa |
| **Cashback** (Méliuz etc.) ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Outra lógica de economia |
| **Delivery** (iFood Mercado, Rappi) ⚠️ | 🟡 preço do app | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | Os preços costumam ser diferentes dos da loja física |
| **LLM genérico** (ChatGPT, Gemini, Claude) | ❌ alucina preços | 🟡 | 🟡 | ✅ | ✅ | 🟡 | 🟡 | **Concorrente indireto mais importante.** É exatamente a "Abordagem A" da comparação da Semana 3 |
| **EconoMIA** (proposta) | ✅ base local com data e fonte | ✅ | ✅ | ✅ | ✅ | ✅ Guia Alimentar | ✅ | — |

> ⚠️ Os apps marcados não foram testados nesta pesquisa. Vale alguém do grupo instalar e conferir antes da apresentação.

### 2.2 Diferencial defensável (o que dizer para a banca)

1. **Integração:** o problema real atravessa preço, orçamento, lista, receitas e desperdício, e cada app atual resolve só uma parte. Essa é a tese do PDF e a tabela acima confirma.
2. **Explicabilidade e honestidade sobre os dados:** cada preço vem com data e fonte, e o app separa o que é confirmado do que é estimado. Nenhum concorrente faz isso.
3. **"Barato" não é igual a "melhor":** por causa do ponto 1.6, o app equilibra preço, nutrição, deslocamento e necessidade real.
4. **Contexto local:** português, DF, encartes e notas fiscais brasileiras (NFC-e).
5. **Versus ChatGPT puro:** um LLM sozinho não sabe o preço de hoje no Gama. A comparação LLM × RAG da Semana 3 vira uma **evidência experimental** do diferencial, e não apenas um requisito do desafio.

> **Cuidado na apresentação:** não digam que "não existe nada parecido". O Menor Preço Brasil e o Grocery AI existem. O argumento é que **nenhum integra** essas funções para o contexto brasileiro.

---

## 3. Análise de viabilidade

### 3.1 Recorte geográfico: Gama ou DF inteiro

| Critério | Só o Gama | DF inteiro (33+ RAs) |
| --- | --- | --- |
| Coleta de preços em 7 semanas | ✅ é viável visitar 4 a 6 mercados | ❌ inviável manualmente |
| Contato com usuários reais (questionário e entrevistas) | ✅ alguém do grupo mora ou estuda lá | 🟡 dispersos |
| Representatividade | 🟡 cerca de 137 mil habitantes urbanos, com renda domiciliar média de **R$ 5.034** contra **R$ 6.938** no DF (PDAD 2021, [IPEDF](https://ipe.df.gov.br/documents/9915964/10216206/PDAD_2021-Apresentacao_Sul.pdf) [51]). É um perfil de renda média, alinhado ao público | ✅ |
| Deslocamento entre lojas | ✅ dá para mapear distâncias reais | ❌ |
| Escalabilidade | Basta ter `regiao` no modelo de dados | — |

**Recomendação:** **MVP no Gama**, com a arquitetura pronta para várias regiões. No relatório, apresentar o Gama como **piloto** e o DF como trabalho futuro. Os dados da PDAD sobre o Gama servem para justificar a escolha (vale baixar o [relatório da RA](https://ipe.df.gov.br/documents/9915964/10215637/Gama.pdf) [52]).

### 3.2 Viabilidade dos dados (o ponto crítico)

| Fonte de preço | Viabilidade | Prós | Contras |
| --- | --- | --- | --- |
| **A. Coleta própria em loja** (fotos de gôndola e etiqueta) | ✅ alta | Controle total, data conhecida, também gera evidência do problema (seção 1.3) | Trabalhosa. Precisa de uma lista fixa de cerca de 40 a 60 itens e cobre poucas datas |
| **B. NFC-e via QR code** (notas da equipe e de voluntários) | ✅ alta, **testar na semana 1** | Dado oficial com item, preço unitário, loja e data. O QR code aponta para a página pública de consulta da Sefaz-DF (`fazenda.df.gov.br/nfce/...`). Alimenta direto o agente **Recibaldo** | A nota pode trazer **CPF**, que precisa ser descartado (LGPD). A página pode ter captcha ou mudar de formato. As descrições vêm abreviadas ("ARROZ T1 5KG CAMIL"), então é preciso normalizar |
| **C. Encartes** (PDF ou imagem das redes) | 🟡 média | Promoções reais. É um ótimo caso de **multimodalidade** (Semana 5) | Só mostram promoções e têm validade curta |
| **D. Menor Preço Brasil** | ❌ para automação | Teria a melhor cobertura | Não há API pública. Raspar o app é juridicamente arriscado e frágil. **Use só como referência manual e benchmark** |
| **E. Dados oficiais agregados** (DIEESE, IPCA) | ✅ | Contexto e tendência | Não têm preço por loja |

**Recomendação:** combinar **A + B** como base principal, usar **C** como entrada multimodal e **E** como contexto. Com isso, a base de preços fica **pequena porém confiável e com data**, o que já está alinhado à proposta ("distinguir preços confirmados de valores históricos").

**Teste prático para esta semana:** peguem uma NFC-e de mercado do Gama, leiam o QR code e vejam se a página da Sefaz-DF mostra os itens sem login nem captcha. Se mostrar, a fonte B está validada.

### 3.3 Viabilidade técnica por componente

| Componente | Semana | Viabilidade | Observação |
| --- | --- | --- | --- |
| RAG (receitas, Guia Alimentar, conservação de alimentos) | 2 | ✅ alta | Há fontes oficiais gratuitas: Guia Alimentar, materiais da Embrapa sobre desperdício e tabela TACO (Unicamp) para nutrientes |
| Preços via **banco estruturado** (SQL), não via RAG | 2 e 3 | ✅ | Já está no PDF. O LLM consulta por *tool calling* |
| Comparação LLM × RAG | 3 | ✅ | O risco é o conjunto de testes ficar pequeno. Montem desde já um gabarito com cerca de 50 perguntas |
| Multiagente (5 agentes + orquestrador) | 4 | ✅ | LangGraph, CrewAI ou chamadas diretas. Para o prazo, 3 agentes bem feitos valem mais que 5 frágeis |
| Leitura de nota fiscal e encarte (Recibaldo) | 5 | 🟡 média | Mesmo os melhores modelos multimodais erram em notas fiscais reais: no benchmark **ReceiptBench (2026)**, o Gemini-3-Pro teve F1 de cerca de 0,74 e o GPT-5 de cerca de 0,71 ([arXiv 2603.11442](https://arxiv.org/pdf/2603.11442) [53]). **Isso justifica a revisão humana prevista no PDF.** Para NFC-e, ler o QR code é muito mais confiável que fazer OCR |
| Cálculos determinísticos | Todas | ✅ | Já está na proposta. Isso reduz muito o risco de alucinação numérica |
| Aplicação integrada | 6 | ✅ | Desde que exista um esqueleto funcionando a partir da semana 2 |

### 3.4 Viabilidade econômica e stack (🟡 em decisão)

> **Status: em decisão.** Objetivo: fazer o deploy real da aplicação e praticar LLMOps (versionamento de prompts, registro de chamadas, custo, latência e avaliação contínua das respostas). O LLM e a forma de execução (API ou Ollama) ainda não foram definidos. Cada escolha será registrada em [decisoes.md](../decisoes.md).

**Critérios de escolha**

- Custo dentro de planos gratuitos ou de estudante
- Qualidade em português e em tarefas com imagem (notas fiscais e encartes)
- Suporte a *tool calling*
- Latência
- Facilidade de deploy e de monitoramento
- Privacidade dos dados de notas fiscais

**Modelos (LLM)**

- APIs proprietárias: Claude (Anthropic), GPT (OpenAI ou Azure OpenAI), Gemini (Google)
- Open-source via Ollama: Qwen3, Llama, Gemma, Mistral (texto); Qwen3-VL, Gemma (imagem)
- Abordagem híbrida: modelo local para tarefas simples e API para tarefas complexas

**Execução do modelo (se open-source)**

- Ollama
- llama.cpp
- vLLM

**Orquestração dos agentes**

- LangGraph
- CrewAI
- LlamaIndex
- Chamadas diretas ao SDK do modelo

**RAG e busca vetorial**

- pgvector
- Chroma
- Qdrant
- FAISS

**LLMOps (observabilidade, avaliação e versionamento)**

- Langfuse
- LangSmith
- MLflow
- Ragas
- DeepEval
- Promptfoo

**Deploy e infraestrutura**

- Docker e Docker Compose
- GitHub Actions
- Azure for Students
- Render, Railway, Fly.io
- Hugging Face Spaces
- Banco de dados: Postgres ou Supabase

**Custo:** a definir após a escolha do LLM e o primeiro protótipo.

**Questões em aberto**

- API, Ollama ou abordagem híbrida?
- Onde o Ollama vai rodar? A assinatura Azure for Students não permite VM com GPU (cota da série N igual a zero), o que limita o Ollama a CPU ⚠️ ([Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2141487/request-for-gpu-enabled-vm-quota-increase-for-azur) [54])
- O Azure OpenAI está disponível na assinatura de estudante? Há relatos de modelos indisponíveis e cota baixa ⚠️ ([Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5949792/azure-for-students-unable-to-deploy-any-azure-open) [55])

### 3.5 Viabilidade legal e ética

| Tema | Ação |
| --- | --- |
| LGPD: notas fiscais podem ter CPF | Descartar o CPF na ingestão e nunca guardar a imagem original sem necessidade |
| LGPD: questionário com pessoas | Termo de consentimento (TCLE) simples, sem coletar nome nem telefone, a menos que a pessoa se ofereça para uma entrevista |
| Raspagem de sites e apps | Evitar. Preferir coleta manual, NFC-e do próprio usuário e encartes públicos |
| Recomendação nutricional | O app **não substitui nutricionista**. Usar só orientações gerais do Guia Alimentar e deixar isso explícito |
| Recomendação financeira | O app não dá conselho financeiro. Ele organiza informação, como o próprio PDF já diz |

### 3.6 Veredito

| Dimensão | Nota (1 a 5) | Comentário |
| --- | --- | --- |
| Relevância do problema | 5 | Há muitos dados oficiais recentes, inclusive do DF |
| Diferenciação | 4 | Existem soluções parciais, mas nenhuma integrada |
| Viabilidade técnica | 4 | As tecnologias são maduras. A leitura de imagem exige revisão humana |
| Viabilidade de dados | 3 | **É o ponto fraco.** Fica viável com o recorte no Gama e a combinação de fontes A + B |
| Viabilidade de prazo | 4 | Depende de cortar escopo (ver seção 4) |
| **Geral** | **Viável com recorte** | |

---

## 4. Riscos específicos do EconoMIA

Estes riscos complementam a tabela do README.

| Risco | Prob. | Impacto | Mitigação |
| --- | --- | --- | --- |
| Base de preços pequena ou velha, o que leva a recomendações erradas | Alta | Alto | Mostrar a data em todo preço, avisar quando estiver desatualizado e repetir a coleta nas semanas 2 e 5 |
| Normalização de produtos ("ARROZ T1 5KG" = "Arroz Camil Tipo 1 5kg") | Alta | Médio | Tabela de equivalência manual para os cerca de 60 itens, com o LLM sugerindo correspondências e uma pessoa validando |
| O usuário confia demais em "promoção boa" | Média | Médio | Sempre mostrar o cálculo (preço por kg, deslocamento) |
| Recomendar comida barata e pouco saudável | Média | Alto | O Miau-ricio aplica a classificação NOVA do Guia Alimentar e avisa quando o item é ultraprocessado |
| Escopo grande demais (6 funcionalidades e 5 agentes em 7 semanas) | Alta | Alto | Definir um **núcleo obrigatório** (orçamento, comparação e leitura de NFC-e) e deixar o resto como opcional |
| Público de baixa renda não usar IA (seção 1.10) | Média | Médio | Fluxos guiados com botões e chat opcional, e testes com usuários reais na semana 7 |
| Variação de layout das notas e encartes | Média | Médio | Priorizar o QR code da NFC-e e deixar o OCR como alternativa |

---

## 5. Como definir o público-alvo e criar as personas (🟡 em decisão)

Vocês ainda não definiram o público e querem um método. Esta é uma abordagem **mista e rápida**, que cabe na Semana 1 e no começo da Semana 2.

### 5.1 Etapas

| # | Etapa | Duração | Saída |
| --- | --- | --- | --- |
| 1 | **Proto-personas** (hipóteses do grupo, em 1 hora no Miro) | 1 dia | 3 ou 4 hipóteses de perfil para testar |
| 2 | **Questionário online** (Google Forms, divulgado em grupos do Gama, da faculdade, da família e em grupos de bairro no WhatsApp) | 4 a 5 dias | Dados quantitativos para segmentar |
| 3 | **Entrevistas semiestruturadas** com 5 a 8 respondentes que aceitarem, de 20 minutos cada | 2 a 3 dias | Dores, falas reais e contexto |
| 4 | **Observação contextual** (opcional, mas forte): acompanhar 2 pessoas numa ida ao mercado ou pedir que mostrem como fazem a lista | 1 dia | Comportamento real em vez do comportamento declarado |
| 5 | **Segmentação e personas finais**, cruzando renda, transporte, tamanho da família e quem decide as compras | 1 dia | 2 ou 3 personas com dados, mais o mapa de empatia e a jornada |

**Tamanho da amostra:** para uma estimativa com 95% de confiança e margem de ±10%, são necessárias **cerca de 96 respostas**. A meta é **100 ou mais**. Deixem claro no relatório que a amostra é **por conveniência** (não probabilística). É uma limitação aceitável para validar o problema, mas não para generalizar para a população.

### 5.2 Proto-personas para testar (hipóteses)

| Hipótese | Perfil | Transporte | Dor principal suposta |
| --- | --- | --- | --- |
| **"Mãe que faz o mês"** | 30 a 45 anos, 3 a 5 pessoas na casa, renda de 2 a 5 SM | Ônibus ou a pé + compras pequenas na semana | O orçamento não fecha, não tem tempo de comparar, as crianças precisam se alimentar bem |
| **"Universitário na primeira casa"** | 18 a 25 anos, mora sozinho ou divide, renda de até 2 SM | A pé ou de app de transporte | Não sabe planejar, desperdiça, vive de ultraprocessados |
| **"Casal de carro do atacarejo"** | 30 a 55 anos, 2 a 4 pessoas, renda de 5 SM ou mais | Carro, compra grande no atacarejo | Acha que está economizando, mas não confere preço unitário nem desperdício |
| **"Aposentado de renda fixa"** | 60 anos ou mais, 1 a 2 pessoas, até 3 SM | A pé ou de ônibus, mercado de bairro | Os preços sobem e a renda não acompanha. Tem pouca familiaridade com apps |

O questionário vai **confirmar, fundir ou descartar** essas hipóteses. Não as tratem como personas finais.

### 5.3 Rascunho do questionário (cerca de 5 minutos)

**Bloco A: perfil**
1. Em qual região do DF você mora? (Gama / outra: ___)
2. Idade (faixas)
3. Quantas pessoas moram na sua casa?
4. Renda familiar mensal (faixas em salários mínimos, com a opção "prefiro não dizer")
5. Você é a pessoa que mais decide ou faz as compras de mercado da casa? (Sim / divido / não)

**Bloco B: hábitos de compra**
6. Com que frequência você vai ao mercado? (mais de 1 vez por semana / semanal / quinzenal / mensal)
7. **Como você costuma ir ao mercado?** (carro próprio / a pé / ônibus / app de transporte / bicicleta / delivery) *(múltipla escolha)*
8. Em quantos mercados diferentes você costuma comprar por mês?
9. Quanto sua casa gasta, em média, com mercado por mês? (faixas)
10. Você faz lista de compras? (sempre / às vezes / nunca). Em que formato? (papel / celular / de cabeça)

**Bloco C: dores (escala de 1 a 5, de "discordo totalmente" a "concordo totalmente")**
11. "É difícil saber qual mercado está mais barato."
12. "Não tenho tempo para comparar preços ou ver encartes."
13. "Já comprei uma promoção que depois percebi que não compensava."
14. "Costumo jogar comida fora porque estragou ou sobrou."
15. "Gostaria de comer de forma mais saudável, mas acho caro."
16. "Meu dinheiro do mercado acaba antes do fim do mês."
17. "Ir a outro mercado mais barato não compensa por causa do deslocamento."

**Bloco D: solução**
18. Você já usou algum app para lista, preço ou receitas? Qual?
19. Você usa ChatGPT ou outra IA? (nunca / já testei / uso com frequência)
20. Você confiaria numa sugestão de compras feita por IA se ela mostrasse de onde veio cada preço? (escala de 1 a 5)
21. Das funções abaixo, quais você **mais** usaria? (escolha até 3: comparar preços / montar lista dentro do orçamento / receitas com o que tenho em casa / ler nota fiscal e acompanhar gastos / saber se a promoção compensa / dicas de alimentação saudável)
22. Topa uma conversa de 20 minutos sobre o assunto? (se sim, um contato)

> O consentimento (LGPD) vai no topo do formulário: objetivo acadêmico, respostas anônimas, uso apenas no projeto e possibilidade de desistir.

### 5.4 Como analisar

- **Cruzar a pergunta 7 (transporte) com as perguntas 8 e 17:** isso confirma ou derruba a hipótese de que o deslocamento elimina a economia, e define se o agente de preços deve considerar distância.
- **Cruzar a renda (4) com a dor 16 e o uso de IA (19):** isso mostra se o público que mais precisa usaria o app.
- **Ranquear a pergunta 21:** isso define a **prioridade das funcionalidades** no MVP. É a evidência para cortar escopo com justificativa.
- **Clusterização simples** (k-means ou só tabelas cruzadas) sobre renda, transporte, tamanho da casa e dores. Os clusters viram as personas finais. É também um bom exercício de Ciência de Dados para a semana 1.

---

## 6. Referências

Os números entre colchetes no texto (por exemplo, [1]) remetem a esta lista, em ordem de primeira citação.

- **[1]** SOU BRASÍLIA. Cesta básica em Brasília custa R$ 747,10 e consome 49,83% do mínimo (dados DIEESE, jul. 2026). https://soubrasilia.com/cesta-basica-brasilia-julho-2026-747-reais-dieese-queda-26-capitais/
- **[2]** DIEESE. *Pesquisa Nacional da Cesta Básica de Alimentos*: análise de julho de 2026. https://www.dieese.org.br/analisecestabasica/2026/202607cestabasica.pdf
- **[3]** IBGE. Famílias com até dois salários gastam 61% do orçamento com alimentos e habitação (*Pesquisa de Orçamentos Familiares 2017-2018*). Agência de Notícias IBGE. https://agenciadenoticias.ibge.gov.br/agencia-noticias/25606-familias-com-ate-dois-salarios-gastam-61-do-orcamento-com-alimentos-e-habitacao.html
- **[4]** CNA. *Comunicado Técnico IPCA*, ed. 11, 16 jul. 2026 (dados IBGE/IPCA até jun. 2026). https://cnabrasil.org.br/storage/arquivos/files/Ed.11-CT-CNA-IPCA-16jul2026.pdf
- **[5]** FOLHA DE PERNAMBUCO. Endividamento das famílias atinge maior nível da série histórica (dados CNC/PEIC), 2026. https://www.folhape.com.br/economia/endividamento-das-familias-atinge-maior-nivel-da-serie-historica/505078/
- **[6]** PODER360. Após 5 meses de alta, endividamento das famílias fica estável (dados CNC/PEIC), 2026. https://www.poder360.com.br/poder-economia/apos-5-meses-de-alta-endividamento-das-familias-fica-estavel/
- **[7]** CNC. *Pesquisa de Endividamento e Inadimplência do Consumidor (PEIC)*, maio 2026. https://static.poder360.com.br/2026/06/endividamento-cnc-peic-maio2026.pdf
- **[8]** SUPERHIPER (Abras). Consumidor muda hábito de compra: menos visitas, carrinhos maiores e mais promoções (dados Worldpanel by Numerator, *Consumer Insights 2026*), 17 set. 2026. https://www.superhiper.com.br/consumidor-muda-habito-de-compra-menos-visitas-carrinhos-maiores-e-mais-promocoes/
- **[9]** ABC DA COMUNICAÇÃO. Brasileiro pesquisa mais, compara mais e continua fiel às marcas que entregam valor (dados McKinsey & Company, *An Update on Brazilian Consumer Sentiment*), 22 jul. 2026. https://www.abcdacomunicacao.com.br/brasileiro-pesquisa-mais-compara-mais-e-continua-fiel-as-marcas-que-entregam-valor/
- **[10]** DIÁRIO DO RIO. Cariocas recorrem a promoções e mercados alternativos para driblar alta dos preços (levantamento Asserj), 8 jul. 2025. https://diariodorio.com/cariocas-recorrem-a-promocoes-e-mercados-alternativos-para-driblar-alta-dos-precos
- **[11]** MAIS GOIÁS. Procon encontra variação de mais de 250% no preço de itens da cesta básica em Goiânia, 2026. https://www.maisgoias.com.br/cidades/procon-encontra-variacao-de-mais-de-250-no-preco-de-itens-da-cesta-basica-em-goiania/
- **[12]** A CRÍTICA. Erva-mate tem diferença de 344% entre supermercados de Dourados, aponta Procon, out. 2026. https://acritica.net/economia/erva-mate-tem-diferenca-de-344-entre-supermercados-de-dourados-aponta-procon/
- **[13]** ND MAIS. Pesquisa do Procon encontra variação de até 749% nos preços de supermercados e cesta básica tem diferença de R$ 396 (Procon Lages), 3 set. 2026. https://ndmais.com.br/economia/pesquisa-do-procon-encontra-variacao-de-ate-749-nos-precos-de-supermercados-e-cesta-basica-tem-diferenca-de-r-396/
- **[14]** INFOMONEY. Dependendo do tamanho da embalagem, preço de produto pode triplicar (pesquisa Idec), 24 jun. 2009. https://www.infomoney.com.br/mercados/dependendo-do-tamanho-da-embalagem-preco-de-produto-pode-triplicar/
- **[15]** BRASIL. Lei nº 13.175, de 21 de outubro de 2015. Altera a Lei nº 10.962/2004 para obrigar a informação do preço por unidade de medida.
- **[16]** CADA MINUTO. Procon autua supermercados por práticas abusivas em Maceió, 20 fev. 2025. https://www.cadaminuto.com.br/noticia/2025/02/20/procon-autua-supermercados-por-praticas-abusivas-em-maceio
- **[17]** TRIBUNA DE JUNDIAÍ. Supermercados têm mesmo novas regras em 2026? Veja o que mudou e quais direitos já existiam, 2026. https://tribunadejundiai.com.br/mais/brasil/supermercados-novas-regras-2026-direitos/
- **[18]** BRASIL. Ministério da Justiça e Segurança Pública. Portaria nº 392, de 29 de setembro de 2021 (informação sobre redução de quantidade em embalagens).
- **[19]** IDEC. Reduflação: pode um produto diferente ou menor com embalagem igual? https://idec.org.br/dicas-e-direitos/reduflacao-pode-um-produto-diferente-ou-menor-com-embalagem-igual
- **[20]** DIÁRIO DO NORDESTE. Reduflação de produtos não segue lei e consumidores denunciam embalagens "enganosas"; veja direitos, 2022. https://diariodonordeste.verdesmares.com.br/negocios/reduflacao-de-produtos-nao-segue-lei-e-consumidores-denunciam-embalagens-enganosas-veja-direitos-1.3293136
- **[21]** HOJE EM DIA. Desperdício de alimentos chega a R$ 1 mil por família por ano, diz Embrapa (pesquisa Embrapa/FGV, 2018). https://www.hojeemdia.com.br/economiaefinancas/desperdicio-de-alimentos-chega-a-r-1-mil-por-familia-por-ano-diz-embrapa-1.717638
- **[22]** PORPINO, G. Material de Gustavo Porpino (Embrapa) sobre desperdício de alimentos nos lares brasileiros. Biblioteca Digital Jurídica do STJ. https://bdjur.stj.jus.br/jspui/bitstream/2011/155327/Gustavo_Porpino.pdf
- **[23]** O PRESENTE RURAL. Mundo joga fora mais de um bilhão de refeições por dia, diz ONU (dados PNUMA, *Food Waste Index Report 2024*). https://opresenterural.com.br/mundo-joga-fora-mais-de-um-bilhao-de-refeicoes-por-dia-diz-onu/
- **[24]** IDEC. Estudo UFMG/Idec sobre a evolução dos preços de ultraprocessados e de alimentos in natura (2018-2024), 5 nov. 2025. https://idec.org.br/node/31258
- **[25]** GAZETA SP. Alimentos saudáveis disparam de preço e ultraprocessados ficam baratos. https://www.gazetasp.com.br/economia/arroz-feijao-e-frutas-devem-ficar-mais-caros-ate-2026-veja-precos/
- **[26]** BRASIL. Ministério da Saúde. *Guia Alimentar para a População Brasileira*. 2. ed. Brasília, 2014.
- **[27]** CFN. ONU e governo brasileiro ensinam 10 passos simples para uma alimentação saudável. https://cfn.org.br/onu-e-governo-brasileiro-ensinam-10-passos-simples-para-uma-alimentacao-saudavel/
- **[28]** JORNAL DE BRASÍLIA. Insegurança alimentar grave persiste no DF, aponta levantamento (dados ObservaDF/UnB e IBGE/PNAD Contínua 2024), 17 jun. 2026. https://jornaldebrasilia.com.br/brasilia/inseguranca-alimentar-grave-persiste-no-df-aponta-levantamento/
- **[29]** CORREIO BRAZILIENSE. Na contramão do Brasil, DF tem aumento na insegurança alimentar (dados IBGE/PNAD Contínua: Segurança Alimentar 2024), out. 2025. https://www.correiobraziliense.com.br/cidades-df/2025/10/7268826-na-contramao-do-brasil-df-tem-aumento-na-inseguranca-alimentar.html
- **[30]** MONITOR MERCANTIL. Mulheres dedicam o dobro de horas dos homens a afazeres domésticos (dados IBGE/PNAD Contínua: Outras Formas de Trabalho). https://monitormercantil.com.br/mulheres-dedicam-o-dobro-de-horas-dos-homens-a-afazeres-domesticos/
- **[31]** SANTOS, G. M. G. C. et al. Barreiras percebidas para o consumo de frutas e de verduras ou legumes em adultos brasileiros. *Ciência & Saúde Coletiva*, v. 24, n. 7, 2019. DOI 10.1590/1413-81232018247.19992017. http://www.scielo.br/j/csc/a/LSm9mRVdJnBCpF7zvPXxsSP/?lang=pt
- **[32]** UNICEF. Estudo inédito do UNICEF aponta alto consumo de alimentos ultraprocessados em lares atendidos pelo Bolsa Família, 16 dez. 2021. https://www.unicef.org/brazil/comunicados-de-imprensa/estudo-inedito-do-unicef-aponta-alto-consumo-de-alimentos-ultraprocessados-em-lares-atendidos-pelo-bolsa-familia
- **[33]** GALVÃO; DINIZ. Ambiente alimentar na SCIA-Estrutural (DF). *Cadernos de Agroecologia*. https://cadernos.aba-agroecologia.org.br/cadernos/article/download/8993/6657/33730
- **[34]** BRASIL. MDS; USP. *Desertos e Pântanos Alimentares*: relatório, 2024. https://cms.revistaforum.com.br/u/archivos/2025/1/28/Relatório%20-%20Desertos%20e%20Pântanos%20Alimentares.pdf
- **[35]** Food environment in Brazil: food deserts and food swamps in large urban cities. *Revista de Saúde Pública*. https://scielo.br/j/rsp/a/jYmdChpKNPgyFr8SDwQCHmF/?lang=en
- **[36]** JORNAL DE BRASÍLIA. Mais ricos frequentam mais lojas e fazem mais esporte (dados IPEDF). https://jornaldebrasilia.com.br/blogs-e-colunas/do-alto-da-torre/mais-ricos-frequentam-mais-lojas-e-fazem-mais-esporte/
- **[37]** TELETIME. TIC Domicílios 2025 aponta que 50 milhões de brasileiros já usam IA, 9 dez. 2025. https://teletime.com.br/09/12/2025/tic-domicilios-2025-aponta-que-50-milhoes-de-brasileiros-ja-usam-ia/
- **[38]** CETIC.BR. *TIC Domicílios 2025*: resumo executivo. https://www.cetic.br/media/docs/publicacoes/2/pt-br/20260511173151/tic_domicilios_2025_resumoexecutivo%20pt.pdf
- **[39]** MOBILE TIME. 50 milhões de brasileiros usam IA generativa, aponta TIC Domicílios 2025, 9 dez. 2025. https://www.mobiletime.com.br/noticias/09/12/2025/50-mi-ia-generativa-tic-domicilios-2025/
- **[40]** CANALTECH. Um a cada três brasileiros já usa IA generativa, aponta pesquisa (dados TIC Domicílios 2025). https://canaltech.com.br/inteligencia-artificial/um-a-cada-tres-brasileiros-ja-usa-ia-generativa-aponta-pesquisa/
- **[41]** CONFAZ. Convênio de Cooperação Técnica ICMS nº 3, de 27 de setembro de 2019 (aplicativo Menor Preço Brasil). https://www.legisweb.com.br/legislacao/?id=382945
- **[42]** BEM PARANÁ. Aplicativo que permite pesquisa de 29 milhões de preços ajuda a economizar na Black Friday (Menor Preço / Nota Paraná). https://www.bemparana.com.br/consumidor/aplicativo-que-permite-pesquisa-de-29-milhoes-de-precos-ajuda-a-economizar-na-black-friday/
- **[43]** ARAUJO, A. C. *LudiiPrice*: aplicativo de comparação de preços a partir do QR code de cupons fiscais. Trabalho de Conclusão de Curso, UFS. https://ri.ufs.br/bitstream/riufs/15903/2/Adan_Cordeiro_Araujo.pdf
- **[44]** MOBILLS. Melhores aplicativos de lista de compras (blog). https://www.mobills.com.br/blog/aplicativo-de-lista-de-compras/
- **[45]** MEU TUDO. Aplicativo de lista de compras: conheça algumas opções (blog). https://meutudo.com.br/blog/aplicativo-lista-de-compras/
- **[46]** GRATE. Best Recipe App in 2026: 8 Apps for Saving, Organizing, and Cooking (blog). https://grate-six.vercel.app/blog/best-recipe-app
- **[47]** 9TO5GOOGLE. Whisk is now Samsung Food, 30 ago. 2023. https://9to5google.com/2023/08/30/whisk-samsung-food-app-rebrand/
- **[48]** APP STORE. Grocery AI (Pocket Labs): página do aplicativo. https://apps.apple.com/ca/app/grocery-ai/id1544118181
- **[49]** APP STORE. Grocery List: Budget App (EasyGrocery): página do aplicativo. https://apps.apple.com/app/id6741698303
- **[50]** CANALTECH. Aplicativos para economizar no mercado. https://canaltech.com.br/apps/aplicativos-para-economizar-no-mercado/
- **[51]** IPEDF. *Pesquisa Distrital por Amostra de Domicílios (PDAD) 2021*: apresentação da região Sul. https://ipe.df.gov.br/documents/9915964/10216206/PDAD_2021-Apresentacao_Sul.pdf
- **[52]** IPEDF/Codeplan. *PDAD*: relatório da Região Administrativa do Gama. https://ipe.df.gov.br/documents/9915964/10215637/Gama.pdf
- **[53]** *From Recognition to Reasoning: Benchmarking and Enhancing MLLMs on Real-World Receipt Document Understanding* (ReceiptBench). arXiv:2603.11442, 2026. https://arxiv.org/pdf/2603.11442
- **[54]** MICROSOFT Q&A. Request for GPU-Enabled VM Quota Increase for Azure Students. https://learn.microsoft.com/en-us/answers/questions/2141487/request-for-gpu-enabled-vm-quota-increase-for-azur
- **[55]** MICROSOFT Q&A. Azure for Students: unable to deploy any Azure OpenAI model in Azure AI Foundry. https://learn.microsoft.com/en-us/answers/questions/5949792/azure-for-students-unable-to-deploy-any-azure-open
