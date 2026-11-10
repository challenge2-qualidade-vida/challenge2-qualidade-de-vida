# Semana 2 — Avaliação do RAG: base de 7 para 20 fontes

Este documento registra como o RAG do Miau-ricio é avaliado, quais documentos entraram para a base chegar a 20 fontes e o que mudou com eles. A medição foi feita **antes e depois** da ampliação, com o mesmo conjunto de perguntas, o mesmo modelo de embeddings, o mesmo limiar e o mesmo LLM, para que a única diferença seja a base. Spec: [specs/16-ampliar-base-conhecimento](../../specs/16-ampliar-base-conhecimento/spec.md).

## 1. Resumo

| | Antes (7 fontes, 4.346 trechos) | Depois (20 fontes, 6.151 trechos) | Diferença |
| --- | --- | --- | --- |
| **Recall@5** (o trecho certo está entre os 5 primeiros) | 0,50 | **0,83** | +0,33 |
| **MRR** (quão alto aparece o primeiro trecho certo) | 0,44 | **0,76** | +0,33 |
| **Acurácia do comportamento** (respondeu, recusou ou avisou quando devia) | 40% | **48%** | +7,5 p.p. |
| **Taxa de resposta** (entre as que deviam ser respondidas) | 26% | **35%** | +9,3 p.p. |
| Recusa correta (RN11) | 100% | 100% | 0 |
| Aviso de preço (RN04) | 100% | 100% | 0 |
| Fonte esperada citada (entre as respondidas) | 86% | 84% | −1,5 p.p. |

**O que os números dizem:**

1. **A busca melhorou muito.** As 6 categorias que dependiam dos documentos novos saíram de Recall@5 0 (ou 0,5) para 0,6 a 1,0, sem piorar receitas nem conservação.
2. **A resposta final melhorou pouco, e o gargalo agora é o LLM.** Depois da ampliação, 32 das 35 perguntas que deviam ser respondidas e não foram tinham trechos acima do limiar. O `qwen2.5:7b` respondeu `NAO_ENCONTRADO` ou escreveu sem citar os trechos, e a resposta foi descartada pela RN10. Só 3 caíram por falta de trecho relevante.
3. **O gargalo do LLM foi resolvido com a resposta estruturada** (seção 6): com o prompt v2 em JSON, a acurácia vai a 91%, e a 93% com a busca por ingrediente, mantendo 100% de recusa correta e de aviso de preço.
4. **A TACO como texto é arriscada.** A busca acha a tabela certa em 5 de 5 perguntas, mas o LLM leu a coluna errada: disse que o ovo cozido tem 2,9 g de proteína (o certo é 13,3 g; 2,9 g é o teor de gordura saturada, em outra tabela). Isso reforça a #22: dados nutricionais devem vir de consulta estruturada, não do LLM.

## 2. Como a avaliação funciona

### Conjunto de perguntas v2

`data/avaliacao/perguntas_rag_v2.json`, com **67 perguntas**: as 26 da v1, mantidas para comparar com os resultados antigos, e 41 novas. Cada pergunta tem uma categoria e um **comportamento esperado**:

- `responder`: a pergunta tem gabarito, com os documentos (e, no Guia, as seções) que deveriam aparecer;
- `nao_encontrar`: a base não tem a informação, e o sistema deve dizer que não encontrou (RN11);
- `aviso_de_preco`: pergunta sobre preço atual, que deve receber o aviso da RN04 sem passar pela base.

| Categoria | Perguntas | O que testa |
| --- | --- | --- |
| `receita_pt` | 8 | Receitas brasileiras do afrodite.json |
| `receita_entre_idiomas` | 5 | Pergunta em português, receita em inglês (RecipeNLG) |
| `guia_alimentar` | 6 | Guia Alimentar para a População Brasileira |
| `conservacao` | 6 | Embrapa e "Na cozinha com as FLV" |
| `nutricao` | 5 | TACO (calorias, proteína, fibra) |
| `alimentacao_infantil` | 5 | Guia para menores de 2 anos |
| `desperdicio` | 4 | Campanha de redução de desperdício, aproveitamento integral, perdas de FLV |
| `seguranca_alimentar` | 5 | IFC, higiene em serviços de alimentação, rastreabilidade |
| `orientacao_nutricional` | 2 | Ultraprocessados, protocolo do Guia |
| `comportamento_alimentar` | 3 | Pandemia, comensalidade, ambiente escolar |
| `robustez` | 5 | Erros de digitação e linguagem informal ("oq da pra fazer c/ couve flor") |
| `sem_resposta` | 10 | Fora da base, incluindo armadilhas perto do domínio ("calorias de um Big Mac", "geladeira que não gela") |
| `preco` | 3 | Preço atual (RN04) |

