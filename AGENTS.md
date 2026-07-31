# AGENTS.md — mapa de divulgación progresiva

Este archivo **no contiene las reglas**, apunta a dónde están y cuándo leerlas. No cargues todo `docs/` de una vez: lee solo lo que tu tarea necesita.

## Flujo líder → implementador → revisor

1. **Líder** (`.claude/agents/leader.md`) — toma el único item `in_progress` (o el siguiente `todo` si no hay ninguno) de `feature_list.json`, lo descompone en pasos verificables, y escribe el plan en `progress/current.md`. **No implementa.**
2. **Implementador** (`.claude/agents/implementer.md`) — ejecuta un paso del plan: escribe código de producto + sus tests. Deja el resultado en disco (código + entrada en `changes.md`) y devuelve al líder solo una referencia ligera (archivo + resumen de una línea). **No se autoaprueba.**
3. **Revisor** (`.claude/agents/reviewer.md`) — corre `bash init.sh`, contrasta contra `CHECKPOINTS.md` y `docs/conventions.md`, y aprueba o devuelve con feedback escrito en `progress/current.md`. **No edita código de producto.**

Se invoca líder al empezar o retomar una feature; implementador por cada paso del plan; revisor al terminar cada paso y obligatoriamente antes de marcar una feature `done` en `feature_list.json`.

## Tabla de routing

| Tarea | Agente / skill | Lee | Escribe |
|---|---|---|---|
| Planificar la siguiente feature | `leader` | `feature_list.json`, `progress/current.md`, `CHECKPOINTS.md` | `progress/current.md` (plan de pasos) |
| Implementar un paso | `implementer` | `progress/current.md`, `docs/conventions.md`, `docs/architecture.md` | código en `src/`, tests en `tests/`, `changes.md` |
| Revisar / aprobar una feature | `reviewer` | `CHECKPOINTS.md`, `docs/conventions.md`, salida de `init.sh` | `progress/current.md` (veredicto), `feature_list.json` (status → `done` si aprueba) |
| Investigar producto/mercado | `researcher` + skill nada específico | `docs/product-research.md`, `design/prototypes/HANDOFF.md` | `docs/product-research.md` |
| Diseñar/formalizar una pantalla | `designer` | `design/prototypes/HANDOFF.md`, `design/design-system.md` | `design/screens/*.md` |
| Generar/actualizar datos semilla | skill `seed-data` | `docs/product-research.md` §5-6, `data/seed/` | `scripts/seed.py`, `data/seed/*.json`, `data/seed/CREDITS.md` |
| Cambiar el esquema SQLite | skill `db-migrations` | `docs/architecture.md` §2, `src/api/adopta_api/models/` | `src/api/adopta_api/models/`, notas en `changes.md` |
| Correr verificación completa | skill `run-verification` | `init.sh`, `CHECKPOINTS.md` | `docs/verification.md` |
| Registrar aprendizajes/errores | skill `update-memory` | (lo que pasó en la sesión) | `memory/memory.md`, `changes.md`, `progress/history.md` |
| Calcular compatibilidad adoptante↔mascota | skill `match-scoring` | `docs/product-research.md` §5, `docs/decisions/0003-*.md` | `src/api/adopta_api/services/affinity.py` |
| Arreglar un bug | `implementer` (bug = paso no planificado, pasa igual por revisor) | `changes.md` (buscar cuándo se introdujo), `docs/conventions.md` | código + entrada en `changes.md` |
| Hacer un release | `reviewer` + `run-verification` | `CHANGELOG.md`, `docs/verification.md` | `CHANGELOG.md` |

## Dónde está cada cosa (no lo dupliques aquí, ve directo)

- **Alcance y estado de features:** `feature_list.json` (máx. 1 `in_progress`, verificado por `init.sh` y por el pre-commit hook).
- **Qué es "estado final correcto":** `CHECKPOINTS.md`.
- **Por qué el producto es como es:** `docs/product-research.md`.
- **Por qué la arquitectura es como es:** `docs/architecture.md` + `docs/decisions/*.md` (ADRs).
- **Cómo se escribe código en este repo:** `docs/conventions.md`.
- **Cómo se ve la app:** `design/design-system.md`, `design/screens/*.md`, prototipos interactivos en `design/prototypes/`.
- **Estado vivo de la sesión:** `progress/current.md`. **Bitácora histórica:** `progress/history.md`.
- **Aprendizajes de proceso:** `memory/memory.md`. **Cambios granulares:** `changes.md`. **Cambios de release:** `CHANGELOG.md`.
- **Cómo retomar todo el proyecto de cero:** `CLAUDE.md`.

## Regla dura de estado

Antes de cualquier acción no trivial: leer `progress/current.md`. Al terminar un paso: actualizarlo. Nunca dejar una decisión importante solo en el chat.
