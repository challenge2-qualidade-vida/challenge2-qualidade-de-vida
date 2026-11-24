# Spec: ampliar a base de conhecimento e avaliar o RAG antes e depois

| Campo | Valor |
| --- | --- |
| Issue | #16 (épico #15; avaliação ligada à #29) |
| Status | Em revisão |
| Contexto delimitado | Receitas e nutrição |
| Agente | Miau-ricio |

## Problema

O desafio da semana 2 pede uma base de conhecimento com **pelo menos 20 documentos-fonte**. A versão 1 do RAG ([spec 15](../15-rag-receitas/spec.md)) tem 7: o Guia Alimentar, o "Na cozinha com as frutas, legumes e verduras", três materiais da Embrapa, o afrodite.json e o RecipeNLG. O catálogo da `chore/16-base-conhecimento` lista outros 20 documentos com licença conferida, mas nenhum deles foi baixado nem indexado.

Ampliar a base pode piorar o RAG: textos pouco relacionados competem com as receitas na busca e podem subir o score das perguntas sem resposta. Por isso a mudança precisa ser medida. A avaliação da versão 1 só mede a recuperação, com 26 perguntas, e não diz se a resposta final se comporta como deveria.

## Comportamento esperado

1. **Avaliação intensiva, feita antes de mudar a base.**
   - Conjunto `data/avaliacao/perguntas_rag_v2.json`: as 26 perguntas da v1 e perguntas novas sobre os temas dos documentos que vão entrar, perguntas com erros de digitação e linguagem informal, mais perguntas sem resposta e perguntas de preço.
   - Cada pergunta tem uma categoria e um comportamento esperado: `responder`, `nao_encontrar` (RN11) ou `aviso_de_preco` (RN04).
   - **Recuperação:** o comando `comparar` passa a mostrar Recall@5 e MRR por categoria e aceita `--saida`, para guardar cada execução num arquivo próprio.
   - **Resposta:** o comando novo `avaliar-respostas` roda o caso de uso completo (recuperação, limiar, LLM e fontes) em cada pergunta e mede a acurácia do comportamento, a taxa de resposta, as recusas corretas, os avisos de preço, as respostas que citam a fonte esperada e a latência.
   - **Comparação:** o comando novo `comparar-execucoes ANTES DEPOIS` mostra a diferença entre duas execuções, no total e por categoria.
2. **Linha de base.** A avaliação roda com a base atual e o resultado fica salvo em `data/avaliacao/v2/`.
3. **Base ampliada para 20 fontes.** Os 13 documentos do catálogo de maior impacto para o Miau-ricio (critérios em [docs/semana-2/avaliacao-rag.md](../../docs/semana-2/avaliacao-rag.md)), incluindo a TACO, entram em `DOCUMENTOS_DE_ORIENTACAO` e no `FONTES.md`, com título, instituição, ano, link e licença.
4. **Nova avaliação e comparação.** A base é indexada de novo, a avaliação roda outra vez e a comparação fica documentada.

## Termos do domínio

`Fonte`, `Trecho`, `Documento`, `RespostaComFontes`, `Receita`, `Alimento`.

## Regras de negócio

- RN01: as métricas são calculadas por funções determinísticas, nunca pelo LLM.
- RN04: pergunta de preço recebe o aviso, e não uma resposta da base.
- RN10: uma resposta só conta como fundamentada se citar trechos, e as fontes vêm do código.
- RN11: sem informação na base, o sistema diz que não encontrou.

## Entradas e saídas

- **Entrada:** o conjunto de perguntas com gabarito, a coleção do Qdrant e o LLM configurado.
- **Saídas:**
  - `data/avaliacao/v2/recuperacao_<rotulo>.json` e `data/avaliacao/v2/respostas_<rotulo>.json`;
  - a tabela de comparação no terminal;
  - o relatório em `docs/semana-2/avaliacao-rag.md`.

## Fora do escopo

- A TACO como consulta estruturada de calorias e nutrientes (#22). Aqui ela entra só como texto no RAG, o que tem limitações (ver o relatório).
- Medir a fidelidade da resposta com um LLM juiz. A avaliação mede se a fonte esperada foi citada, não se cada frase é fiel ao trecho.
- Os 3 documentos da revista TES (Fiocruz), cujo servidor não respondeu, e os 4 de baixo impacto deixados de fora.

## Critérios de aceitação

Ver [cenarios.feature](cenarios.feature).

## Dependências

[Spec 15](../15-rag-receitas/spec.md) (RAG v1), catálogo de fontes da `chore/16-base-conhecimento`, decisão sobre a TACO no RAG em `docs/decisoes.md`.

## Riscos e limitações

- Na CPU, a avaliação das respostas leva de 30 a 60 minutos.
- A TACO é uma tabela. Dividida por página, os números perdem a ligação com o cabeçalho das colunas, e o LLM pode ler o valor errado.
- Documentos técnicos ou voltados a serviços de alimentação (IFC, NBR 15635) podem aparecer em perguntas domésticas.
- Todas as fontes novas têm licença não comercial ou CC BY. Valem para o uso acadêmico.