**Regra usada para montar o gabarito:** os ids dos documentos novos foram definidos **antes** da indexação, e cada pergunta nova foi conferida no texto do PDF. Assim, a linha de base mostra exatamente o que a base antiga não cobria. O gabarito **não foi ajustado depois** de ver os resultados, para não enviesar a comparação (ver a g01 na seção 5).

### Métricas

**Recuperação** (comando `comparar`): busca o top-5 de cada pergunta, sem limiar.

- **Recall@5:** fração das perguntas com resposta em que algum trecho do gabarito está no top-5.
- **MRR:** média de 1/posição do primeiro trecho certo (1 se é o primeiro, 0,5 se é o segundo, 0 se não aparece).
- **Separação:** menor score das perguntas com resposta menos o maior score das sem resposta. Negativa quer dizer que nenhum limiar separa os dois grupos sem erro.
- Tudo também **por categoria**. As perguntas de preço ficam de fora, porque não passam pela busca.

**Resposta** (comando `avaliar-respostas`): roda o caso de uso completo (RN04, busca, limiar, desempate, LLM e montagem das fontes) em cada pergunta.

- **Acurácia do comportamento:** o comportamento obtido é igual ao esperado.
- **Taxa de resposta:** entre as que deviam ser respondidas, quantas foram.
- **Recusa correta:** entre as sem resposta, quantas disseram que não encontraram.
- **Aviso de preço:** entre as de preço, quantas receberam o aviso.
- **Fonte esperada citada:** entre as respondidas que têm gabarito, quantas citaram um documento dele.
- **Falsas recusas e respostas indevidas:** a lista de ids de cada erro, para investigar.

**Reprodutibilidade:** na avaliação, o LLM roda com **temperatura 0 e semente 42**. Com a temperatura padrão (0,2) e sem semente, a mesma pergunta mudava de resultado entre duas execuções. Com a semente fixa, repetir as 30 primeiras perguntas deu o mesmo resultado nas 30.

### Como rodar

Com o Qdrant e o Ollama no ar, na pasta do projeto:

```bash
# recuperação (cerca de 10 s)
poetry run python -m economia.receitas.cli comparar --modelos e5 --saida data/avaliacao/v2/recuperacao_<rotulo>.json

# resposta completa (de 3 a 5 min com GPU; na CPU, de 30 a 60 min)
poetry run python -m economia.receitas.cli avaliar-respostas --saida data/avaliacao/v2/respostas_<rotulo>.json

# só algumas categorias, ou as N primeiras perguntas
poetry run python -m economia.receitas.cli avaliar-respostas --categorias nutricao preco --saida /tmp/teste.json

# comparar duas execuções do mesmo tipo
poetry run python -m economia.receitas.cli comparar-execucoes data/avaliacao/v2/respostas_antes.json data/avaliacao/v2/respostas_depois.json
```

Os resultados desta comparação estão em `data/avaliacao/v2/` (`recuperacao_antes.json`, `recuperacao_depois.json`, `respostas_antes.json` e `respostas_depois.json`), com a resposta de cada pergunta, para quem quiser conferir uma a uma.

## 3. Escolha dos documentos

O catálogo da `chore/16-base-conhecimento` (Isabel) tem 21 documentos com licença conferida. Um deles, o "Na cozinha com as FLV", já estava na base. Para chegar a 20 fontes, faltavam 13.

**Critérios de impacto para o Miau-ricio** (pessoa que planeja as compras e cozinha em casa):

1. Responde perguntas que as personas fariam: o que cozinhar, como guardar, como alimentar a família, quanto de cada nutriente.
2. Cobre um tema que a base não tinha: crianças pequenas, nutrição, desperdício, segurança dos alimentos.
3. Tem texto extraível do PDF.
4. Fica fora: estudos sobre processos industriais e textos sobre programas institucionais que não ajudam a decisão doméstica.

