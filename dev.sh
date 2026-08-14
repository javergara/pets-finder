#!/usr/bin/env bash
# Levanta la API (FastAPI) y la web (Vite) juntas con un solo comando.
# Uso: bash dev.sh — Ctrl+C detiene ambas.
#
# Por defecto usa la SQLite local (data/app.db). Para probar contra otra base
# —por ejemplo una réplica de producción construida desde el API público—
# exporta DATABASE_URL antes de llamarlo y se respeta:
#
#   DATABASE_URL="sqlite:///C:/ruta/replica-prod.db" bash dev.sh
#
# ⚠️ NUNCA apuntes DATABASE_URL a producción aquí.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d .venv ]; then
  echo "No existe .venv/ — corre primero: bash init.sh" >&2
  exit 1
fi

# El venv guarda los ejecutables en Scripts/ (Windows) o bin/ (Linux, macOS).
# Se invoca el intérprete directamente en vez de `source activate`, que además
# de ser específico de plataforma no hace falta para esto.
if [ -x .venv/Scripts/python.exe ]; then
  PY=".venv/Scripts/python.exe"
elif [ -x .venv/bin/python ]; then
  PY=".venv/bin/python"
else
  echo "No encuentro el intérprete del venv — corre: bash init.sh" >&2
  exit 1
fi

# DATABASE_URL del entorno si viene; si no, la SQLite local de siempre.
DB_URL="${DATABASE_URL:-sqlite:///$ROOT_DIR/data/app.db}"
echo "API  → http://127.0.0.1:8000  (DB: $DB_URL)"
echo "Web  → http://127.0.0.1:5173"

PYTHONPATH="$ROOT_DIR/src/api" DATABASE_URL="$DB_URL" \
  "$PY" -m uvicorn reencuentro_api.main:app --port 8000 --reload &
API_PID=$!

(cd src/web && npm run dev -- --port 5173) &
WEB_PID=$!

trap 'kill "$API_PID" "$WEB_PID" 2>/dev/null' EXIT INT TERM
wait "$API_PID" "$WEB_PID"
