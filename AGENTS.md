# AGENTS.md — mapa de divulgación progresiva

Este archivo **no contiene las reglas**, apunta a dónde están y cuándo leerlas. No cargues todo `docs/` de una vez: lee solo lo que tu tarea necesita.

> Contexto del proyecto: **Reencuentro** (mascotas perdidas/encontradas post-terremoto) + su **fase 2, el módulo de adopción** (`/adoptar`). La era anterior (**Adopta**) vive en la rama `adopta-v1` — no la toques salvo para leer: **`git show origin/adopta-v1:ruta`** (o el tag `adopta-v1.0.0`; `adopta-v1` a secas no resuelve, no hay rama local).

## Dónde vive el módulo de adopción (fase 2)

Se portó **a mano** desde `adopta-v1`, archivo por archivo — no hay merge ni cherry-pick de esa rama, que sigue siendo archivo histórico intocable.

- **Backend** (`src/api/reencuentro_api/`): modelos `pet`, `home_profile`, `swipe`, `match`, `favorite`; servicios `afinidad`, `descubrir`, `filtros`, `solicitudes` (+ `titulos.titulo_pet`); routers `pets`, `swipes`, `solicitudes`, `favoritos` (+ el perfil de hogar dentro de `users` y la vista de bots dentro de `paginas`).
- **Frontend** (`src/web/src/`): 9 rutas bajo `/adoptar` en `App.tsx`; pantallas `CatalogoAdopcion`, `PublicarMascota`, `DescubrirMascotas`, `CuestionarioHogar`, `MisSolicitudes`, `SolicitudDetalle`, `MisFavoritas`, `MascotaDetalle`, `EditarMascota`; utilidades puras en `lib/adopcion.ts` y `lib/hogar.ts`.
- **Esquema**: cuatro `.sql` en `migrations/` con su anti-drift en `tests/api/test_migracion_*.py`. ⚠️ **Escritos y sin ejecutar** — bloquean el merge a `main`.

**ADRs que lo gobiernan**, y que hay que leer antes de cambiarle la mecánica:

- **0002** (heredado) — el match **no es mutuo**: el swipe-derecha crea la solicitud de inmediato, sin que el publicador acepte nada. Lo que él decide después es el **estado**.
- **0003** (heredado) — la **afinidad se calcula al vuelo**, sin caché ni columna: cambiar el perfil de hogar cambia el score en el siguiente request, sin paso de invalidación.
- **0013** (nuevo) — la comunicación de una solicitud es **WhatsApp directo, sin chat interno**. Supera al ADR 0004 (chat con WebSockets), que queda archivado con `adopta-v1`: su `ConnectionManager` en memoria no funciona en serverless.
- **Recorte deliberado**: el **apadrinamiento** del backlog original no se implementó (no hay pasarela de pagos y no se hace a medias). Ver `docs/product-research.md` §11.
- **Contexto del portado**: `docs/integracion-adopcion.md` (las diferencias de stack entre las dos eras).

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
| Investigar producto/mercado | `researcher` | `docs/product-research.md` | `docs/product-research.md` |
| Diseñar/formalizar una pantalla | `designer` | `design/design-system.md` | `design/design-system.md` (los tokens son la fuente; ya no hay prototipos en el árbol) |
| Generar/actualizar datos semilla | skill `seed-data` | `docs/product-research.md`, `src/api/reencuentro_api/services/ciudades.py` | `scripts/seed.py`, fotos en `data/media/seed/` |
| Cambiar el esquema (SQLite local **y** Postgres de prod) | skill `db-migrations` | `docs/architecture.md` §2, `migrations/README.md`, `src/api/reencuentro_api/models/` | `src/api/reencuentro_api/models/`, **`migrations/AD-0N-<tabla>.sql` + su anti-drift en `tests/api/`**, notas en `changes.md` |
| Correr verificación completa | skill `run-verification` | `init.sh`, `CHECKPOINTS.md` | `docs/verification.md` |
| Registrar aprendizajes/errores | skill `update-memory` | (lo que pasó en la sesión) | `memory/memory.md`, `changes.md`, `progress/history.md` |
| Arreglar un bug | `implementer` (bug = paso no planificado, pasa igual por revisor) | `changes.md` (buscar cuándo se introdujo), `docs/conventions.md` | código + entrada en `changes.md` |
| Hacer un release | `reviewer` + `run-verification` | `CHANGELOG.md`, `docs/verification.md` | `CHANGELOG.md` |

## Dónde está cada cosa (no lo dupliques aquí, ve directo)

- **Alcance y estado de features:** `feature_list.json` (máx. 1 `in_progress`, verificado por `init.sh` y por el pre-commit hook) + `feature_list_adopcion.json` (backlog fuente de la fase 2; los items se copian al primero al arrancarlos, y el revisor marca `done` en **los dos**).
- **Qué esquema tiene producción y por qué:** `migrations/README.md` (tabla con el estado de cada `.sql`) + `docs/architecture.md` §2. **Nada de esquema se crea solo en el deploy** (`SKIP_DB_CREATE_ALL=1`).
- **Qué es "estado final correcto":** `CHECKPOINTS.md`.
- **Por qué el producto es como es:** `docs/product-research.md`. **Por qué se pivotó:** `docs/decisions/0005-pivot-reencuentro.md`.
- **Por qué la arquitectura es como es:** `docs/architecture.md` + `docs/decisions/*.md` (ADRs).
- **Cómo se escribe código en este repo:** `docs/conventions.md`.
- **Cómo se ve la app:** `design/design-system.md` (tokens; perdido=`danger`, encontrado=`forest`).
- **Estado vivo de la sesión:** `progress/current.md`. **Bitácora histórica:** `progress/history.md`.
- **Aprendizajes de proceso:** `memory/memory.md`. **Cambios granulares:** `changes.md`. **Cambios de release:** `CHANGELOG.md`.
- **Cómo retomar todo el proyecto de cero:** `CLAUDE.md`.

## Regla dura de estado

Antes de cualquier acción no trivial: leer `progress/current.md`. Al terminar un paso: actualizarlo. Nunca dejar una decisión importante solo en el chat.
