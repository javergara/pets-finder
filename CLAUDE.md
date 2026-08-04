# CLAUDE.md — Adopta

Guía maestra para retomar este proyecto. Si es tu primera vez aquí, lee esto completo antes de tocar código.

## Qué es esto

**Adopta** es una app de adopción de mascotas con descubrimiento tipo swipe, para Bogotá/Colombia (es-CO). Se diferencia de un Tinder-de-mascotas genérico en decisiones de producto deliberadas: **el match no es mutuo** (el like del adoptante crea el match de inmediato, el refugio solo decide sobre la *solicitud de adopción* después), el **cuestionario de hogar es obligatorio** (input del score de afinidad), **no hay lenguaje de descarte** ("Ahora no", nunca "rechazar"), y **no hay comisión** (la monetización futura es apadrinamiento). El detalle completo está en `docs/product-research.md`.

El proyecto se construyó siguiendo un sistema de *harness engineering* (ver `AGENTS.md`) sobre trabajo de diseño preexistente (`design/prototypes/HANDOFF.md` y 3 prototipos interactivos `.dc.html`) que ya existía en este directorio antes de empezar — esa es la fuente de verdad de producto, no un documento genérico inventado desde cero. El razonamiento completo de esa decisión está en `plan.md`.

## Cómo levantarlo en local

```bash
bash init.sh   # una vez (o cuando cambien dependencias): venv, seed, lint, tests — debe quedar en verde
bash dev.sh    # levanta API (FastAPI, :8000) + web (Vite, :5173) juntos, Ctrl+C detiene ambas
```

Abrir `http://localhost:5173/` — redirige a `/descubrir`. No hay login: el adoptante activo es el usuario semilla `id=1` (Ana Martínez, ver `scripts/seed.py`).

Para resetear los datos a un estado limpio en cualquier momento: `python3 scripts/seed.py` (determinista, mismo resultado siempre).

## Mapa del repo

- **`AGENTS.md`** — el mapa real de divulgación progresiva: qué agente/skill usar para cada tipo de tarea, y dónde leer/escribir. Empieza ahí, no aquí, para trabajo día a día.
- **`plan.md`** — el plan original de bootstrap del proyecto, con el contexto de por qué se tomaron las decisiones de producto/stack.
- **`feature_list.json`** — alcance completo, las 15 features (`01`-`15`) en `status: "done"`. Regla dura: máximo un item `in_progress`.
- **`CHECKPOINTS.md`** — qué significa "terminado", por feature y globalmente. Fuente de verdad del revisor.
- **`docs/product-research.md`** — producto: roles, decisiones de mecánica y por qué, flujo de adopción, fórmula de afinidad.
- **`docs/architecture.md`** + **`docs/decisions/`** — arquitectura y ADRs (stack, match no-mutuo como regla de backend, afinidad calculada al vuelo, WebSockets para chat en tiempo real en vez de un BaaS externo).
- **`docs/conventions.md`** — estilo de código, estructura de carpetas, tests, commits.
- **`docs/verification.md`** — evidencia real de que el MVP funciona (salida de `init.sh`, cobertura de tests, recorrido manual en navegador).
- **`design/design-system.md`** + **`design/screens/*.md`** — tokens visuales y spec de las 11 pantallas. **`design/prototypes/`** — prototipos interactivos originales (referencia).
- **`.claude/agents/`** — líder/implementador/revisor/investigador/diseñador (subagentes del propio Claude Code para este repo). **`.claude/skills/`** — seed-data, db-migrations, run-verification, update-memory, match-scoring.
- **`progress/current.md`** (estado vivo) y **`progress/history.md`** (bitácora) — leer `current.md` antes de cualquier trabajo no trivial.
- **`memory/memory.md`** — gotchas y decisiones de proceso (p. ej. por qué `ruff`/`black` apuntan a Python 3.10, por qué se usa `oxlint` en vez de `eslint`, por qué `services/affinity.py` es una función pura).
- **`src/api/`** — FastAPI + SQLAlchemy (`adopta_api/{models,schemas,services,routers}`). **`src/web/`** — React + Vite + TS + Tailwind v4.
- **`tests/api/`** (pytest, 195 tests) y **`src/web/src/**/*.test.tsx`** (Vitest, 93 tests).

## Reglas de trabajo (resumen — el detalle vive en cada doc referenciado)

- Una feature a la vez en `feature_list.json`; `init.sh` y el pre-commit lo rechazan si no.
- Patrón líder→implementador→revisor (`AGENTS.md`): el líder planifica, el implementador construye + testea, el revisor corre `init.sh` de verdad y aprueba o rechaza — nunca se autoaprueba una feature.
- Estado en disco: `progress/current.md` antes/después de cada paso no trivial. Nada importante vive solo en el chat.
- Conventional Commits, un commit por unidad lógica de trabajo. Ramas `main`/`develop`.
- Antes de dar una feature por terminada: cada `acceptance` de `feature_list.json` necesita un test real que lo cubra (esto se descubrió y corrigió durante la Fase 7 — ver `memory/memory.md` y `progress/history.md`).

## Estado actual (2026-08-04)

**Proyecto completo: las 15 features de `feature_list.json` en `done`.** MVP (`01`-`05`, 2026-07-31) + post-MVP (`06`-`07`) + backlog completo (`08`-`15`), cada una revisada por un agente revisor independiente que corrió `bash init.sh` de verdad y verificó manualmente en navegador antes de aprobar. Estado final: 195 tests de API + 93 de frontend, todos en verde, lint/formato limpios.

Funcionalidad completa: registro liviano + cuestionario de hogar interactivo (`08`), filtros de descubrimiento (`06`), perfil del adoptante (`07`), panel del refugio con publicación de mascotas y revisión de solicitudes (`09`), acciones del refugio sobre la solicitud — agendar visita / pedir info / descartar (`10`), chat en tiempo real adoptante↔refugio sobre WebSockets propios (`11`, ver ADR 0004), apadrinamiento sin pasarela de pago real (`12`), favoritos (`13`), mapa de refugios sin dependencias externas (`14`), y landing pública en `/` (`15`).

No queda trabajo pendiente en `feature_list.json`. Para retomar el proyecto con trabajo nuevo: definir una feature nueva (no prevista en el alcance original) siguiendo el mismo patrón líder→implementador→revisor, o revisar `docs/product-research.md` §7 si hace falta repensar el alcance de cero.
