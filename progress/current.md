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

## Veredicto del revisor — feature 01 (2026-08-12, segunda pasada): APROBADA

Re-revisión sobre `develop` @ `a728850` (`fix: atender hallazgos del revisor en la feature 01`). Los 3 hallazgos de la primera pasada quedaron corregidos y verificados por diff y por ejecución real:

1. `src/web/src/lib/mapa.ts`: cabecera reescrita en términos del pivot (versión provisional de la feature 01 con bbox de Bogotá, parametrización por zona en la 04, referencia al ADR 0005 §5). Ya no menciona `14-shelter-map` ni constantes de seed inexistentes.
2. `src/api/reencuentro_api/services/geo.py`: el docstring apunta a su consumidor real del pivot (`services/coincidencias.py`, feature 08).
3. `tests/api/test_health.py` nuevo: `GET /health` → 200 `{"status": "ok"}` — el acceptance 3 queda cubierto por test directo.
4. (Menor a) La entrada de `changes.md` del pivot ahora referencia el commit `1aaf320`.

Evidencia de esta sesión:

- `bash init.sh` corrido de verdad: **verde completo** — deps, seed, ruff/black/oxlint limpios, **10/10 tests de API** (users + geo + health) y **12/12 de web**.
- Grep del acceptance 2 (`adopta_api|adopta|swipe|match|affinity|afinidad|apadrin|sponsor|favorit|refugio|shelter|deck|descubrir|cuestionario`, case-insensitive) sobre `src/`, `scripts/`, `tests/`: **cero coincidencias** en código vivo.
- `git branch`/`git tag`: `adopta-v1` y `adopta-v1.0.0` intactos, ambos en `cde337f` (`git rev-parse`).
- `python3 scripts/validate_feature_list.py feature_list.json` → exit 0, antes y después del cambio de status.
- `feature_list.json`: `01-pivot-fundaciones` pasada a `done` con edición de texto puntual sobre la línea 9; `git diff feature_list.json` confirma que **solo** cambió esa línea (gotcha de `memory/memory.md` §2026-08-04 respetado — sin `json.dump`, sin `git checkout`).
- Consistencia con ADRs: sin chat interno ni librerías de mapas (ADR 0005 §3/§5), sin dependencias nuevas (la única prevista, `python-multipart`, llega en la 03).

Pendiente de la sesión principal: commit del cambio de status + este veredicto. Siguiente feature: `02-reportes-backend` (líder planifica aquí).

## Veredicto del revisor — feature 02 (2026-08-12): RECHAZADA (1 hallazgo puntual)

Revisión independiente sobre `develop` @ `32ddbf3`. Casi todo pasa con evidencia ejecutable; queda **un** hallazgo que contradice el acceptance 4 y el propio docstring del seed. El status queda en `in_progress`; corrige el implementador.

### Lo que pasa (verificado en esta sesión)

- `bash init.sh` corrido de verdad: **verde completo** — 32/32 tests de API (ciudades 5, geo 5, health 1, reports 17, users 4) + 12/12 de web, ruff/black/oxlint limpios.
- **Acceptance 1** (POST ambos tipos + 422 condicionales): cubierto por tests directos — 201 perdido, 201 encontrado, y 6 casos 422 (`encontrado` sin `situacion`, `perdido` con `situacion`, `encontrado` con `nombre_mascota`, zona desconocida, `Otro` sin `ciudad_texto`, teléfono vacío) en `test_reports.py`.
- **Acceptance 2** (filtros + exclusión de reunidos + orden): cubierto — `test_listado_excluye_reunidos_por_defecto`, `test_listado_ordena_por_fecha_evento_descendente`, `test_listado_filtra_por_tipo_especie_y_zona`, `test_listado_estado_reunido_y_todos`.
- **Acceptance 3** (403/404 en español): cubierto — `test_editar_reporte_ajeno_devuelve_403_en_espanol` asevera el texto en español; `test_obtener_reporte_inexistente_devuelve_404` ejercita el 404 (mensaje "El reporte 9999 no existe" verificado por lectura de código).
- **Acceptance 5** (bounding boxes contienen su centro): cubierto — `test_cada_zona_contiene_su_propio_centro`, más `test_colombia_contiene_todas_las_zonas` y el guard del propio seed que aborta si una coord cae fuera de su caja.
- **Acceptance 4, parcial**: fallback SVG verificado (el loro, especie "otro", id 9, queda con `/media/seed/report_9.svg` en disco); la tabla `reports` es determinista fila a fila — dos corridas de `.venv/bin/python3 scripts/seed.py` y `diff` del dump completo de `reports`: **idéntico** (17 filas, incluyendo `foto_url` y `creado_en`).
- Consistencia con ADR 0005 y CHECKPOINTS: modelo único `Report` (§2), estados solo activo|reunido (sin lenguaje de fracaso), sin dependencias nuevas, comentario de rutas literales-antes-que-dinámicas en `routers/reports.py` y `main.py`, entrada en `changes.md`.

