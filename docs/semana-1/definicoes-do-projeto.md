# Semana 1 — Definições do projeto

## 1. Essential Question

> **"Tenho R$ X para as compras do mês. Como faço esse dinheiro render sem perder qualidade na alimentação?"**

Deriva da Big Idea do desafio: empoderar pessoas com IA para compreender melhor, decidir melhor e viver melhor.

## 2. Problema

- **Contexto:** comida pesa no orçamento das famílias, e os preços mudam muito de um mercado e de um mês para outro. Comparar preço por quilo, nutrição e deslocamento ao mesmo tempo é difícil sem ajuda.
- **Quem sofre com o problema:** famílias com orçamento apertado, principalmente as de renda de até um salário mínimo por pessoa.
- **Por que é importante:** economizar sem critério pode significar comer pior, e comprar sem planejar gera desperdício.

**Evidências:**

| Evidência | Dado | Fonte |
|-----------|------|-------|
| Peso da comida na renda | Em setembro de 2026, a cesta básica de Brasília custou **R$ 773,78**, ou **51,61% do salário mínimo líquido** (105 horas de trabalho) | [Conab/DIEESE](https://www.dieese.org.br/analisecestabasica/2026/202609cestabasica.pdf) |
| Preços instáveis | Em Brasília, em 12 meses: tomate +66%, feijão carioca +48%, batata +84%; café −21% | Conab/DIEESE, idem |
| Falta de acesso | **24,2%** dos domicílios brasileiros tinham insegurança alimentar em 2024 (3,2% em nível grave). No Centro-Oeste, 20,5% | [IBGE, PNAD Contínua](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102212_informativo.pdf) |
| Preço varia entre mercados | Em 6 supermercados de uma mesma cidade da Região 1 (Anápolis), a banana variou de R$ 3,99 a R$ 7,69 o kg (93%), e o pão francês, 62% | [Procon Anápolis, março/2026](https://www.anapolis.go.gov.br/wp-content/uploads/2026/03/plan-e-rel-cesta-basica-26..pdf) |
| Comida saudável não é necessariamente mais cara | No Brasil, o custo total de uma alimentação baseada em alimentos in natura ou minimamente processados ainda é menor que o de uma baseada em ultraprocessados | [Guia Alimentar, Ministério da Saúde](https://bvsms.saude.gov.br/bvs/publicacoes/guia_alimentar_populacao_brasileira_2ed.pdf) |

> **Sobre o DF:** a imprensa citou 27% de domicílios com insegurança alimentar em 2024, com base no IBGE ([Correio Braziliense](https://www.correiobraziliense.com.br/cidades-df/2025/10/7268826-na-contramao-do-brasil-df-tem-aumento-na-inseguranca-alimentar.html)). As reportagens divergem sobre o valor de 2023, e a Sedes-DF pediu cautela por causa da amostra. Por isso, esse número não é usado como dado principal.

**O que os apps atuais não resolvem:** há comparadores de preço e contadores de calorias, mas falta juntar preço, orçamento e nutrição em uma só decisão.

## 3. Stakeholders

| Stakeholder | Interesse / necessidade | Como é afetado pela solução |
|-------------|-------------------------|-----------------------------|
| Famílias com orçamento apertado | Fazer o dinheiro render sem comer pior | Recebem uma cesta possível, com critérios explicados |
| Pessoas pouco familiarizadas com tecnologia | Usar sem cadastro e sem jargão | Interface de celular, conversa em português, sem login |
| Pessoas com restrições alimentares | Ter restrições respeitadas | A cesta nunca inclui o que foi excluído. O app avisa que não substitui nutricionista |
| Nutricionistas e profissionais de saúde | Que a orientação não prejudique quem precisa de dieta específica | O app recusa perguntas de saúde e indica o profissional |
| Mercados | Preços apresentados corretamente | Todo preço mostra origem e data; nenhum mercado é favorecido sem critério |
| Consumidores que enviam cupons | Colaborar sem expor dados | O CPF não é lido, e a pessoa confere os itens antes de salvar |
| Banca e grupo do desafio | Solução justificada e medida | Decisões, métricas e limitações documentadas |

## 4. Decisão que a IA vai apoiar

**Apoia:** o que comprar, em quantos mercados e como aproveitar os alimentos, dentro do orçamento.

**A IA não decide sozinha:**

- O usuário escolhe orçamento e restrições, pode trocar qualquer item e decide se vai a um ou dois mercados.
- Preços e cálculos não vêm do LLM: vêm de código determinístico.
- Questões de saúde, dieta para doenças e alergias graves ficam com profissionais.
- Os preços de cupons só entram na base depois que a pessoa confere.

## 5. Riscos e limitações

| Risco | Impacto | Como mitigar |
|-------|---------|--------------|
| Respostas incorretas (alucinação) | Preço, nutriente ou recomendação inventados | Preço e cálculo em código; RAG; a Mia bloqueia fonte inventada; cardápio sem LLM depois de ele sugerir feijão cru |
| Preços desatualizados ou de exemplo | A cesta parece barata, mas custa mais | Origem e data em cada preço; aviso visível de preços de exemplo |
| Otimização enganosa | Cesta barata, mas pobre | Metas de energia, proteína, fibra e hortaliças, limite por alimento e mínimo de proteína animal |
| Viés nos dados ou no modelo | Base com poucos mercados e alimentos pode favorecer regiões e culturas alimentares | Comparar critérios explícitos; ampliar com a coleta e os cupons; declarar a limitação |
| Metas iguais para todos | Crianças, idosos e gestantes têm necessidades diferentes | O app avisa que considera adultos e é para a população geral; não substitui nutricionista |
| Privacidade / LGPD | Orçamento, hábitos e localização são sensíveis | Sem login; posição não gravada; dados só no aparelho, com botão para apagar; CPF não lido |
| Contribuição maliciosa de preços | Base colaborativa pode ser manipulada | Limite por IP, conferência humana e consulta à SEFAZ; ainda é uma limitação em uso público |

## 6. Métricas de sucesso

| Métrica | Como medir | Meta proposta |
|---------|-----------|---------------|
| Aderência ao orçamento | % de cestas dentro do limite | 100% |
| Adequação nutricional | % de cestas que cumprem as metas | 100% |
| Custo por 1.000 kcal e por g de proteína | Cesta × cesta de referência DIEESE | Menor que a referência |
| Economia sem perda de qualidade | % de economia com a mesma energia, cumprindo as metas | Medir com a coleta real |
| Qualidade dos dados | % de preços com fonte, data e até 30 dias | ≥ 90% |
| Precisão de preço | % de preços do app a ±5% da gôndola | ≥ 80%, depois da coleta |
| Qualidade das respostas | Correção com gabarito, LLM × LLM + RAG | RAG melhor que LLM sozinho |
| Utilidade percebida | % de testadores que dão 4 ou 5 e montam a cesta sozinhos | ≥ 70% |

> As metas numéricas são uma proposta para o grupo confirmar. Resultados: [semana 7](../semana-7/relatorio-final.md).

## 7. Fontes confiáveis

Lista completa em [FONTES.md](../../data/base-conhecimento/FONTES.md): Guia Alimentar (Ministério da Saúde), TACO (NEPA/Unicamp), IN 75/2020 (ANVISA), OMS, DIEESE/Conab, IBGE e Procon Anápolis.

## 8. Equipe e papéis

| Integrante | GitHub | Papel |
|------------|--------|-------|
| Guilherme Barros | [@dida0982](https://github.com/dida0982) | AI Engineering e frontend |
| Paulo Vitor Gomes | [@gpaulovit](https://github.com/gpaulovit) | AI Engineering e LLMOps |
| Isabel Azar | [@iAiBel](https://github.com/iAiBel) | Engenharia de dados e backend |
| Pedro Lucas Dourado | [@pedrolucasdourado](https://github.com/pedrolucasdourado) | Arquiteto de LLMOps |
| Mariah Gladys | [@necrophagial](https://github.com/necrophagial) | Scrum master e documentação |
