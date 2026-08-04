# Estado actual

**Fase activa:** backlog — `feature_list.json`
**Feature actual:** ninguna `in_progress`. `14-shelter-map` cerrada `done` (revisor, 2026-08-04, ver cierre resumido más abajo). `13-favorites` cerrada `done` (ver cierre resumido más abajo).

## Contexto

`06`-`13` están `done` (ver cierres resumidos más abajo). `14-shelter-map` es la siguiente feature del backlog: "Vista de mapa con refugios cercanos y sus mascotas publicadas." `depends_on: ["01-foundations-data"]` (done), hoja del grafo.

Existe un documento de diseño **ya aprobado por el usuario** con todas las decisiones de esta feature tomadas: `/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md`. Este plan es una transcripción operativa de ese documento — **ninguna decisión de UX/arquitectura se reabre aquí**, incluida la decisión ya confirmada con el usuario de **no usar un mapa real con tiles externos** (Leaflet/Google Maps/OSM): en su lugar, un "mapa" propio en CSS/SVG puro, posicionando los pines por interpolación lineal de `lat`/`lng` real dentro del bounding box de Bogotá ya usado en el resto del proyecto, sin dependencia nueva ni conexión a internet en runtime.

**Como `13-favorites`, esta feature NO tiene diseño previo en `design/`** (las 11 pantallas del HANDOFF original no la contemplaban) — libertad de UX, atada a los tokens de `design/design-system.md` y a los patrones ya usados en el resto del repo (mismo criterio que `Apadrinar.tsx`/`Favoritos.tsx`).

**`acceptance` estaba vacío** en `feature_list.json` para este item; el documento de diseño ya lo proponía (§4, 6 líneas) y el líder lo escribió tal cual al poner la feature en `in_progress` en esta sesión (ver más abajo).

## Verificación del líder antes de planificar (2026-08-04, releído el código real, no solo el documento de diseño)

- `src/api/adopta_api/models/shelter.py`: confirmado, **no tiene** `lat`/`lng` todavía (solo `id`, `nombre`, `ciudad`, `verificado`, `adopciones_cerradas`, `tiempo_respuesta_horas`, `logo_url`).
- `src/api/adopta_api/schemas/user.py::UserOut`: confirmado, **no expone** `lat`/`lng` todavía (campos actuales: `id`, `nombre`, `email`, `ciudad`, `barrio`, `avatar_url`, `bio`, `creado_en`, `home_profile`, `metricas`).
- `src/api/adopta_api/routers/shelters.py`: confirmado, **no existe** un `GET /api/shelters` (plural, sin id) — los 6 endpoints actuales son todos `/{shelter_id}[...]` (`obtener_refugio`, `listar_solicitudes`, `obtener_solicitud`, `agendar-visita`, `pedir-informacion`, `descartar`).
- `scripts/seed.py`: confirmado, `BOGOTA_LAT_RANGE = (4.55, 4.80)` (línea 31) y `BOGOTA_LNG_RANGE = (-74.20, -74.00)` (línea 32) siguen con los valores citados en el documento de diseño — el bounding box que usará `lib/mapa.ts::posicionEnMapa` en el frontend. `SHELTERS` (línea 44) es una lista de 3 dicts sin `lat`/`lng` propios todavía (se agregan en el Paso 1).
- Patrón `lat`/`lng` ya existente a replicar: `models/user.py` (líneas 23-24) y `models/pet.py` (líneas 35-36) ya usan `Mapped[float | None] = mapped_column(Float, nullable=True)` — mismo patrón exacto para `Shelter.lat/lng` en el Paso 1.
- `routers/users.py`: confirmadas las **dos** construcciones manuales de `UserOut` (`registrar_usuario` y `obtener_perfil`, sin `model_validate`) que el documento de diseño señala como puntos que hay que tocar explícitamente para que `lat`/`lng` no queden ausentes pese a estar en el schema.
- `services/geo.py::distancia_km` confirmado existente (fórmula haversine pura, usada hoy por `services/filters.py`) — reutilizable tal cual para `distancia_km` en `GET /api/shelters`.
- `schemas/shelter.py` confirmado: no tiene aún `ShelterMapOut`/`ShelterMapPetOut` (se agregan en el Paso 2).
- Confirmado programáticamente que ningún otro item de `feature_list.json` quedó `in_progress` antes de poner `14-shelter-map` en ese estado (`python3 scripts/validate_feature_list.py feature_list.json` → exit 0 antes y después del cambio).

Conclusión: el documento de diseño sigue 100% vigente, sin necesidad de ajustar ninguna decisión.

## Decisiones ya tomadas en el documento de diseño (NO reabrir)

Documento de diseño aprobado por el usuario (base de este plan): `/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md`

