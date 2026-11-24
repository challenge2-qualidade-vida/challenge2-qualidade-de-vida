#!/usr/bin/env bash
# Roda a matriz da #69 (LLM puro x RAG) uma execução por vez, registra cada uma e, no fim,
# gera o relatório em Markdown, faz o commit e o push dos resultados.
#
# Uso: scripts/rodar-matriz-llm.sh            (matriz completa, 67 perguntas)
#      LIMITE=2 scripts/rodar-matriz-llm.sh   (teste rápido, sem commit)
#
# Retoma de onde parou: uma execução com o JSON já gravado é pulada.
set -uo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"

MODELOS=(${MODELOS:-qwen2.5:7b qwen3.5:9b gemma3:12b qwen3.5:27b gemma3:27b})
MODOS=(rag puro)
LIMITE="${LIMITE:-}"
SUFIXO="${SUFIXO:-linux-$(date +%Y%m%d)}"
SAIDA="${SAIDA:-data/avaliacao/v3/pc-linux}"
[ -n "$LIMITE" ] && SAIDA="${SAIDA}-teste"
ESTADO="$SAIDA/estado.jsonl"
POETRY="${POETRY:-$HOME/.local/bin/poetry}"
mkdir -p "$SAIDA"

registrar() { # modo llm tentativa inicio fim codigo arquivo
  printf '{"modo":"%s","llm":"%s","tentativa":%s,"inicio":"%s","fim":"%s","segundos":%s,"codigo":%s,"arquivo":"%s"}\n' \
    "$1" "$2" "$3" "$(date -d @"$4" -Iseconds)" "$(date -d @"$5" -Iseconds)" "$(($5 - $4))" "$6" "$7" >>"$ESTADO"
}

echo "== Matriz #69 | $(date -Iseconds) | sufixo $SUFIXO | saída $SAIDA"
for llm in "${MODELOS[@]}"; do
  if ! ollama show "$llm" >/dev/null 2>&1; then
    echo "-- baixando $llm"
    ollama pull "$llm" || { echo "!! não baixou $llm"; continue; }
  fi
  for modo in "${MODOS[@]}"; do
    nome="completo_${modo}_${llm/:/-}"
    arquivo="$SAIDA/$nome.json"
    if [ -f "$arquivo" ]; then
      echo "-- já existe $arquivo, pulando"
      continue
    fi
    extras=()
    [ "$modo" = rag ] && extras=(--prompt resposta_com_fontes@v2 --estruturada --segunda-tentativa)
    [ -n "$LIMITE" ] && extras+=(--limite "$LIMITE")
    for tentativa in 1 2; do
      sufixo="$SUFIXO"
      [ "$tentativa" -gt 1 ] && sufixo="$SUFIXO-t$tentativa"
      echo "== $modo $llm (tentativa $tentativa) | $(date -Iseconds)"
      inicio=$(date +%s)
      "$POETRY" run python -m economia.receitas.cli avaliar-respostas \
        --modo "$modo" --llm "$llm" --perguntas data/avaliacao/perguntas_rag_v3.json \
        --sufixo-run "$sufixo" --saida "$arquivo" "${extras[@]}" \
        >"$SAIDA/$nome.log" 2>&1
      codigo=$?
      fim=$(date +%s)
      registrar "$modo" "$llm" "$tentativa" "$inicio" "$fim" "$codigo" "$arquivo"
      echo "   código $codigo em $((fim - inicio)) s"
      [ "$codigo" -eq 0 ] && break
      mv "$SAIDA/$nome.log" "$SAIDA/$nome.falha$tentativa.log"
      sleep 30
    done
  done
  ollama stop "$llm" >/dev/null 2>&1 || true # libera a VRAM para o próximo modelo
done

RELATORIO="docs/semana-3/matriz-llm-pc-linux.md"
[ -n "$LIMITE" ] && RELATORIO="$SAIDA/relatorio-teste.md"
"$POETRY" run python scripts/relatorio_matriz_llm.py "$SAIDA" "$RELATORIO"
echo "== Relatório em $RELATORIO | $(date -Iseconds)"

if [ -z "$LIMITE" ]; then
  git add "$SAIDA" "$RELATORIO"
  git commit -m "feat(receitas): adiciona os resultados da matriz de LLMs no PC Linux" &&
    git push origin HEAD
fi
echo "== Fim | $(date -Iseconds)"
