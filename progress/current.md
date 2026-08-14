# Estado vivo — pivot Reencuentro

> Actualizado: 2026-08-12. La era Adopta vive en la rama `adopta-v1` + tag `adopta-v1.0.0` (`cde337f`). Los veredictos completos de las features 01-09 están en el historial de git de este archivo.

## Qué está pasando

**Backlog ejecutable CERRADO: 30 features en `done`, release 2.2.0 desplegado en <https://petfinder-col.com>.** En la jornada post-lanzamiento se cerraron 20, 21, 26-34 (benchmarks incluidos) + fixes de UX (sin default Armenia, fotos sin recorte, marca Pet Finder Col). Suites: 115 tests de API + 103 de web. Tablas de prod: users, reports, sightings, organizaciones, necesidades — todas migradas con autorización explícita ANTES de cada merge.

**2026-08-13 — Primera corrida real del crawler (Drive de Cali)**: 204 reportes importados a prod (107 perdidos + 97 encontrados, todos con foto, 170 con teléfono) como usuario sistema id 49 "Rescate Animal Cali (importado)", `fuente=crawl`, idempotente. Detalle y gotcha del WAF de Vercel en `changes.md` (2026-08-13) y `memory/memory.md`.

**Lo que queda requiere decisiones del dueño**: `22-alertas-por-zona` (elegir mecanismo, ADR), `23-moderacion-reportes` (alcance), `24-ai-matching-fotos` (ADR costo/proveedor), `25-ops-produccion-pendientes` (checklist en dashboards: SKIP_DB_CREATE_ALL, A record, Website Builder, pausa de Supabase) — y la rotación de credenciales de Supabase (recordatorio aparte, fuera del backlog a pedido del usuario).

## Feature 35 en curso (2026-08-13): marca, recorte y visibilidad

Implementado, `bash init.sh` en verde (115 API + 117 web) y verificación visual en navegador real hecha (landing con logo y botones, recorte cuadrado subido 600x600 desde un original 900x600). Pendiente: veredicto del revisor → done → merge a main.

- Landing: "Ver todos los reportes" / "Ver el mapa" como botones con borde (sin competir con los CTAs); logo wordmark arriba; link a /ayudar renombrado.
- FotoUpload: paso de recorte con react-easy-crop (proporciones Original/Cuadrada/Horizontal + zoom/arrastre); `recortarImagen()` en lib/imagen.ts (canvas, devuelve el original si el encuadre cubre todo); luego la compresión existente.
- Marca: favicon = isotipo oficial (?v=3), logo.svg en nav y landing, apple-touch-icon.png desde el avatar (design/logo/).
- Renombre: pestaña "Ayudar" → "Centros de ayuda" (nav, h1 de /ayudar, landing, RegistrarOrganizacion). La ruta /ayudar no cambia.
- Fix aparte: test de Reportes con fecha-bomba (creado_en fijo hacía fallar "· hace" al día siguiente) → fixture relativo a la corrida.

## Próximo paso

Tomar la siguiente feature del backlog (`20`-`24`) con el patrón líder→implementador→revisor, o ejecutar el checklist `25` (dueño). Regla dura vigente: nunca `seed.py` contra prod; migraciones aditivas ANTES de mergear a `main` si hay esquema nuevo.

## Hecho en la feature 19

- [x] Diagnóstico previo medido en prod: API caliente ~0,35 s (no es el problema); causas reales = (1) arranque en frío del serverless (boot Python + create_all contra Postgres), (2) fotos a tamaño completo (173-448 KB reales, hasta 5 MB posibles) descargadas enteras por cada tarjeta.
- [x] `lib/imagen.ts`: `comprimirImagen()` — reescala a máx 1280px y recomprime a JPEG 0.8 en el navegador; fallback al original si no hay canvas/createImageBitmap, el formato no decodifica o el resultado no es más pequeño. Integrada en `FotoUpload` antes de `subirFoto`.
- [x] `ReporteCard`: la foto pasa de `background-image` (carga siempre) a `<img loading="lazy">` con alt descriptivo — el navegador solo baja las fotos cercanas al viewport.
- [x] `main.py`: `SKIP_DB_CREATE_ALL=1` omite `create_all` en el arranque (para prod; el esquema ya existe) — recorta round-trips del cold start. Sin la variable, comportamiento intacto (dev/tests). **Pendiente del dueño: añadir la env var en Vercel** (opcional, la app funciona igual sin ella).
- [x] Branding pestaña: `<title>petfinder-col</title>`, `lang="es"`, y `public/favicon.svg` propio (huella crema sobre fondo forest, tokens del design system) en vez del SVG por defecto de Vercel/Vite.
- [x] Tests: +2 API (`test_arranque.py`) y +4 web (3 en `imagen.test.ts`, 1 en `FotoUpload.test.tsx` con mock pass-through). `bash init.sh` verde: 70 API + 64 web; build de prod verificado (título y favicon en dist/).

## Hecho en la feature 18

- [x] `DELETE /api/reports/{id}?user_id=` en `routers/reports.py`: 204 autor / 403 ajeno (mensaje en español) / 404 inexistente. La foto queda huérfana en Storage (documentado en el docstring — decisión: no darle a este endpoint credenciales de borrado sobre el bucket).
- [x] `client.ts`: `eliminarReporte(id, userId)` (request() ya manejaba 204 sin body).
- [x] `ReporteDetalle.tsx`: sección "Eliminar este reporte" visible solo para el autor, confirmación en dos pasos en la página (sin window.confirm), estado eliminando/deshabilitado, error en español, navega a /reportes al borrar.
- [x] Tests: +3 API (`test_reports.py`, sección feature 18) y +2 web (`ReporteDetalle.test.tsx`: flujo dos pasos con cancelar + no-autor no ve el botón). `bash init.sh` verde: 68 API + 60 web.

## Hecho en la feature 17 (histórico)

- [x] `OTRAS_CIUDADES_COLOMBIA` en `src/web/src/lib/ciudades.ts`: las 32 capitales departamentales (menos las 6 que ya son zonas) + ciudades grandes no capitales (Bello, Soacha, Soledad, Buenaventura, Palmira, Barrancabermeja, Dosquebradas, Tuluá), alfabético.
- [x] `Registro.tsx`: el campo Ciudad pasa de `<input type="text">` a `<select>` con dos optgroups — "Zonas con mapa propio" (las 6, en el orden de `NOMBRES_ZONAS`, default Armenia) y "Resto de Colombia". Backend sin cambios (`User.ciudad` sigue string libre).
- [x] Tests: 2 nuevos en `Registro.test.tsx` (es un SELECT con las 6 zonas primero + muestra de capitales; la ciudad elegida viaja tal cual en el payload). `bash init.sh` verde: 65 API + 58 web.

## Hecho en la feature 10 (histórico)

- [x] Observación del revisor de la 09 atendida: `resuelto_en` del seed movido al 2026-08-11 (siempre en el pasado, sigue determinista).
- [x] `bash init.sh` en verde completo; seed determinista verificado (doble corrida).
- [x] **Recorrido manual completo en Chrome real** (evidencia en `docs/verification.md` §3): landing → gate registro con ?volver= → reporte "Bruno E2E" con pin por click → listado → detalle con href wa.me exacto y coincidencia "a 4.92 km" → marcar reunida → contador 2→3 → mapa Todo Colombia con 15 activos. Datos reseteados al final.
- [x] Greps de cierre limpios (adopta/leaflet/mapbox/WebSocket solo en comentarios de herencia/negación; única dep nueva python-multipart).
- [x] `docs/verification.md` regenerado con evidencia real; CHANGELOG `[2.0.0] - 2026-08-12` fechado.

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

## Veredicto del revisor — feature 17 (2026-08-12): APROBADA