| Pregunta | Decisión | Por qué |
|---|---|---|
| Mapa real (Leaflet/Google Maps/OSM) vs. propio | **Propio, CSS/SVG puro, sin dependencia externa ni red en runtime** | Coherente con cada decisión de esta sesión de mantener reproducibilidad 100% local (mismo espíritu que ADR 0004, WebSockets propios en vez de un BaaS para el chat). |
| `Shelter.lat/lng` propios o derivados de sus mascotas | **Propios** (columnas nuevas, nullable, sembradas con valores fijos) | Un refugio es un lugar físico estable; derivarlo de `Pet` rompe con 0 mascotas disponibles, es inestable (el pin se movería con cada publicación/adopción), y acopla el endpoint del mapa a `Pet` sin necesidad. Mismo patrón que `User.lat/lng`. |
| `UserOut` expone `lat/lng` | **Sí, se agregan** | Ya existen en `User` desde la feature 06, solo falta exponerlos — sin esto no hay marcador "tú estás aquí" en el mapa. |
| Mini-lista de mascotas por refugio: ¿misma respuesta o llamada aparte? | **Incluida en `GET /api/shelters`** | `GET /api/pets` no soporta filtrar por `shelter_id` hoy; con 3 refugios/17 mascotas del seed, una llamada adicional por click no aporta nada. |

**Backend**
- `models/shelter.py` (vía skill `db-migrations`): agregar `lat: Mapped[float | None]` / `lng: Mapped[float | None]` (mismo patrón que `Pet.lat/lng`).
- `scripts/seed.py`: coordenadas **fijas** por refugio en `SHELTERS` (no `random.uniform` — cambiar el orden de draws aleatorios alteraría silenciosamente las coordenadas ya sembradas de `Pet`/`User` más abajo en el script). 3 puntos reales aproximados dentro de `BOGOTA_LAT_RANGE`/`BOGOTA_LNG_RANGE`, mismo estilo de comentario que `BARRIO_COORDS`.
- `schemas/shelter.py` — nuevos schemas:
  ```python
  class ShelterMapPetOut(BaseModel):
      model_config = ConfigDict(from_attributes=True)
      id: int
      nombre: str
      fotos: list[str]

  class ShelterMapOut(BaseModel):
      id: int
      nombre: str
      verificado: bool
      lat: float | None
      lng: float | None
      mascotas_disponibles: int
      mascotas: list[ShelterMapPetOut]
      distancia_km: float | None = None  # solo si user_id válido y ambos lados tienen lat/lng
  ```
- `schemas/user.py::UserOut` — agregar `lat: float | None`, `lng: float | None`. Actualizar las **dos** construcciones manuales de `UserOut` en `routers/users.py` (`registrar_usuario` y `obtener_perfil`) para pasar `lat=user.lat, lng=user.lng` explícitamente.
- Endpoint nuevo — `GET /api/shelters` en `routers/shelters.py` (antes de `obtener_refugio` en el archivo, mismo criterio de orden que `pets.py`):
  - Query param opcional `user_id`. Si se pasa y no existe → 404 español.
  - Para cada `Shelter`: cuenta `Pet.estado == "disponible"` de ese refugio → `mascotas_disponibles` (campo **nuevo**, distinto de `ShelterMetricsOut.mascotas_publicadas` que cuenta el histórico total). Incluye la lista de esas mascotas disponibles (`ShelterMapPetOut`).
  - `distancia_km` vía `services/geo.py::distancia_km` — solo si `user_id` válido y tanto usuario como refugio tienen `lat`/`lng` no nulos; `None` en cualquier otro caso (degradación elegante, mismo criterio que `services/filters.py`).
  - Lista vacía (200, no 404) si no hay refugios.

**Frontend**
- `api/types.ts`: `ShelterMapPet`, `ShelterMap` (mirror de los schemas); agregar `lat`/`lng` a `UserProfile`.
- `api/client.ts`: `listarRefugiosMapa(userId?: number): Promise<ShelterMap[]>` → `GET /api/shelters?user_id=...`.
- `lib/mapa.ts` (nuevo) — constantes de interpolación (duplican intencionalmente el bounding box de `scripts/seed.py`, documentado con comentario que debe mantenerse en sync):
  ```typescript
  const LAT_MIN = 4.55, LAT_MAX = 4.8, LNG_MIN = -74.2, LNG_MAX = -74.0;

  export function posicionEnMapa(lat: number, lng: number): { left: string; top: string } {
    const left = ((lng - LNG_MIN) / (LNG_MAX - LNG_MIN)) * 100;
    const top = ((LAT_MAX - lat) / (LAT_MAX - LAT_MIN)) * 100;  // eje lat invertido: mayor lat = más al norte = arriba
    return { left: `${left}%`, top: `${top}%` };
  }
  ```
  Caso conocido para test: punto medio (`lat=4.675, lng=-74.10`) → `left=50%, top=50%`.
