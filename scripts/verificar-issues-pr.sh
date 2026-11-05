#!/usr/bin/env bash
# Confere a descrição de um pull request: ela precisa fechar pelo menos uma issue (Closes #N),
# e as issues fechadas não podem ser épicos (issues com sub-issues). Épicos são citados com Refs #N
# e fechados manualmente quando todas as sub-issues estiverem concluídas.
# Uso: scripts/verificar-issues-pr.sh "<descrição do PR>"
set -euo pipefail

corpo=$1
repo=${GH_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}

numeros=$(grep -Eio '(close[sd]?|fix(e[sd])?|resolve[sd]?) #[0-9]+' <<<"$corpo" | grep -Eo '[0-9]+' | sort -un || true)
if [ -z "$numeros" ]; then
  echo "A descrição do PR precisa fechar uma issue (ex.: Closes #24)."
  exit 1
fi

erros=0
for numero in $numeros; do
  resultado=$(gh api graphql \
    -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issueOrPullRequest(number:$n){__typename ... on Issue{subIssuesSummary{total}}}}}' \
    -f o="${repo%/*}" -f r="${repo#*/}" -F n="$numero" \
    --jq '.data.repository.issueOrPullRequest | "\(.__typename) \(.subIssuesSummary.total // 0)"' 2>/dev/null || echo "Inexistente 0")
  tipo=${resultado% *}
  sub_issues=${resultado#* }
  if [ "$tipo" != "Issue" ]; then
    echo "#$numero não é uma issue deste repositório."
    erros=1
  elif [ "$sub_issues" -gt 0 ]; then
    echo "#$numero é um épico ($sub_issues sub-issues). Use 'Refs #$numero' e feche o épico manualmente quando todas as sub-issues estiverem concluídas."
    erros=1
  fi
done

exit $erros
