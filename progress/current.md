# Estado vivo — pivot Reencuentro

> Actualizado: 2026-08-12. La era Adopta vive en la rama `adopta-v1` + tag `adopta-v1.0.0` (`cde337f`). Los veredictos completos de las features 01-09 están en el historial de git de este archivo.

## Qué está pasando

**Feature activa: `10-verificacion-final` (in_progress, implementación lista, en revisión).** Features `01`-`09` aprobadas por el revisor independiente. Suites: 51 tests de API + 56 de web, todo en verde.

## Hecho en la feature 10

- [x] Observación del revisor de la 09 atendida: `resuelto_en` del seed movido al 2026-08-11 (siempre en el pasado, sigue determinista).
- [x] `bash init.sh` en verde completo; seed determinista verificado (doble corrida).
- [x] **Recorrido manual completo en Chrome real** (evidencia en `docs/verification.md` §3): landing → gate registro con ?volver= → reporte "Bruno E2E" con pin por click → listado → detalle con href wa.me exacto y coincidencia "a 4.92 km" → marcar reunida → contador 2→3 → mapa Todo Colombia con 15 activos. Datos reseteados al final.
- [x] Greps de cierre limpios (adopta/leaflet/mapbox/WebSocket solo en comentarios de herencia/negación; única dep nueva python-multipart).
- [x] `docs/verification.md` regenerado con evidencia real; CHANGELOG `[2.0.0] - 2026-08-12` fechado.

## Próximo paso

1. Revisor: corre `init.sh`, verifica el acceptance de la 10 y aprueba → `done`.
2. Merge `develop` → `main` (cierre del acceptance 4 de la 10).
3. Última feature: `11-despliegue` (vercel.json, render.yaml, VITE_API_BASE_URL, docs/deploy.md, build de producción probado).

## Veredicto del revisor — feature 10 (2026-08-12): APROBADA, condicionada al merge develop → main

Revisión independiente sobre `develop` @ `2d26816`. Todo lo verificable por el revisor se ejecutó de verdad en esta sesión:

- **`bash init.sh`: verde completo** — 51/51 tests de API + 56/56 de web, lint/formato limpios.
- **Determinismo del seed re-verificado**: doble corrida + `diff` de los dumps completos de `users` (5) y `reports` (17) → idénticos byte a byte. La observación de la 09 quedó atendida (`resuelto_en` del seed al 2026-08-11) y **confirmada en vivo**: un reencuentro marcado ahora queda de primero en `recientes`.
- **E2E de API en vivo propio** (equivalente por API del recorrido de navegador — el revisor no tiene herramientas de browser): crear encontrado con coords exactas (persistidas), coincidencia principal correcta (Mishi a 0.31 km), 403 no-autor → 200 autor → 409 repetido, fuera del listado activo (15), contador 2→3. Seed reseteado al final, sin restos.
- **Recorrido manual en navegador**: ejecutado por la sesión principal y documentado con detalle verificable en `docs/verification.md` §3 (pin por click, href `wa.me` exacto, coincidencia a 4.92 km, contador en vivo). Los pasos equivalentes por API los reprodujo el revisor; la parte puramente visual queda respaldada por esa evidencia y por los 56 tests de componentes.
- **Greps de cierre (ejecutados por el revisor)**: `adopta` en código vivo → solo el comentario de procedencia visual en `ReporteCard.tsx` que apunta a la rama de archivo (juicio del revisor: **aceptable** — documenta un requisito explícito del usuario y de la descripción de la feature 05, no es una referencia muerta al producto de adopción); `leaflet|mapbox|google.maps|websocket` → solo la negación del comentario de `mapa.ts`; dependencias: `diff` de requirements vs `adopta-v1` muestra **solo `python-multipart==0.0.17`** y `package.json` sin cambios; rama `adopta-v1` y tag `adopta-v1.0.0` intactos en `cde337f` (`git rev-parse`).
- **CHANGELOG `[2.0.0] - 2026-08-12`** leído: refleja fielmente lo hecho (Removed/Added por feature, con el hallazgo del 404 de la 03 documentado); `[Unreleased]` queda solo con `11-despliegue`. `progress/current.md` refleja el estado real y `history.md` tiene la entrada de cierre con los hashes de cada feature.
- `feature_list.json`: `10-verificacion-final` a `done` con edición puntual sobre la línea 122; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0.

