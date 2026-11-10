# Semana 1 — Definições do projeto

## 1. Essential Question

_Qual pergunta específica, derivada da Big Idea "Qualidade de Vida", o grupo vai responder?_

Como podemos utilizar inteligência artificial para otimizar o orçamento de compras e reduzir o desperdício de alimentos por meio da gestão automatizada de inventário doméstico e rastreamento de preços locais?

## 2. Problema

- **Contexto:** Famílias e indivíduos enfrentam dificuldades para gerenciar o inventário de alimentos em casa e acompanhar as variações de preços nos supermercados locais, resultando em compras duplicadas, perdas financeiras e desperdício de comida.
- **Quem sofre com o problema:** Pessoas responsáveis pelas compras e pela gestão do orçamento doméstico diário.
- **Por que é importante:** Automatizar a entrada de dados (via OCR de notas fiscais) e monitorar os gastos maximiza o poder de compra e reduz o desperdício, impactando diretamente a estabilidade financeira e a qualidade de vida.
- **Evidências que mostram o problema (com fonte):** (dados do IBGE e/ou FAO sobre desperdício de alimentos no Brasil, sendo: IBGE/IPCA-15 biblioteca.ibge.gov+1
one.oecd
embrapa
Embrapa/FGV gov+1
https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/perdas-e-desperdicio-de-alimentos

citados no primeiro docs)

## 3. Stakeholders

| Stakeholder | Interesse / necessidade | Como é afetado pela solução |
|-------------|-------------------------|-----------------------------|
|Gestor do lar / Consumidor|Controle do orçamento e facilidade no registro de compras|Consegue visualizar o inventário em tempo real, evitar desperdício e economizar utilizando o rastreio de preços locais.|
| | | |

## 4. Decisão que a IA vai apoiar

_Que decisão o usuário toma com ajuda da solução? O que a IA NÃO deve decidir sozinha?_

## 5. Riscos e limitações

| Risco | Impacto | Como mitigar |
|-------|---------|--------------|
| Respostas incorretas (alucinação) | | |
| Viés nos dados ou no modelo | | |
| Privacidade / LGPD | | |
| | | |

## 6. Métricas de avaliação de sucesso

| Métrica | Como medir | Meta |
|---------|------------|------|
| Acurácia da extração OCR de notas fiscais | Comparação das entidades extraídas (produto e preço) com uma base real documentada, avaliada preferencialmente por PR-AUC para lidar com o desbalanceamento das listas de itens. | > 90% de precisão na extração |
| Fidelidade e relevância do RAG | Frameworks de avaliação (ex.: RAGAS ou LLM-as-a-judge) para garantir que a resposta não extrapole o contexto recuperado do banco vetorial. | > 85% de score em fidelidade de contexto |
| LLM x RAG | Teste comparativo de respostas sobre preços e validades locais, com avaliação da incerteza do modelo por métricas de calibração. | RAG com > 95% de precisão factual, e o modelo puro com taxa de erro significativamente maior |
| Multiagente | Percentual de fluxos concluídos sem falha de repasse de contexto entre agentes. | > 95% de sucesso na comunicação entre agentes |
| Negócio | Acompanhamento do ciclo de vida dos produtos no app (itens consumidos x expirados) e questionários rápidos de feedback do usuário. | Redução de 20% no desperdício de alimentos no primeiro mês de uso ativo |

## 7. Fontes confiáveis previstas

| Fonte | Tipo | Referência |
|-------|------|------------|
| Ministério da Agricultura e Pecuária (MAPA) | Página oficial | [Perdas e desperdício de alimentos](https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/perdas-e-desperdicio-de-alimentos) |
| Ministério da Agricultura e Pecuária (MAPA) | Relatório | [Relatório final sobre perdas e desperdício de alimentos](https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/perdas-e-desperdicio-de-alimentos/publicacoes-em-destaque/relatorio-final-perdas-e-desperdicio) |
| Embrapa | Página oficial | [Perdas e desperdício de alimentos: sobre o tema](https://www.embrapa.br/tema-perdas-e-desperdicio-de-alimentos/sobre-o-tema) |
| OCDE | Documento de trabalho | [DAF/COMP/WD(2022)51](https://one.oecd.org/document/DAF/COMP/WD(2022)51/en/pdf) |
| IBGE | Indicador de preços | [IPCA-15, setembro de 2026](https://biblioteca.ibge.gov.br/visualizacao/periodicos/2376/ipca_15_2026_set.pdf) |
| Alan Beattie | Livro | BEATTIE, Alan. *False Economy: A Surprising Economic History of the World*. 2009. |

## 8. Equipe e papéis

| Integrante | GitHub | Papel |
|------------|--------|-------|
| Guilherme Barros | [@dida0982](https://github.com/dida0982) | AI Engineering e frontend |
| Paulo Vitor Gomes | [@gpaulovit](https://github.com/gpaulovit) | AI Engineering e LLMOps |
| Isabel Azar | [@iAiBel](https://github.com/iAiBel) | Engenharia de dados e backend |
| Pedro Lucas Dourado | [@pedrolucasdourado](https://github.com/pedrolucasdourado) | Arquiteto de LLMOps |
| Mariah Gladys | [@necrophagial](https://github.com/necrophagial) | Scrum master e documentação |
