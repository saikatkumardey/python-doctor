#!/usr/bin/env bash
# benchmark.sh — score popular open-source libs against the current python-doctor build
# Usage: ./scripts/benchmark.sh
# Re-run after any scoring changes to verify calibration.

set -euo pipefail

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

REPOS=(
  "https://github.com/psf/requests|requests|library"
  "https://github.com/pallets/flask|flask|web"
  "https://github.com/fastapi/fastapi|fastapi|web"
)

echo "Python Doctor Benchmark"
echo "========================"
echo "Build: $(uv run python-doctor --version 2>/dev/null || python -m python_doctor --version 2>/dev/null || echo 'dev')"
echo "Date:  $(date +%Y-%m-%d)"
echo ""
printf "%-12s %-8s %-10s %s\n" "Project" "Profile" "Score" "Label"
printf "%-12s %-8s %-10s %s\n" "-------" "-------" "-----" "-----"

for entry in "${REPOS[@]}"; do
  IFS='|' read -r url name profile <<< "$entry"
  dest="$TMPDIR/$name"

  git clone --depth 1 --quiet "$url" "$dest" 2>/dev/null

  result=$(uv run python-doctor "$dest" --profile "$profile" --json 2>/dev/null \
    || python -m python_doctor "$dest" --profile "$profile" --json 2>/dev/null)

  score=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['score'])" 2>/dev/null || echo "ERR")
  label=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['label'])" 2>/dev/null || echo "")

  printf "%-12s %-8s %-10s %s\n" "$name" "$profile" "$score" "$label"
done

echo ""
echo "Expected (README): requests 81, flask 78, fastapi 78"
