# Instruções para o GitHub Copilot

As instruções completas do projeto estão em [AGENTS.md](../AGENTS.md). Resumo das regras principais:

- Ler o modelo de domínio (`docs/arquitetura/modelo-de-dominio.md`) e a spec da tarefa (`specs/<issue>-<nome>/`) antes de gerar código.
- Código em português, com os nomes da linguagem ubíqua, sem acentos nos identificadores.
- Camada `dominio` sem dependência de frameworks, banco ou LLM.
- Dinheiro em centavos (inteiro), nunca `float`. Cálculos são funções determinísticas com testes; o LLM nunca calcula valores.
- Todo preço tem data, fonte e origem. Respostas da base de conhecimento citam a fonte.
- Código novo vem com testes de unidade e passos BDD (pytest-bdd).
- Commits em Conventional Commits, em português. Nenhuma IA como coautora: sem `Co-Authored-By` nem menções a ferramentas de IA em commits, merge commits, PRs, issues ou comentários.
- PRs com as labels da issue vinculada e a label do tipo, e revisão pedida a `pedrolucasdourado` e `gpaulovit` (só ao outro, se o autor for um deles).
- Branch `tipo/numero-da-issue-descricao`, com a issue existente.
- Nunca escrever chaves de API, senhas ou dados pessoais.
- Quando uma decisão for tomada, perguntar a justificativa à pessoa, registrar em `docs/decisoes.md` e propor a validação por pesquisa (IA ou manual).