Revisión independiente sobre `develop` @ `7fe7dde` (ya mergeado a `main` con autorización explícita del usuario y deploy verificado en vivo por la sesión principal — esta revisión cierra el `done` formal). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 65/65 tests de API + 58/58 de web** (los 2 nuevos de `Registro.test.tsx` incluidos).
- **Acceptance 1**: test directo — el campo Ciudad es `SELECT` (aserción de `tagName`), con valor por defecto `Armenia`, y las primeras 6 opciones son exactamente las zonas en el orden de `NOMBRES_ZONAS` (Armenia, Pereira, Manizales, Cali, Quibdó, Bogotá) dentro del optgroup "Zonas con mapa propio", seguidas del optgroup "Resto de Colombia". Verificado también por lectura del JSX.
- **Acceptance 2**: test directo — elegir "Medellín" envía `ciudad: 'Medellín'` tal cual en el payload de `registrarUsuario`; los 6 tests preexistentes del registro (incluido el flujo entrar-o-crear y `?volver=`) pasan sin cambios.
- **Acceptance 3 — verificación programática del revisor**: la lista vive **una sola vez** en `lib/ciudades.ts` (`OTRAS_CIUDADES_COLOMBIA`, 34 entradas); script propio del revisor contra la lista real: **32/32 capitales departamentales cubiertas** (las 26 de la lista + las 6 zonas, con Bogotá D.C. por Cundinamarca), sin faltantes, **orden alfabético** correcto (ignorando tildes), **sin duplicados ni solapamiento** con las zonas; las 8 no-capitales añadidas son ciudades grandes razonables (Bello, Soacha, Soledad, Barrancabermeja, Buenaventura, Palmira, Tuluá, Dosquebradas).
- Backend intacto verificado: el commit no toca `src/api/` — `User.ciudad` sigue `String(80)` libre, los valores históricos de producción siguen válidos y no hay migración.
- Estado en disco consistente: entrada en `changes.md` y `progress/current.md` actualizados en el mismo commit.
- `feature_list.json`: `17-registro-ciudades-lista` a `done` con edición puntual sobre la línea 225; `git diff` confirma que **solo** cambió esa línea; `validate_feature_list.py` → exit 0. **17/17 features en `done`.**

Menor recurrente: hash (`7fe7dde`) en la entrada de `changes.md` al commitear este cierre.

## Veredicto del revisor — feature 18 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `2de6fd8`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 68/68 tests de API + 60/60 de web** (+3 API, +2 web de esta feature).
- **Acceptance 1**: test (`204` → detalle `404` → ausente del listado) **+ E2E en vivo del revisor contra el seed real**: `DELETE /api/reports/1?user_id=1` → 204 con body vacío, detalle 404, listado 15→14 activos sin Rocky. Seed reseteado al final.
- **Acceptance 2**: tests (403 con el mensaje exacto "Solo quien creó el reporte puede eliminarlo" y reporte intacto; 404 inexistente) **+ verificados en vivo** (403 con user_id=2 dejando el reporte 200; 404 con id 9999).
- **Acceptance 3**: tests del detalle — el botón "Eliminar este reporte" solo aparece para el autor (`queryByRole` nulo con user_id ajeno); la confirmación es en dos pasos **dentro de la página** y el test cubre el ciclo completo: primer click no llama al API, **Cancelar** vuelve atrás sin llamar, y "Sí, eliminar" llama `eliminarReporte(1, 1)` y navega a `/reportes`. Por lectura: `disabled` + "Eliminando…" durante la llamada, error de `ApiError` en español con fallback, sin `window.confirm`.
- Decisiones consistentes con el nivel de confianza del MVP (ADR 0005 §4): autoría por `user_id` (query param en DELETE, mismo patrón que editar/reunido); la foto huérfana en Storage está **documentada en el docstring** con su porqué (no darle al endpoint credenciales de borrado del bucket) — sin discrepancia doc/código. `request()` del cliente ya maneja 204 explícitamente (verificado por lectura). La ruta dinámica DELETE no eclipsa ninguna literal.
- Estado en disco: entradas de `changes.md` y `progress/current.md` incluidas en el mismo working tree.
- `feature_list.json`: `18-eliminar-reporte` a `done` con edición puntual sobre la línea 238 (el bloque completo del item aparece como adición en `git diff` porque la entrada misma es parte del working tree sin commitear; la edición del revisor fue únicamente el valor de `status`); `validate_feature_list.py` → exit 0. **18/18 features en `done`.**

Pendiente de la sesión principal: commit de la feature + este veredicto (menor recurrente: hash en la entrada de `changes.md`), y el merge/deploy según el flujo autorizado por el usuario.

## Veredicto del revisor — feature 19 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `21cc0b8`). Evidencia ejecutable de esta sesión:

- **Acceptance 5**: `bash init.sh` corrido de verdad — **verde completo, 70/70 tests de API + 64/64 de web** (13 suites).
- **Acceptance 1 (compresión antes de subir)**: `FotoUpload.test.tsx` asevera que `subirFoto` recibe **el archivo comprimido** que devuelve `comprimirImagen(original)` (mock pass-through por defecto, bien aislado); `lib/imagen.test.ts` cubre los tres caminos: sin soporte del navegador (jsdom sin `createImageBitmap` → devuelve el original **por identidad**), reescalado real verificado con aritmética exacta (4000×3000 → **1280×960**, `toBlob` con `image/jpeg` y calidad 0.8, `bitmap.close()` llamado, nombre renombrado a `.jpg`), y JPEG no-más-pequeño → original. El try/catch envuelve todo el camino (formato no decodificable → original). El backend sigue validando tipo/tamaño en ambos casos.
- **Acceptance 2**: por diff — `ReporteCard` pasa de `background-image` a `<img loading="lazy">` con `alt="Foto del reporte de {titulo}"`, contenedor `relative` + badge sobre la foto; render condicional si no hay foto.
- **Acceptance 3**: `tests/api/test_arranque.py` — sin la variable, `create_all` se llama exactamente una vez; con `SKIP_DB_CREATE_ALL=1`, no se llama y `/health` sigue sirviendo (patch sobre `Base.metadata.create_all`, sin tocar DB real). Por lectura: `.strip() == "1"` (tolerante a espacios pegados a mano — lección del fix `3d0ffea`), log de advertencia visible, y el camino por defecto queda intacto para dev/tests.
- **Acceptance 4 — verificado sobre el build real**: `npm run build` limpio (126.87 kB js gzip) y en `dist/`: `<title>petfinder-col</title>` presente, `favicon.svg` con los tokens del design system (`#1f4d3a`/`#f7f3ea`, huella de 4 dedos + palma) y **cero rastros** del SVG por defecto de Vercel (`#863bff` ausente). `lang="es"` de paso (corrección correcta).
- `feature_list.json`: `19-optimizacion-carga-y-tab` a `done` con edición puntual sobre la línea 251; `git diff` muestra ese único cambio de status; `validate_feature_list.py` → exit 0. **19/19 features en `done`.**

Menores (no bloquean): (a) recurrente — hash del commit en la entrada de `changes.md` al commitear; (b) `SKIP_DB_CREATE_ALL` no aparece en la tabla de env vars de `docs/deploy.md` — añadirla (valor `1`, opcional, recorta el cold start) para que la optimización realmente se aplique al configurar el proyecto de Vercel y no dependa de memoria tribal.

## Veredicto del revisor — feature 26 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `2ed3341`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 71/71 tests de API + 64/64 de web**.
- **Acceptance 1**: Medellín añadida en **ambos** lados del duplicado consciente con valores idénticos (Valle de Aburrá: lat 6.13-6.36, lng -75.66/-75.50, centro 6.244/-75.581 — contiene su centro, cubierto por `test_cada_zona_contiene_su_propio_centro`). **El test comparativo backend↔frontend que este revisor venía pidiendo desde la feature 04 ahora existe como test permanente** (`test_zonas_en_sync_con_el_frontend`: parsea `lib/ciudades.ts` y compara cada valor numérico de cada zona — truena si se olvida un lado). Los 4 selectores (reportar `SelectorCiudad`, filtros del listado, mapa y registro) derivan de `NOMBRES_ZONAS` (verificado por grep), así que Medellín aparece automáticamente; el test del registro pasa a 7 zonas encabezando el select y 'Medellín' salió de `OTRAS_CIUDADES_COLOMBIA` (sin duplicado).
- **Acceptance 2 — en vivo**: `GET /api/reports?zona=Medellín` → exactamente los 2 reportes del seed nuevo (Simón, Golden perdido en Laureles ↔ avistado en El Poblado), **ambos pins dentro del bounding box** de la zona (aserción numérica contra la caja real); el par funciona como coincidencia (5.06 km). Determinismo re-verificado: doble corrida del seed → 19 filas idénticas byte a byte.
- **Acceptance 3 — sin migración destructiva**: el diff no toca esquema ni datos existentes (cero cambios en modelos/DB); verificado en vivo que los reportes con zona 'Otro' siguen creándose y visibles. Los reportes de prod con `ciudad_texto` Medellín quedan como están (re-zonificarlos a mano es decisión operativa pendiente del usuario, como anota el acceptance).
- Decisión sobre Palmira registrada y razonable: NO se añade como zona (queda bajo 'Otro') — dentro del área de influencia de Cali y sin volumen que la justifique en el benchmark; consistente con el "Evaluar Palmira" de la descripción. Los tests que usaban "Medellín" como zona inválida pasaron a "Palmira" (correcto).
- `feature_list.json`: `26-zona-medellin` a `done` con edición puntual sobre la línea 343 (el diff neto contra HEAD muestra `todo`→`done` porque el `in_progress` del líder también está sin commitear; la edición del revisor fue únicamente el valor final); único cambio de status en el archivo; `validate_feature_list.py` → exit 0.