| # | Documento | Decisão | Motivo |
| --- | --- | --- | --- |
| 1 | Guia Alimentar para Crianças Menores de 2 Anos (MS, 2019) | **Entrou** | Alimentação da família com bebês; tema ausente na base |
| 2 | Protocolo do Guia Alimentar para adultos (MS e USP, 2021) | **Entrou** | Traduz o Guia em orientações práticas |
| 3 | Laboratório de Inovação FLV (OPAS, 2022) | **Entrou** | Acesso e perdas de frutas, legumes e verduras |
| 4 | Percepção do consumidor sobre riscos e rastreabilidade (BJFT, 2013) | **Entrou** | Segurança dos alimentos do ponto de vista do consumidor |
| 5 | Trajetória das políticas de educação alimentar (TES, 2024) | Fora | Servidor da revista TES fora do ar no download |
| 6 | Desafios para uso do Guia na prática profissional (TES, 2025) | Fora | Servidor da revista TES fora do ar no download |
| 7 | Alimentos ultraprocessados e seus riscos (RACA, 2022) | **Entrou** | Complementa o Guia num tema central |
| 8 | Consumo alimentar e a pandemia (RACA, 2024) | **Entrou** | Comportamento alimentar das famílias |
| 9 | Pandemia e comensalidade (RACA, 2024) | **Entrou** | Comportamento alimentar das famílias |
| 10 | Ambiente escolar e práticas alimentares familiares (RACA, 2023) | **Entrou** | Relação entre escola e alimentação em casa |
| 11 | Alimentação escolar (PNAE) na pandemia (RACA, 2023) | Fora | Política institucional, sem uso na decisão doméstica |
| 12 | Consumo alimentar sustentável na alimentação escolar (TES, 2015) | Fora | Servidor da revista TES fora do ar no download |
| 13 | Food Safety Handbook (IFC, 2020) | **Entrou, só o capítulo 3** | Perigos, APPCC e temperaturas. O manual inteiro gerava 1.079 trechos, a maior parte de normas e formulários para empresas; o capítulo 3 gera 411 |
| 14 | Coberturas comestíveis em frutas (BJFT, 2014) | Fora | Tecnologia industrial |
| 15 | Microfiltração de leite pasteurizado (BJFT, 2014) | Fora | Processo industrial |
| 16 | Pirarucu estocado em gelo (BJFT, 2014) | Fora | Estudo muito específico, de pouco uso doméstico |
| 17 | Higiene em serviços de alimentação, NBR 15635 (BJFT, 2012) | **Entrou** | Boas práticas de higiene |
| 18 | Práticas de higiene em serviços de alimentação (RACA, 2019) | **Entrou** | Boas práticas de higiene |
| 19 | Na cozinha com as FLV (MS e UFMG, 2016) | Já estava | — |
| 20 | TACO, 4ª edição (NEPA/Unicamp, 2011) | **Entrou** | Pedido da equipe; ver a limitação na seção 5 |
| 21 | Campanha para redução de desperdício (Cadernos Saúde Coletiva, 2022) | **Entrou** | Desperdício, tema central do EconoMIA |

Fontes, licenças e links: [data/base-conhecimento/FONTES.md](../../data/base-conhecimento/FONTES.md).

## 4. Resultados

### Recuperação por categoria

| Categoria | Recall@5 antes | Recall@5 depois | MRR antes | MRR depois |
| --- | --- | --- | --- | --- |
| alimentacao_infantil | 0,00 | **1,00** | 0,00 | **1,00** |
| comportamento_alimentar | 0,00 | **1,00** | 0,00 | **1,00** |
| nutricao | 0,00 | **1,00** | 0,00 | **1,00** |
| seguranca_alimentar | 0,00 | **0,60** | 0,00 | **0,50** |
| desperdicio | 0,50 | **1,00** | 0,31 | **1,00** |
| orientacao_nutricional | 0,50 | **1,00** | 0,50 | **1,00** |
| conservacao | 1,00 | 1,00 | 1,00 | 1,00 |
| receita_pt | 0,88 | 0,88 | 0,69 | 0,69 |
| robustez | 0,80 | 0,80 | 0,80 | 0,80 |
| receita_entre_idiomas | 0,20 | 0,20 | 0,05 | 0,05 |
| guia_alimentar | 1,00 | 0,83 | 0,92 | 0,67 |

### Resposta por categoria (acurácia do comportamento)

