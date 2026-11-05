#!/usr/bin/env bash
# Confere se a branch segue tipo/numero-da-issue-descricao e se a issue existe e está aberta.
# Uso: scripts/verificar-branch.sh [branch]  (sem argumento, usa a branch atual)
set -euo pipefail

branch=${1:-$(git rev-parse --abbrev-ref HEAD)}
case "$branch" in
  main | HEAD) exit 0 ;;
esac

padrao='^(feat|fix|docs|refactor|test|chore|ci|perf|build|style)/([0-9]+)-[a-z0-9]+(-[a-z0-9]+)*$'
if [[ $branch =~ $padrao ]]; then
  issue=${BASH_REMATCH[2]}
else
  echo "A branch '$branch' está fora do padrão tipo/numero-da-issue-descricao."
  echo "Ex.: feat/24-endpoint-rag. Crie branches com scripts/nova-branch.sh."
  exit 1
fi

if ! command -v gh >/dev/null; then
  echo "Aviso: GitHub CLI (gh) não encontrado; não foi possível conferir a issue #$issue."
  exit 0
fi

estado=$(gh issue view "$issue" --json state --jq .state 2>/dev/null || true)
if [ -z "$estado" ]; then
  echo "A issue #$issue da branch '$branch' não existe. Crie a issue antes de usar a branch."
  exit 1
fi
if [ "$estado" != "OPEN" ]; then
  echo "A issue #$issue da branch '$branch' está fechada."
  exit 1
fi
