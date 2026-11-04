#!/usr/bin/env bash
# Confere se os commits entre <base> e <topo> seguem o Conventional Commits.
# Uso: scripts/verificar-commits.sh <base> [topo]
set -euo pipefail

base=$1
topo=${2:-HEAD}
padrao='^(feat|fix|docs|refactor|test|chore|ci|perf|build|style|revert)(\([a-z0-9-]+\))?!?: .+'

erros=0
while IFS= read -r linha; do
  sha=${linha%% *}
  mensagem=${linha#* }
  if [[ ! $mensagem =~ $padrao ]]; then
    echo "Commit $sha fora do padrão: $mensagem"
    erros=1
  fi
done < <(git log --no-merges --format='%h %s' "$base..$topo")

if [ $erros -ne 0 ]; then
  echo "Use tipo(escopo): descrição. Ex.: feat(precos): adiciona comparação por preço por unidade"
  exit 1
fi