### Hallazgo que bloquea

**Acceptance 4** dice "dos corridas seguidas producen los mismos datos" y el docstring de `scripts/seed.py` afirma "timestamps `creado_en`/`resuelto_en` explícitos — dos corridas seguidas producen exactamente los mismos datos". Verificado por ejecución real: la tabla **`users` NO es determinista** — `users.creado_en` difiere entre corridas (ej. `2026-08-12 14:55:46.876455` vs `14:55:47.073749` para Ana Martínez) porque el seed no fija `creado_en` en los `User` y corre el default `datetime.now` del modelo. El seed solo fija `creado_en` en los `Report`. Además de fallar el criterio literal, el docstring cae en "documentación que describe un comportamiento que el código no tiene" (CHECKPOINTS).

**Corrección sugerida** (implementador, no revisor): asignar `creado_en` explícito a los `User` del seed (mismo patrón que los reportes, p. ej. `datetime(2026, 8, 12, 8, 0)`) y re-verificar con doble corrida + `diff` de los dumps de `users` **y** `reports`.

Menores (no bloquean): (a) la entrada de `changes.md` dice "(en revisión)" sin hash — añadir `32ddbf3` (más el hash del fix) al aprobar, como pide el checkpoint #4; (b) el comando literal `python3 scripts/seed.py` requiere el venv (`.venv/bin/python3` o venv activado) porque `requests` no está en el Python del sistema — es el mismo modo en que lo corre `init.sh`, solo se deja constancia.

Próximo paso: fix puntual del seed, y el revisor re-verifica (doble corrida + diff ambas tablas) antes de pasar `02-reportes-backend` a `done`.

## Veredicto del revisor — feature 02 (2026-08-12, segunda pasada): APROBADA

Re-revisión sobre `develop` @ `0dab9a6` (`fix: creado_en explícito en los usuarios del seed`). El único hallazgo bloqueante de la primera pasada quedó corregido y lo re-verifiqué con ejecución propia, no solo con el reporte de la sesión principal:

- **Fix verificado por diff**: los `User` del seed llevan `creado_en=datetime(2026, 8, 12, 8, 0)` explícito (mismo patrón que los reportes), con comentario que documenta el porqué. El docstring del seed ("dos corridas producen exactamente los mismos datos") ahora es verdadero.
- **Determinismo total re-verificado en esta sesión**: dos corridas de `.venv/bin/python3 scripts/seed.py` + `diff` de los dumps completos de **ambas** tablas (`users`, 5 filas; `reports`, 17 filas) → **idénticos byte a byte** (`users.creado_en` fijo en `2026-08-12 08:00:00.000000`).
- **`bash init.sh` re-corrido sobre el árbol con el fix: verde completo** — 32/32 tests de API + 12/12 de web, ruff/black/oxlint limpios.
- **Menor (a) resuelto**: la entrada de `changes.md` ahora referencia el commit `32ddbf3` (+ fix de revisión).
- El resto del acceptance ya estaba verificado en la primera pasada (misma sesión): tests directos para POST ambos tipos + 6 casos 422, filtros/exclusión de reunidos/orden desc, 403/404 en español, bounding boxes contienen su centro (`test_ciudades.py`), fallback SVG (loro → `report_9.svg`).
- `feature_list.json`: `02-reportes-backend` pasada a `done` con edición de texto puntual sobre la línea 22; `git diff feature_list.json` confirma que **solo** cambió esa línea (sin `json.dump`, sin `git checkout`); `validate_feature_list.py` → exit 0.

Pendiente de la sesión principal: commit del cambio de status + este veredicto. Siguiente: `03-upload-fotos` o `05-listado-reportes` (ambas dependen solo de lo ya cerrado; decide el líder).

## Veredicto del revisor — feature 03 (2026-08-12): RECHAZADA (bug real encontrado en la verificación en vivo)

