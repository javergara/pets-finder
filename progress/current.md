# Estado actual

**Fase activa:** 7 — MVP local con datos artificiales (implementación completa; falta revisión formal del revisor)
**Feature en progreso:** `01-foundations-data` (backend + frontend implementados y verificados manualmente; pendiente de aprobación por el revisor antes de pasar a `done`)

## Hecho en esta fase (frontend)
- Scaffold Vite + React + TypeScript (`src/web`), + React Router, Tailwind v4 (`@tailwindcss/vite`, tokens en `@theme` de `index.css` mapeados 1:1 a `design/design-system.md`), Vitest + Testing Library.
- `api/client.ts` + `api/types.ts`: cliente tipado hacia el backend.
- `components/SwipeCard.tsx`: gesto de swipe con Pointer Events (arrastre, umbral 110px, sellos, retorno animado) + equivalentes de teclado (`←`/`→`/`Enter`) y botones — la ruta accesible obligatoria del design-system. 3 tests (render, click, teclado) en verde.
- `components/MatchModal.tsx`, `screens/{Descubrir,MascotaDetalle,MisMatches}.tsx` — cubren `02-swipe-deck`, `03-pet-profile`, `04-matches`.
- `dev.sh`: un solo comando levanta API (uvicorn) + web (vite) en paralelo.
- **Verificado en navegador real** (Chrome): deck con fotos reales cargó y ordenó por afinidad, like creó el match y disparó el modal, matches y ficha de mascota mostraron los datos correctos, sin errores de consola.
- Corregido: detección de scripts `lint`/`test` de `src/web` en `init.sh` era frágil (parseaba `npm run --silent`, que suprime el listado) — reemplazada por lectura directa de `package.json`.
- `bash init.sh` corre **completo y en verde**: sistema, `feature_list.json`, venv, pre-commit, seed, npm install, ruff+black, oxlint, pytest (9/9), vitest (3/3).

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente. Stack: React+Vite+TS+Tailwind (v4) / FastAPI+SQLAlchemy / SQLite local. Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).
- Desviaciones documentadas de lo anticipado en fases anteriores: oxlint en vez de eslint (memory.md), Tailwind v4 con `@theme` en vez de config JS+PostCSS, ruff/black `target-version=py310` (no py311).
- Usuario demo: `id=1` (Ana Martínez).

## Próximo paso
Invocar al **revisor** (`.claude/agents/reviewer.md`) para una verificación independiente contra `CHECKPOINTS.md` antes de marcar `01-05` como `done` en `feature_list.json` — el implementador (esta sesión) no se autoaprueba.