- `screens/Mapa.tsx` (nuevo):
  - Ruta `/mapa`, **fuera** de `RequiereHomeProfile` (mismo criterio que `/apadrinar`/`/perfil`).
  - `useEffect`: `listarRefugiosMapa(getActiveUserId())` + `obtenerPerfil(getActiveUserId())` (ya existe, para leer `lat/lng` del usuario y pintar "tú estás aquí"; si son `null`, se omite el marcador sin error).
  - Lienzo: `<div className="relative aspect-[4/3] w-full rounded-2xl border border-line bg-surface-alt">`, proporción fija.
  - Refugios con `lat`/`lng` no nulos → `<button>` `absolute` posicionado con `posicionEnMapa`, `-translate-x-1/2 -translate-y-1/2`. Pin `rounded-full bg-forest`; verificados con distinción visual adicional (anillo/punto interior, sin salir de la paleta). Refugios sin coordenadas no se renderizan.
  - Marcador "tú estás aquí": mismo mecanismo, forma/color distinto (`bg-ochre`) para no confundir con un refugio.
  - Click en un pin abre un panel (tarjeta simple, no modal/portal — mismo patrón que `Apadrinar.tsx`/`Favoritos.tsx`) con: nombre, insignia "Verificado" si aplica, distancia si no es `null` (`font-mono text-[11px]`, primer uso real de `distancia_km` en la UI, sigue la tipografía mono de metadatos del design-system), y mini-lista de `mascotas` (foto+nombre, cada una `<Link to={`/mascota/${id}`}>`). Sin mascotas disponibles → mensaje corto, panel no se oculta.
  - Skeleton `animate-pulse` mientras carga (nunca spinner).
- `App.tsx`: ruta `/mapa` fuera del guard + `NavLink` "Mapa".

**Sin librería de mapas** — cero dependencia nueva, cero conexión a internet en runtime. Único uso de datos geográficos: interpolación lineal en CSS/SVG local.

## Tests requeridos (documento de diseño §3)

**Backend** (extender `tests/api/test_shelters.py`, reutiliza fixtures existentes): `mascotas_disponibles` cuenta solo `estado=="disponible"` (mascota adoptada/cerrada no aparece en la lista); sin `user_id` → `distancia_km` es `None` en todos; con `user_id` válido y coordenadas conocidas → `distancia_km` calculado correctamente (mismo patrón que `test_geo.py`); `user_id` inexistente → 404; lista vacía sin shelters → 200 (regresión del criterio ya usado en `09-shelter-panel`); suite completa de `test_shelters.py` sigue pasando tras agregar `Shelter.lat/lng` (columnas nullable, no requieren tocar `_crear_shelter`). Extender `tests/api/test_users.py`: `GET /api/users/{id}` y `POST /api/users` exponen `lat`/`lng` (aunque sea `null`).

**Frontend**: `lib/mapa.test.ts` (casos conocidos de `posicionEnMapa`: centro, esquina). `screens/Mapa.test.tsx` (patrón de `Favoritos.test.tsx`): skeleton, pines en la posición calculada correcta (`data-testid` por refugio), click abre el panel con nombre/insignia/distancia/mini-lista con links correctos, refugio sin mascotas muestra el mensaje sin ocultar el panel, refugio con `lat`/`lng` null no renderiza pin.

## `acceptance` de `14-shelter-map` (6 líneas, ya escritas en `feature_list.json` en esta sesión)

1. `GET /api/shelters` (sin id) lista todos los refugios con id, nombre, verificado, lat, lng y `mascotas_disponibles` (conteo de `Pet.estado == 'disponible'` de ese refugio, distinto de `ShelterMetricsOut.mascotas_publicadas` que cuenta el histórico total).
2. `GET /api/shelters` incluye `distancia_km` (haversine vía `services/geo.py`) solo cuando se pasa `user_id` y tanto el usuario como el refugio tienen `lat`/`lng`; ausente/null en cualquier otro caso, y 404 en español si `user_id` no existe.
3. `GET /api/shelters` incluye, por refugio, la lista de sus mascotas disponibles (id, nombre, fotos) para el panel de detalle del mapa, sin requerir una llamada adicional a `GET /api/pets`.
4. Existe la pantalla `/mapa` (fuera del guard de `HomeProfile`, igual que `/apadrinar` y `/perfil`) con un lienzo propio en CSS/SVG donde cada refugio se posiciona interpolando linealmente su `lat`/`lng` dentro del bounding box de Bogotá; refugios verificados se distinguen visualmente de los que no lo son.
5. Click en un pin abre un panel con nombre del refugio, insignia de verificado, distancia (si está disponible) y una mini-lista de sus mascotas disponibles, cada una enlazando a `/mascota/:id`.
6. La feature no introduce ninguna dependencia externa de mapas ni conexión a internet en runtime — verificado explícitamente por el revisor con grep de `leaflet`/`mapbox`/`google.maps`/URLs de tiles, y confirmando que `package.json`/`requirements` no ganan una dependencia nueva de mapas.

## Restricción central de esta feature (repetir en cada paso, verificar explícitamente en el cierre)

**Sin mapa real, sin dependencia externa, sin red en runtime.** Ningún paso debe:
- agregar `leaflet`, `react-leaflet`, `mapbox-gl`, `@googlemaps/*` (o similar) a `package.json`,
- hacer `fetch`/`import` de tiles (OpenStreetMap, Mapbox, Google Maps) en runtime,
- agregar ninguna dependencia de mapas a `requirements.txt`/`pyproject.toml`.

El revisor debe verificarlo explícitamente con grep en el Paso 5 (línea 6 del `acceptance`), no asumirlo.

## Secuenciación de pasos verificables (documento de diseño §5)

