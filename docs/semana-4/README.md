# Semana 4 — Sistema multiagentes

**Entregável:** primeiro sistema multiagentes. ✅ Detalhes no [tópico 9](../desenvolvimento/09-agentes.md).

| Agente | Função | Usa LLM? |
|--------|--------|----------|
| **Orquestrador** | Decide quem responde e registra as etapas | Não, regras |
| **Cifrão** | Preços, promoções e cesta, por ferramentas | Sim |
| **Miau-ricio** | Nutrição e aproveitamento com RAG; cardápio por receitas cadastradas | Só no chat |
| **Mia** | Confere valores, fontes, restrições e avisos antes de responder | Não, regras |
| **Recibaldo** | Lê o cupom (ver [semana 5](../semana-5/README.md)) | Não |

**Por que nem todos usam LLM:** rotear com LLM custaria de 5 a 15 s por pergunta, e quem verifica não pode errar como quem é verificado.