**Condición explícita de esta aprobación**: el acceptance 4 incluye "develop mergeado a main", que el revisor NO ejecuta (no hace commits ni merges). La aprobación queda condicionada a que la sesión principal ejecute el merge `develop` → `main` inmediatamente después de commitear este veredicto — si el merge no ocurre, el acceptance 4 no está cumplido y el `done` debe revertirse.

## Veredicto del revisor — feature 11 (2026-08-12): APROBADA — pivot completo, 11/11 features en done

Revisión independiente sobre `develop` @ `cbeb286`. Evidencia ejecutable de esta sesión:

- **Acceptance 1**: `npm run build` corrido por el revisor en `src/web` — build de producción limpio (`tsc -b && vite build`, 43 módulos, `dist/assets/index-*.js` 264.67 kB / **81.54 kB gzip**, sin errores ni warnings). `src/web/vercel.json` tiene el rewrite SPA (`/(.*)` → `/index.html`).
- **Acceptance 2**: `render.yaml` leído y validado en coherencia de rutas: el disco `reencuentro-data` (1 GB) se monta en `/opt/render/project/src/data` — exactamente el `data/` de la raíz del checkout, que es donde resuelven `media.py` (`parents[3]` desde `reencuentro_api/`) y `models/base.py` (`parents[4]` desde `models/`, con override por `DATABASE_URL`); `DATABASE_URL=sqlite:////opt/render/project/src/data/app.db` (ruta absoluta, dentro del disco); `rootDir: src/api` + `uvicorn reencuentro_api.main:app --port $PORT` + `healthCheckPath: /health` consistentes (los módulos resuelven por `__file__`, independiente del cwd).
- **Acceptance 3**: `docs/deploy.md` documenta los pasos exactos (push del archivo `adopta-v1` + tags incluido, Blueprint de Render, seed inicial por Shell con su advertencia de `drop_all`, Root Directory de Vercel, verificación post-deploy con persistencia tras redeploy) y **todas** las env vars en tabla: `VITE_API_BASE_URL`, `CORS_ORIGINS`, `DATABASE_URL` (+`PYTHON_VERSION`), con el límite documentado (migrar a Postgres/S3 = ADR nuevo, coherente con ADR 0005 §7).
- **Acceptance 4**: verificado en vivo por el revisor — uvicorn local con `CORS_ORIGINS=https://reencuentro-revisor.vercel.app`: `/health` → 200 `{"status":"ok"}`; preflight `OPTIONS` con ese Origin devuelve **`access-control-allow-origin: https://reencuentro-revisor.vercel.app` exacto**; un Origin no permitido recibe 400 sin el header. Proceso detenido tras la prueba.
- **`bash init.sh` re-corrido: verde completo** — 51/51 tests de API + 56/56 de web (la feature no toca código de producto: `client.ts` ya usaba `VITE_API_BASE_URL` y `main.py` ya leía `CORS_ORIGINS`).
- **Condición de la feature 10 verificada como cumplida**: `2d26816` es ancestro de `main` (`git merge-base --is-ancestor`), con el commit de release `4fc4892` en `main`.
- `feature_list.json`: `11-despliegue` a `done` con edición puntual sobre la línea 142; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0.

**Con esto las 11 features del pivot Reencuentro quedan en `done` (11/11).** El deploy real lo ejecuta el usuario siguiendo `docs/deploy.md`, como define el alcance de la feature. Pendiente de la sesión principal: commit de este cierre (y actualizar el "(en revisión)" de la entrada 11 de `changes.md` al hash `cbeb286`).