| Categoria | Antes | Depois |
| --- | --- | --- |
| alimentacao_infantil | 0% | **60%** |
| comportamento_alimentar | 0% | **67%** |
| desperdicio | 25% | **75%** |
| orientacao_nutricional | 50% | **100%** |
| seguranca_alimentar | 0% | **40%** |
| nutricao | 0% | 20% |
| sem_resposta | 100% | 100% |
| preco | 100% | 100% |
| receita_entre_idiomas | 20% | 20% |
| receita_pt | 50% | 38% |
| conservacao | 33% | 17% |
| robustez | 40% | 20% |
| guia_alimentar | 50% | 0% |

- **Passaram a acertar (12):** r07, n02, i01, i04, i05, d01, d02, h01, h03, u01, p01, p03.
- **Deixaram de acertar (7):** r05, r08, g01, g04, c03, g06, b04.

Das 7 que pioraram, 6 têm o trecho certo no top-5 nas duas execuções; o que mudou foi o conjunto de trechos que o LLM recebeu, e ele passou a não citar. Ou seja, as perdas vêm da instabilidade do LLM, não da busca.

## 5. Achados e limitações

1. **O LLM é o gargalo.** Na execução "depois", 32 das 35 falsas recusas tinham trechos acima do limiar. Ou o `qwen2.5:7b` respondeu `NAO_ENCONTRADO`, ou escreveu a resposta sem `[n]`, e o código descarta resposta sem citação (RN10). Isso já aparecia na v1 e piorou o Guia Alimentar: com mais documentos parecidos no top-5 (Guia adulto, Guia infantil, protocolo), o modelo hesita mais. **É a próxima melhoria de maior impacto**: ajustar o prompt, testar um modelo maior ou decidir o que fazer com uma resposta sem citação.
2. **A TACO só serve para achar a tabela, não para ler o número.** A busca acertou as 5 perguntas de nutrição. Das respostas, 4 foram recusadas e a 1 respondida tinha **valor errado** (2,9 g de proteína no ovo cozido, contra 13,3 g na tabela). Dividida por página, a tabela perde a ligação entre os números e as colunas. Os valores nutricionais devem vir da consulta estruturada da #22, como cálculo determinístico (RN01).
3. **Receitas entre idiomas seguem fracas** (Recall@5 de 0,20, igual antes e depois). As receitas do afrodite.json com nomes parecidos ocupam o top-5. Vale testar a busca separada por idioma ou o `qwen3-embedding`.
4. **A margem do limiar diminuiu.** Os documentos novos subiram o score de 6 das 10 perguntas sem resposta. A s10 ("imposto de renda") foi de 0,818 para 0,845, exatamente o limiar. A s07 ("geladeira que não gela") já estava acima dele (0,852) antes e continua. A recusa continuou em 100% porque o LLM recusou, não porque o limiar barrou. Vale recalibrar o limiar com o conjunto v2 (o `comparar` sugere 0,846).
5. **Segurança dos alimentos citou outras fontes.** A h01 (temperatura da geladeira) e a h03 (higiene) foram respondidas com o Guia adulto e o Guia infantil, e não com a IFC ou os artigos de higiene. As respostas fazem sentido, mas o gabarito esperava outro documento.
6. **Gabarito estrito na g01.** "O que são ultraprocessados" passou a trazer o Guia infantil e o artigo da RACA sobre ultraprocessados, que também respondem à pergunta. Como o gabarito só aceita seções do Guia adulto, a pergunta conta como erro de busca. O gabarito foi mantido, para não ajustar a medida ao resultado; numa v3, vale aceitar os documentos novos.
7. **Licenças.** Todas as fontes novas são CC BY, CC BY-NC-SA ou de reprodução livre com citação. Para o uso acadêmico, servem. Para um produto comercial, as NC precisam ser trocadas.

## 6. Redação da resposta: o que corrigiu o gargalo do LLM

A seção 5 mostrou que a maior parte das falhas vinha do LLM: ele respondia sem citar os trechos, e a resposta era descartada pela RN10. Três mudanças foram testadas na base de 20 fontes, uma de cada vez, com o mesmo conjunto de 67 perguntas:

1. **Segunda tentativa** (`pedido_de_citacao_v1`): se a resposta vem sem `[n]`, o LLM recebe a própria resposta e o pedido de reescrever citando. Só uma vez.
2. **Resposta estruturada**: o LLM devolve um JSON `{encontrou, resposta, trechos_usados}`. O Ollama restringe a saída ao esquema, e a lista dos trechos usados não depende de o modelo lembrar dos colchetes.
3. **Prompt v2** (`resposta_com_fontes_v2`): pede o JSON, mostra um exemplo e diz que uma resposta parcial ainda é uma resposta (`encontrou: false` só quando nenhum trecho tem relação com a pergunta).

