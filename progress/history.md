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

## 2026-07-31 — Fase 5: Sistema de harness engineering
- `AGENTS.md`, `CHECKPOINTS.md`, `init.sh` (probado en verde dos veces, idempotente), `scripts/validate_feature_list.py` (probado: rechaza >1 in_progress).
- Corregido `.pre-commit-config.yaml`: el tag `v3.3.3` de `mirrors-prettier` no existe en el repo real; se cambió a `v3.1.0` (última estable disponible). Gotcha registrado en `memory/memory.md`.
- `memory/memory.md`, `changes.md`, `CHANGELOG.md` creados.
- 5 subagentes en `.claude/agents/` (leader, implementer, reviewer, researcher, designer) y 5 skills en `.claude/skills/` (seed-data, db-migrations, run-verification, update-memory, match-scoring).
- `.claude/settings.json` + hooks de post-edit (lint/format) y validación de `feature_list.json` (probados: bloquean con exit 2 un estado inválido).

## 2026-07-31 — Fase 6: Diseño formalizado
- `design/design-system.md` formalizado desde `design/prototypes/HANDOFF.md` §3/§9 (color, tipografía, forma, imágenes, estados, accesibilidad, gesto de swipe). Sin modo oscuro (no estaba diseñado, no se inventó).
- `design/screens/*.md`: las 11 pantallas, detalle completo para las 4 del alcance MVP (descubrir, mascota-detalle, match-modal, mis-matches) y breve para el resto (backlog/post-MVP), cada una etiquetada con su id de `feature_list.json`.

## 2026-07-31 — Fase 7: Implementación del MVP
- Backend (FastAPI+SQLAlchemy+SQLite): modelos, `services/affinity.py` (score puro + reglas duras), `services/matching.py` (match no-mutuo), routers, `scripts/seed.py` (17 mascotas/3 refugios/5 adoptantes, fotos reales con fallback offline). 9 tests iniciales.
- Frontend (React+Vite+TS+Tailwind v4): deck de swipe (Pointer Events + teclado/botones), ficha, modal de match, mis matches. Verificado en Chrome real sin errores de consola. `dev.sh` para un solo comando.
- **Primera revisión del revisor (agente independiente): RECHAZADA.** 3 gaps contra `CHECKPOINTS.md`: inserción de mascotas difíciles de ubicar no implementada, `GET /api/pets/{id}` sin test, estado vacío de matches sin test.
- Corregidos los 3 gaps: `services/deck.py` (inserción cada 4-5 tarjetas) + 6 tests, 3 tests de endpoint, 2 tests de frontend.
- **Segunda revisión: APROBADA.** El revisor verificó línea por línea las correcciones, corrió `init.sh` en verde (18 tests API + 5 web), y marcó `01-foundations-data`, `02-swipe-deck`, `03-pet-profile`, `04-matches`, `05-affinity-score` como `done` en `feature_list.json`.

## 2026-07-31 — Fase 8: Verificación
- `bash init.sh` corrido de nuevo desde working tree limpio: en verde. `docs/verification.md` con evidencia real (salida completa, cobertura de tests por feature, verificación manual E2E en navegador, confirmación de ADR 0002/0003 en código).
- App levantada en local (`dev.sh`) a pedido del usuario para verla en su navegador.

## 2026-07-31 — Fase 9: Cierre
- `CLAUDE.md` escrito: resumen del proyecto, cómo levantarlo, mapa del repo, reglas de trabajo, estado actual y próximos pasos sugeridos.
- `CHANGELOG.md` actualizado a `[0.1.0] - 2026-07-31` (primer MVP funcional), con sección `Added`/`Fixed` completa.
- Bootstrap del proyecto (las 9 fases de `plan.md`) completo. Commit final de cierre.

## 2026-08-03/04 — Cierre del backlog completo (features 06-15)

Tras el cierre del MVP (Fase 9, `01`-`05`), se retomó el proyecto en una sesión continua que completó las 10 features restantes de `feature_list.json`, en orden: `06-filters`, `07-adopter-profile`, `08-onboarding-cuestionario`, `09-shelter-panel`, `10-adoption-request-flow`, `11-chat`, `12-sponsorship`, `13-favorites`, `14-shelter-map`, `15-public-landing`. Las 15 features del proyecto quedan en `status: "done"`.

Cada feature siguió el ciclo completo líder→implementador→revisor (`AGENTS.md`), con el líder completando primero el `acceptance` de las features de backlog que lo tenían vacío (`08`-`15` no traían criterios de aceptación desde la investigación original, a diferencia de `01`-`07`). Las features sin diseño previo en `design/` (`13-favorites`, `14-shelter-map`) se diseñaron desde cero con `AskUserQuestion` para decisiones de arquitectura ambiguas. `11-chat` reabrió el ADR 0001 (documentado en el ADR nuevo 0004): se decidió WebSockets nativos sobre FastAPI en vez de migrar a un BaaS, preservando la reproducibilidad 100% local. `12-sponsorship` y `14-shelter-map` tomaron la misma decisión de fondo (sin pasarela de pago real / sin mapa con tiles externos) por la misma razón.

Cada feature se verificó manualmente en navegador real (Chrome) antes de la aprobación del revisor, además de `bash init.sh` en verde. Estado final: 195 tests de backend (pytest) + 93 de frontend (Vitest), todos en verde. Commits: `c1f4149` (06), `b165cca` (07), `c73ece3` (08), `60528e9` (09), `50c4482` (10), `254192c` (11), `9c5f25f` (12), `9f8e4d6` (13), `c2fb3e2` (14), `cd3467e` (15).

Gotcha de proceso documentado en `memory/memory.md`: el agente revisor rompió temporalmente su propio cambio a `feature_list.json` varias veces (por `git checkout` accidental o por reserialización completa vía `json.dump`), siempre detectado y corregido en la misma sesión antes de commitear.