Revisión independiente sobre `develop` @ `b1f19ed`. `bash init.sh` corrido de verdad: verde completo (37/37 tests de API + 14/14 de web, lint limpio). Los tests unitarios del acceptance existen y pasan (201 jpeg/webp con nombre uuid ≠ filename hostil, 415 y 413 en español sin dejar restos, `FotoUpload` con preview local + callback `foto_url` + error sin callback). `python-multipart==0.0.17` es la única dependencia nueva, como prevé el ADR 0005 §6. Pese a eso, **la feature no cumple su propio propósito en la app real**:

### Hallazgo que bloquea

**El `foto_url` que devuelve `POST /api/uploads` responde 404 en la app real.** Verificado en vivo con `TestClient` sobre `reencuentro_api.main:app` (sin monkeypatch): subir un JPEG devuelve 201 con `/media/uploads/f9f1...jpg`, pero `GET` de esa misma URL → **404**. Causa raíz, confirmada imprimiendo las constantes de ambos módulos:

- `routers/uploads.py` línea 18: `REPO_ROOT = Path(__file__).resolve().parents[3]`. Ese archivo vive un nivel más profundo que `main.py` (está dentro de `routers/`), así que `parents[3]` resuelve a **`src/`**, no a la raíz del repo. Resultado real: `UPLOADS_DIR = .../peptinder/src/data/media/uploads` (el archivo quedó ahí, verificado en disco), mientras el montaje estático `/media` sirve `.../peptinder/data/media` (`main.MEDIA_DIR`). Directorios distintos → el archivo se guarda pero nunca es servible.
- Los 5 tests de `test_uploads.py` no lo atrapan porque el fixture autouse monkeypatchea `UPLOADS_DIR` a `tmp_path` — prueban el handler, pero nunca la ruta real. El acceptance 1 ("201 con foto_url bajo /media/uploads/ y el archivo queda en disco") y la descripción de la feature ("responde `foto_url` **servible bajo `/media`**") quedan incumplidos en el comportamiento real; además el docstring del router promete algo que el código no hace (CHECKPOINTS: "documentación que describe un comportamiento que el código no tiene").

**Corrección sugerida** (implementador): `parents[4]` en `uploads.py` (o mejor: derivar `UPLOADS_DIR` de una única fuente compartida con `main.MEDIA_DIR` para que no pueda divergir), **más un test de regresión que no dependa del monkeypatch**, p. ej. `assert uploads.UPLOADS_DIR == main.MEDIA_DIR / "uploads"` — ese test habría atrapado este bug y protege el invariante para siempre. Nota de limpieza: la verificación del revisor creó y ya borró `src/data/media/uploads/` (artefacto del bug); tras el fix conviene re-verificar que ninguna corrida vuelva a crear `src/data/`.

Menor (no bloquea): la entrada de `changes.md` dice "(en revisión)" — añadir el hash (`b1f19ed` + fix) al aprobar.

Todo lo demás está bien (código, tests, `client.ts::subirFoto` con FormData sin `Content-Type` manual, estados del componente). Próximo paso: fix + test de regresión, y el revisor repite la verificación en vivo (subida real → GET del `foto_url` → 200 con los mismos bytes) antes de pasar `03-upload-fotos` a `done`.

## Veredicto del revisor — feature 03 (2026-08-12, segunda pasada): APROBADA

Re-revisión sobre `develop` @ `c30355c` (`fix: las fotos subidas se guardaban fuera del directorio servido en /media`). El bug de la primera pasada quedó corregido de raíz, no con un parche del número:

- **Fix verificado por diff**: nuevo `reencuentro_api/media.py` como fuente única de `REPO_ROOT`/`MEDIA_DIR`/`UPLOADS_DIR`; `main.py` (montaje `/media`) y `routers/uploads.py` importan de ahí — ya no existen dos `parents[N]` calculados por separado que puedan divergir. El docstring del router quedó actualizado a la realidad.
- **Los 2 tests de regresión pedidos existen y pasan**: `test_uploads_dir_es_subdirectorio_del_media_montado` (invariante `UPLOADS_DIR == MEDIA_DIR / "uploads"` + `REPO_ROOT` verificado contra `init.sh` real en disco) y `test_foto_subida_es_servible_bajo_media` (ciclo completo con el directorio real: subida → GET del propio `foto_url` → 200 con los mismos bytes, con limpieza en `finally`). Habrían atrapado el bug original.
- **`bash init.sh` re-corrido: verde completo** — 39/39 tests de API + 14/14 de web, lint limpio.
- **Verificación en vivo del revisor repetida** (mismo script de la primera pasada, `TestClient` sobre la app real sin monkeypatch): `POST /api/uploads` con JPEG real → 201 con `/media/uploads/16bad92e...jpg` → `GET` de esa URL → **200 `image/jpeg` con los mismos bytes**; archivo en `data/media/uploads/` (el directorio servido), borrado tras la prueba. Confirmado además que ninguna corrida vuelve a crear `src/data/` y que `data/media/uploads/` queda solo con su `.gitkeep`.
- El resto del acceptance ya estaba verificado en la primera pasada (misma sesión): 415/413 en español con tests, nombre uuid ≠ filename hostil, `FotoUpload` con preview local + entrega de `foto_url` al padre + estado de error. `python-multipart==0.0.17` única dependencia nueva (ADR 0005 §6).
- `feature_list.json`: `03-upload-fotos` a `done` con edición puntual sobre la línea 36; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0.

