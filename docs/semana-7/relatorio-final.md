# EconoMIA — Relatório final

**Challenge 2 · Big Idea: Qualidade de Vida** · Residência em IA Brasília, Turma 2 · Grupo 3
Versão de 03/11/2026, com os resultados medidos até esta data.

## Resumo

A EconoMIA ajuda famílias a responder: *"Tenho R$ X para as compras do mês. Como faço esse dinheiro render sem perder qualidade na alimentação?"*. O app monta a cesta mais barata que cumpre metas nutricionais, compara um ou dois mercados, sugere o cardápio e explica cada escolha.

Em 160 cenários, **100% das cestas ficaram dentro do orçamento e cumpriram as metas**, a R$ 2,86 por 1.000 kcal, contra R$ 6,72 da referência DIEESE. No experimento com gabarito, a correção subiu de **59%** (LLM sozinho) para **94%** (agentes com RAG).

**A principal limitação:** o app ainda usa **preços de exemplo**, então os percentuais de economia não valem como promessa. Um teste com preços reais de outra cidade da mesma região manteve as conclusões, mas a coleta em Brasília e o teste com usuários ainda precisam ser feitos.

## 1. O problema

- A cesta básica de Brasília custou **R$ 773,78** em setembro de 2026: **51,61% do salário mínimo líquido** ([Conab/DIEESE](https://www.dieese.org.br/analisecestabasica/2026/202609cestabasica.pdf)).
- **24,2%** dos domicílios brasileiros tinham insegurança alimentar em 2024 ([IBGE](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102212_informativo.pdf)).
- Em 6 supermercados de Anápolis, na mesma região da cesta DIEESE que o DF, a banana variou 93% e o pão francês, 62% ([Procon Anápolis](https://www.anapolis.go.gov.br/wp-content/uploads/2026/03/plan-e-rel-cesta-basica-26..pdf)).

Stakeholders, decisão apoiada e o que a IA não decide: [definições da semana 1](../semana-1/definicoes-do-projeto.md).

## 2. A solução

| Etapa | O que o app faz |
|-------|-----------------|
| Orçamento | Recebe valor, pessoas, período, restrições e o que já há em casa |
| Cesta | Monta a opção mais barata que cumpre as metas; qualquer item pode ser trocado |
| Mercados | Compara um × dois mercados, com o deslocamento, e mostra os mais próximos |
| Cardápio | Sugere refeições só com o que está na cesta, usando antes o que estraga |
| Chat | Responde em português com agentes e RAG |
| Cupom | Lê o QR code da NFC-e, consulta a SEFAZ-DF e a pessoa confere antes de salvar |

### Arquitetura e decisões técnicas

**Princípio: o LLM conversa, e as contas ficam com o código.** Todas as ferramentas são gratuitas. A lista completa de justificativas está em [decisoes.md](../decisoes.md).

| Componente | Escolha | Por quê |
|------------|---------|---------|
| Otimizador | Programação linear inteira (SciPy/HiGHS) | Garante o menor custo e é auditável |
| RAG | TF-IDF (scikit-learn) | Base pequena e leve, sem baixar modelo |
| LLM | Ollama local (`qwen2.5:7b`); Groq ou Gemini na nuvem | Grátis; o local não envia dados para fora |
| Agentes | Orquestrador e Mia por regras; Cifrão e Miau-ricio com LLM | Rotear com LLM custaria de 5 a 15 s; quem verifica não pode errar como o verificado |
| Cardápio | Receitas cadastradas, sem LLM | O LLM sugeriu "feijão carioca cru" |
| Multimodalidade | QR code da NFC-e, não OCR | Dado oficial, sem erro de leitura |

## 3. Resultados

Os relatórios completos são gerados pelos scripts em [experimentos/](../../experimentos/).

### Métricas do projeto ([relatório](metricas.md))

160 cenários, com preços de exemplo:

| # | Métrica | Resultado |
|---|---------|-----------|
| 1 | Economia × referência DIEESE | 72,5% bruta; 57,0% com a mesma energia. **Não usar como promessa** |
| 2 | Aderência ao orçamento | **100%**; 68% dos cenários têm solução, e nos demais o app informa o mínimo necessário |
| 3 | Adequação nutricional | **100%** cumprem as metas e as restrições |
| 4 | Custo por 1.000 kcal / por g de proteína | **R$ 2,86 / R$ 0,111** (referência: R$ 6,72 / R$ 0,181) |
| 5 | Qualidade dos dados | 100% com data e fonte, mas **100% são de exemplo** |
| 6 | Precisão na gôndola | **Não medida** |
| 7 | Qualidade das respostas | A seguir |
| 8 | Utilidade percebida | **Não medida** |

**Por que a economia parece tão grande:** a referência tem 6 kg de carne por pessoa por mês e 155% da energia da meta, enquanto a cesta troca parte da carne por feijão, ovo e frango. A comparação favorece o app. Por isso, a métrica mais honesta é a 4.

### Experimento LLM × RAG ([relatório](../semana-3/resultados-llm-x-rag.md))

17 perguntas com gabarito, rodada de 03/11/2026:

| Critério | A: LLM sozinho | B: LLM + RAG | C: só regras | D: agentes (final) |
|----------|---------------|--------------|--------------|-------------------|
| Correção | 59% | 94% | 82% | **94%** |
| Conhecimento | 40% | 100% | 90% | **100%** |
| Saúde | 100% | 100% | 0% | **100%** |
| Informação ausente da base | 50% | 50% | 50% | **50%** |
| Fundamentação | 0% | 80% | 100% | **90%** |
| Latência | 11,1 s | 15,8 s | 0,0 s | **13,9 s** |
| Tokens por pergunta | 1.315 | 1.757 | 0 | **1.185** |

**Decisão:** usar RAG e agentes. **Ponto fraco:** só 50% de acerto quando a base não tem a resposta. A amostra é pequena, a correção é por palavras-chave e o modelo local varia entre rodadas: a fundamentação de D foi de 100% para 90% de uma rodada para outra.

### Sensibilidade a preços reais ([relatório](sensibilidade-precos.md))

Trocamos os preços de 12 dos 28 alimentos pelas médias reais do Procon Anápolis:

| Medida | Exemplo | Com preços reais |
|--------|---------|------------------|
| Dentro do orçamento e nas metas | 100% | **100%** |
| Cenários com solução | 109 de 160 | **144 de 160** |
| Custo por pessoa/dia | R$ 5,77 | **R$ 4,89** |
| Custo por 1.000 kcal (referência) | R$ 2,86 (R$ 6,72) | **R$ 2,41 (R$ 6,38)** |

O método resiste a preços reais, mas **estes não são preços do DF**, e 16 alimentos seguem com preço de exemplo.

### O que os testes mudaram

| Problema encontrado | Como apareceu | Correção |
|---------------------|---------------|----------|
| Cesta sem nenhuma proteína animal | Métricas | Meta de ≥ 20% da proteína |
| Aderência de 87% ao orçamento | Métricas | Deslocamento sai do orçamento |
| Fonte inventada pelo LLM | Experimento | Verificação da Mia |
| "Jantar: feijão carioca cru" | Teste de ponta a ponta | Cardápio por código |
| Leite atribuído à TACO, que não publica o valor | Conferência com o original | Fonte própria declarada |
| Frases atribuídas ao Guia sem respaldo | Conferência com o original | Texto corrigido ou removido |

**Testes automatizados:** 222 passando, sem chamar LLM nem internet. Eles não pegaram o erro do feijão cru porque usam um LLM falso; o erro apareceu no teste com o LLM real, e essa diferença é um aprendizado do projeto.

## 4. Riscos e limitações

| Risco | Situação |
|-------|----------|
| Preços | **Aberto:** mercados e preços do app são fictícios, com aviso na tela |
| Alucinação | Reduzido; ainda possível no chat, em texto que a Mia não sabe conferir |
| Nutrição | Metas para adultos da população geral; micronutrientes não são medidos diretamente. Não substitui nutricionista |
| Monotonia | A cesta mais barata pode repetir poucos alimentos e incluir açúcar até o limite de 10% da energia. É preciso ouvir usuários |
| Viés | Base de 28 alimentos e foco no DF; pode não representar outras culturas alimentares ou regiões |
| Privacidade | Sem login; posição e orçamento não vão para disco no servidor; CPF não é lido |
| Contribuição maliciosa | Limite por IP e conferência humana, sem moderação. Em uso público, seria preciso moderar |
| Disponibilidade | No plano gratuito do Render, o site dorme e as contribuições se perdem ao reiniciar |

## 5. O que falta, e depende do grupo

1. **Coletar preços** em 3 ou 4 mercados de Brasília, com a localização, e recalcular as métricas.
2. **Conferir 20 preços na gôndola** ([planilha](verificacao-gondola.csv)).
3. **Testar com 5 a 8 pessoas** ([roteiro](../desenvolvimento/11-metricas.md#métrica-8-utilidade-percebida-roteiro-de-teste-com-usuários)).
4. **Testar um cupom real** do DF.
5. **Publicar o site** ([guia](../desenvolvimento/12-publicacao.md)), o que exige a conta do grupo. A imagem Docker ainda não foi construída em nenhuma máquina.
6. **Revisar as receitas** e completar os integrantes e papéis no README.

## 6. Conclusão

O fluxo orçamento → cesta → comparação → cardápio funciona de ponta a ponta, e cada recomendação mostra critério e fonte. Medimos que separar o que é cálculo do que é conversa evita erros que o LLM cometeu na prática. Ainda não dá para afirmar quanto uma família de Brasília economizaria: essa resposta depende da coleta real e do teste com pessoas.