Menores (no bloquean): (a) recurrente — hash del commit en la entrada de `changes.md`; (b) nit cosmético: el comentario del test del registro ("capitales departamentales del resto del país") incluye a Medellín en la muestra, que ahora vive en el grupo de zonas — la aserción sigue siendo válida (presencia global), solo el comentario quedó impreciso; (c) el test de sync no compara `COLOMBIA` ni detecta zonas extra solo-frontend — extensión barata si algún día hace falta.

## Veredicto del revisor — feature 28 (2026-08-12): APROBADA, condicionada a la migración de prod antes del merge a main

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `8d9713d`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 78/78 tests de API + 67/67 de web**.
- **Acceptance 1**: 7 tests del endpoint (201 con y sin nombre, orden `fecha desc, id desc`, 409 encontrado, 409 reunido, 404 en POST y GET, 422 comentario vacío con `Field(min_length=1, max_length=200)`) **+ E2E en vivo del revisor**: dos avistamientos sin registro sobre Rocky (201, orden por fecha correcto), 409 en encontrado y en reunido reales del seed, 404 y 422 confirmados. Seed reseteado.
- **Acceptance 2**: test del pin secundario **`bg-ochre`** (distinguible del principal `bg-danger`/`bg-forest`, ids desplazados `+1_000_000` para no chocar) y de la lista cronológica ("Vista el 13/08/2026 — comentario (nombre)"); el formulario inline tiene su propio `MapaLienzo` con pin por click (default: coords del reporte, cubierto por el test del payload), fecha default hoy, comentario obligatorio con validación local, y añade el nuevo a la lista sin recargar (test).
- **Acceptance 3**: backend con test doble (409 encontrado + 409 reunido, también en vivo — los avistamientos no pueden ni existir ahí) y frontend con test de sección ausente en encontrado; para reunido la condición `estado === 'activo'` está verificada por lectura (mismo guard ya testeado de contacto/coincidencias).
- Arquitectura consistente: rutas literales `/{report_id}/avistamientos` declaradas antes de `/{report_id}`; modelo con tipos portables (String/Float/Date/DateTime — sin problema en Postgres); tono del copy correcto ("le sirve a su familia", sin fracaso); color ochre coherente con el rol de "tercer estado" del design system.
- **Decisión "sin registro para avisar"**: el alcance decía "decidir con el usuario"; quedó documentada en el docstring del modelo y en changes.md, y la sesión principal indica que el usuario está al tanto. **Observación no bloqueante**: es coherente con la fricción-cero del producto (y con PawBoost/Love Lost), pero implica que los avistamientos son anónimos y sin moderación — si aparece abuso, la feature 27/29 del backlog (moderación) es el lugar para atacarlo.
- `feature_list.json`: `28-avistamientos` a `done` con edición puntual sobre la línea 369 (diff neto `todo`→`done` porque el `in_progress` del líder está sin commitear); único cambio de status; `validate_feature_list.py` → exit 0.

**Condición explícita (como en la feature 15)**: hay tabla nueva (`sightings`) — el merge/push a `main` (auto-deploy) exige ejecutar ANTES el `CREATE TABLE` aditivo en Supabase Postgres autorizado por el usuario; sin eso, los endpoints nuevos fallarían en prod. En dev/tests `create_all` la crea sola.

Menores (no bloquean): (a) recurrente — hash del commit en `changes.md`; (b) sugerencia de una línea: añadir al test existente del estado reunido la aserción `queryByText('Avistamientos') → null` para blindar también la variante de UI; (c) recordar `SKIP_DB_CREATE_ALL`: si prod lo tiene en 1, la tabla nueva NO se creará sola en el deploy — la migración manual del punto anterior es obligatoria, no opcional.

## Veredicto del revisor — feature 32 (2026-08-12): APROBADA, condicionada a la migración de prod antes del merge a main

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `67ecc73`). Evidencia ejecutable de esta sesión:

- **Acceptance 5 (primera mitad)**: `bash init.sh` corrido de verdad — **verde completo, 89/89 tests de API + 80/80 de web** (16 suites); `npm run build` corrido por el revisor — limpio (130.43 kB js gzip).
- **Acceptance 1**: 11 tests de API (201 fundación y acopio, 404 usuario, 422 tipo/zona/Otro, filtros tipo+zona con cerradas fuera, `estado=todos`, 403 editar/eliminar, 404) + tests de frontend (tarjetas con dirección/horario, **pin `bg-ochre` por tipo** con `COLOR_POR_CLASE` ampliado usando los hex reales de los tokens — ochre `#b57c2e`, ink `#1b1a17` —, chips y zona que re-consultan con el payload exacto, vacío con invitación, gate `?volver=` y payload con el pin en el centro de la zona) **+ E2E en vivo del revisor**: registrar acopio → visible y filtrable por tipo+zona → 422s → 403s ajenos → cerrar la saca del listado default (y queda en `estado=cerrado`) → eliminada por el autor (204). Sin restos; seed reseteado.
- **Acceptance 2**: tests del detalle — hrefs exactos (`https://wa.me/573001112233?text=` con `mensajeAyudaOrganizacion` decodificado + `tel:+573001112233`), sección "Cómo donar" condicional (ausente sin `como_donar` — coherente con la decisión de texto libre sin pagos), bloque "Administrar" solo-autor (`queryByText` nulo para otros), edición de horario/como_donar con llamada al API, banner de cerrado que oculta contacto, y eliminar con confirmación en dos pasos + navegación (patrón feature 18). En API: 403 en español para editar y eliminar ajenos (tests + en vivo).
- **Acceptance 3**: `estado="activo"` por defecto en el GET (mismo patrón de reportes) — test + en vivo; `/ayudar` alimenta mapa y tarjetas del mismo endpoint.
- **Acceptance 4**: mismas reglas de `ReportIn` reutilizadas en el `model_validator` (test + en vivo: zona inválida y Otro sin ciudad_texto → 422).
- Consistencia: decisiones del plan aprobado por el usuario respetadas (publica cualquiera con cuenta — ADR 0005 §4; `como_donar` informativo sin pagos; sección unificada `/ayudar` con nav y CTA en la landing); modelo con tipos portables; `direccion` obligatoria con su porqué documentado; foto huérfana documentada apuntando a la feature 20 del backlog; rutas literales no afectadas (router propio `/api/organizaciones`).
- `feature_list.json`: `32-red-de-apoyo` a `done` con edición puntual sobre la línea 421; verificado que el otro cambio de status del diff (`33-necesidades-ayuda` en `todo`) es un item nuevo de backlog del líder en el mismo working tree, no una edición del revisor; `validate_feature_list.py` → exit 0.

**Condición explícita (patrón 15/28)**: tabla nueva `organizaciones` — el merge/push a `main` exige ejecutar ANTES el `CREATE TABLE` aditivo en Supabase Postgres (autorizado en el plan aprobado). Recordatorio crítico: con `SKIP_DB_CREATE_ALL=1` en prod, la tabla NO se crea sola en el deploy.

Menores (no bloquean): (a) recurrente — hash del commit en `changes.md`; (b) el listado ordena por `creado_en desc` (razonable para un directorio; anotado por si el volumen pide orden por zona/tipo después).

## Veredicto del revisor — feature 33 (2026-08-12): APROBADA, condicionada a la migración de prod antes del merge a main

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `12c4d38`). Evidencia ejecutable de esta sesión:

