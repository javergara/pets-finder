#!/usr/bin/env bash
# PostToolUse hook (Edit|MultiEdit|Write): si el archivo tocado es feature_list.json,
# lo valida y bloquea (exit 2) devolviendo el error a Claude si es inválido.
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

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

case "$FILE" in
  */feature_list.json|feature_list.json)
    ERRORS="$(python3 scripts/validate_feature_list.py "$FILE" 2>&1)"
    if [ -n "$ERRORS" ]; then
      echo "feature_list.json inválido, revertir o corregir antes de continuar:" >&2
      echo "$ERRORS" >&2
      exit 2
    fi
    ;;
esac
exit 0
