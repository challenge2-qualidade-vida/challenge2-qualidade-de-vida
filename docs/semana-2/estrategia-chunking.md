# Estratégia de chunking — proposta inicial

**Status:** proposta para validação com Engenharia de IA.

1. Preservar títulos e subtítulos como contexto.
2. Separar primeiro por seção e parágrafo.
3. Não dividir listas de ingredientes nem etapas de preparo.
4. Agrupar parágrafos até um limite de tokens definido após a escolha do modelo de embeddings (#13).
5. Usar sobreposição pequena apenas quando necessária.
6. Repetir em cada trecho: `documento_id`, fonte, instituição, ano, tipo, URL, arquivo e página.

Os números de tokens e sobreposição ficam pendentes porque o modelo de embeddings ainda é definido na #13. Validar com o conjunto de perguntas #23, medindo Recall@k e qualidade das citações.