- **Acceptance 4 (primera mitad)**: `bash init.sh` corrido de verdad — **verde completo, 97/97 tests de API + 83/83 de web**; `npm run build` corrido por el revisor — limpio (131.39 kB js gzip).
- **Acceptance 1**: 8 tests de API + **E2E en vivo del revisor** con el ciclo completo: el autor publica 2 necesidades (201, estado pendiente, `cubierta_en` null) → otro usuario 403 en publicar y en cubrir → categoría inválida 422 (Literal) → cubrir 200 con `cubierta_en` seteado → **409 al repetir** → 404 para una necesidad de otra organización (chequeo de pertenencia `organizacion_id` verificado). Limpieza completa (204 × 2) y seed reseteado.
- **Acceptance 2**: tests del detalle — pendientes primero (orden `estado desc` con el truco alfabético "pendiente">"cubierta" **comentado en el código**, verificado también en vivo), botón "Quiero ayudar" con **prefill exacto decodificado**: `Hola, vi en Pet Finder Col que necesitan 50 kg de comida para perro adulto. Quiero ayudar.` sobre el `wa.me` del teléfono normalizado de la organización, cubiertas con "Cubierta 💚" (misma mecánica de esperanza que "reunido"), y controles de autor (form Categoría+¿Qué necesitan?+Publicar, "Marcar cubierta") ausentes para no-autores (`queryBy*` nulos) — payloads exactos aseverados (`crearNecesidad(1, {...})`, `cubrirNecesidad(1, 5, 1)`).
- **Acceptance 3**: `necesidades_pendientes` como campo calculado de `OrganizacionOut` (default 0 documentado), llenado en el listado con **una sola query agregada (sin N+1, verificado por lectura)** y en el detalle; test de API del contador en ambos + test de RedDeApoyo (visible solo con >0) + en vivo (2 → 1 tras cubrir).
- Consistencia: patrón `marcar_reunido` replicado fielmente (403/409/timestamp), rutas anidadas sin conflicto de matching con `/{organizacion_id}` (segmentos distintos), tipos portables (String/DateTime), sin transacciones en la app (WhatsApp como canal, decisión del plan aprobado), tono de esperanza correcto.
- `feature_list.json`: `33-necesidades-ayuda` a `done` con edición puntual sobre la línea 435 (diff `todo`→`done`, el `in_progress` del líder estaba sin commitear); único cambio de status; `validate_feature_list.py` → exit 0.

**Condición explícita (patrón 15/28/32)**: tabla nueva `necesidades` — el merge/push a `main` exige ejecutar ANTES el `CREATE TABLE` aditivo en Supabase Postgres (ya autorizado explícitamente por el usuario en esta sesión, "Sí, ambas"). Con `SKIP_DB_CREATE_ALL=1` en prod la tabla no se crea sola en el deploy.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 34 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `89094ea`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 99/99 tests de API + 87/87 de web** (17 suites).
- **Acceptance 1**: tests del listado — "12 perdidas · 5 encontradas" en el resumen, el total filtrado ("1 con estos filtros") y la opción del select con conteo (`Perdidas (12)` con `value="perdido"` aseverado); en la landing, línea de dimensión del problema con los conteos del backend, no bloqueante (catch → no aparece) y oculta con 0+0 (mock default en beforeEach).
- **Acceptance 2**: `lib/tiempo.ts::tiempoRelativo` es pura (con `ahora` inyectable) y sus tests cubren **todos** los rangos con un AHORA fijo (momento/min/1 hora/horas/ayer/días/1 semana/semanas) más la equivalencia con/sin sufijo Z — el anclaje a UTC de los timestamps sin zona del backend es exactamente el gotcha correcto. Usada en el pie de la tarjeta (test con regex `10/08/2026 · hace`) y en el meta del detalle ("Publicado hace X"), complementando la fecha del evento sin reemplazarla.
- **Acceptance 3**: `GET /api/reports/conteos` con **una sola query agregada** (`group_by(tipo)` sobre activos, verificado por lectura) — los contadores por tipo nunca se calculan contando arrays en el cliente. Interpretación anotada: el "N con estos filtros" sí es el `length` del resultado ya traído — correcto, porque ese array es exactamente el resultado filtrado y una query extra sería redundante; el criterio apunta a los contadores por tipo, que vienen del backend. **Verificación en vivo del revisor**: conteos idénticos al SQL directo sobre el seed ({perdidos: 9, encontrados: 8}), y tras marcar a Rocky reunido bajan a 8/8 — solo activos cuentan. Seed reseteado.
- Regla de rutas respetada: `/conteos` declarada antes que las dinámicas (leído en `routers/reports.py`, comentario incluido) con test de regresión propio (200 con DB vacía, nunca 422). Sin cambio de esquema → sin migración de prod, correcto.
- `feature_list.json`: `34-contadores-y-recencia` a `done` — nota de proceso: el primer `sed` del revisor apuntó a la línea 449 (una línea abajo del status) y **no cambió nada** (verificado por `git diff`); se corrigió con la edición puntual sobre la línea 448 real. Diff neto `todo`→`done` (el `in_progress` del líder estaba sin commitear); único cambio de status; `validate_feature_list.py` → exit 0.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 21 (2026-08-12): APROBADA, condicionada a la evidencia manual del acceptance 2 post-deploy

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `7224b0d`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 103/103 tests de API + 89/89 de web**; `npm run build` corrido por el revisor — limpio (132.05 kB js gzip).
- **Acceptance 1**: tests del botón "Compartir este reporte" — con `navigator.share` presente, payload exacto aseverado (`{title: 'Pet Finder Col', text: 'Rocky — Se perdió en Armenia. Ayuda a difundir:', url}`); sin share, `clipboard.writeText(url)` + confirmación visual "Link copiado — pégalo donde quieras." (con auto-ocultado a los 3 s y catch del share cancelado por lectura — correcto, cancelar no es error).
- **Acceptance 3**: ADR 0009 leído — corto, con las 3 opciones evaluadas (SSR/prerender descartado por cambiar el stack; inyección para todos descartada por latencia en la ruta caliente) y la elegida bien fundamentada: rewrite condicionado por user-agent **solo para bots**, declarado en `vercel.json` ANTES del fallback SPA (verificado por lectura del orden), regex de 7 rastreadores, humanos sin costo. Documenta la degradación aceptable (bot no listado → vista genérica) y `SITE_URL`.
- **Backend verificado**: 4 tests de `test_paginas.py` (og tags exactos, **escape correcto de `&` y comillas** — sin inyección HTML —, foto relativa → absoluta con el sitio, foto absoluta de Supabase tal cual, sin foto omite `og:image`, 404) **+ en vivo del revisor**: `GET /reporte/1` con User-Agent de WhatsApp devuelve el HTML con `og:title "Rocky — Se perdió en Armenia"` + description/image/url correctos; `SITE_URL` respetada (incluye `.strip()` de espacios — lección aprendida aplicada); 404 y `/api/*` intactos. Seed sin tocar. La ruta top-level `/reporte/{id}` en la API no colisiona (solo había `/api/*` y `/health`).
- **Acceptance 2 (vista previa real en WhatsApp) — CONDICIÓN de esta aprobación**: es verificación manual post-deploy que el revisor no puede ejecutar (requiere prod desplegado y el rastreador real). Queda condicionada a que la sesión principal ejecute el `curl` con user-agent de WhatsApp contra producción y **documente la evidencia en `changes.md`** (el propio acceptance exige "verificación manual documentada"). Si la evidencia no llega o falla, este `done` debe revertirse.
- Sin cambio de esquema → sin migración, correcto.
- `feature_list.json`: `21-compartir-reporte` a `done` con edición puntual sobre la línea 278 (diff neto `todo`→`done` por el `in_progress` sin commitear del líder); único cambio de status; `validate_feature_list.py` → exit 0.

