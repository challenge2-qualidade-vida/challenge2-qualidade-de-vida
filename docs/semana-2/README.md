# Semana 2: base de conhecimento e recuperação (RAG)

**Entregável da semana (semana 2):** primeiro mecanismo de RAG. O Miau-ricio, agente do contexto "Receitas e nutrição", responde perguntas sobre receitas e alimentação usando uma base de conhecimento e cita a fonte de cada resposta.

**Status:** entregue (versão 1). Épico: #15.

## Resumo executivo

A versão 1 do mecanismo RAG foi entregue com foco em resposta baseada em evidências e rastreabilidade. A solução combina uma base de conhecimento estruturada em receitas, guias e materiais de orientação, recuperação vetorial com embeddings em português e inglês, reordenação por relevância de ingredientes e geração de resposta com um modelo local. O resultado é um agente que consegue responder questões sobre receitas e alimentação com citação das fontes recuperadas, além de sinalizar quando a base não cobre a pergunta.

## O que foi entregue

- Base de conhecimento com receitas brasileiras (afrodite.json), amostra de receitas internacionais (RecipeNLG) e textos de orientação (guia alimentar e materiais de conservação e aproveitamento).
- Divisão em trechos (chunking) por tipo de documento: uma receita por trecho; guia e textos de orientação por seção e parágrafo.
- Embeddings com `intfloat/multilingual-e5-base` e banco vetorial Qdrant.
- Desempate do top-5 pelos ingredientes que faltam, calculado por função determinística (RN01).
- Resposta redigida por LLM local (`qwen2.5:7b`, via Ollama) apenas com os trechos recuperados, com as fontes inseridas pelo código (RN10).
- Resposta "não encontrei" quando a base não cobre a pergunta (RN11), com limiar de similaridade calibrado em 0,845.
- Avaliação com perguntas e gabarito (Recall@5, MRR, latência).
- Demonstração por linha de comando e por notebook.

## Resultados da versão 1

Métricas obtidas com o modelo e5 na coleção completa (4.346 trechos) e 25 perguntas, em máquina Linux com 8 CPUs lógicas, sem GPU.

| Métrica | Resultado |
| --- | --- |
| Recall@5 | 0,76 (16 de 21 perguntas com resposta) |
| MRR | 0,63 |
| Latência por consulta (somente a recuperação) | 0,46 s |
| Indexação | cerca de 47 min |
| Limiar de similaridade (RN11) | 0,845 (antes 0,80) |

Ponto fraco conhecido: a busca entre idiomas (pergunta em português, receita em inglês) errou 4 de 5 perguntas. Detalhes e limitações em [estrategia-rag.md](estrategia-rag.md), seções 5 e 8.

## Documentos desta pasta

| Documento | Conteúdo |
| --- | --- |
| [estrategia-rag.md](estrategia-rag.md) | Fluxo do RAG, base de conhecimento, chunking, embeddings, banco vetorial, resultados e limitações |

## Onde está o restante da entrega

| O que | Onde |
| --- | --- |
| Comportamento esperado (spec e cenários) | [specs/15-rag-receitas/](../../specs/15-rag-receitas/spec.md) |
| Decisões técnicas e justificativas | [docs/decisoes.md](../decisoes.md) |
| Fontes da base de conhecimento, com licenças | [data/base-conhecimento/FONTES.md](../../data/base-conhecimento/FONTES.md) |
| Perguntas e gabarito da avaliação | [data/avaliacao/perguntas_rag_v1.json](../../data/avaliacao/perguntas_rag_v1.json) |
| Resultados por pergunta | [data/avaliacao/resultados_v1.json](../../data/avaliacao/resultados_v1.json) |
| Prompts do Miau-ricio | [prompts/miau-ricio/](../../prompts/miau-ricio/) |
| Notebook de demonstração | [notebooks/01-rag-receitas-passo-a-passo.ipynb](../../notebooks/01-rag-receitas-passo-a-passo.ipynb) |
| Termos e regras de negócio | [modelo de dominio](../arquitetura/modelo-de-dominio.md) |

## Limitações e pendências

- **Licenças:** o afrodite.json não declara licença nem origem, e o RecipeNLG é de uso não comercial. Ver [decisoes.md](../decisoes.md) (decisão de 05/11/2026).
- **Busca entre idiomas:** fraca com o e5.
- **Comparação com o `qwen3-embedding:4b`:** adiada para depois, quando o projeto rodar no Mac M4.
- **Busca de receitas sob demanda (RN26):** pendente.
- **Fora da versão 1:** restrições do perfil (RN27), notas recentes (RN21), envio para a lista de compras (RN29) e endpoint da API (#24).

## Conclusão

A versão 1 estabelece a base funcional do agente RAG para receitas e alimentação, com recuperação relevante, citação de fontes e comportamento de resposta em cenários cobertos pela base. O principal ganho foi a criação de um fluxo completo de busca + geração com evidências e avaliação objetiva. As principais metas de evolução seguem concentradas em melhor recuperação cruzada de idiomas, expansão da base e suporte a novas regras de negócio e fluxos de uso.

