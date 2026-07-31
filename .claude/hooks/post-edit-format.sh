#!/usr/bin/env bash
# PostToolUse hook (Edit|MultiEdit|Write): formatea/lintea solo el archivo tocado.
# Recibe el evento de la herramienta como JSON por stdin (campo tool_input.file_path).
set -uo pipefail

PAYLOAD="$(cat)"
FILE="$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
')"

[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

case "$FILE" in
  src/api/*.py)
    if [ -x .venv/bin/ruff ]; then
      .venv/bin/ruff check --fix "$FILE" >&2
      .venv/bin/black "$FILE" >&2
    fi
    ;;
  src/web/*.ts|src/web/*.tsx|src/web/*.js|src/web/*.jsx|src/web/*.css|src/web/*.json)
    if [ -x src/web/node_modules/.bin/prettier ]; then
      src/web/node_modules/.bin/prettier --write "$FILE" >&2
    fi
    ;;
  *)
    exit 0
    ;;
esac
exit 0
