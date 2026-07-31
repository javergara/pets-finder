# Estado actual

**Fase activa:** 2 — Investigación de producto (completa, pendiente checkpoint del usuario)
**Feature en progreso:** ninguna (todas en `todo`; la primera se activa al iniciar Fase 7)

## Hecho en esta fase
- `docs/product-research.md`: producto, roles, decisiones de mecánica ya tomadas (y por qué), flujo de adopción E2E, fórmula de afinidad, validación de las 11 pantallas de `design/prototypes/HANDOFF.md`, alcance MVP vs. backlog.
- `feature_list.json` poblado con 15 items: 5 `milestone: mvp` (01-05), 2 `post-mvp` (06-07), 8 `backlog` (08-15). Todos en `status: todo`, ids únicos, cero `in_progress`.

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente.
- Fuente de verdad de producto: `design/prototypes/HANDOFF.md`.
- Stack MVP: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local (ADR pendiente en Fase 3).
- Match no mutuo; cuestionario de hogar obligatorio → en MVP se resuelve con `HomeProfile` sintético (flujo interactivo = feature 08, backlog).

## Próximo paso
Checkpoint de Fase 2 con el usuario. Luego Fase 3: `docs/architecture.md` + ADRs (stack, match no-mutuo/reglas de negocio en backend).
