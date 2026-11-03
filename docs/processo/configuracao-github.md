# Configuração do repositório no GitHub

Configurações que só uma pessoa com acesso de **administrador** no repositório consegue aplicar. Elas completam as checagens locais (pre-commit) e do CI (workflow `Convenções`).

## 1. Só merge commit

Em **Settings > General > Pull Requests**:

- [x] **Allow merge commits**
- [ ] Allow squash merging
- [ ] Allow rebase merging
- [x] **Always suggest updating pull request branches**
- [x] **Automatically delete head branches** (apaga a branch depois do merge)

Pelo terminal, com o GitHub CLI:

```bash
gh api -X PATCH repos/challenge2-qualidade-vida/challenge2-qualidade-de-vida -F allow_merge_commit=true -F allow_squash_merge=false -F allow_rebase_merge=false -F delete_branch_on_merge=true -F allow_update_branch=true
```

## 2. Proteção da main

Em **Settings > Rules > Rulesets > New ruleset > New branch ruleset**:

- **Nome:** `main`
- **Enforcement status:** Active
- **Target branches:** Include default branch
- **Regras:**
  - [x] Restrict deletions
  - [x] Block force pushes
  - [x] Require a pull request before merging
    - Required approvals: **1**
    - [x] Dismiss stale pull request approvals when new commits are pushed
    - Allowed merge methods: **Merge**
  - [x] Require status checks to pass
    - **Branch ligada a uma issue**, **Mensagens de commit** e **Título, issue e spec** (workflow `Convenções`)
    - Checks de lint e testes, quando o CI da #26 existir

Os checks só aparecem na lista depois de rodarem uma vez num PR.

## 3. Padrão de nome de branch (opcional)

Se o plano da organização oferecer a regra **Restrict branch names** (metadata restrictions), um segundo ruleset pode barrar no próprio GitHub branches fora do padrão:

- **Target branches:** All branches, exceto `main`
- **Restrict branch names:** must match regex `^(feat|fix|docs|refactor|test|chore|ci|perf|build|style)/[0-9]+-[a-z0-9-]+$`

Sem essa regra, o padrão é garantido pelo `scripts/nova-branch.sh`, pelo hook de push e pelo check **Branch ligada a uma issue**, que impede o merge.
