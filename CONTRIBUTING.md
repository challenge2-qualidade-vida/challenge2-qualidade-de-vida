# Como contribuir

O fluxo completo, com SDD, BDD e DDD, está em [docs/processo/fluxo-de-trabalho.md](docs/processo/fluxo-de-trabalho.md). As instruções para assistentes de IA estão em [AGENTS.md](AGENTS.md).

## Configuração inicial (uma vez)

1. Instale e autentique o GitHub CLI (`gh auth login`).
2. Instale o pre-commit e ative os hooks:
   ```bash
   pipx install pre-commit
   ```
   ```bash
   pre-commit install
   ```

## Fluxo básico

1. **Issue.** Pegue uma tarefa no GitHub Project. Se ela não existir, crie a issue antes de qualquer branch.
2. **Branch.** Crie com o script, que só funciona se a issue existir e estiver aberta:
   ```bash
   scripts/nova-branch.sh feat 24 endpoint-rag
   ```
3. **Spec.** Para funcionalidades, escreva `specs/<issue>-<nome>/spec.md` e `cenarios.feature` a partir de [specs/_modelo](specs/_modelo/).
4. **Commits.** Pequenos, no padrão Conventional Commits em português:
   ```bash
   git commit -m "feat(rag): adiciona rota de perguntas sobre receitas"
   ```
5. **Pull request.** Abra para a `main` usando o modelo de PR, com `Closes #N`, e peça revisão.
6. **Merge.** Depois de 1 aprovação e com o CI passando, use **Create a merge commit**.

## Nome das branches

`tipo/numero-da-issue-descricao`. Exemplos: `feat/24-endpoint-rag`, `docs/32-diagrama-arquitetura`.

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`, `build`, `style`.

## Mensagens de commit

`tipo(escopo): descrição`. Exemplos:

- `feat(precos): adiciona comparação por preço por unidade`
- `fix(planejamento): corrige soma do custo estimado da lista`
- `docs(spec): adiciona spec do endpoint do RAG`

Sem linhas `Co-Authored-By` de ferramentas de IA.

## Regras do grupo

- Não subir chaves de API, senhas ou arquivos `.env` (já estão no `.gitignore`, e o gitleaks bloqueia no commit).
- Não subir dados pessoais reais (LGPD). Use dados públicos ou anonimizados.
- Toda fonte usada na base de conhecimento deve ser registrada em `data/base-conhecimento/FONTES.md`.
- Decisões técnicas importantes vão em `docs/decisoes.md`, com a justificativa.
- Termos novos do negócio entram primeiro no [modelo de domínio](docs/arquitetura/modelo-de-dominio.md).
- Nada de push direto na `main`, squash ou rebase no merge.