**Paso 0 — Líder (COMPLETADO en esta sesión, 2026-08-04):** `14-shelter-map` → `in_progress`, `acceptance` (6 líneas) escrito en `feature_list.json`, este plan escrito en `progress/current.md`. Verificación del código real (arriba) confirmó que el documento de diseño sigue 100% vigente.

**Paso 1 — Backend: modelo + seed + `UserOut.lat/lng` (HECHO, implementador, 2026-08-04)**
- `models/shelter.py`: `Shelter.lat`/`lng` (`Mapped[float | None]`, `Float` nullable) agregados, mismo patrón que `Pet.lat/lng`.
- `scripts/seed.py::SHELTERS`: coordenadas fijas agregadas (Teusaquillo/Fontibón/Bosa, reales, repartidas), sin tocar el orden de `random.uniform` que consumen `Pet`/`User` más abajo.
- `schemas/user.py::UserOut`: `lat`/`lng` agregados. `routers/users.py`: las dos construcciones manuales de `UserOut` (`registrar_usuario`, `obtener_perfil`) actualizadas con `lat=user.lat, lng=user.lng`.
- `data/app.db` recreado con `python3 scripts/seed.py`. Verificado: `pytest tests/api -q` → 188/188 sin regresión; `ruff check`/`black --check` limpios; `bash init.sh` completo en verde (188 API + 73 frontend). Detalle en `changes.md` (entrada 2026-08-04). No se tocó `routers/shelters.py` ni frontend — sigue pendiente el Paso 2.

**Paso 2 — Backend: `ShelterMapOut`/`ShelterMapPetOut` + `GET /api/shelters` + tests (HECHO, implementador, 2026-08-04)**
- `schemas/shelter.py`: `ShelterMapPetOut`/`ShelterMapOut` agregados tal cual el diseño.
- `routers/shelters.py`: `GET /api/shelters` agregado (antes de `obtener_refugio`), `user_id` opcional (404 español si no existe), `mascotas_disponibles`/`mascotas` filtrando `Pet.estado == "disponible"`, `distancia_km` vía `services/geo.py::distancia_km` solo si `user_id` válido y ambos lados tienen `lat`/`lng`, lista vacía (200) si no hay refugios.
- `tests/api/test_shelters.py`: nueva sección "GET /api/shelters (feature 14-shelter-map)" con 5 casos (vacío→200, conteo solo `disponible`, sin `user_id`→`distancia_km` null, con `user_id`+coordenadas conocidas→distancia correcta vía `pytest.approx`, `user_id` inexistente→404). `tests/api/test_users.py`: 2 casos nuevos (`lat`/`lng` en `GET /api/users/{id}` y `POST /api/users`).
- Verificado: `pytest tests/api -q` → 195/195 (188 previos + 7 nuevos) sin regresión; `ruff check`/`black --check` limpios; `bash init.sh` completo en verde (195 API + 73 frontend). Detalle en `changes.md` (entrada 2026-08-04, paso 2). No se tocó frontend — pasos 3-4 pendientes.

**Paso 3 — Frontend: tipos/cliente + `lib/mapa.ts` (HECHO, implementador, 2026-08-04)**
- `api/types.ts`: `ShelterMapPet`/`ShelterMap` agregados (mirror exacto de los schemas backend); `UserProfile` gana `lat: number | null`/`lng: number | null`.
- `api/client.ts`: `listarRefugiosMapa(userId?: number)` → `GET /api/shelters` con `?user_id=` condicional (template string, sin `URLSearchParams` — un solo param opcional).
- `lib/mapa.ts` (nuevo): `posicionEnMapa` tal cual el diseño, constantes verificadas idénticas a `scripts/seed.py::BOGOTA_LAT_RANGE/BOGOTA_LNG_RANGE`; resultado redondeado a 4 decimales para evitar ruido de punto flotante en el caso del centro exacto.
- `lib/mapa.test.ts` (nuevo, 3 tests): centro → 50%/50%, esquina noroeste → 0%/0%, esquina sureste → 100%/100%.
- Efecto colateral necesario: 4 tests existentes con fixtures `UserProfile` (`RequiereHomeProfile.test.tsx`, `Cuestionario.test.tsx`, `MiPerfil.test.tsx`, `Registro.test.tsx`) actualizados con `lat: null, lng: null` para volver a compilar, sin tocar sus aserciones.
- Verificado: `npx tsc -b` sin errores; `npm test -- --run` → 76/76 (73 previos + 3 nuevos) sin regresión; `npm run lint` (oxlint) y `npx prettier --check .` limpios. Detalle en `changes.md` (entrada 2026-08-04, paso 3). No se creó `Mapa.tsx` ni se tocó `App.tsx` — paso 4 pendiente.

