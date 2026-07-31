# Estado actual

**Fase activa:** 4 — Convenciones de desarrollo (completa, pendiente checkpoint del usuario)
**Feature en progreso:** ninguna

## Hecho en esta fase
- `docs/conventions.md`: estructura de carpetas (`services/` como capa de lógica pura, separada de `routers/`), convenciones de nombres (Python/TS/rutas HTTP/IDs de features y ADRs), manejo de errores (mensajes en español, sin stack traces, encolado de swipes offline), estrategia de tests (pytest + Vitest, cada `acceptance` de `feature_list.json` con test asociado), formato/lint, y política de commits/ramas.
- `pyproject.toml`: config de `ruff` (lint) + `black` (formato) para `src/api`.
- `.prettierrc.json`: config de formato para `src/web`.
- `.pre-commit-config.yaml`: hooks de `ruff`/`ruff-format` (Python), `prettier` (TS/JS/CSS/JSON), y un hook local que valida que `feature_list.json` tenga como máximo 1 item `in_progress` — probado en aislado, funciona.

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente.
- Stack: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local (ADR 0001).
- Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).

## Pendiente (no bloqueante, se resuelve en Fase 7)
- El hook de pre-commit no se ha activado (`pre-commit install`) porque aún no hay un venv de Python creado — `init.sh` (Fase 5/8) lo instalará como parte del setup.
- La config de ESLint para `src/web` se genera con el scaffold de Vite en Fase 7 (depende del preset elegido), siguiendo las reglas descritas en `docs/conventions.md` §5.

## Próximo paso
Checkpoint de Fase 4 con el usuario. Luego Fase 5: sistema de harness engineering (AGENTS.md, CHECKPOINTS.md, init.sh, progress/, memory/, changes.md, CHANGELOG.md, .claude/agents, .claude/skills, .claude/settings.json).
