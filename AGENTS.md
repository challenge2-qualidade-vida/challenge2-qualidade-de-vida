# Instruções para assistentes de IA

Este arquivo vale para qualquer assistente de IA usado no projeto (Claude Code, GitHub Copilot, Cursor, Codex). As regras aqui têm prioridade sobre os padrões da ferramenta.

## Projeto

**EconoMIA:** assistente de planejamento de compras de supermercado, com sistema multiagente (orquestrador, agente de planejamento, Cifrão, Miau-ricio, Mia e Recibaldo), RAG e leitura de imagens. Projeto acadêmico da Residência em IA Brasília.

## Leitura obrigatória antes de escrever código

1. [docs/arquitetura/modelo-de-dominio.md](docs/arquitetura/modelo-de-dominio.md): linguagem ubíqua, contextos delimitados e regras de negócio (RN01 a RN15).
2. A spec da tarefa em `specs/<numero-da-issue>-<nome>/` (`spec.md` e `cenarios.feature`).
3. [docs/processo/fluxo-de-trabalho.md](docs/processo/fluxo-de-trabalho.md): fluxo de trabalho e convenções.

Se a tarefa for uma funcionalidade e não houver spec, escreva a spec e os cenários primeiro, a partir de [specs/_modelo](specs/_modelo/), e peça revisão antes de implementar.

## Stack

- Python, gerenciado com Poetry (`pyproject.toml`)
- API: FastAPI (em definição na #31)
- Banco relacional: PostgreSQL
- Testes: pytest e pytest-bdd
- Lint e formatação: Ruff

As escolhas do RAG (LLM, embeddings, banco vetorial, framework) estão em definição na #13. Não introduza uma biblioteca nova sem registrar a decisão em `docs/decisoes.md`.

## Regras de código

- **Idioma:** código em português (classes, funções, variáveis, módulos), seguindo a coluna "Nome no código" do modelo de domínio. Sem acentos nos identificadores (`Orcamento`, `preco_por_unidade`). Comentários e docstrings em português.
- **Arquitetura:** cada contexto em `src/economia/<contexto>/` com as camadas `dominio`, `aplicacao` e `infraestrutura`. A camada `dominio` não importa frameworks, banco nem bibliotecas de LLM.
- **Dinheiro:** valores em centavos (inteiro) no objeto de valor `Dinheiro`. Nunca usar `float` para dinheiro.
- **Cálculos:** somas, comparações e cálculos de preço são funções determinísticas com testes. O LLM nunca calcula valores (RN01).
- **Preços:** todo preço tem data, fonte e origem (RN02, RN03). O LLM e o RAG não são fonte de preço atual (RN04).
- **Fontes:** respostas baseadas na base de conhecimento citam a fonte. Sem informação, dizer que não encontrou (RN10, RN11).
- **Prompts:** ficam em arquivos versionados, fora do código Python.
- **Testes:** todo código novo vem com testes de unidade. Funcionalidades vêm com os passos BDD dos cenários da spec em `tests/bdd/`.
- **Segredos e dados pessoais:** nunca escrever chaves de API, senhas ou dados pessoais em código, testes, prompts ou exemplos. Usar variáveis de ambiente e dados fictícios.

## Git

- **Branch:** `tipo/numero-da-issue-descricao` (ex.: `feat/24-endpoint-rag`). Criar com `scripts/nova-branch.sh`. A issue precisa existir e estar aberta. Se não existir, avise a pessoa desenvolvedora que a issue deve ser criada antes e não crie a branch.
- **Commits:** Conventional Commits em português: `tipo(escopo): descrição`. Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`, `build`, `style`, `revert`.
- **Coautoria:** não adicionar linhas `Co-Authored-By` nem menções a ferramentas de IA em commits, PRs ou issues.
- **Pull request:** título no padrão dos commits, descrição pelo modelo de PR, com `Closes #N` para a tarefa. Épicos (issues com sub-issues) são citados com `Refs #N`, nunca com `Closes`: o épico é fechado manualmente quando todas as sub-issues estiverem concluídas.
- **Merge:** sempre merge commit. Nunca squash nem rebase na `main`. Nunca fazer push direto na `main`.

## O que não fazer

- Não implementar funcionalidade sem spec.
- Não inventar termos fora do modelo de domínio. Se precisar de um termo novo, proponha a inclusão no modelo de domínio.
- Não mudar regras de negócio sem atualizar o modelo de domínio e a spec.
- Não desativar hooks nem checagens do CI (`--no-verify`).