**Nota importante ligada a la condición**: el default de `SITE_URL` es `https://petfinder-col.com`, pero la bitácora registra la app en `pets-finder-sable.vercel.app` — si el dominio custom no existe o difiere, hay que **fijar `SITE_URL` en las env vars de Vercel al dominio real** o los `og:url` (y `og:image` de fotos relativas) apuntarán a un host equivocado; la verificación del acceptance 2 lo detectará. Añadir `SITE_URL` a la tabla de env vars de `docs/deploy.md` (mismo pendiente que `SKIP_DB_CREATE_ALL` de la feature 19).

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 27 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `07b7af6` — que además cierra con evidencia post-deploy la condición de la 21, verificado en el log). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 103/103 tests de API + 93/93 de web**. Feature solo-frontend: el backend no se toca (`estado=reunido` existe desde la 09), sin migración — correcto.
- **Acceptance 1**: test del link de la franja de la landing con href exacto `/reportes?estado=reunido`, y test de que llegar con ese query param arranca con el filtro preseleccionado (select con `value='reunido'` aseverado) y consulta reunidos de entrada (`useSearchParams`, leído).
- **Acceptance 2**: filtro "Estado" (En búsqueda / Reunidas 💚) que añade `estado: 'reunido'` al payload del backend (test con `toHaveBeenLastCalledWith`); badge celebratorio "Reunida 💚" en `bg-forest` **reemplazando** el badge de tipo solo cuando `estado === 'reunido'` (test + lectura del condicional). Sin mezclar en la vista default: el estado inicial es `'activo'` y en ese caso no se envía `estado` — el backend sigue excluyendo reunidos por defecto (los tests previos del listado con `{}` pasan sin cambios, y verificado en vivo: 17 activos sin reunidos, 2 reunidos navegables con el filtro).
- **Acceptance 3**: checkbox "Solo reencuentros 💚" en el mapa — test de la re-consulta con `{estado: 'reunido'}` y del pin en `bg-forest`; por lectura: el contador del header cambia a "N reencuentros", la selección se limpia al alternar la capa, y todos los pins de la capa reunidos van en forest (celebración, no danger).
- Tono consistente: reencuentros como contenido celebrable y navegable (la métrica de esperanza del producto), 💚 coherente con la franja y el detalle.
- `feature_list.json`: `27-vista-reencuentros` a `done` con edición puntual sobre la línea 356 (diff neto `todo`→`done` por el `in_progress` sin commitear del líder); único cambio de status; `validate_feature_list.py` → exit 0.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 20 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `e68a6d1`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 109/109 tests de API + 93/93 de web**.
- **Acceptance 1**: test con mock del endpoint de Storage aseverando la llamada **exacta** (`DELETE https://abc123.supabase.co/storage/v1/object/fotos/mifoto.jpg` con `Authorization: Bearer <service key>`) al eliminar un reporte cuya foto vive en el bucket propio. La misma `borrar_foto` está conectada también en `eliminar_organizacion` (deuda de la 32 saldada), antes del delete de la fila.
- **Acceptance 2**: test del bucket caído (`ConnectionError`) → **204**, el reporte desaparece (404) y queda el log "se elimina igual" (aseverado con `caplog`). Por lectura: `try/except Exception` total con `logger.exception`, documentado en el docstring con su porqué ("una foto huérfana es aceptable, un 500 al eliminar no") — el `noqa: BLE001` está justificado ahí mismo.
- **Acceptance 3**: test del archivo local borrado del disco real (`tmp_path`) **+ E2E en vivo del revisor sin mocks**: subir foto → crear reporte con ella → `DELETE` → **el archivo desaparece de `data/media/uploads/`** junto con el reporte (204); las 20 fotos del seed intactas. Seed reseteado.
- Bordes bien cubiertos: foto de **otro host** intocable (el mock lanza `AssertionError` si se llamara al delete — test por construcción), `/media/seed/` intocable (test con archivo real), `foto_url=None` no-op, Supabase sin configurar con URL absoluta → log sin tocar nada. Detalle de seguridad correcto: `Path(foto_url).name` (basename) impide traversal fuera de `UPLOADS_DIR`.
- **Limpieza de huérfanas pre-existentes**: la descripción pedía "limpieza puntual documentada" — cumplida como documentación en `changes.md` (listar objetos del bucket vs `foto_url` referenciados en reports+organizaciones; ejecutar contra prod solo con autorización explícita). Razonable no ejecutarla ahora (volumen mínimo y requiere autorización).
- Consistencia: sin credenciales nuevas (reusa la service key de `subir_a_supabase` con la config leída al llamar y los `.strip()`), docstrings de las features 18/32 actualizados — sin discrepancia doc/código. Sin cambio de esquema → sin migración.
- `feature_list.json`: `20-fotos-huerfanas-storage` a `done` con edición puntual sobre la línea 265 (diff neto `todo`→`done` por el `in_progress` sin commitear del líder); único cambio de status; `validate_feature_list.py` → exit 0.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 29 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `653a08f`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 111/111 tests de API + 97/97 de web** (18 suites); `npm run build` corrido por el revisor — limpio (132.53 kB js gzip).
- **Acceptance 1**: test de API que edita **todos** los campos nuevos en una pasada (raza/color/tamano/barrio/fecha_evento/lat/lng/foto_url — cada uno aseverado) **+ E2E en vivo del revisor** sobre el reporte 1 del seed: los 8 campos persisten; `tamano` inválido → 422 (Literal, test + vivo). En la UI: pantalla `/reporte/:id/editar` con pin corregible por click sobre `MapaLienzo`, foto actual visible + re-subida vía `FotoUpload` (que ya comprime), características por especie con el catálogo compartido.
- **Acceptance 2**: 403 para no-autor intacto (test previo sin cambios + verificado en vivo); campos no enviados intactos (test asevera nombre y zona; en vivo además tipo/especie); **bonus verificado en vivo**: enviar `zona`/`especie` en el PUT se ignora (no están en `ReportUpdate` — no editables por diseño, con el porqué comentado en el schema y explicado en la UI: "no se puede cambiar — elimina y créalo de nuevo"). El redirect client-side del no-autor (replace al detalle, sin render del form) tiene test propio; la barrera real sigue siendo el 403 del API.
- **Acceptance 3**: test de precarga campo a campo (descripción, raza `Labrador`, color, tamaño, barrio, fecha, teléfono, y la zona visible como no-editable) + validación de obligatorios idéntica a la de creación (descripción/teléfono con trim, test de que no llama al API); el payload del guardado conserva las coords actuales sin click (test con `objectContaining`).
- Diseño consistente: el router `editar_reporte` no cambió (el `exclude_none` + `setattr` existente cubre los campos nuevos — mínima superficie), MisReportes conserva su edición inline corta, sin cambio de esquema → sin migración.
- `feature_list.json`: `29-editar-reporte-completo` a `done` — **nota de proceso**: segundo off-by-one del mismo tipo que en la 34 (el primer `sed` apuntó a la línea 383 en vez de la 382 y no cambió nada, detectado por `git diff` y corregido con la edición puntual correcta); diff neto `todo`→`done`, único cambio de status, `validate_feature_list.py` → exit 0.

Menores (no bloquean): (a) recurrente — hash del commit en la entrada de `changes.md`; (b) limitación heredada del `exclude_none`: una característica ya guardada no puede "limpiarse" de vuelta a "Sin especificar" desde la edición (el `''` del select se convierte en `undefined` y el campo no viaja — el valor viejo queda). Mismo comportamiento pre-existente de `barrio`; si algún día molesta, la vía es un sentinel explícito o `exclude_unset`, no un parche rápido.

