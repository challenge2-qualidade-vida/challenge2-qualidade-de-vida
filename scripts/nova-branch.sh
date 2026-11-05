#!/usr/bin/env bash
# Cria uma branch ligada a uma issue existente e aberta, a partir da main atualizada.
# Uso: scripts/nova-branch.sh <tipo> <numero-da-issue> <descricao>
# Ex.: scripts/nova-branch.sh feat 24 endpoint-rag
set -euo pipefail

TIPOS="feat fix docs refactor test chore ci perf build style"

uso() {
  echo "Uso: $0 <tipo> <numero-da-issue> <descricao>"
  echo "Tipos: $TIPOS"
  echo "Ex.: $0 feat 24 endpoint-rag"
  exit 1
}

[ $# -eq 3 ] || uso
tipo=$1
issue=$2
descricao=$3

[[ " $TIPOS " == *" $tipo "* ]] || { echo "Tipo inválido: $tipo"; uso; }
[[ $issue =~ ^[0-9]+$ ]] || { echo "Número de issue inválido: $issue"; uso; }
[[ $descricao =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || {
  echo "Descrição inválida: $descricao"
  echo "Use só letras minúsculas sem acento, números e hífens (ex.: endpoint-rag)."
  exit 1
}

command -v gh >/dev/null || {
  echo "O GitHub CLI (gh) é necessário para conferir a issue. Instale e rode 'gh auth login'."
  exit 1
}

estado=$(gh issue view "$issue" --json state --jq .state 2>/dev/null || true)
if [ -z "$estado" ]; then
  echo "A issue #$issue não existe."
  echo "Crie a issue (card) no GitHub Project antes de criar a branch."
  exit 1
fi
if [ "$estado" != "OPEN" ]; then
  echo "A issue #$issue está fechada. Reabra a issue ou crie uma nova antes de criar a branch."
  exit 1
fi

branch="$tipo/$issue-$descricao"
git fetch origin main
git switch -c "$branch" origin/main --no-track
echo "Branch $branch criada a partir de origin/main, ligada à issue #$issue."
