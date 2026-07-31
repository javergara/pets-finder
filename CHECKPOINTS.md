# CHECKPOINTS.md — qué significa "terminado" (fuente de verdad del revisor)

El revisor no aprueba nada que no cumpla lo de este archivo, con evidencia ejecutable — no basta con que "parezca" correcto.

## Checkpoint global (aplica siempre)

- `bash init.sh` termina en verde: dependencias instaladas, seed corrido, linters sin errores, **todos** los tests pasan, `feature_list.json` válido (máximo 1 `in_progress`, ids únicos, `depends_on` referencian ids existentes).
- Ningún commit incluye `data/app.db`, `.env`, `node_modules/`, `.venv/`, ni fotos de `data/seed/images/`.
- El mensaje del último commit sigue Conventional Commits y describe el porqué, no solo el qué.
- `progress/current.md` refleja el estado real (no quedó una fase o feature "en progreso" sin actualizar tras terminarla).

## Checkpoint por feature (antes de pasar `status` a `done` en `feature_list.json`)

1. Todos los criterios de `acceptance` de la feature en `feature_list.json` tienen un test que los ejercita, y ese test pasa.
2. El código sigue `docs/conventions.md` (estructura de carpetas, nombres, manejo de errores) — el revisor lo verifica leyendo el diff, no solo corriendo el linter.
3. Si la feature toca una decisión registrada en un ADR (`docs/decisions/`), el código es consistente con esa decisión (p. ej. una feature de matches no puede introducir un endpoint de "aceptar match" — viola ADR 0002).
4. Hay al menos una entrada nueva en `changes.md` referenciando la feature y el commit.
5. Ninguna otra feature quedó `in_progress` en simultáneo.
6. El implementador no marcó la feature como aprobada — solo el revisor puede pasarla a `done`.

## Checkpoint por fase del proyecto (bootstrap, ver `plan.md`)

| Fase | Estado final correcto |
|---|---|
| 1 — Bootstrap + Git | Repo git con `main`+`develop`, `.gitignore`/`.env.example` presentes, primer commit limpio, diseño preexistente preservado sin modificar. |
| 2 — Investigación | `docs/product-research.md` completo, `feature_list.json` poblado con `acceptance` verificable en cada item de alcance MVP, cero `in_progress`. |
| 3 — Arquitectura | `docs/architecture.md` + ADRs cubriendo al menos: stack, mecánica de match, estrategia de afinidad. |
| 4 — Convenciones | `docs/conventions.md` + config de lint/formato + `.pre-commit-config.yaml` funcional (probado, no solo escrito). |
| 5 — Harness | Todos los archivos de este checkpoint global existen y `init.sh` corre (aunque falle por falta de código de producto todavía, debe **ejecutarse** sin error de sintaxis/setup). |
| 6 — Diseño | `design/design-system.md` + un archivo por pantalla en `design/screens/` cubriendo las 11 pantallas de `design/prototypes/HANDOFF.md` (mínimo las 5 del alcance MVP con detalle completo, el resto puede ser más breve). |
| 7 — MVP | La app levanta en local con el comando único documentado, seed determinista corrido, las 5 features MVP de `feature_list.json` en `status: done` con revisor aprobando cada una. |
| 8 — Verificación | `bash init.sh` en verde con evidencia capturada en `docs/verification.md` (salida real de comandos, no descripción). |
| 9 — Cierre | `CLAUDE.md` completo y verificado (alguien nuevo podría retomar el proyecto solo con ese archivo + este mapa), `CHANGELOG.md`/`changes.md`/`progress/history.md`/`memory/memory.md` al día, commit final limpio. |

## Qué NO es un checkpoint válido

- "Los tests deberían pasar" sin haberlos corrido.
- Una feature en `done` sin que el revisor haya corrido `init.sh` en esa sesión.
- Documentación que describe un comportamiento que el código no tiene (revisar código, no solo el docstring/comentario).