## Veredicto del revisor — feature 12 (2026-08-12): APROBADA — 12/12 features en done

Revisión independiente sobre `develop` @ `371d4d3` (+ fix de copy `6334a42`). Evidencia ejecutable de esta sesión:

- **Acceptance 5 / 1 (comportamiento local intacto)**: `bash init.sh` corrido de verdad — **verde completo, 53/53 tests de API + 58/58 de web** (13 suites). El diff de `tests/api/test_uploads.py` es solo de adición: los 7 tests de la feature 03 (415/413, uuid, servible bajo /media) pasan sin una línea modificada. El seed local sigue en filesystem (verificado por la corrida del seed dentro de init.sh).
- **Acceptance 1 (bucket mockeado)**: tests directos — con `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` vía `monkeypatch.setenv`, el POST va a `.../storage/v1/object/fotos/` con `Authorization: Bearer <key>`, `Content-Type` correcto y el contenido byte a byte; `foto_url` devuelta es la URL pública absoluta `https://...supabase.co/storage/v1/object/public/fotos/<uuid>.jpg`; **nada toca el disco local**; y el fallo del bucket responde **502 en español** sin dejar restos.
- **Acceptance 2 (`mediaUrl`)**: `client.test.ts` — relativa prefijada con la base de la API, absoluta devuelta tal cual.
- **Acceptance 3 (Postgres)**: `.venv/bin/python3 -c "import psycopg2"` → 2.9.10; `psycopg2-binary==2.9.10` en requirements (línea 8); por lectura, los modelos usan **solo** tipos portables — conteo exacto de `mapped_column`: 19 String, 6 Float, 3 DateTime, 2 Date; cero JSON/Text/tipos específicos de SQLite. `base.py` ya aceptaba `DATABASE_URL` por entorno con `connect_args` condicional a sqlite.
- **Acceptance 4 (config de deploy)**: `render.yaml` **sin sección `disk`**, con `DATABASE_URL`/`SUPABASE_URL`/`SUPABASE_SERVICE_KEY`/`CORS_ORIGINS` en `sync:false` y `SUPABASE_BUCKET=fotos`; `docs/deploy.md` reescrito con los pasos completos (connection string del **pooler** puerto 6543, bucket **público** `fotos`, advertencia ⚠️ de `drop_all` en el seed de producción, auto-deploy por push, verificación post-deploy con persistencia tras Manual Deploy) y la tabla con **todas** las env vars.
- **Seguridad (grep del revisor)**: `SUPABASE_SERVICE_KEY`/`service_role` aparece únicamente en backend (lectura por `os.environ`), `render.yaml` (`sync:false`, sin valor), docs/ADR y tests (valor fake); **cero** menciones de Supabase en `src/web/` y ninguna key con pinta real (`eyJ...`) en el repo.
- Consistencia con el harness: ADR 0006 documenta la decisión del usuario y las 3 opciones evaluadas; `architecture.md` §7 y README actualizados; config leída al llamar (no al importar) — patrón correcto para tests; sin SDK nuevo (`requests` ya era dependencia); entrada en `changes.md`. El fix `6334a42` (eyebrow nacional en la landing) verificado en verde dentro de la misma corrida.
- `feature_list.json`: `12-persistencia-supabase` a `done` con edición puntual sobre la línea 155; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0. **12/12 features en `done`.**

Menores (no bloquean): (a) recurrente — hash (`371d4d3`) en la entrada de `changes.md` al commitear; (b) sugerencia de robustez para el futuro: un fixture autouse que haga `monkeypatch.delenv("SUPABASE_URL"/"SUPABASE_SERVICE_KEY", raising=False)` blindaría los tests locales contra un shell de desarrollador que tenga esas variables exportadas.
