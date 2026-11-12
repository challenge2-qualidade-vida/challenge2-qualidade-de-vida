# Spec: comparação do LLM puro com o LLM com RAG, com registro no Langfuse

| Campo | Valor |
| --- | --- |
| Issue | #69 (relacionada à #29 e ao épico #25) |
| Status | Rascunho |
| Contexto delimitado | Receitas e nutrição |
| Agente | Miau-ricio |

## Problema

A equipe precisa saber quanto o RAG melhora as respostas do Miau-ricio em relação ao LLM sozinho, e qual LLM local usar. Hoje a avaliação só roda com o RAG, mede o comportamento (respondeu, recusou, avisou) e a fonte citada, e não mede a qualidade do texto. As chamadas ao LLM também não ficam registradas em lugar nenhum: para entender uma resposta ruim, é preciso rodar de novo.

## Comportamento esperado

Quem desenvolve roda a avaliação escolhendo o **modo** e o **LLM**:

1. **Modo RAG.** O caso de uso atual: busca, limiar, redação com os trechos e fontes montadas pelo código.
2. **Modo LLM puro.** A mesma pergunta vai direto ao LLM, com a mesma persona e sem trechos. A resposta não tem fontes. O LLM pode dizer que não sabe.

Entre duas execuções, só mudam o modo e o LLM. Ficam fixos: o conjunto de perguntas, o prompt de cada modo, a temperatura (0), a semente, a janela de contexto, o máximo de tokens de saída, o modo de raciocínio desligado e o modelo de embeddings.

Cada execução grava um arquivo de resultado com a configuração usada e, por pergunta, as métricas:

- comportamento esperado e obtido, e a fonte esperada citada (já existem);
- **ROUGE-1 F1**, **ROUGE-L F1** e **cosseno** entre a resposta e a resposta de referência;
- **Hit@k**: se um trecho do gabarito está entre os k recuperados (só no modo RAG);
- **latência** e **tokens** de entrada e de saída.

Com as chaves do Langfuse configuradas, cada pergunta vira um registro no Langfuse com as etapas (busca e chamadas ao LLM), o modelo, o nome e a versão do prompt, os tokens e a latência, e as métricas entram como pontuações do registro. Sem as chaves, tudo funciona igual e nada é enviado.

## Termos do domínio

`Trecho`, `Fonte`, `Receita`. Os termos da avaliação (execução, resposta de referência, modo) são do ferramental de avaliação e não entram no modelo de domínio.

## Regras de negócio

- **RN01:** todas as métricas são contas determinísticas do código. O LLM não calcula nenhuma.
- **RN04, RN10, RN11:** continuam valendo no modo RAG, sem mudança. No modo puro não há fonte a citar; por isso ele existe só na avaliação e não é exposto à pessoa usuária.
- **RN30:** nenhum dado pessoal ou sensível é enviado ao Langfuse. O conjunto de avaliação só tem perguntas fictícias.

Específicas desta funcionalidade:

- A resposta de referência de cada pergunta é escrita a partir dos trechos do gabarito e revisada por uma pessoa.
- Perguntas sem resposta na base e perguntas de preço não têm resposta de referência, e as métricas de texto não se aplicam a elas.
- Uma falha ao falar com o Langfuse não interrompe a avaliação nem muda a resposta.

## Entradas e saídas

- **Entrada:** `avaliar-respostas --modo puro|rag --llm <modelo do Ollama> --perguntas <arquivo> --saida <arquivo>`, mais as opções que já existem (`--limite`, `--categorias`, `--prompt`, `--estruturada`, `--segunda-tentativa`).
- **Arquivo de perguntas:** `data/avaliacao/perguntas_rag_v3.json`, igual ao v2 com o campo opcional `resposta_referencia`.
- **Saída:** arquivo JSON em `data/avaliacao/v3/` com a configuração da execução (modo, LLM, digest e quantização do modelo, prompt, temperatura, semente, contexto, saída máxima, máquina), as métricas médias, as métricas por categoria e o resultado de cada pergunta.

## Fora do escopo

- Expor o modo puro na API ou na tela.
- Registrar no Langfuse as perguntas reais das pessoas (precisa do mascaramento da RN30).
- Conferir se cada número da resposta está certo (fatos esperados por pergunta).
- Trocar o LLM ou o prompt padrão do produto: isso é decisão da equipe, depois dos resultados.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature).

## Dependências

- RAG de receitas ([spec 15](../15-rag-receitas/spec.md)) e avaliação das respostas ([spec 16](../16-ampliar-base-conhecimento/spec.md)).
- Projeto no Langfuse Cloud e as chaves de acesso.
- Modelos baixados no Ollama.
- Decisões a registrar em `docs/decisoes.md`: biblioteca do Langfuse, modelos do experimento, modelo juiz.

## Riscos e limitações

- O ROUGE penaliza a resposta certa escrita com outras palavras. O cosseno entre embeddings varia pouco (quase sempre entre 0,7 e 1,0 no e5). As duas medidas servem para comparar execuções, não como nota absoluta.
- Nenhuma das métricas automáticas confere se um número da resposta está certo.
- Os modelos de 27B podem não caber em 24 GB de memória. Um piloto de 10 perguntas decide quais entram.
- No modo puro, as perguntas sem resposta na base medem outra coisa: se o modelo responde mesmo sem ter de onde tirar.
