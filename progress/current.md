# Estado vivo — pivot Reencuentro

> Actualizado: 2026-08-12. La era Adopta vive en la rama `adopta-v1` + tag `adopta-v1.0.0` (`cde337f`). Los veredictos completos de las features 01-09 están en el historial de git de este archivo.

## Qué está pasando

**Feature activa: `17-registro-ciudades-lista` (in_progress, implementación lista, en revisión).** Features `01`-`16` aprobadas por el revisor independiente. Suites: 65 tests de API + 58 de web, todo en verde.

## Hecho en la feature 17

- [x] `OTRAS_CIUDADES_COLOMBIA` en `src/web/src/lib/ciudades.ts`: las 32 capitales departamentales (menos las 6 que ya son zonas) + ciudades grandes no capitales (Bello, Soacha, Soledad, Buenaventura, Palmira, Barrancabermeja, Dosquebradas, Tuluá), alfabético.
- [x] `Registro.tsx`: el campo Ciudad pasa de `<input type="text">` a `<select>` con dos optgroups — "Zonas con mapa propio" (las 6, en el orden de `NOMBRES_ZONAS`, default Armenia) y "Resto de Colombia". Backend sin cambios (`User.ciudad` sigue string libre).
- [x] Tests: 2 nuevos en `Registro.test.tsx` (es un SELECT con las 6 zonas primero + muestra de capitales; la ciudad elegida viaja tal cual en el payload). `bash init.sh` verde: 65 API + 58 web.

## Hecho en la feature 10 (histórico)

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

## Veredicto del revisor — feature 13 (2026-08-12): APROBADA

Revisión independiente sobre `develop` @ `6144940`. Evidencia ejecutable de esta sesión:

- **Acceptance 5**: `bash init.sh` corrido de verdad — **verde completo, 55/55 tests de API** (incluye `test_vercel_entry.py` 2/2) **+ 58/58 de web**; `npm run build` corrido por el revisor — bundle limpio (43 módulos, 81.52 kB js gzip, sin errores).
- **Acceptance 1**: `test_vercel_entry.py` importa la app **por la ruta del entry** (`from api.index import app`), pega `/health` y `/api/reports` vía `TestClient`, y asevera `app is app_del_paquete` — no hay app paralela; `api/index.py` solo hace `sys.path` + re-export de la instancia real.
- **Acceptance 2**: `vercel.json` raíz leído — `buildCommand: cd src/web && npm ci && npm run build`, `outputDirectory: src/web/dist`, rewrites de `/api/(.*)` **y** `/health` a `/api/index` (en orden, antes del fallback), y fallback SPA `/((?!api/).*)` → `/index.html` con el negative lookahead que excluye `/api`.
- **Acceptance 3**: `client.ts` — `VITE_API_BASE_URL ?? (DEV ? 'http://127.0.0.1:8000' : '')`. Dev/Vitest intactos (los tests existentes de `mediaUrl` pasan sin cambios dentro de init.sh); para prod, verificado por evaluación directa que la base vacía produce rutas relativas same-origin (`/api/reports`, `/media/x.jpg`) y que las URLs absolutas de Supabase pasan tal cual — coherente porque en producción **todas** las fotos son absolutas del bucket (ADR 0006), así que el no-montaje de `/media` en serverless no rompe nada (montaje condicional con `try/OSError` + `is_dir`, comportamiento local intacto).
- **Acceptance 4**: `git ls-files | grep render` **vacío** (render.yaml eliminado; también el `vercel.json` viejo de `src/web`); `grep -i render docs/deploy.md` **cero menciones**; el deploy.md reescrito documenta el proyecto único (Root Directory = raíz, framework Other), la tabla con las **4 env vars** (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET`), la no-necesidad explícita de `VITE_API_BASE_URL`/`CORS_ORIGINS`, el seed contra producción **desde la máquina local** con su ⚠️ de `drop_all`, y los límites reales del free tier (fotos como cuello de botella, pausa de Supabase a la semana).
- Consistencia con el harness: ADR 0007 registra el bloqueo real de Render (tarjeta), la decisión y sus consecuencias (cold start ~1-2 s, `create_all` idempotente por lifespan); `.vercelignore` y `requirements.txt` raíz con `-r` (fuente de verdad intacta en `src/api`); architecture/README actualizados; entrada en `changes.md`.
- `feature_list.json`: `13-api-vercel-serverless` a `done` con edición puntual sobre la línea 169; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0. Queda `14-mapa-leaflet` en `todo` (siguiente).

Menores (no bloquean): (a) recurrente — hash (`6144940`) en la entrada de `changes.md` al commitear; (b) la reescritura de `deploy.md` perdió la sección de prerrequisito de GitHub que instruía pushear **también `adopta-v1` y los tags** como respaldo remoto del archivo (`git push -u origin main develop adopta-v1 --tags`) — si el push inicial ya se hizo con todo, es irrelevante; si no, conviene restaurar esa línea para no perder el respaldo remoto de la era Adopta; (c) el deploy.md dice "importar `pets-finder`" — confirmar que ese es el nombre real del repo en GitHub del usuario.

## Veredicto del revisor — feature 14 (2026-08-12): APROBADA

Revisión independiente sobre `develop` @ `d3bb11f`. Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 55/55 tests de API + 52/52 de web**, 100% offline (los tests no tocan Leaflet: guard `MODE === 'test'` verificado por lectura); `git show` de `src/web/package.json` muestra **solo** `leaflet ^1.9.4` (+`@types/leaflet` en devDependencies, solo tipos); `npm run build` corrido por el revisor — bundle limpio, 125.26 kB js gzip (+~44 kB, exactamente lo que anota el ADR 0008).
- **Acceptance 1 (por lectura de `MapaLienzo.tsx`)**: `L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png')` **con atribución** a OpenStreetMap; `fitBounds` al bounding box vía `cajaDeZona(zona)` en un efecto dependiente de `zona` — cubre las 6 zonas y la vista "Colombia"/"Otro" (fallback nacional de `lib/ciudades.ts`, sin cambios).
- **Acceptance 2 (por lectura)**: `CircleMarker` con `fillColor` de `COLOR_POR_CLASE` — hex **idénticos** a los tokens de `index.css` verificado por el revisor (`bg-danger`→`#9b3b2e`, `bg-forest`→`#1f4d3a`, fallback `#b57c2e`=ochre) + tooltip por pin; `mapa.on('click')` entrega `lat/lng` reales redondeadas a 4 decimales vía ref (callback siempre fresco). El contrato del componente (`zona`/`pines`/`onClickCoords`/`children`) se conserva — cero cambios en las pantallas consumidoras.
- **Acceptance 3**: la lista `sr-only` renderiza un botón real por pin con `aria-label` y `colorClass`; los tests de `MapaReportes` pasaron **sin cambios** (ya usaban los botones por etiqueta: colores, filtro por zona, click→mini-tarjeta) y `ReporteDetalle` asevera el pin accesible con `bg-danger`. Los tests adaptados de `ReportarMascota` cubren el payload con el centro de la zona y documentan honestamente en comentario que el click real es verificación de navegador.
- **Acceptance 5 (manual en navegador)**: ejecutado por la sesión principal y documentado en `changes.md` (tiles reales en `/mapa` con Colombia, Armenia real con el pin de Rocky en `/reporte/1`, click que movió el pin a Montenegro con tooltip en el formulario). **Limitación declarada**: este revisor no tiene herramientas de navegador y no puede repetir la verificación visual de tiles/click; el equivalente se validó por lectura exhaustiva del componente + los tests del contrato accesible + el build de producción. La evidencia manual queda a cargo de la sesión principal.
- Harness: ADR 0008 registra la decisión del usuario (Google Maps descartado por exigir facturación) y **reemplaza formalmente** la parte de mapa del ADR 0005 §5 — el código es consistente con el ADR vigente (CHECKPOINTS #3); `lib/mapa.ts` + test eliminados (la interpolación ya no existe: sin código muerto); CHANGELOG Unreleased → 2.1.0 con 12-14.
- `feature_list.json`: `14-mapa-leaflet` a `done` con edición puntual sobre la línea 183; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0. **14/14 features en `done`.**

Menores (no bloquean): (a) recurrente — hash (`d3bb11f`) en la entrada de `changes.md` al commitear; (b) **drift de harness**: `CHECKPOINTS.md` §"Checkpoints específicos del pivot (features 01-11)" todavía dice "grep de `leaflet|mapbox` vacío" y "única dependencia nueva `python-multipart`" — cierto para las features 01-11 a las que está scoped, pero ya superado por los ADRs 0006-0008; conviene actualizar esa sección para que el próximo revisor no rechace por una regla obsoleta.

## Veredicto del revisor — feature 15 (2026-08-12): APROBADA (solo develop; el merge a main queda condicionado a la migración de prod)

Revisión independiente sobre `develop` @ `e6743ad` (confirmado por el revisor que **no** está en `main`: `git merge-base --is-ancestor` falla, como debe ser hasta que el usuario autorice el ALTER aditivo en producción). Evidencia ejecutable de esta sesión:

- **Acceptance 5**: `bash init.sh` corrido de verdad — **verde completo, 64/64 tests de API + 55/55 de web**. Coherencia del seed verificada en vivo contra las historias: Luna = Labrador/Negro/grande ("Labradora negra con mancha blanca"), Toby = Beagle/Tricolor ("Beagle tricolor"), Rocky = Criollo / mestizo + Miel / dorado ("criollo color miel"), y el loro (especie "otro") **sin** características — 16/17 reportes con características.
- **Acceptance 1**: test que verifica los 3 selects predefinidos con sus opciones, el cambio de catálogo perro→gato, y la desaparición de Raza con especie "otro"; test del payload (características elegidas van; y por lectura, `raza || undefined` etc. — sin elegir no se envían, con reset de raza al cambiar especie). Orden en el JSX verificado por lectura: raza/color/tamaño (líneas 168-209) antes del nombre (226) y de la descripción (257).
- **Acceptance 2**: `test_listado_filtra_por_raza_color_y_tamano` (match exacto con URL-encoding real de "Miel / dorado" y "Siamés", combinación con tipo/zona) **+ prueba en vivo del revisor contra el seed real**: `?raza=Labrador` → solo Luna; `?color=Blanco` → 2; combinado `especie+tamano+zona` → solo Luna; DB reseteada al final.
- **Acceptance 3**: test de filtros del listado con el payload exacto acumulado (`{especie, raza, color, tamano}`) y la Raza apareciendo **solo** tras elegir especie; chips de características en `ReporteCard` verificados por lectura (renderizado condicional, sin chips para null).
- **Acceptance 4**: `test_tamano_invalido_devuelve_422` (Literal en el schema) + verificado en vivo (`tamano="gigante"` → 422); los reportes con características null siguen apareciendo sin filtros (test + en vivo: el loro visible en el listado activo).
- Diseño consistente: columnas **nullable** (los reportes preexistentes no se rompen — clave para la migración aditiva de prod), catálogo como fuente única en `lib/caracteristicas.ts` con el backend guardando texto tal cual (match exacto garantizado por construcción), filtros combinables sobre el mismo endpoint. Entrada en `changes.md`.
- `feature_list.json`: `15-caracteristicas-busqueda` a `done` con edición puntual sobre la línea 197; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0.

**Condición explícita**: este `done` cubre el código en `develop`. El **merge/push a `main`** (que dispara el auto-deploy) queda condicionado a ejecutar ANTES la migración de producción autorizada por el usuario (`ALTER TABLE` aditivo de `raza`/`color`/`tamano` + backfill, sin drop) — si se mergea sin migrar, la API de prod fallaría al seleccionar columnas inexistentes.

Menores (no bloquean): (a) recurrente — hash (`e6743ad`) en la entrada de `changes.md` al commitear; (b) apareció un `StarletteDeprecationWarning` (httpx/starlette, ajeno a esta feature) en pytest — inofensivo hoy, anotarlo para cuando se actualicen dependencias.

## Veredicto del revisor — feature 16 (2026-08-12): APROBADA

Revisión independiente sobre `develop` @ `6d7cbcb`. Evidencia de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 65/65 tests de API + 56/56 de web**. El commit toca solo clases CSS (`App.tsx`, `ReporteDetalle.tsx`) + docs: cero cambios de comportamiento, y los tests de `App.test.tsx` pasan sin modificar (los links siguen accesibles por rol — `shrink-0 whitespace-nowrap` no cambia la semántica).
- **Acceptance 1-2 (por lectura del diff, causa raíz coherente)**: la Nav compartida era el desborde de TODAS las rutas internas (5 links sin wrap → 545px); el fix es exactamente el descrito — `overflow-x-auto` + `[scrollbar-width:none]` en el `<nav>`, `shrink-0 whitespace-nowrap` en `linkClass` y `shrink-0` en la marca (la nav se desliza dentro de sí misma en vez de empujar la página), y `flex-wrap` en el header del detalle (título largo + badge). La medición post-fix documentada: /reportes 369, /reportar 369, /reporte/1 384, /mapa 384, /mis-reportes 384 — todo ≤390px.
- **Acceptance 3 (táctiles, por lectura)**: sin cambios de tamaño en esta feature — CTAs de la landing `px-8 py-6 text-xl` (≈48px+ de alto), botones de contacto `px-5 py-3` (≈48px), submits de reportar/registro `py-3`. Los links de la nav (`py-2`, navegación secundaria) y el submit inline de mis-reportes (`py-2`) quedan algo por debajo de 44px pero no son los "objetivos táctiles principales" del acceptance y no fueron tocados.
- **Limitación declarada**: el desborde horizontal no es verificable en jsdom (sin layout real) y este revisor no tiene herramientas de navegador — la evidencia del acceptance 1 y 5 (mediciones de `scrollWidth` por ruta en iframe de 390px y screenshots de landing/listado/formulario/detalle/mapa) es la documentada por la sesión principal en `changes.md`; lo que sí es verificable por lectura (las clases exactas del fix y la causa raíz) coincide punto por punto con esa evidencia.
- Nota al margen: la entrada de `changes.md` registra también la limpieza de datos de prueba en producción (autorizada por el usuario; cuenta real id 6 intacta) — no es parte del acceptance de la 16, sin objeciones del revisor.
- `feature_list.json`: `16-mobile-ui` a `done` con edición puntual sobre la línea 211; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0.

El merge a `main` (deploy directo, sin migración esta vez) queda en manos de la sesión principal tras este veredicto. Menor recurrente: hash (`6d7cbcb`) en la entrada de `changes.md` al commitear.