## Veredicto del revisor — feature 30 (2026-08-12): APROBADA (con 1 observación de entorno documentada)

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `3bf23c3`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 115/115 tests de API + 99/99 de web**.
- **Acceptance 1 (q combinable, case-insensitive)**: tests de API (`q=rOcKy` case-insensitive, combinada con tipo, sin resultados → `[]`) **+ en vivo sobre el seed real**: `q=rocky` → Rocky; `q=laureles` → el reporte con ese barrio; `q=pañoleta` → los 2 de Medellín y combinada con `tipo=encontrado` → 1; `GOLDEN`/`ROCKY` en mayúsculas funcionan. El `or_` cubre exactamente los 4 campos del acceptance y `q` en blanco se ignora (strip).
- **Acceptance 2 (paginación con total y orden estable)**: test de API (página1+página2 == listado completo, header `X-Total-Count: 3`, sin limit → completa + header, 422 en limit 0/101 y offset -1) **+ en vivo con el seed real**: `limit=12`+`limit=12&offset=12` → 12+5 ids **idénticos** al listado completo, header 17 en ambas páginas; `q=pañoleta&limit=1` → total 2 en el header con páginas de 1 sin duplicados. Por lectura: el count va sobre la subquery filtrada ANTES de ordenar/paginar (correcto), el orden estable es `fecha_evento desc, id desc`, y **sin `limit` la respuesta sigue completa** — MapaReportes y MisReportes intactos (verificado en vivo con `estado=todos&user_id=1`).
- **Acceptance 3 (UI)**: campo "Buscar" con test de que `q` viaja conservando los filtros (`{tipo:'perdido', q:'collar rojo'}, 12, 0`); "Cargar más (N restantes)" con test de acumulación (offset=length, 12+1, total estable); los 8 tests preexistentes del listado migrados al cliente paginado con aserciones `(filtros, 12, 0)` — todos verdes. El "N con estos filtros" del resumen ahora usa el total del backend (upgrade correcto sobre la 34; el criterio de la 34 queda mejor cumplido, no roto). `listarReportesPaginado` con fetch propio para leer el header — decisión razonable documentada (request() no expone headers).
- **Observación de entorno (no bloquea, verificada por el revisor con SQLite puro)**: el `LIKE` de SQLite solo es case-insensitive para ASCII — `q=PAÑOLETA` (mayúscula con Ñ) no matchea "pañoleta" en dev local (0 resultados), pero en **Postgres de producción `ILIKE` sí es case-insensitive unicode** y funcionará. `ilike` es la elección portable correcta; arreglarlo en SQLite requeriría la extensión ICU (no lo amerita). Queda documentado aquí para que nadie lo confunda con un bug en dev.
- Sin cambio de esquema → sin migración. `feature_list.json`: `30-busqueda-y-paginacion` a `done` — esta vez la línea se localizó por número exacto con grep antes de editar (lección de los off-by-one de la 34/29); línea 395, diff `todo`→`done`, único cambio de status; `validate_feature_list.py` → exit 0.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 31 (2026-08-12): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `599d0fb`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 115/115 tests de API + 103/103 de web**; `npm run build` corrido por el revisor — limpio (133.78 kB js gzip).
- **Acceptance 1**: tests con `vi.stubGlobal` de `navigator.geolocation` — coords reales dentro de Armenia (4.51, -75.7) van al payload del reporte con redondeo a 4 decimales (aseverado con `objectContaining`), y **permiso denegado** muestra el aviso exacto ("No pudimos obtener tu ubicación — pon el pin manualmente.") con el submit manual publicando igual después (flujo intacto, test completo). Por lectura: navegador sin `geolocation` → aviso propio, mismo fallback.
- **Acceptance 2**: test de coords de Medellín con zona Armenia elegida → tarjeta "parece que estás en Medellín" y el botón "Cambiar a Medellín y usar mi ubicación" actualiza el selector (aseverado). Por lectura: si ninguna zona contiene las coords → "Usar Otro lugar de Colombia" (con `cambiarZona(ZONA_OTRO)`), y "Ignorar" descarta la sugerencia sin tocar nada; el caso sin zona elegida autoselecciona la zona real (sinergia correcta con el fix reciente de "sin zona preseleccionada").
- **Acceptance 3**: test del botón "📍 Centrar en mi ubicación" en `/mapa` invocando `getCurrentPosition`; el centrado (`MapaLienzo.centro` → `setView([lat,lng], 15)`) verificado por lectura — **limitación declarada**: el `setView` real es comportamiento de Leaflet no verificable en jsdom (el efecto es no-op natural con `mapaRef` null); queda a cargo de la verificación manual en navegador de la sesión principal post-deploy, igual que en la feature 14.
- **Verificación numérica extra del revisor**: los casos de los tests del frontend replicados contra los bounding boxes del **backend** (fuente de verdad) — (4.51,-75.7)→Armenia, (6.244,-75.581)→Medellín, Cartagena→None — coinciden; y comprobado que **las 7 zonas no se solapan** entre sí, así que `zonaQueContiene` es determinista (nunca depende del orden de iteración).
- Diseño consistente: helpers puros en `lib/ciudades.ts` sobre las cajas existentes (sin tercera copia de datos), fallbacks que nunca bloquean el flujo manual, sin permisos pedidos hasta que el usuario toca el botón (correcto en privacidad/UX). Sin cambio de esquema → sin migración.
- `feature_list.json`: `31-pin-mi-ubicacion` a `done` — línea 408 localizada por número exacto antes de editar; diff `todo`→`done`, único cambio de status; `validate_feature_list.py` → exit 0.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 35 (2026-08-13): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `a43b5c7`). Evidencia ejecutable de esta sesión:

- **Acceptance 5**: `bash init.sh` corrido de verdad — **verde completo, 129/129 tests de API + 117/117 de web**; `npm run build` corrido por el revisor — limpio (141.63 kB js gzip; el +8 kB es `react-easy-crop`). Nota de contexto: el conteo de API subió respecto al reporte del líder (115→129) porque el HEAD base ya incluye el trabajo del crawler (`a43b5c7`), ajeno al alcance de esta revisión.
- **Acceptance 1**: test del listado/mapa como **botones con borde** — asevera `href` y que la clase contiene `border-forest` (no link subrayado); por lectura, jerarquía correcta (borde vs los 2 CTAs llenos, y "Centros de ayuda" baja a link de texto).
- **Acceptance 2 (recorte)**: `recortarImagen` con tests propios — área que cubre toda la imagen → **devuelve el original por identidad** (sin re-codificar), área parcial → canvas con los args exactos de `drawImage(100,50,400,300 → 0,0,400,300)` y JPEG a 0.92 (calidad alta a propósito: la compresión posterior es la de siempre), sin soporte → original. `FotoUpload` con el flujo completo testeado vía stub de `react-easy-crop` (imposible en jsdom, decisión honesta): elegir archivo abre el encuadre sin subir nada; **sin ajustar, sube el archivo elegido y `recortarImagen` ni se llama**; con encuadre ajustado sube la versión recortada (payload del área exacto); Cancelar cierra sin subir. El orden recorte→compresión y el `e.target.value=''` para reelegir el mismo archivo, correctos por lectura.
- **Acceptance 3 (marca)**: tests — logo en la nav con `alt='Pet Finder Col'`, `src=/logo.svg` y link a `/`; logo en la landing. Verificado por el revisor **sobre el build real**: `dist/favicon.svg` idéntico al isotipo oficial (huella+casa sobre forest `#1F4D3A`), `?v=3` en `dist/index.html` (cache-busting correcto y bien explicado en el comentario), `apple-touch-icon.png` y `logo.svg` presentes en `dist/`. El test viejo de la marca sigue pasando porque el `alt` da el mismo nombre accesible — señalado honestamente por el líder y verificado.
- **Acceptance 4**: tests del renombre en nav (`Centros de ayuda` → `/ayudar`), landing ("Centros de ayuda: acopio, fundaciones y donaciones") y h1 de `/ayudar`; la ruta no cambió; grep confirma que en la UI no quedan restos de "Ayudar"/"Red de apoyo" (solo un comentario de código de la 32).
- **Fix de test preexistente correcto**: `Reportes.test.tsx` tenía `creado_en` fijo que se volvía "ayer" al día siguiente — ahora es relativo a la corrida (`Date.now() - 2h`). Es exactamente la clase de test dependiente del reloj que hay que erradicar; bien resuelto.
- Dependencia nueva: solo `react-easy-crop ^6.2.3` (UI, sin servicios externos — no amerita ADR). Sin cambios de esquema ni de API → sin migración. La verificación visual del recorte real en navegador (900x600 → 600x600) queda documentada por la sesión principal, límite de jsdom declarado.
- `feature_list.json`: `35-marca-recorte-y-visibilidad` a `done` — línea 461 localizada por número exacto; único cambio de status; `validate_feature_list.py` → exit 0.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear.