**Paso 4 — Frontend: `screens/Mapa.tsx` + ruta/nav + tests (HECHO, implementador, 2026-08-04)**
- `screens/Mapa.tsx` (nuevo): skeleton `animate-pulse` mientras `listarRefugiosMapa`/`obtenerPerfil` no resolvieron, lienzo `aspect-4/3` (misma clase Tailwind v4 que `Favoritos.tsx`/`MascotaDetalle.tsx`/`MisMatches.tsx`, no `aspect-[4/3]`), pines de refugios posicionados con `posicionEnMapa` + `data-testid="pin-refugio-{id}"` (verificados con punto interior `bg-bg`; sin `lat`/`lng` no se renderizan), marcador "tú estás aquí" (`bg-ochre` + `rotate-45`, solo si el usuario activo tiene `lat`/`lng`), panel de detalle al hacer click (nombre, insignia "Verificado", distancia si `distancia_km !== null`, mini-lista de mascotas con link a `/mascota/:id`, mensaje "Sin mascotas disponibles ahora mismo." si `mascotas.length === 0` sin ocultar el panel, mensaje de selección si no hay refugio elegido).
- `App.tsx`: ruta `/mapa` fuera de `RequiereHomeProfile` (junto a `/apadrinar`/`/perfil`) + `NavLink` "Mapa" entre "Apadrinar" y "Panel del refugio".
- `screens/Mapa.test.tsx` (nuevo, 6 casos): skeleton, pines en la posición correcta (`data-testid` por refugio, verificado contra `posicionEnMapa` importada directamente en el test), click abre panel con nombre/insignia/distancia/mini-lista con links correctos, refugio sin mascotas sin ocultar el panel, refugio con `lat`/`lng` null no renderiza pin, mensaje de selección inicial.
- Verificado: `npx vitest run` → 82/82 en verde (76 previos + 6 nuevos); `npx tsc -b` sin errores; `npm run lint` (oxlint) y `npx prettier --check .` limpios (tras `prettier --write` sobre los 2 archivos nuevos); `bash init.sh` completo en verde de punta a punta: **195 tests de API + 82 de frontend**. Detalle en `changes.md` (entrada 2026-08-04, paso 4). Cierra los 4 pasos de implementación — falta solo el Paso 5 (cierre del revisor).

**Paso 5 — Cierre del revisor (agente independiente, NO el líder ni el implementador)**
- `bash init.sh` completo en verde (backend + frontend), corrido en esa sesión (no heredado).
- Grep explícito de `leaflet|mapbox|google\.maps|tile.*openstreetmap` (y variantes) sobre el código nuevo de la feature → cero resultados esperados.
- Confirmar que `src/web/package.json` y `src/api/requirements.txt`/`pyproject.toml` no ganaron ninguna dependencia nueva de mapas (diff contra el estado previo a la feature).
- Verificar las 6 líneas de `acceptance` una por una contra un test real (tabla acceptance↔test, mismo formato que cierres anteriores).
- Recorrido manual en navegador real (`bash dev.sh`): abrir `/mapa`, confirmar que los 3 refugios sembrados aparecen en posiciones razonables dentro del lienzo (no amontonados, no fuera del cuadro), que el refugio verificado se distingue visualmente, que el marcador "tú estás aquí" aparece para el usuario semilla (id=1, Ana Martínez); click en un pin abre el panel con distancia real y la mini-lista de mascotas navegable a su ficha.
- Confirmar programáticamente que ningún otro item de `feature_list.json` quedó `in_progress`.
- Resetear `data/app.db` con `python3 scripts/seed.py` después de la verificación manual.
- Solo entonces `status` → `done` en `feature_list.json`.

## Verificación end-to-end esperada

- `bash init.sh` en verde tras cada paso (backend y frontend por separado durante implementación; completo al cierre).
- Recorrido manual en navegador real, detallado en el Paso 5.
- Resetear `data/app.db` con `python3 scripts/seed.py` después de cualquier verificación manual que haya mutado datos.

## Cobertura de tests vs. `acceptance` de `14-shelter-map` (implementador, 2026-08-04, tras el Paso 4)

Repasada línea por línea contra tests reales, antes de invocar al revisor:

