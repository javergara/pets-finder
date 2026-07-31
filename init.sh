#!/usr/bin/env bash
# Verificación e inicialización del proyecto Adopta. Idempotente: correrlo
# varias veces seguidas no debe romper nada ni duplicar trabajo.
# Uso: bash init.sh
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

FAILED=0
say()  { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
skip() { printf '  \033[33m⚠ omitido:\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; FAILED=1; }

# ---------------------------------------------------------------------------
say "1. Dependencias del sistema"
for bin in python3 node npm; do
  if command -v "$bin" >/dev/null 2>&1; then
    ok "$bin encontrado ($("$bin" --version 2>&1 | head -n1))"
  else
    fail "$bin no está instalado — requerido"
  fi
done

# ---------------------------------------------------------------------------
say "2. feature_list.json"
if [ -f feature_list.json ]; then
  if python3 scripts/validate_feature_list.py feature_list.json; then
    ok "feature_list.json válido"
  else
    fail "feature_list.json inválido (ver detalle arriba)"
  fi
else
  fail "feature_list.json no existe"
fi

# ---------------------------------------------------------------------------
say "3. Entorno Python (.venv)"
if command -v python3 >/dev/null 2>&1; then
  if [ ! -d .venv ]; then
    python3 -m venv .venv && ok "venv creado en .venv/" || fail "no se pudo crear .venv"
  else
    ok ".venv ya existe"
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --quiet --upgrade pip
  if [ -f requirements-dev.txt ]; then
    pip install --quiet -r requirements-dev.txt && ok "dependencias de desarrollo instaladas"
  fi
  if [ -f src/api/requirements.txt ]; then
    pip install --quiet -r src/api/requirements.txt && ok "dependencias de la API instaladas"
  else
    skip "src/api/requirements.txt no existe todavía (API no implementada, ver Fase 7)"
  fi
else
  fail "sin python3 no se puede preparar el entorno"
fi

# ---------------------------------------------------------------------------
say "4. Pre-commit hook"
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install --install-hooks >/dev/null 2>&1 && ok "hook de pre-commit instalado" \
    || fail "no se pudo instalar el hook de pre-commit"
else
  skip "pre-commit no disponible en el entorno actual"
fi

# ---------------------------------------------------------------------------
say "5. Datos semilla (SQLite)"
if [ -f scripts/seed.py ]; then
  python3 scripts/seed.py && ok "seed corrido, data/app.db poblado" || fail "scripts/seed.py falló"
else
  skip "scripts/seed.py no existe todavía (ver Fase 7)"
fi

# ---------------------------------------------------------------------------
say "6. Frontend (src/web)"
if [ -f src/web/package.json ]; then
  (cd src/web && npm install --silent) && ok "dependencias de src/web instaladas" \
    || fail "npm install falló en src/web"
else
  skip "src/web/package.json no existe todavía (ver Fase 7)"
fi

# ---------------------------------------------------------------------------
say "7. Lint"
if command -v ruff >/dev/null 2>&1 && [ -d src/api ] && find src/api -name '*.py' -print -quit | grep -q .; then
  ruff check src/api && ok "ruff sin errores" || fail "ruff encontró errores en src/api"
  black --check src/api && ok "black: formato correcto" || fail "black encontró código sin formatear en src/api"
else
  skip "sin archivos .py en src/api todavía"
fi
if [ -f src/web/package.json ] && (cd src/web && npm run --silent | grep -q '^  lint$' 2>/dev/null); then
  (cd src/web && npm run lint --silent) && ok "eslint sin errores" || fail "eslint encontró errores en src/web"
else
  skip "sin script 'lint' en src/web todavía"
fi

# ---------------------------------------------------------------------------
say "8. Tests"
if [ -d tests/api ] && find tests/api -name 'test_*.py' -print -quit | grep -q .; then
  pytest tests/api && ok "tests de API pasan" || fail "tests de API fallaron"
else
  skip "sin tests en tests/api todavía"
fi
if [ -f src/web/package.json ] && (cd src/web && npm run --silent | grep -q '^  test$' 2>/dev/null); then
  (cd src/web && npm run test --silent) && ok "tests de web pasan" || fail "tests de web fallaron"
else
  skip "sin script 'test' en src/web todavía"
fi

# ---------------------------------------------------------------------------
say "Resultado"
if [ "$FAILED" -eq 0 ]; then
  printf '\033[32mTodo en verde.\033[0m\n'
  exit 0
else
  printf '\033[31mHay pasos en rojo — revisar arriba.\033[0m\n'
  exit 1
fi
