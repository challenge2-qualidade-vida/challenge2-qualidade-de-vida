# Escopo do MVP e priorização

> **Status:** priorização definida pela equipe em 03/11/2026. As notas de dificuldade e impacto são uma proposta inicial para a equipe revisar. A justificativa da priorização está em [decisoes.md](../decisoes.md).

## Critérios

A priorização considera três critérios:

- **Dificuldade de implementar:** esforço, dependências e riscos técnicos.
- **Entregável da semana:** qual entrega do roadmap a funcionalidade atende.
- **Impacto na solução:** quanto ela resolve o problema da pessoa e demonstra o EconoMIA.

Escala: baixa, média, alta.

## Tabela de priorização

| Prioridade | Funcionalidade | Fluxos | Agente | Dificuldade | Semana do roadmap | Impacto | Situação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Sugestão de receitas e perguntas sobre alimentação (RAG) | F13 | Miau-ricio | Média: RAG, extração do TudoGostoso, catálogo de `Alimento` | 2 (primeiro RAG) e 3 (LLM × RAG) | Alto: primeiro componente integrado, base da comparação da semana 3 | MVP, [spec 15](../../specs/15-rag-receitas/spec.md) escrita |
| 2 | Cadastro de nota fiscal, com revisão e comparação com as notas anteriores | F9 | Recibaldo | Alta: QR code da Sefaz-DF, leitura de imagem, HMAC da chave, revisão | 5 (multimodal); a leitura pelo QR code pode começar antes | Alto: alimenta o perfil, a comparação de preços e as receitas | MVP |
| 3 | Planejador de compras pelo perfil: cadastro, lista, custo estimado e ajuste ao orçamento | F1, F2, F3, F4 | Planejamento | Média: regras determinísticas de prioridade e ajuste (RN23, RN24) | 4 (multiagente) | Alto: é o núcleo do problema de orçamento | MVP |
| 4 | Preços dos mercados e leitura de encartes | F5, F10 | Cifrão | Alta: fontes de salvaguarda, normalização de produtos, leitura de encartes | 5 e 6 | Alto: comparação entre mercados | MVP, **bloqueado** pelas fontes de salvaguarda |
| 5 | Chat que aciona os agentes | F15 | Orquestrador | Média: LangGraph, memória, streaming | 4 (multiagente) | Alto: demonstra o sistema multiagente | MVP |
| 6 | Verificação de cálculos, fontes e limitações | — | Mia | Média: regras de conferência sobre dados tipados | 4 (multiagente) | Médio: garante a RN01 e a RN14 | MVP, depois do orquestrador |
| — | Promoção vale a pena? | F6 | Cifrão | Média: depende do preço de salvaguarda | — | Médio | Fora do MVP |
| — | Custo de deslocamento | F7 | Cifrão | Alta: localização e rotas | — | Baixo | Fora do MVP (regra prevista no modelo de domínio) |
| — | Histórico e tendência de preços | F8 | Cifrão | Média: precisa de semanas de dados | — | Médio | Fora do MVP |
| — | Foto de lista escrita à mão | F11 | Recibaldo | Média | — | Baixo: repete a multimodalidade das notas | Fora do MVP |
| — | Informação nutricional estimada pela TACO | F14 | Miau-ricio | Média: cálculo determinístico por ingrediente | — | Médio | Fora do MVP (regra prevista no modelo de domínio) |
| — | Interação por voz | F16 | Orquestrador | Alta | — | Baixo | Fora do MVP |
| — | Despensa com validade | F12 | Miau-ricio | — | — | — | Cortada (princípio de usabilidade) |

Os números de fluxo (F1 a F16) vêm do levantamento de fluxos da proposta e do Relatório 1. As regras de cada funcionalidade estão no [modelo de domínio](../arquitetura/modelo-de-dominio.md).

## A fazer

- [ ] Reescrever os **requisitos funcionais** a partir deste escopo, com critérios de aceitação.
- [ ] Reescrever os **requisitos não funcionais** a partir das decisões de arquitetura (desempenho, segurança, LGPD, observabilidade, disponibilidade).
- [ ] Atualizar o **diagrama de fluxo da aplicação**, com o escopo do MVP e a arquitetura definida.
- [ ] Desenhar o **diagrama de fluxo de usuário** de cada funcionalidade principal (um por agente): Miau-ricio, Recibaldo, Planejamento, Cifrão, Orquestrador e Mia.
- [ ] Revisar as notas de dificuldade e impacto desta tabela com a equipe.