1. **`GET /api/shelters` lista todos los refugios con id/nombre/verificado/lat/lng/`mascotas_disponibles`** → `tests/api/test_shelters.py::test_listar_refugios_mapa_sin_refugios_devuelve_200_vacio` (200 con lista vacía) + `test_listar_refugios_mapa_cuenta_solo_mascotas_disponibles` (conteo correcto, distinto del histórico de `ShelterMetricsOut`). Cubierta.
2. **`distancia_km` solo con `user_id` válido y ambos lados con `lat`/`lng`; 404 si `user_id` no existe** → `test_listar_refugios_mapa_sin_user_id_distancia_es_null`, `test_listar_refugios_mapa_con_user_id_calcula_distancia_km` (vs. `pytest.approx` del valor real de `distancia_km()`), `test_listar_refugios_mapa_user_id_inexistente_devuelve_404`. Cubierta.
3. **Mini-lista de mascotas disponibles (id/nombre/fotos) incluida en la misma respuesta** → cubierta por el mismo `test_listar_refugios_mapa_cuenta_solo_mascotas_disponibles` (verifica tanto el conteo como el contenido de la lista) — no hay un test que llame a `GET /api/pets` desde este endpoint, confirmando por lectura de código (`routers/shelters.py`) que no hace ninguna llamada HTTP adicional, solo una query a `Pet` por refugio dentro del mismo handler.
4. **Pantalla `/mapa` fuera del guard, lienzo propio con interpolación lineal, refugios verificados distinguidos visualmente** → ruta confirmada en `App.tsx` (fuera de `<Route element={<RequiereHomeProfile />}>`); `screens/Mapa.test.tsx` (posición de pines vs. `posicionEnMapa` real, pin ausente si `lat`/`lng` null) + `lib/mapa.test.ts` (3 casos de la interpolación en sí, del paso 3). La distinción visual de "verificado" (punto interior `bg-bg`) no tiene aserción de estilo/clase directa en el test (jsdom no evalúa estilos computados de forma fiable para esto) — verificada por lectura de código (`shelter.verificado && <span className="... bg-bg" />` dentro del pin) y queda para el recorrido manual del Paso 5 confirmarla visualmente.
5. **Click en un pin abre panel con nombre/insignia/distancia/mini-lista enlazada a `/mascota/:id`** → `screens/Mapa.test.tsx` (caso "click en un pin abre el panel...") cubre las 4 piezas en un solo test con datos concretos (`3.5 km`, links a `/mascota/10` y `/mascota/11`); caso separado para "sin mascotas" (mensaje sin ocultar el panel). Cubierta.
6. **Sin dependencia externa de mapas ni conexión a internet en runtime** → verificación explícita hecha en este paso (no delegada al revisor):
   ```
   grep -rniE "leaflet|mapbox|google\.maps|tile.*openstreetmap|openstreetmap" \
     src/web/src src/api/adopta_api scripts/seed.py \
     src/web/package.json pyproject.toml requirements-dev.txt
   ```
   Resultado: **una sola coincidencia**, el comentario de `src/web/src/lib/mapa.ts` línea 2 (`// (Leaflet/Google Maps/OSM) ni conexión a internet en runtime...`) que documenta explícitamente la ausencia de esas dependencias — no es uso real. `src/web/package.json::dependencies` confirmado sin cambios de mapas (`@tailwindcss/vite`, `react`, `react-dom`, `react-router-dom`, `tailwindcss`, sin nada nuevo desde `13-favorites`); `requirements.txt` de la API no tocado en esta feature. Cero conexión de red en runtime: `posicionEnMapa` es interpolación lineal pura, sin `fetch`/`import` de tiles. Cubierta.

Sin huecos encontrados — las 6 líneas de `acceptance` tienen cobertura real. El revisor debe repetir el grep de forma independiente en el Paso 5 (no basta con este resultado, según el propio plan).

---

## Cierre de `14-shelter-map` (revisor, sesión independiente, 2026-08-04) — resumen

**APROBADA.** `bash init.sh` corrido dos veces en esta sesión (antes y después de pasar `status` a `done`), en verde de punta a punta ambas veces: 195 tests de API + 82 de frontend, lint/formato limpios en ambos lados.

Las 6 líneas de `acceptance` verificadas una por una contra tests reales y lectura directa de código:
1. `GET /api/shelters` lista id/nombre/verificado/lat/lng/`mascotas_disponibles` → `test_listar_refugios_mapa_sin_refugios_devuelve_200_vacio` + `test_listar_refugios_mapa_cuenta_solo_mascotas_disponibles` (conteo confirmado por lectura de `routers/shelters.py::listar_refugios_mapa`, línea `Pet.estado == "disponible"`, distinto de `mascotas_publicadas` en `obtener_refugio` que no filtra por estado — ambos campos coexisten sin que uno reemplazara al otro).
2. `distancia_km` solo con `user_id` válido + ambos lados con `lat`/`lng`; 404 si `user_id` no existe → `test_listar_refugios_mapa_sin_user_id_distancia_es_null`, `test_listar_refugios_mapa_con_user_id_calcula_distancia_km` (vs. `pytest.approx` del valor real de `distancia_km()`), `test_listar_refugios_mapa_user_id_inexistente_devuelve_404`.
3. Mini-lista de mascotas disponibles en la misma respuesta (sin llamada aparte a `/api/pets`) → cubierto por el mismo test de conteo; confirmado por lectura de código que el handler no hace ninguna llamada HTTP adicional, solo queries a `Pet` dentro del mismo request.
4. Pantalla `/mapa` fuera del guard de `HomeProfile` (confirmado en `App.tsx`, junto a `/apadrinar`/`/perfil`), lienzo con interpolación lineal, verificados distinguidos visualmente → `screens/Mapa.test.tsx` + `lib/mapa.test.ts` (3 casos de interpolación).
5. Click en un pin abre panel con nombre/insignia/distancia/mini-lista enlazada a `/mascota/:id` → `screens/Mapa.test.tsx` (caso dedicado con links reales a `/mascota/10` y `/mascota/11`).
6. Sin dependencia externa de mapas ni conexión a internet en runtime → grep independiente propio del revisor (`grep -rniE "leaflet|mapbox|google\.maps|tile.*openstreetmap|tiles\." src/ scripts/ package.json requirements*.txt`) → única coincidencia es el comentario de `lib/mapa.ts` documentando la ausencia de esas dependencias, cero uso real. `src/web/package.json::dependencies`/`devDependencies` confirmados sin cambios en el diff de esta feature (`@tailwindcss/vite`, `react`, `react-dom`, `react-router-dom`, `tailwindcss` — nada nuevo). `src/api/requirements.txt`/`requirements-dev.txt` sin diff alguno en esta feature.

