#!/usr/bin/env bash
# Levanta la API (FastAPI) y la web (Vite) juntas con un solo comando.
# Uso: bash dev.sh — Ctrl+C detiene ambas.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d .venv ]; then
  echo "No existe .venv/ — corre primero: bash init.sh" >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

PYTHONPATH="$ROOT_DIR/src/api" DATABASE_URL="sqlite:///$ROOT_DIR/data/app.db" \
  uvicorn reencuentro_api.main:app --port 8000 --reload &
API_PID=$!

(cd src/web && npm run dev -- --port 5173) &
WEB_PID=$!

trap 'kill "$API_PID" "$WEB_PID" 2>/dev/null' EXIT INT TERM
wait "$API_PID" "$WEB_PID"