## Veredicto del revisor — feature 36 (2026-08-13): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `af71e2b`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 134/134 tests de API + 122/122 de web** (19 suites).
- **Acceptance 3 (función pura espejo)**: `lib/titulo.ts::tituloReporte` y `services/titulos.py::titulo_reporte` leídos lado a lado — lógica idéntica (nombre manda; especie + tamaño + color en minúscula; color "Otro" omitido; `filter(Boolean)`/generator sin huecos; única divergencia razonable: el backend tiene fallback "Mascota" para especie desconocida, imposible en el frontend tipado). **4 tests unitarios en cada lado, caso a caso equivalentes** (nombre manda, composición completa, ausencias sin huecos ×3, color Otro).
- **Acceptance 1**: test de la tarjeta sin nombre → heading exacto "Perro mediano café"; por diff, `tituloReporte` reemplaza el patrón `nombre ?? especie` en **todos** los consumidores (ReporteCard, ReporteDetalle incluidas las coincidencias, MapaReportes en etiqueta de pin y mini-tarjeta, MisReportes en título y modal de edición), y las constantes `ETIQUETA_ESPECIE` huérfanas se eliminaron (quedan solo donde los chips las siguen usando — sin código muerto). Con nombre, el nombre sigue mandando (tests en ambos lados).
- **Acceptance 2**: test de API end-to-end (`og:title content="Perro mediano café — Se perdió en Armenia"`) **+ verificación en vivo del revisor sobre el seed real**: el reporte 2 (perro encontrado sin nombre) responde a un user-agent de WhatsApp `og:title "Perro mediano miel / dorado — Encontrada en Armenia"`, y Rocky (con nombre) queda intacto — los tests previos de `test_paginas.py` no se tocaron y pasan. Seed reseteado.
- Sin cambios de esquema ni de API → sin migración. Las features 37-39 del lote quedan en `todo` sin revisar (los 3 `+status: todo` del diff son sus entradas nuevas del líder, no ediciones del revisor).
- `feature_list.json`: `36-titulo-descriptivo` a `done` — línea 475 localizada por número exacto; único `done` del diff; `validate_feature_list.py` → exit 0.