Menor pendiente para la sesión principal al commitear: la entrada de `changes.md` de la feature 03 aún dice "(en revisión)" — actualizarla a "commit `b1f19ed` (+ fix `c30355c`)", como se hizo con la 01 y la 02.

## Veredicto del revisor — feature 04 (2026-08-12): APROBADA

Revisión independiente sobre `develop` @ `f09ee0d`. Evidencia ejecutable de esta sesión:

- **`bash init.sh` corrido de verdad: verde completo** — 39/39 tests de API + 27/27 de web (7 suites), lint/formato limpios.
- **Acceptance 1 (reporte end-to-end con foto y pin) — verificación en vivo propia del revisor**, independiente de la de la sesión principal y sobre otra zona: `TestClient` sobre la app real → subir JPEG (201, servible bajo `/media/uploads/`, GET 200) → POST `/api/reports` con las coords de un click simulado en el lienzo de **Quibdó** (fracción 0.25/0.75 → `lat=5.6675, lng=-76.665`, réplica exacta de `coordsDesdeFraccion` con redondeo a 4 decimales) → GET del reporte creado (id 18): **coords del pin persistidas exactas** y `foto_url` ligada. Limpieza completa: archivo subido borrado, seed reseteado (17 reportes, 0 restos de la prueba), `data/media/uploads/` solo con `.gitkeep`. Además cubierto por test de frontend (`publica un reporte perdido con las coords del pin puesto por click`, con `getBoundingClientRect` simulado y `closeTo` contra el centro de Armenia).
- **Acceptance 2 (gate `?volver=`)**: test del redirect en `ReportarMascota.test.tsx` (sin usuario → "Registro stub") + el roundtrip ya existente en `Registro.test.tsx` (`?volver=/reportar/perdido` vuelve al formulario; URL externa se ignora).
- **Acceptance 3 (campos condicionales)**: 2 tests directos (perdido muestra nombre y no situación; encontrado al revés) + 2 tests de payload (perdido sin `situacion`, encontrado con `situacion` y sin `nombre_mascota`).
- **Acceptance 4 (inversas)**: `mapa.test.ts` con roundtrip fracción→coords→posición para **todas** las zonas más el lienzo nacional (`Otro`), 4 fracciones incluyendo esquinas.
- **Checkpoint de sincronía de zonas**: verificado programáticamente con script del revisor que parsea `lib/ciudades.ts` y compara contra `services/ciudades.py` — **6 zonas + COLOMBIA, 6 campos cada una, valores idénticos**.
- Consistencia con ADR 0005 §5 y CHECKPOINTS: sin librerías de mapas (el commit no toca `package.json`; lienzo CSS puro con retícula), pines `bg-danger`/`bg-forest` según el design-system, tono sin lenguaje de fracaso ("Mucho ánimo — cada reporte acerca un reencuentro"). Entrada de la feature en `changes.md`.
- `feature_list.json`: `04-reportar-ui` a `done` con edición puntual sobre la línea 48; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0.

Menores para la sesión principal (no bloquean): (a) actualizar "(en revisión)" de la entrada de `changes.md` a "commit `f09ee0d`" al commitear, como en las features anteriores; (b) sugerencia opcional para una feature futura: convertir el chequeo de sincronía py↔ts de zonas en un test permanente (hoy el checkpoint se cumple por revisión del revisor).

## Veredicto del revisor — feature 05 (2026-08-12): APROBADA

Revisión independiente sobre `develop` @ `e2e3853` (+ `b3a55c6` chore de status). Evidencia ejecutable de esta sesión:

- **`bash init.sh` corrido de verdad: verde completo** — 39/39 tests de API + 31/31 de web (8 suites), lint/formato limpios.
- **Acceptance 1**: test de render con tipo/especie/zona/fecha por tarjeta (con `within` para no chocar con las opciones del filtro) + título por especie cuando no hay nombre. El orden lo decide la API — confirmado doble: (a) verificación en vivo del revisor contra el seed real (`TestClient`): 15 activos, `fecha_evento` estrictamente descendente (2026-08-12 → 2026-08-09), reunidos excluidos (Firulais ausente); (b) `grep sort|reverse|orderBy` vacío en `Reportes.tsx`/`ReporteCard.tsx` — el frontend no reordena, y el test asevera que el listado inicial se pide con `{}`.
- **Acceptance 2**: test con el payload exacto de `listarReportes` en cada cambio de filtro (`{tipo:'perdido'}` → `{tipo:'perdido', zona:'Cali'}`); en vivo, los mismos query params que construye el cliente (`?tipo=perdido&zona=Armenia`, `?especie=gato`) filtran correctamente (3 perdidos de Armenia, 6 gatos).
- **Acceptance 3**: test del `href` de la tarjeta → `/reporte/7`.
- **Checkpoint estético (requisito explícito del usuario)**: comparado contra `git show adopta-v1:src/web/src/components/SwipeCard.tsx` — `ReporteCard` hereda `rounded-[22px]`, `border-line bg-surface`, la sombra exacta `0_18px_40px_-28px_rgba(27,26,23,.5)` (en hover), el badge `rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg` y la foto `bg-surface-alt bg-cover bg-center`, con la semántica nueva perdido=`bg-danger` / encontrado=`bg-forest` del design-system.
- Extras correctos: estado vacío con acción (test), esqueletos de carga, `lugar` usa `ciudad_texto` cuando zona=Otro, sin dependencias nuevas, ruta `/reportes` registrada. Entrada de la feature en `changes.md`.
- `feature_list.json`: `05-listado-reportes` a `done` con edición puntual sobre la línea 61; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0. DB dejada en el estado limpio del seed.

Menor recurrente para la sesión principal: actualizar "(en revisión)" de la entrada de `changes.md` al hash (`e2e3853`) al commitear.

## Veredicto del revisor — feature 06 (2026-08-12): APROBADA

Revisión independiente sobre `develop` @ `e20938c`. Evidencia ejecutable de esta sesión:

- **`bash init.sh` corrido de verdad: verde completo** — tests de API en verde y 42/42 de web (10 suites), lint/formato limpios.
- **Acceptance 1 (hrefs exactos)**: `contacto.test.ts` asevera los strings completos (`https://wa.me/573001234567?text=Hola`, `tel:+573001234567`), incluyendo no duplicar el indicativo (`573001234567` entra tal cual), limpieza de `+`/espacios/guiones y URL-encoding del mensaje; `ReporteDetalle.test.tsx` asevera el prefijo exacto `https://wa.me/573001234561?text=` con el teléfono del seed normalizado y el `tel:+573001234561` literal.
- **Acceptance 2 (mensaje menciona reporte y app)**: el test del componente decodifica el `?text=` y asevera "Rocky" y "Reencuentro"; tests unitarios cubren ambas variantes por tipo.
- **Acceptance 3 (mini-mapa con el pin)**: test del componente (posición dentro del lienzo + `bg-danger` por tipo) **más comprobación numérica propia del revisor**: replicando `posicionEnMapa` para el reporte 1 del seed (Rocky, Armenia, coords confirmadas en DB: 4.540, -75.680) la posición interpolada es exactamente `left=58.3333%`, `top=44.4444%` — coincide con el valor esperado calculado a mano contra el bounding box de Armenia.
- **Extra (estado reunido)**: test presente — franja "Esta mascota ya se reencontró con su familia. 💚" y cero botones de contacto. Consistente con el tono del producto: celebración, nunca lenguaje de fracaso, y sin fricción inútil (contactar por una mascota ya reencontrada no tiene sentido).
- Consistencia con ADR 0005 §3: el contacto es exactamente wa.me + tel:, sin chat interno ni dependencia nueva alguna (el commit no toca package.json). `target="_blank" rel="noreferrer"` en WhatsApp. Ruta `/reporte/:id` registrada. Funciones de `lib/contacto.ts` puras como pide conventions. Entrada de la feature en `changes.md`.
- `feature_list.json`: `06-detalle-contacto` a `done` con edición puntual sobre la línea 73; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0.

Menor recurrente: actualizar "(en revisión)" de la entrada de `changes.md` al hash (`e20938c`) al commitear.
