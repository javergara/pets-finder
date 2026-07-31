# Historial (append-only)

## 2026-07-31 — Fase 1: Bootstrap + Git
- Se encontró que el directorio de trabajo no estaba vacío: contenía diseño preexistente para "Adopta" (generado con DesignSync) en vez de partir de cero como sugería el prompt genérico original ("PawMatch"). Se acordó con el usuario usar ese diseño como fuente de verdad del producto y mantener FastAPI+SQLite local (no Supabase) para el MVP. Detalle completo en `plan.md`.
- `git init` con identidad local (sin tocar `~/.gitconfig`, autorizado explícitamente por el usuario).
- Diseño existente movido de `design/*` a `design/prototypes/*` sin modificar contenido.
- Creados: `.gitignore`, `.env.example`, `README.md`, `feature_list.json` (esqueleto vacío), estructura de carpetas del repo.

## 2026-07-31 — Fase 2: Investigación de producto
- `docs/product-research.md` redactado a partir de `design/prototypes/HANDOFF.md`, formalizando las decisiones de producto ya tomadas (match no mutuo, cuestionario obligatorio, sin lenguaje de descarte, sin comisión) y documentando el flujo de adopción end-to-end y la fórmula de afinidad.
- `feature_list.json` poblado: 15 features (5 MVP, 2 post-MVP, 8 backlog), todas en `todo`, con `acceptance` verificable para las 5 de MVP.

## 2026-07-31 — Fase 3: Arquitectura y ADRs
- `docs/architecture.md` y tres ADRs: 0001 (stack local FastAPI+SQLite, por qué no Supabase todavía), 0002 (match no-mutuo como regla de backend, no solo copy — Swipe crea Match automáticamente), 0003 (afinidad calculada al vuelo, sin persistir, para evitar invalidación de caché al editar HomeProfile/Pet).

## 2026-07-31 — Fase 4: Convenciones de desarrollo
- `docs/conventions.md`: estructura de carpetas, nombres, manejo de errores, tests, lint/formato, commits/ramas.
- `pyproject.toml` (ruff+black), `.prettierrc.json`, `.pre-commit-config.yaml` (ruff/ruff-format/prettier + hook local que valida máximo 1 `in_progress` en `feature_list.json`, probado en aislado).