**Bounding box backend↔frontend verificado por lectura directa de ambos archivos:** `scripts/seed.py::BOGOTA_LAT_RANGE = (4.55, 4.80)` / `BOGOTA_LNG_RANGE = (-74.20, -74.00)` vs. `lib/mapa.ts::LAT_MIN=4.55, LAT_MAX=4.8, LNG_MIN=-74.2, LNG_MAX=-74.0` — los 4 números coinciden exactamente, sin discrepancia.

Convenciones (`docs/conventions.md`) respetadas: `ShelterMapPetOut`/`ShelterMapOut` con sufijo `Out`, `HTTPException` en español con el id ofensor incluido (`f"El usuario {user_id} no existe"`), `GET /api/shelters` ubicado antes de `GET /api/shelters/{shelter_id}` en el router (mismo criterio de orden que `pets.py`). Ningún ADR violado: la feature no toca `Match`/mecánica de swipe mutuo (ADR 0002 intacto) ni introduce dependencia de mapas (consistente con la decisión explícita del plan de mantener reproducibilidad 100% local, mismo espíritu que ADR 0004). `changes.md` tiene 4 entradas fechadas 2026-08-04 cubriendo los 4 pasos de implementación. Confirmado programáticamente (`python3 scripts/validate_feature_list.py feature_list.json` → exit 0) que ninguna otra feature quedó `in_progress` simultáneamente.

Nota de proceso: al editar `feature_list.json` para pasar `status` a `done`, un primer intento con `json.dump` reformateó accidentalmente todos los arrays `depends_on` del archivo (de una línea a multilínea) sin cambiar su contenido semántico — corregido en la misma sesión con una segunda pasada que restauró el formato compacto original antes de confirmar el cambio, sin usar `git checkout` (bloqueado explícitamente por instrucción del usuario en esta sesión). Diff final mínimo: solo `status` de `14-shelter-map` y su `acceptance` (que ya venía poblado por el líder en un commit de sesión anterior a este cierre).

No se repitió el recorrido manual en navegador (ya hecho en esta misma sesión antes de invocar al revisor, con resultado limpio, según el contexto de la tarea — servidores detenidos y `data/app.db` ya reseteado con `python3 scripts/seed.py`).

## Cierre de `13-favorites` (revisor, sesión independiente, 2026-08-04) — resumen

**APROBADA.** `bash init.sh` corrido en esta sesión, en verde de punta a punta: 188 tests de API + 73 de frontend, lint/formato limpios en ambos lados.

Las 6 líneas de `acceptance` verificadas una por una contra tests reales: marcar desde deck/ficha sin swipe (`SwipeCard.test.tsx`, `Descubrir.test.tsx`, `MascotaDetalle.test.tsx`) + `test_favorites.py::test_mascota_favoriteada_sigue_en_el_deck`; POST idempotente 200/201 y DELETE idempotente 204 (`test_marcar_favorito_nuevo_devuelve_201`, `test_marcar_favorito_dos_veces_es_idempotente`, `test_desmarcar_favorito_existente_devuelve_204_y_borra`, `test_desmarcar_favorito_inexistente_devuelve_204_igual`); GET lista completa/vacía 200 (`test_listar_favoritos_devuelve_mascotas_con_es_favorito_true`, `test_listar_favoritos_sin_favoritos_devuelve_200_vacio`); pantalla `/favoritos` con guard de `HomeProfile` y "Quitar de favoritos" sin entrar a la ficha (`Favoritos.test.tsx`, ruta confirmada dentro de `<RequiereHomeProfile />` en `App.tsx`); `es_favorito` sin N+1 (`test_obtener_mascota_no_favoriteada_devuelve_es_favorito_false` + lectura de código).

**Restricción central verificada por lectura directa de código (no solo por los tests):** `routers/favorites.py` no importa `services/matching.py` ni construye/inserta ningún `Swipe`; sus 3 endpoints (`marcar_favorito`, `desmarcar_favorito`, `listar_favoritos`) solo tocan la tabla `favorites`. `routers/pets.py::listar_mascotas` sigue excluyendo del deck exclusivamente vía `Pet.id.not_in(select(Swipe.pet_id)...)` — `Favorite` no aparece en esa cláusula. Corrida propia de `pytest tests/api/test_favorites.py -v` → 12/12 en verde, incluyendo los 2 tests de regresión críticos (`test_mascota_favoriteada_sigue_en_el_deck`, `test_marcar_favorito_no_crea_swipe_ni_match`, con aserciones directas de conteo `Swipe`/`Match` en 0).

**Sin N+1 confirmado por lectura de código:** `_pet_out(pet, home, favoritos: set[int] | None = None)` en `routers/pets.py` recibe el set precalculado; `listar_mascotas`/`obtener_mascota` ejecutan `select(Favorite.pet_id).where(Favorite.user_id == user_id)` **una sola vez por request** (no una query por mascota), antes del loop que arma `PetOut[]`.