Depois, a **busca por ingrediente**: quando a pergunta lista 2 ou mais ingredientes, além da busca geral, o sistema busca "Receita com <ingrediente>" só entre as receitas e garante pelo menos uma por ingrediente. Ela resolveu uma pergunta real que voltava "não encontrei": "quero fazer um almoço completo com arroz, feijão, carne e alface".

| Configuração | Acurácia | Taxa de resposta | Recusa correta | Aviso de preço | Fonte esperada | Latência média |
| --- | --- | --- | --- | --- | --- | --- |
| v1, texto livre (referência) | 48% | 35% | 100% | 100% | 84% | 2,9 s |
| v1 + segunda tentativa | 72% | 65% | 100% | 100% | 83% | 3,1 s |
| **v2 estruturada** | **91%** | **89%** | 100% | 100% | 77% | 2,5 s |
| v2 estruturada + segunda tentativa | 91% | 89% | 100% | 100% | 77% | 2,2 s |
| v2 estruturada + segunda tentativa + busca por ingrediente | **93%** | **91%** | 100% | 100% | 73% | 2,5 s |

**Leitura:**

- A **resposta estruturada com o prompt v2** é o que resolve: a acurácia vai de 48% para 91%, sem perder nenhuma recusa correta (RN11) nem aviso de preço (RN04). Com ela, a segunda tentativa nunca foi acionada, porque o modelo sempre devolveu a lista de trechos. Ela fica como proteção barata, já que só custa quando é usada.
- Só a segunda tentativa, sem mudar o prompt, já sobe a acurácia de 48% para 72%.
- A **fonte esperada citada cai** (84% para 73%) porque o sistema passa a responder mais. Nas receitas em inglês, por exemplo, ele responde com uma receita parecida do afrodite.json em vez da do gabarito. A resposta é útil, mas não é a que o gabarito esperava.
- A busca por ingrediente quase não muda o conjunto v2 (+1,5 ponto), porque ele quase não tem pedidos de refeição com vários ingredientes. Uma v3 do conjunto deve incluir esse tipo de pergunta.

**O que a avaliação não mede, e os erros que apareceram:** a acurácia confere o comportamento (respondeu, recusou ou avisou) e a fonte citada, não se cada frase é fiel ao trecho. Conferindo à mão as respostas da v2, apareceram números errados:

- ovo cozido com 2,9 g de proteína (a TACO diz 13,3 g; 2,9 g é a gordura saturada);
- feijão carioca com 62,92 g de fibra em 100 g (a TACO diz 8,5 g);
- "comida refrigerada a no mínimo 70 °C" (70 °C é a temperatura de reaquecimento).

Responder mais aumenta a chance desse tipo de erro. Dois próximos passos tratam disso: tirar os números nutricionais do LLM (consulta estruturada da TACO, #22) e medir a fidelidade (faithfulness, #29).

**Na tela de perguntas** ([spec 24](../../specs/24-endpoint-rag/spec.md)), a configuração vem do `.env`. O padrão do código continua a v1 até a equipe decidir (ver `docs/decisoes.md`). Para usar a melhor configuração medida:

```bash
PROMPT_DE_RESPOSTA=resposta_com_fontes_v2
RESPOSTA_ESTRUTURADA=true
SEGUNDA_TENTATIVA_DE_CITACAO=true
```

Para repetir a comparação:

```bash
poetry run python -m economia.receitas.cli avaliar-respostas --prompt resposta_com_fontes_v2 --estruturada --segunda-tentativa --saida data/avaliacao/v2/respostas_teste.json
poetry run python -m economia.receitas.cli comparar-execucoes data/avaliacao/v2/respostas_depois.json data/avaliacao/v2/respostas_teste.json
```

## 7. Ambiente da medição

- Linux x86_64, 16 CPUs lógicas.
- Ollama 0.40 com `qwen2.5:7b`, contexto de 8.192 tokens, temperatura 0, semente 42.
- Embeddings `intfloat/multilingual-e5-base` na CPU, Qdrant 1.20, limiar 0,845, top-5.
- Medição de 10/11/2026.