Menor recurrente: hash del commit en la entrada de `changes.md` al commitear (la entrada de la 36 aún no está en changes.md — añadirla con el commit, checkpoint #4).

## Veredicto del revisor — feature 37 (2026-08-13): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `a65fbca`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 138/138 tests de API + 122/122 de web**.
- **Acceptance 1**: `razones_coincidencia` es una función pura nueva con 3 tests unitarios (razones básicas con lista exacta aseverada; mismo día/color/tamaño; color distinto u "Otro" **no afirma nada** — aseverado con `all("color" not in r)`) + test del endpoint con las razones del par sembrado. **Verificación en vivo del revisor sobre el seed real**: Rocky↔encontrado → `['mismo perro', 'misma zona (Armenia)', 'a 0.6 km', '1 día de diferencia', 'mismo color', 'mismo tamaño']` (el par comparte Criollo/Miel-dorado/mediano en el seed — correcto), y el par de Medellín → `misma zona (Medellín)`, `a 5.06 km`. Todas las frases en español, formato de chips.
- **Acceptance 2 (orden intacto)**: el diff de `ordenar_coincidencias` es **cero líneas** (solo adiciones debajo de la función), los 6 tests previos de `test_coincidencias.py` no se tocaron (diff solo con `+`), y en vivo el primer candidato de Rocky sigue siendo el id 2 a 0.6 km — el motor determinista de la 08 no cambió.
- **Acceptance 3**: test del detalle ampliado con los chips ("mismo perro", "1 día de diferencia" aseverados); por diff, las razones se pintan como chips `bg-forest-tint` bajo cada candidato y el badge suelto "a X km" de la derecha se retiró sin perder la información (ahora viaja dentro de las razones — cumple la letra del acceptance 1 que pide 'a X km' en la lista).
- Diseño consistente: separación correcta informar-vs-ordenar (documentada en el docstring — especie/zona son filtros, distancia/días son puntaje, color/tamaño solo informativos), `CoincidenciaOut.razones: list[str]` sin tocar `ReportOut`, sin cambio de esquema de DB → **sin migración** (el campo es calculado en el response).
- `feature_list.json`: `37-coincidencias-explicables` a `done` — línea 488 por número exacto; diff `todo`→`done`, único cambio de status; `validate_feature_list.py` → exit 0. Las 38-39 siguen en `todo`, sin tocar.

Pendiente obligatorio al commitear (checkpoint #4): añadir la entrada de la feature 37 a `changes.md` con su hash — igual que en la 36, la entrada aún no existe en el working tree.

## Veredicto del revisor — feature 38 (2026-08-13): APROBADA

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `7fb80aa`). Evidencia ejecutable de esta sesión:

- **Acceptance 4**: `bash init.sh` corrido de verdad — **verde completo, 145/145 tests de API + 125/125 de web** (20 suites). Los toques a tests preexistentes (`test_avistamientos`/`test_organizaciones`/`test_reports`) son solo el reformateo de black del tropiezo reportado — cero cambios semánticos, verificado por diff.
- **Acceptance 2 (función pura con tests)**: `services/busqueda.py` — pura de verdad (candidatos por parámetro, dataclass frozen). Tests unitarios: **parecido relativo a los criterios dados** (1 criterio cumplido → 100, no 25), pesos con no-cumplidos que bajan (75 = 45/60 exacto), señas insensibles a tildes/mayúsculas (3 de 4 palabras → 75), sin criterios → 0, y filtro+orden con la aritmética verificada por el revisor (100 > 56=25/45 > 44=20/45, gato fuera). Diseño sólido: stopwords y tokens <3 fuera, color "Otro" no puntúa (consistente con la 36/37), señas contra descripción+nombre+raza+barrio, muestra de palabras comunes en la razón.
- **Acceptance 1**: endpoint con test (solo el tipo pedido y solo activos; 422 con `tipo=reunido` vía pattern) **+ en vivo sobre el seed real**: búsqueda "Luna" entre encontrados → 4 resultados, todos encontrado/activo/perro, **orden por parecido desc** verificado; ruta estática `/busqueda` declarada antes de las dinámicas (regla comentada) y no eclipsada (200 en vivo); tope 20 resultados por lectura.
- **Hallazgo positivo verificado en vivo**: a diferencia del `q` de la feature 30 (limitado por el LIKE ASCII de SQLite), las señas usan normalización unicode **propia en Python** (`unicodedata` NFD) — "PAÑOLETA VERDE" matchea la pañoleta de Simón al **100%** también en dev local. La comparación es idéntica en SQLite y Postgres: sin sorpresas entre entornos.
- **Acceptance 3**: tests de `/buscar` (submit con params por defecto al tipo "encontrado", modo "Encontré una" → busca perdidos, resultado con "Se parece en un 85%" + razones) y de la landing (link "🔎 Busca a tu mascota por descripción" → `/buscar`). Reutiliza los catálogos existentes (caracteristicas/ciudades) sin duplicar datos.
- Sin cambio de esquema → sin migración (parecido/razones son calculados del response). Sin AI, explicable — consistente con `docs/product-research.md`.
- `feature_list.json`: `38-busqueda-por-descripcion` a `done` — línea 501 por número exacto; diff `todo`→`done`, único cambio de status; `validate_feature_list.py` → exit 0. La 39 sigue en `todo`.

Pendiente obligatorio al commitear (checkpoint #4): entrada de la feature 38 en `changes.md` con su hash (aún no existe en el working tree, mismo patrón de la 36/37).

## Veredicto del revisor — feature 39 (2026-08-13): APROBADA, condicionada a la migración de prod antes del merge a main

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `430b24c`). Evidencia ejecutable de esta sesión:

- **Acceptance 5 (primera mitad)**: `bash init.sh` corrido de verdad — **verde completo, 152/152 tests de API + 127/127 de web**.
- **Acceptance 1**: 3 tests de API (alta 201 **sin exponer email ni token** — aseverado; idempotencia con mayúsculas/espacios → 200 con el mismo id; 422 correo inválido con mensaje en español vía `field_validator` normalizador + 404 reporte inexistente) y la caja del detalle con 2 tests (suscribe+confirma con el payload exacto; **reunido no la ofrece**). **E2E en vivo del revisor sobre el seed real**: ciclo completo alta→idempotente→avistamiento→reunido→baja→422/404, todo correcto. La carrera de duplicados se resuelve con `IntegrityError`+rollback+relectura (patrón sano) sobre el `UniqueConstraint(report_id, email)`.
- **Acceptance 2**: test con `_enviar_email` monkeypatcheado — el avistamiento dispara 1 email (destino, asunto con el **título compuesto de la 36**, comentario y **link de baja aseverado en el html**) y el reunido dispara el segundo ("volvió a casa"); test de proveedor que explota → el endpoint responde 201 igual (doble cinturón: try/except en `notificar_novedad` por suscriptor y best-effort en `_enviar_email`). Verificado también en vivo.
- **Acceptance 3**: test de la baja (200 con "no te escribimos más", fila borrada, link repetido → 404 "ya no es válido") + en vivo con el token real de la DB; HTML mínimo en español con los colores de la marca; el token aleatorio (`secrets.token_hex(16)`, único) es la autorización — razonable y documentado.
- **Acceptance 4**: test con `caplog` — sin `RESEND_API_KEY` el envío devuelve False con el log "RESEND_API_KEY sin configurar" y nada más se rompe. El default de `RESEND_FROM` (remitente de pruebas de Resend) es sensato.
- **ADR 0011** leído: 3 opciones evaluadas (SMTP y WhatsApp Business descartados con razones reales), la clave solo en env vars de Vercel, y la **limitación del envío síncrono dentro del request documentada honestamente** con su criterio de salida (cola si crece el volumen). Consistente con el patrón operativo de Supabase. `SITE_URL` reutilizada para los links.
- Seguridad revisada: `SuscripcionOut` sin email/token, `html.escape` sobre novedad y título (sin inyección HTML en los correos), sin key hardcodeada (grep implícito: solo `os.environ`).
- `feature_list.json`: `39-alertas-por-reporte` a `done` — línea 514 por número exacto; diff `todo`→`done`, único cambio de status; `validate_feature_list.py` → exit 0.

**Condición explícita (patrón 15/28/32/33)**: tabla nueva `suscripciones` — el merge/push a `main` exige ejecutar ANTES el `CREATE TABLE` aditivo (con el índice de `report_id` y los unique de `email`+`token`) en Supabase Postgres, con autorización del dueño. Con `SKIP_DB_CREATE_ALL=1` en prod la tabla NO se crea sola. Además, para que los correos salgan de verdad: cuenta de Resend + DNS del dominio + `RESEND_API_KEY`/`RESEND_FROM` en Vercel (mientras tanto, no-op con log — aceptable por diseño).

Pendiente obligatorio al commitear (checkpoint #4): entrada de la feature 39 en `changes.md` con su hash. Menor: los `import secrets`/`import re` dentro de cuerpos de función funcionan pero lo idiomático es tenerlos arriba del módulo — nit de estilo, no bloquea.

## Veredicto del revisor — feature 40 (2026-08-13): APROBADA, condicionada al paquete de migración de prod (40-42) antes del merge a main

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `47e6fcc`). Evidencia ejecutable de esta sesión:

- **Acceptance 4 (primera mitad)**: `bash init.sh` corrido de verdad — **verde completo, 155/155 tests de API + 130/130 de web**.
- **Acceptance 1 (avisos)**: componente `AvisoSeguridad` puro (dos textos por contexto, tono correcto, estilo ochre de advertencia) con tests — "espacio público" en ReportarMascota y "nadie debe pedirte dinero" en ReporteDetalle; por diff también en RegistrarOrganizacion (publicar) y OrganizacionDetalle (contactar). En el detalle el aviso aparece solo en activos con canal de contacto (condición leída) — bien ubicado donde ocurren las estafas.
- **Acceptance 2 (cámara)**: test del input con `capture="environment"` que entra al mismo flujo de recorte (asevera el encuadre); la galería conserva `id=foto-upload` y `accept` restrictivo; ambos convergen en `handleChange` → recorte de la 35 → compresión de la 19 (leído).
- **Acceptance 3 (multicanal)**: 3 tests de API (normalización `" @MiCuenta "` → `MiCuenta`, opcionales null, `"@"` → null vía `field_validator`) + test de UI con hrefs exactos (`https://www.instagram.com/micuenta/` y la URL de Facebook http respetada tal cual) + el aviso en el mismo test. **E2E en vivo del revisor**: POST con redes normaliza y persiste, los reportes del seed sin las columnas siguen sirviendo (null), limpieza hecha. `target="_blank" rel="noreferrer"` en ambos botones.
- **Verificación de la corrección del regex**: las dos expectativas de payload flagged (PUT de MisReportes y `crearOrganizacion` de RegistrarOrganizacion) están intactas en contenido y sin los campos nuevos (las organizaciones no los tienen) — solo quedó una sangría cosmética rara en `RegistrarOrganizacion.test.tsx:58` (sintácticamente válida; prettier del pre-commit la normalizará).
- **Hallazgo menor del E2E (no bloquea)**: `ReportUpdate` no reusa el validator de normalización — un `PUT` por API puede guardar `"@otra"` con el arroba. Mitigado por partida doble: la pantalla de edición no expone estos campos y `urlPerfilPlataforma` limpia el `@` al construir el href (verificado en el código). Fix sugerido de una línea cuando se toque: aplicar el mismo `field_validator` en `ReportUpdate`.
- `feature_list.json`: `40-seguridad-y-contacto-multicanal` a `done` — línea 528 por número exacto; los otros dos `+status: todo` del diff son las entradas nuevas 41-42 del líder, no ediciones del revisor; `validate_feature_list.py` → exit 0.

**Condición explícita**: columnas nuevas `reports.instagram`/`reports.facebook` — el merge a `main` exige el `ALTER TABLE ADD COLUMN` aditivo en Supabase Postgres, que irá en el **paquete conjunto 40-42 autorizado por el dueño** (con `SKIP_DB_CREATE_ALL=1` nada se crea solo). El merge no ocurre hasta entonces, como declara el plan.

Pendiente obligatorio al commitear (checkpoint #4): entrada de la feature 40 en `changes.md` con su hash.

## Veredicto del revisor — feature 41 (2026-08-13): APROBADA, condicionada al paquete de migración de prod (40-42) antes del merge a main

Revisión independiente sobre el working tree de `develop` (sin commitear, sobre `56ab37d`). Evidencia ejecutable de esta sesión:

- **Acceptance 4 (primera mitad)**: `bash init.sh` corrido de verdad — **verde completo, 160/160 tests de API + 133/133 de web**.
- **Acceptance 1**: 5 tests de API (orden principal-primero en POST y GET, 422 con 3 extras vía `max_length=2`, solo principal, sin fotos → `[]`, DELETE borra extras con `borrar_foto` monkeypatcheado y el orden aseverado) **+ E2E en vivo del revisor con fotos reales**: subí 3 JPEGs por `/api/uploads`, creé el reporte (principal + 2 extras), `fotos` volvió en orden exacto, 422 con 3 extras, y el **DELETE borró los 3 archivos del disco** (verificado por existencia física antes/después). Uploads y seed limpios al final.
- **Acceptance 2**: test de `FotoUpload` multi (acumula, notifica la lista completa, contador "2/3 fotos — la primera es la principal", quitar re-notifica) — cada foto pasa por el mismo flujo de recorte/compresión (converge en `subir()`, leído); tests del detalle (miniaturas cambian la foto grande por `src`; con una sola foto no hay miniaturas). `ReportarMascota` deriva todo de la lista (`fotos[0]` → principal, resto → `fotos_extra`, y quitar todas deja el payload sin foto — sin estado obsoleto, leído).
- **Acceptance 3 (compatibilidad)**: `foto_url` intacto en tarjetas/mapa/og — verificado en vivo que `og:image` aparece **una sola vez** y con la principal; los tests existentes de tarjetas/og no se tocaron (el diff no los incluye); `Reporte.fotos` opcional en types con fallback a `foto_url` (fixtures viejos sin tocar); los reportes del seed responden `fotos = [principal]` vía la property.
- Diseño consistente: `maxFotos` default 1 conserva el comportamiento exacto anterior (EditarReporte sigue mono-foto, fuera de alcance); relationship con `cascade delete-orphan` + `lazy selectin` (sin N+1 en listados); property `fotos` como única fuente del contrato de salida; tabla con FK indexada y tipos portables.
- `feature_list.json`: `41-fotos-multiples` a `done` — línea 541 por número exacto; diff `todo`→`done`, único cambio de status; `validate_feature_list.py` → exit 0. La 42 sigue en `todo`.

**Condición explícita**: tabla nueva `report_fotos` — va en el **paquete conjunto de migración 40-42** (ALTER de la 40 + CREATE TABLE de la 41/42) autorizado por el dueño ANTES del merge a `main`; con `SKIP_DB_CREATE_ALL=1` en prod nada se crea solo.

Pendiente obligatorio al commitear (checkpoint #4): entrada de la feature 41 en `changes.md` con su hash. Menor: `lazy="selectin"` dispara una query extra por página del listado (aceptable hoy; si el listado crece, medir).
