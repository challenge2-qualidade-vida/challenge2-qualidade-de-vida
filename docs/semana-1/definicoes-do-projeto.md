# Semana 1 — Definições do projeto

## 1. Essential Question

_Qual pergunta específica, derivada da Big Idea "Qualidade de Vida", o grupo vai responder?_

## 2. Problema

- **Contexto:**
- **Quem sofre com o problema:**
- **Por que é importante:**
- **Evidências que mostram o problema (com fonte):**

## 3. Stakeholders

| Stakeholder | Interesse / necessidade | Como é afetado pela solução |
|-------------|-------------------------|-----------------------------|
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
|-------|---------|--------------|
|Acurácia da extração OCR de notas fiscais|Comparação de entidades extraídas (produto/preço) vs. base real documentada, avaliada preferencialmente via PR-AUC para lidar com o desbalanceamento das listas de itens.|> 90% de precisão na extração.|

|Fidelidade e Relevância |Utilização de frameworks de observabilidade (ex: RAGAS / LLM-as-a-judge) para garantir que a resposta não extrapole o contexto recuperado do banco vetorial. |>85% de score em fidelidade de contexto |

|LLM X RAG |Teste comparativo de respostas sobre preços e validades locais. Avaliação da incerteza do modelo utilizando métricas de calibração. | >95% de sucesso na comunicação entre agentes. |

|Multiagente |Percentual de fluxos concluídos sem falha de repasse de contexto entre agentes | A meta é que o RAG atinja > 95% de precisão factual, com o modelo puro (apresentando pontuações de erro significativamente maiores.) |

|Negócio |Acompanhamento do ciclo de vida dos produtos no app (considerando: itens consumidos vs. expirados) e questionários de feedback rápido do usuário. | Espera-se uma redução de 20% no desperdício de alimentos no primeiro mês de uso ativo.) |

## 7. Fontes confiáveis previstas
https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/perdas-e-desperdicio-de-alimentos
https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/perdas-e-desperdicio-de-alimentos/publicacoes-em-destaque/relatorio-final-perdas-e-desperdicio
https://www.embrapa.br/tema-perdas-e-desperdicio-de-alimentos/sobre-o-tema
https://one.oecd.org/document/DAF/COMP/WD(2022)51/en/pdf
https://biblioteca.ibge.gov.br/visualizacao/periodicos/2376/ipca_15_2026_set.pdf
https://www.google.com/search?q=Beattie%2C+Alan.+False+Economy+-+A+Surprising+Economic+History+Of+The+World+(2009)&oq=Beattie%2C+Alan.+False+Economy+-+A+Surprising+Economic+History+Of+The+World+(2009)&gs_lcrp=EgZjaHJvbWUyBggAEEUYOdIBBzE2N2owajeoAgiwAgE&sourceid=chrome&source=chrome.ob&ie=UTF-8
-

## 8. Equipe e papéis

| Integrante | GitHub | Papel |
|------------|--------|-------|
| Guilherme Barros | [@dida0982](https://github.com/dida0982) | AI Engineering e frontend |
| Paulo Vitor Gomes | [@gpaulovit](https://github.com/gpaulovit) | AI Engineering e LLMOps |
| Isabel Azar | [@iAiBel](https://github.com/iAiBel) | Engenharia de dados e backend |
| Pedro Lucas Dourado | [@pedrolucasdourado](https://github.com/pedrolucasdourado) | Arquiteto de LLMOps |
| Mariah Gladys | [@necrophagial](https://github.com/necrophagial) | Scrum master e documentação |
