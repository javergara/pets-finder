# Estado actual

**Fase activa:** 1 — Bootstrap + Git
**Feature en progreso:** ninguna (feature_list.json aún vacío; se puebla en Fase 2)

## Hecho en esta fase
- `git init`, identidad local de git configurada (sin tocar config global).
- `.gitignore`, `.env.example`, `README.md`, `feature_list.json` (esqueleto).
- Diseño preexistente (`design/HANDOFF.md`, 3 prototipos `.dc.html`, `ios-frame.jsx`, `support.js`) movido a `design/prototypes/` tal cual, sin modificar contenido.
- Estructura de carpetas objetivo creada: `docs/`, `design/screens`, `design/assets`, `data/seed`, `progress/`, `memory/`, `src/api`, `src/web`, `tests/`, `scripts/`, `.claude/agents`, `.claude/skills`.

## Decisiones vigentes (ver plan.md para contexto completo)
- Producto = **Adopta** (no "PawMatch"), es-CO únicamente, sin i18n bilingüe.
- Fuente de verdad de producto: `design/prototypes/HANDOFF.md`.
- Stack MVP: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local (ADR pendiente en Fase 3).
- Match no mutuo; cuestionario de hogar obligatorio (para MVP, `HomeProfile` sintético en seed; flujo interactivo de onboarding queda en backlog).

## Próximo paso
Rama `develop`, primer commit, mostrar árbol + `feature_list.json` inicial + commit al usuario para checkpoint de Fase 1. Luego Fase 2 (product-research.md).
