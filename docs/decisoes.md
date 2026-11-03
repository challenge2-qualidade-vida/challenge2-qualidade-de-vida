# Decisões técnicas

Registre aqui cada decisão importante e a justificativa (restrição do desafio: "Justificar decisões técnicas").

| Data | Decisão | Alternativas consideradas | Justificativa | Quem decidiu |
|------|---------|---------------------------|---------------|--------------|
| 03/11/2026 | Desenvolvimento guiado por spec (SDD), com cenários BDD e modelo de domínio (DDD) | Desenvolver direto a partir das issues | Equipe e assistentes de IA trabalham a partir da mesma spec e da mesma linguagem do negócio, com critérios de aceitação executáveis | Equipe |
| 03/11/2026 | Código em português, seguindo a linguagem ubíqua do modelo de domínio | Código em inglês com glossário | Specs, cenários BDD e código usam os mesmos termos, sem tradução | Equipe |
| 03/11/2026 | Specs em `specs/<issue>-<nome>/` com modelo próprio e testes BDD com pytest-bdd | GitHub Spec Kit; behave | Modelo simples, fácil de seguir; pytest-bdd integra com o pytest já usado nos testes | Equipe |
| 03/11/2026 | Conventional Commits com descrição em português | Mensagens livres; Conventional Commits em inglês | Histórico padronizado e legível pela equipe; checado no commit e no CI | Equipe |
| 03/11/2026 | Branches `tipo/numero-da-issue-descricao`, só com issue existente e aberta | `semana-N/descricao`; `numero-descricao` | Toda branch fica ligada a uma tarefa do Project; checado por script, hook de push e CI | Equipe |
| 03/11/2026 | Merge na `main` só com merge commit | Squash and merge; rebase and merge | Preserva os commits de cada PR e o registro de quando cada PR entrou | Equipe |
| 03/11/2026 | PR exige 1 aprovação, CI passando, issue vinculada e spec atualizada em PR de funcionalidade | Merge sem revisão | Garante revisão e rastreabilidade entre issue, spec e código | Equipe |
| 03/11/2026 | Épicos nunca são fechados por PR: PRs usam `Refs #N` para o épico, e o épico é fechado manualmente quando todas as sub-issues terminam | Fechar o épico pelo PR | O GitHub não verifica as sub-issues ao fechar pelo PR; o fechamento manual garante que o épico só termina com todas as tarefas concluídas | Equipe |
| 03/11/2026 | Ruff, pre-commit, gitleaks e pytest-cov como ferramentas de qualidade | flake8 + black + isort; sem hooks locais | Ruff reúne lint e formatação; gitleaks evita vazar chaves de API de LLM; pre-commit aplica as regras antes do push | Equipe |
| 03/11/2026 | Banco relacional PostgreSQL | SQLite; MySQL | Robusto para a aplicação e compatível com a extensão pgvector, opção avaliada na #13 | Equipe |
| 03/11/2026 | Poetry para gerenciar as dependências Python | pip com `requirements.txt`; uv | Dependências e versões travadas em `pyproject.toml` e `poetry.lock` | Equipe |
