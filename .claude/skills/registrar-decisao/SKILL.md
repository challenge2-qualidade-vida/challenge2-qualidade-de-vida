---
name: registrar-decisao
description: Registra decisões técnicas, de produto ou de processo em docs/decisoes.md. Use sempre que uma escolha for feita ou proposta (biblioteca, LLM, banco, arquitetura, regra de negócio, convenção, ferramenta), mesmo que a pessoa só diga "vamos usar X" ou "decidimos Y". Pergunta a justificativa antes de registrar e propõe a validação por pesquisa.
---

# Registrar decisão

Toda decisão do projeto precisa de uma justificativa dada pela equipe. Sem justificativa, a decisão não é registrada como tomada.

## Passos

1. **Identificar a decisão.** Resuma em uma frase o que foi decidido e quais alternativas foram citadas.
2. **Perguntar a justificativa.** Pergunte à pessoa por que a escolha foi feita. Não preencha a justificativa por conta própria e não deduza a partir da conversa. Se fizer sentido, pergunte também:
   - quais alternativas foram consideradas;
   - quem decidiu (pessoa ou equipe).
3. **Sem resposta, sem decisão.** Se a pessoa não souber ou não quiser justificar agora, registre com o status **Sem justificativa** e avise que a decisão fica pendente até ser justificada.
4. **Registrar.** Adicione uma linha na tabela de [docs/decisoes.md](../../../docs/decisoes.md) com:
   - data (DD/MM/AAAA);
   - decisão;
   - alternativas consideradas;
   - justificativa, com as palavras da pessoa;
   - quem decidiu;
   - validação: **Pendente**.
5. **Propor a validação.** Pergunte se a justificativa deve ser validada agora e por qual caminho:
   - **IA:** pesquisa em documentação oficial, artigos e benchmarks, citando os links encontrados;
   - **Manual:** a equipe pesquisa e informa as fontes depois.
6. **Atualizar a validação.** Depois da pesquisa, troque o status da coluna de validação:
   - **Validada**, com as fontes (links ou referências);
   - **Contestada**, quando a pesquisa contradiz a justificativa. Nesse caso, mostre o que foi encontrado e pergunte se a decisão será mantida, revista ou trocada. Não altere a decisão sem a confirmação da pessoa.

## Regras

- Uma pesquisa feita por IA é sugestão de fonte, não validação final: a pessoa confirma que as fontes sustentam a justificativa.
- Cite apenas fontes que foram de fato abertas e lidas. Não invente links.
- Decisões que mudam regras de negócio também atualizam o [modelo de domínio](../../../docs/arquitetura/modelo-de-dominio.md).
- Decisões que adicionam biblioteca ou serviço também atualizam a seção "Stack" do [AGENTS.md](../../../AGENTS.md) quando passam a valer para o código.
