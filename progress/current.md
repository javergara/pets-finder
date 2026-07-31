# Estado actual

**Fase activa:** 3 — Arquitectura y ADRs (completa, pendiente checkpoint del usuario)
**Feature en progreso:** ninguna (todas en `todo`; la primera se activa al iniciar Fase 7)

## Hecho en esta fase
- `docs/architecture.md`: vista general (monorepo `src/api`+`src/web`), capas del backend (models/schemas/services/routers), frontend (tokens compartidos con design-system, gestos con Pointer Events crudos reutilizando el prototipo), datos/seed, arranque de un solo comando, y qué queda fuera deliberadamente (auth, realtime, migraciones formales) y por qué no es deuda técnica todavía.
- `docs/decisions/0001-stack-tecnico.md`: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local; por qué no Supabase/Firebase todavía (HANDOFF.md lo sugiere para chat en tiempo real, que es backlog).
- `docs/decisions/0002-mecanica-match-no-mutuo.md`: el match no-mutuo y el HomeProfile obligatorio como reglas de negocio de **backend** (Swipe crea Match automáticamente), no solo de copy — para que no se implemente por error un flujo de doble consentimiento.
- `docs/decisions/0003-afinidad-calculada-al-vuelo.md`: por qué el score no se persiste (evita invalidación de caché al editar HomeProfile/Pet).

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente.
- Fuente de verdad de producto: `design/prototypes/HANDOFF.md`.
- Stack MVP: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local (formalizado en ADR 0001).
- Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).

## Próximo paso
Checkpoint de Fase 3 con el usuario. Luego Fase 4: `docs/conventions.md` + linters/formatters + pre-commit.