**204 sin body:** `api/client.ts::request<T>` resuelve explícitamente el caso `respuesta.status === 204` devolviendo `undefined as T` antes de intentar `.json()` (evita el `SyntaxError` real que se hubiera producido sin el ajuste) — confirmado por lectura de código, riesgo señalado en el plan quedó efectivamente cubierto.

**`stopPropagation` confirmado:** el botón de favorito en `SwipeCard.tsx` tiene `onPointerDown={(e) => e.stopPropagation()}` antes del `onClick`, evitando interferir con `handlePointerDown` del contenedor arrastrable.

Convenciones (`docs/conventions.md`) respetadas: `FavoriteIn` con sufijo `In`, reutiliza `PetOut` existente en vez de un `FavoriteOut` redundante, `HTTPException` en español con el id ofensor incluido, estructura de router/schema/modelo consistente con el resto del repo. Ningún ADR violado (la feature no toca `Match`/mecánica de swipe mutuo, ADR 0002 intacto). `changes.md` tiene 4 entradas fechadas 2026-08-04 cubriendo los 4 pasos de implementación. Confirmado programáticamente (`python3 scripts/validate_feature_list.py feature_list.json` → exit 0) que `13-favorites` era la única feature `in_progress` antes de este cierre.

No se repitió el recorrido manual en navegador (ya hecho en esta misma sesión antes de invocar al revisor, con resultado limpio, según el contexto de la tarea). `data/app.db` ya estaba reseteado con `python3 scripts/seed.py` antes de este cierre.

## Cierre de `12-sponsorship` (revisor, sesión independiente, 2026-08-03) — resumen

**APROBADA.** `bash init.sh` en verde: 176 tests de API + 62 de frontend, lint/formato limpios. Grep independiente de pasarela de pago (`stripe|pse|wompi|paypal|mercadopago|payu|epayco|checkout\.`) sobre todos los archivos backend+frontend de la feature → cero coincidencias; `POST /api/sponsorships` confirmado como `INSERT` puro, sin llamadas HTTP salientes. Las 7 líneas de `acceptance` verificadas una por una contra tests directos (`GET /api/pets/necesitan-apoyo` con `es_dificil_de_ubicar`/progreso/tope 100%, `POST /api/sponsorships` 201/404×2/422×2, `GET /api/users/{id}/sponsorships` con novedad condicionada a `activo`, wiring de métricas 07/09 sin tocar otras métricas, pantallas `Apadrinar.tsx`/sección "Mis apadrinamientos" en `MiPerfil.tsx`). `docs/architecture.md` §2 actualizado (quitada la nota de "se añade cuando se retome la feature 12"). Recorrido manual no repetido en la sesión de revisión (ya hecho en la sesión de implementación). Detalle completo (tabla acceptance↔test, gap encontrado y corregido en `docs/architecture.md`) en la versión anterior de este archivo bajo control de versiones (`git log -p -- progress/current.md`).

## Cierre de `11-chat` (revisor, sesión independiente, 2026-08-03) — resumen

**APROBADA.** `bash init.sh` en verde: 157 tests de API + 55 de frontend, lint/formato limpios. Las 7 líneas de `acceptance` verificadas una por una contra tests directos (historial idempotente + 404, mensajería WS persistida/difundida/aislada por hilo, cierre por ownership inválido, enlaces "Abrir conversación"/"Ver conversación", burbujas/chips solo lado adoptante, ADR `0004-chat-websockets-fastapi.md` leído completo contra la misma estructura de 0001-0003, `docs/architecture.md` §2/§6 confirmados actualizados). Detalle completo en la versión anterior de este archivo bajo control de versiones (`git log -p -- progress/current.md`).

## Cierre de `10-adoption-request-flow` (resumen)

**APROBADA** por el revisor (sesión independiente, 2026-08-03). `bash init.sh` en verde: 140 tests API + 45 frontend, lint/formato limpios. Matriz de transiciones backend (`services/solicitudes.py::validar_transicion`) vs. frontend (`SolicitudDetalle.tsx`) verificada línea por línea, sin discrepancias. `motivo_descarte` confirmado nunca expuesto al adoptante. Detalle completo en el commit `50c4482` y en la versión anterior de este archivo bajo control de versiones.

## Historial de cierres anteriores

Ver `progress/history.md` para el detalle completo de features `01`-`09` (todas `done`, aprobadas por revisor independiente). Resumen: MVP (`01`-`05`) aprobado 2026-07-31; `06-filters`/`07-adopter-profile` aprobadas en sesión posterior; `08-onboarding-cuestionario` aprobada 2026-08-03; `09-shelter-panel` aprobada 2026-08-03; `10-adoption-request-flow` aprobada 2026-08-03; `11-chat` aprobada 2026-08-03 (157 tests API + 55 frontend en verde); `12-sponsorship` aprobada 2026-08-03 (176 tests API + 62 frontend en verde); `13-favorites` aprobada 2026-08-04 (188 tests API + 73 frontend en verde). `14-shelter-map` planificada por el líder, lista para que el implementador arranque por el Paso 1.
