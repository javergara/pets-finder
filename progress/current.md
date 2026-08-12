# Estado vivo — pivot Reencuentro

> Actualizado: 2026-08-12. La era Adopta (15 features done, release 1.0.0) cerró y vive en la rama `adopta-v1` + tag `adopta-v1.0.0` (commit `cde337f`). Este archivo arranca de cero para el pivot.

## Qué está pasando

**Feature activa: `01-pivot-fundaciones` (in_progress).** Pivot del producto a app de reporte de mascotas perdidas/encontradas tras el terremoto del Eje Cafetero (2026-08-10). Plan completo aprobado por el usuario (11 features, ver `feature_list.json` y ADR 0005).

## Decisiones vigentes del pivot (resumen — detalle en ADR 0005)

- Nombre: **Reencuentro**. Contacto directo WhatsApp/tel (sin chat). Registro liviano reutilizado.
- Zonas: Armenia, Pereira, Manizales, Cali, Quibdó, Bogotá + vista "Todo Colombia" (fallback nacional). Fuente de verdad: `services/ciudades.py` (feature 02).
- Un solo modelo `Report` (tipo perdido|encontrado). Upload multipart local (`python-multipart`, única dep nueva).
- `ReporteCard` (feature 05) adapta el JSX de las tarjetas de `adopta-v1` (`git show adopta-v1:src/web/src/components/SwipeCard.tsx`).
- Despliegue (feature 11): Vercel (web) + Render con disco (API).

## Hecho en la feature 01

- [x] Rama `adopta-v1` + tag `adopta-v1.0.0` creados y verificados (`git log adopta-v1 -1` → `cde337f`).
- [x] Borrado masivo del código/tests/diseño de adopción (git rm, ~100 archivos).
- [x] Rename `adopta_api` → `reencuentro_api` (git mv) + adaptación de main/models/schemas/routers/conftest/dev.sh.
- [x] Frontend mínimo: `App.tsx` nuevo (nav Reencuentro), `LandingEmergencia` v1 (2 CTAs), `Registro` con `?volver=` seguro, session con clave nueva + `hasActiveUser()`, client.ts recortado.
- [x] Seed provisional (5 usuarios, determinista). `data/seed/` → `data/media/{seed,uploads}` + .gitignore.
- [x] `feature_list.json` v2 (11 features), CLAUDE.md, AGENTS.md, CHECKPOINTS.md, README, ADR 0005, adenda ADR 0001, product-research y architecture reescritos, conventions/skills/agents actualizados, CHANGELOG Unreleased 2.0.0.
- [x] Verificación parcial: validate_feature_list OK, seed OK, ruff/black OK, pytest 9/9, oxlint OK, vitest 12/12.

## Próximo paso

1. Corrida completa de `bash init.sh` + revisión del diff.
2. Revisor independiente (agente `reviewer`) corre `init.sh` y aprueba → `01-pivot-fundaciones` a `done`.
3. Commit `feat!: pivot a Reencuentro (fundaciones)` en `develop`.
4. Siguiente: `02-reportes-backend` (líder → plan de pasos aquí).

## Veredicto del revisor — feature 01 (2026-08-12): RECHAZADA

Revisión independiente sobre `develop` @ `1aaf320`. `bash init.sh` corrido de verdad en esta sesión: **verde completo** (deps, seed 5 usuarios, ruff/black/oxlint limpios, 9 tests de API + 12 de web). `python3 scripts/validate_feature_list.py feature_list.json` sale 0. Rama `adopta-v1` y tag `adopta-v1.0.0` verificados, ambos en `cde337f`. Commit conventional (`feat!` + BREAKING CHANGE), sin archivos prohibidos, sin dependencias que violen el ADR 0005 (package.json sin leaflet/mapbox/ws; `python-multipart` aún no hace falta — llega en la 03). Web mínima bien cubierta por tests (2 CTAs en `App.test.tsx`; `?volver=` con 4 casos en `Registro.test.tsx`, incluida la URL externa que se ignora).

**No se aprueba** por 3 hallazgos contra el `acceptance` y `CHECKPOINTS.md`. El status queda en `in_progress`; corrige el implementador, no el revisor.

1. **Viola el acceptance 2** ("no queda ninguna referencia a features de adopción en src/"): `src/web/src/lib/mapa.ts` líneas 1-6. El comentario de cabecera referencia la feature de adopción `14-shelter-map` y afirma que las constantes "duplican intencionalmente BOGOTA_LAT_RANGE/BOGOTA_LNG_RANGE de scripts/seed.py" — esas constantes ya no existen en el seed nuevo (grep vacío). El archivo sobrevivió al pivot sin tocarse (no aparece en el diff de `1aaf320`). Además cae en "documentación que describe un comportamiento que el código no tiene" (CHECKPOINTS, sección "Qué NO es un checkpoint válido"). Si se conserva como base para la feature 04 (`coordsDesdeFraccion` parametrizado por zona), el comentario debe reescribirse en términos del pivot; si no, borrar el archivo y su test hasta la 04.

2. **Viola el acceptance 2**: `src/api/reencuentro_api/services/geo.py` líneas 3-4 del docstring: "usada por services/filters.py para el filtro de distancia del deck de descubrimiento (User.lat/lng vs Pet.lat/lng)". `services/filters.py`, el deck de descubrimiento y el modelo `Pet` son features de adopción borradas en este mismo commit. Conservar el haversine es correcto (lo usará `services/coincidencias.py` en la feature 08), pero el docstring debe decir eso.

3. **Viola el checkpoint por feature #1** (cada criterio de `acceptance` con un test que lo ejercite): el acceptance 3 incluye `/health` como parte de la API mínima y no existe ningún test que lo pegue (`grep -rn health tests/` vacío; `test_users.py` solo cubre POST/GET `/api/users`). Falta un test tipo `client.get("/health") == 200, {"status": "ok"}`.

Menores (no bloquean, pero aprovechar la corrección): (a) la entrada de `changes.md` del 2026-08-12 no referencia el hash del commit (`1aaf320`) como piden el checkpoint #4 y el patrón de las entradas anteriores; (b) la nav y los CTAs enlazan rutas aún no registradas (`/reportar/*`, `/reportes`, `/mapa`, `/mis-reportes`) — aceptable en la versión mínima porque está declarado en comentarios y planificado en las features 04/05/07/09, solo se deja constancia.

Próximo paso: el implementador corrige 1-3, y el revisor re-corre `init.sh` + greps antes de pasar `01-pivot-fundaciones` a `done`.
