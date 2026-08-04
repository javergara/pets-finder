# Estado actual

**Fase activa:** backlog — `feature_list.json`
**Feature actual:** ninguna en `in_progress`. `13-favorites` → **`done`** (aprobada por el revisor, sesión independiente, 2026-08-04). Ver cierre resumido más abajo.

## Contexto

`06`-`12` están `done` (ver cierres resumidos más abajo). `13-favorites` es la siguiente feature del backlog: "Guardar mascotas sin hacer swipe definitivo, para revisar después." `depends_on: ["03-pet-profile"]` (done), hoja del grafo.

Existe un documento de diseño **ya aprobado por el usuario** con todas las decisiones de esta feature tomadas: `/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md`. Este plan es una transcripción operativa de ese documento — **ninguna decisión de UX/arquitectura se reabre aquí**.

**A diferencia de casi todas las features anteriores, `13-favorites` NO tiene diseño previo en `design/`**: confirmado por el líder en esta sesión que ningún archivo bajo `design/` menciona "favorit" (grep case-insensitive, cero resultados) — las 11 pantallas del HANDOFF original no la contemplaban. Es una adición pura del backlog de `feature_list.json`, con más libertad de UX pero atada a los tokens ya establecidos (`design/design-system.md`) y a los patrones de componentes/API ya usados en el resto del repo.

## Verificación del líder antes de planificar (2026-08-04, releído el código real, no solo el documento de diseño)

- `grep -rli "favorit" design/` → **cero resultados** (confirmado, no solo heredado del documento de diseño).
- `src/api/adopta_api/models/`: confirmado, **no existe** `favorite.py`. Archivos actuales: `base.py`, `chat.py`, `home_profile.py`, `match.py`, `pet.py`, `shelter.py`, `sponsorship.py`, `swipe.py`, `user.py`.
- `routers/pets.py::listar_mascotas` (líneas 48-50) confirmado línea por línea: excluye del deck únicamente vía `Pet.id.not_in(select(Swipe.pet_id).where(Swipe.user_id == user_id))` — no toca ningún concepto de `Favorite` (que no existe aún). Esto es exactamente la restricción central de la feature: favoritos debe ser una tabla/acción totalmente separada de `Swipe`.
- `routers/pets.py::_pet_out(pet: Pet, home: HomeProfile | None) -> PetOut` (línea 19) confirmada con esa firma exacta — el punto de extensión para agregar `es_favorito` sin N+1 es cambiar esta firma para aceptar un set precalculado, mismo criterio que ya usa `home` para `afinidad`. `obtener_mascota` (línea 108) y `listar_mascotas` (línea 33) son los dos call sites con `user_id` disponible; `publicar_mascota` (línea 88) llama `_pet_out(pet, home=None)` sin `user_id` — debe quedar con el default `False` sin romper.
- `SwipeCard.tsx`: confirmado que solo tiene el badge de afinidad como overlay sobre la foto (`{pet.afinidad && (...)}`, línea 81-83), sin overlay `top-right` todavía. `Descubrir.tsx`: confirmados los 3 botones circulares (`✕` línea 87, `i` línea 95, `♥` línea 103) — el glifo `♥` ya usado ahí es para "Me interesa" (like/swipe), **no** para favoritos; no hay colisión visual porque el nuevo botón de favorito vive en `SwipeCard.tsx` (overlay sobre la carta), no como cuarto botón circular en el footer.
- `src/web/src/api/client.ts::request<T>` (línea 23) confirmado: en el camino feliz siempre hace `respuesta.json()` (línea 32) sin chequear `status`. El nuevo `DELETE /api/users/{user_id}/favorites/{pet_id}` devuelve 204 sin body — `request` necesita ajuste explícito para ese caso (`status === 204 ? undefined : respuesta.json()`), con un test que lo cubra, no asumir que "simplemente funciona" (gotcha real, no hipotético, confirmado leyendo el código).
- Confirmado programáticamente que ningún otro item de `feature_list.json` quedó `in_progress` antes de poner `13-favorites` en ese estado (`python3 scripts/validate_feature_list.py feature_list.json` → exit 0 antes y después del cambio).

## Restricción central de esta feature (repetir en cada paso, verificar explícitamente en el cierre)

**Favoritos es una tabla y una acción completamente independientes de `Swipe`.** Marcar/desmarcar favorito nunca debe:
- insertar una fila en `swipes`,
- pasar por `services/matching.py::registrar_swipe`,
- crear un `Match`,
- ni excluir la mascota de `GET /api/pets?user_id=` (el deck).

"Sin hacer swipe definitivo, para revisar después" es literalmente el requisito de producto, no una frase decorativa. El Paso 2 debe incluir tests de regresión explícitos que lo prueben con aserciones directas (conteos de `Swipe`/`Match` en 0, mascota favoriteada siguiendo presente en el deck) — plantilla exacta: `tests/api/test_endpoints.py::test_mascota_excluida_tras_swipe`, con la aserción invertida.

## Decisiones ya tomadas en el documento de diseño (NO reabrir)

Documento de diseño aprobado por el usuario (base de este plan): `/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md`

**Backend**
- `models/favorite.py` (nuevo, vía skill `db-migrations`): `Favorite` — `id`, `user_id` (FK `users.id`), `pet_id` (FK `pets.id`), `creado_en: datetime` (default `now(timezone.utc)`). Sin campo de dirección/estado — la existencia de la fila es la señal (mismo criterio que `HomeProfile`/`Thread`). Docstring debe explicitar la independencia de `Swipe`. **Sin `UniqueConstraint` de esquema** — la idempotencia se garantiza en el router con un `select` previo (mismo criterio que `guardar_home_profile` en `08-onboarding-cuestionario` hace upsert manual). Registrar en `models/__init__.py`.
- `schemas/favorite.py` (nuevo): `FavoriteIn { pet_id: int }` — body del `POST`. No hace falta `FavoriteOut` propio: `POST`/`GET` devuelven `PetOut` (ya existente), reutilizable.
- `schemas/pet.py::PetOut` — agregar `es_favorito: bool = False`, mismo nivel que `afinidad`.
- `routers/pets.py::_pet_out` — cambiar firma a `_pet_out(pet, home, favoritos: set[int] | None = None)`. En `listar_mascotas`/`obtener_mascota`, cuando `user_id is not None`, precalcular UNA sola vez `favoritos = set(session.execute(select(Favorite.pet_id).where(Favorite.user_id == user_id)).scalars())` y pasarlo a cada llamada de `_pet_out` (sin N+1). `es_favorito` se calcula independientemente de `home` (a diferencia de `afinidad`) — favoritos y afinidad son conceptualmente independientes. Call sites con `home=None` sin pasar `favoritos` (ej. `publicar_mascota`) quedan con el default `False`, comportamiento correcto.
- `routers/favorites.py` (nuevo, mismo criterio de nesting que `routers/sponsorships.py`: `APIRouter(prefix="/api")`, rutas completas):
  - `POST /api/users/{user_id}/favorites` (body `FavoriteIn`) → `PetOut`. Idempotente: si ya existe, 200 sin duplicar; si es nuevo, 201 (`response.status_code` dinámico, no fijo en el decorador). 404 español si `user_id`/`pet_id` no existen.
  - `DELETE /api/users/{user_id}/favorites/{pet_id}` → 204. Idempotente (204 exista o no la fila — nunca 404 por "ya no estaba").
  - `GET /api/users/{user_id}/favorites` → `list[PetOut]`. 404 si el usuario no existe; lista vacía (200, no 404) si no tiene favoritos. **No exige `HomeProfile`** (a diferencia de `listar_mascotas`/`obtener_mascota`) — favoritos no depende de `home` por decisión de producto; el guard de `HomeProfile` en la ruta `/favoritos` del frontend es una decisión de UX, no de API.
  - Registrar en `main.py` (el orden no es crítico, no colisiona con `/api/pets/{pet_id}` como sí pasó con `sponsorships`).

**Frontend**
- `api/types.ts`: agregar `es_favorito: boolean` a `interface Pet`.
- `api/client.ts`: `marcarFavorito(userId, petId)`, `desmarcarFavorito(userId, petId)`, `listarFavoritos(userId)`. Ajustar `request<T>` para el caso 204 sin body (`status === 204 ? undefined : respuesta.json()`), con test explícito.
- `SwipeCard.tsx` — botón de favorito como overlay `top-right` sobre la foto (simétrico al badge de afinidad en `top-left`). **Imprescindible**: `onPointerDown` con `e.stopPropagation()` (la carta entera captura `pointerdown` para el gesto de arrastre; sin `stopPropagation`, tocar el corazón dispara también el drag). Glifo `♥`/`♡` según `pet.es_favorito`, `aria-label` dinámico. Componente controlado: nueva prop `onToggleFavorito: () => void`, mismo criterio que `onSwipe`/`onOpenDetail` (la lógica HTTP vive en `Descubrir.tsx`, no en el componente de presentación).
- `Descubrir.tsx` — `handleToggleFavorito()`: llama `marcarFavorito`/`desmarcarFavorito` según el estado actual, actualiza optimistamente el `Pet` en el array `mascotas` (mismo espíritu que `handleSwipe`). **A diferencia de swipe, NO quita la carta del array** — solo actualiza su campo `es_favorito`. Pasa `onToggleFavorito` a `<SwipeCard>`.
- `MascotaDetalle.tsx` — botón de favorito junto al badge de afinidad en el header (no en la barra fija inferior, que ya tiene ✕/"Me interesa adoptar" y no debe ganar un tercer botón). Toggle optimista sobre el `pet` ya cargado.
- `screens/Favoritos.tsx` (nuevo) — patrón de grid de `MisMatches.tsx` (skeleton, estado vacío con copy + link a `/descubrir`). `listarFavoritos(getActiveUserId())` en `useEffect`. Cada tarjeta: foto, nombre, badge de afinidad si viene, link a `/mascota/:id`, y botón **"Quitar de favoritos" visible directamente en la tarjeta** (sin entrar a la ficha — requisito explícito) que llama `desmarcarFavorito` y remueve la tarjeta del array local, sin modal de confirmación (acción reversible de un tap).
- `App.tsx`: ruta `/favoritos` **dentro** de `RequiereHomeProfile` (junto a `/descubrir`, `/mascota/:id`, `/matches`) + `NavLink` "Favoritos" (entre "Descubrir" y "Mis matches").

**Sin librería de iconos** — patrón existente de glifo de texto en botones. Favorito sigue el mismo criterio: `♥` (relleno, `forest`) activo / `♡` (contorno, `muted`) inactivo — no SVG nuevo, ningún color ajeno a la paleta.

## Tests requeridos (documento de diseño §3)

**Backend** (`tests/api/test_favorites.py`, patrón de `test_sponsorships.py`): marcar nuevo (201) / idempotente (200, sin duplicar fila) / usuario inexistente (404) / mascota inexistente (404); desmarcar existente (204, borra) / desmarcar inexistente (204 igual, idempotente); listar con mascotas completas / usuario inexistente (404) / vacío (200, no 404). **Tests de regresión críticos** (plantilla exacta en `tests/api/test_endpoints.py::test_mascota_excluida_tras_swipe`, aserción invertida): favoritear una mascota y verificar que SIGUE apareciendo en `GET /api/pets?user_id=`; verificar que favoritear no crea ningún `Swipe` ni `Match` (conteos en 0).

**Frontend**: `SwipeCard.test.tsx` actualizado (fixture `es_favorito: false`, nuevo caso de que el botón de favorito no dispara el gesto de arrastre); `Favoritos.test.tsx` (loading, vacío, listado, quitar); caso de toggle en `MascotaDetalle` (test existente o nuevo, según lo que ya haya).

## `acceptance` de `13-favorites` (6 líneas, ya escritas en `feature_list.json` en esta sesión)

1. Un usuario puede marcar una mascota como favorita desde el deck (Descubrir) o desde su ficha (MascotaDetalle), sin que eso cuente como un swipe: la mascota sigue apareciendo en el deck.
2. `POST /api/users/{user_id}/favorites` es idempotente (200 si ya existía, 201 si es nuevo) y `DELETE /api/users/{user_id}/favorites/{pet_id}` también (204 exista o no la fila).
3. `GET /api/users/{user_id}/favorites` devuelve la lista completa de mascotas favoritas del usuario (`PetOut[]`), vacía si no tiene ninguna (200, no 404).
4. Favoritear una mascota nunca crea un `Swipe` ni un `Match`, y nunca la excluye de `GET /api/pets?user_id=` (verificado con test de regresión explícito).
5. Existe una pantalla `/favoritos` (dentro del guard de `HomeProfile`) donde el usuario revisa sus favoritos y puede quitarlos directamente desde la lista, sin entrar a la ficha.
6. `PetOut` expone `es_favorito` (bool, default `false`) calculado sin N+1 cuando se pasa `user_id`, igual que ya ocurre con `afinidad`.

## Secuenciación de pasos verificables (documento de diseño §5)

**Paso 0 — Líder (COMPLETADO en esta sesión):** `13-favorites` → `in_progress`, `acceptance` (6 líneas) escrito en `feature_list.json`, este plan escrito en `progress/current.md`.

**Paso 1 — Backend: modelo + schemas (COMPLETADO 2026-08-04, implementador)**
- `models/favorite.py` (nuevo): clase `Favorite` (`id`, `user_id`/`pet_id` FK, `creado_en`), docstring explícito de independencia de `Swipe`. Registrado en `models/__init__.py`.
- `schemas/favorite.py` (nuevo): `FavoriteIn { pet_id: int }`.
- `schemas/pet.py::PetOut`: agregado `es_favorito: bool = False`.
- `data/app.db` recreado con `python3 scripts/seed.py` (sin filas de ejemplo en `favorites`).
- Verificado: import de `Favorite` sin error; `pytest tests/api -q` → 176/176 sin regresión; `ruff check`/`black --check` limpios; `bash init.sh` completo en verde (176 API + 62 frontend). Detalle en `changes.md` (2026-08-04). No se tocó `routers/` ni frontend, según lo planeado.

**Paso 2 — Backend: router + wiring de `_pet_out`/`listar_mascotas`/`obtener_mascota` + tests (COMPLETADO 2026-08-04, implementador)**
- `routers/favorites.py` (nuevo): los 3 endpoints tal cual el diseño (`POST`/`DELETE`/`GET`). Registrado en `main.py` (sin colisión de prefijo).
- `routers/pets.py::_pet_out` cambió de firma a `(pet, home, favoritos: set[int] | None = None)`; `listar_mascotas`/`obtener_mascota` precalculan el set de favoritos una sola vez cuando `user_id is not None` y lo pasan a cada llamada (sin N+1, confirmado por lectura de código).
- `tests/api/test_favorites.py` (nuevo, 12 tests): todos los casos de la sección "Tests requeridos" arriba, **incluyendo los 2 tests de regresión críticos** (`test_mascota_favoriteada_sigue_en_el_deck`, `test_marcar_favorito_no_crea_swipe_ni_match`).
- Verificado: `pytest tests/api -q` → 188/188 en verde (176 previos + 12 nuevos, sin regresión); `ruff check`/`black --check` limpios; `bash init.sh` completo en verde (188 API + 62 frontend). Detalle en `changes.md` (2026-08-04). No se tocó frontend en este paso.

**Paso 3 — Frontend: tipos/cliente + botón en el deck (COMPLETADO 2026-08-04, implementador)**
- `api/types.ts::Pet` gana `es_favorito: boolean`.
- `api/client.ts::request<T>` resuelve el caso `204` (`respuesta.status === 204` → `undefined as T`, antes de llamar `.json()`) — necesario para `DELETE .../favorites/{pet_id}`. Nuevas `marcarFavorito`/`desmarcarFavorito`/`listarFavoritos`. Sin `client.test.ts` propio en el repo (no existía antes); el caso 204 queda cubierto indirectamente vía `Descubrir.test.tsx` a través del componente, mismo patrón que el resto de `client.ts`.
- `SwipeCard.tsx`: botón de favorito (`♥`/`♡`, `aria-label` dinámico) dentro de la fila flex del badge de afinidad, empujado a la derecha con `ml-auto` (en vez de overlay absoluto separado, para que quede en el borde derecho con o sin badge de afinidad presente). `onPointerDown={(e) => e.stopPropagation()}` antes de que el contenedor arranque el drag. Prop controlada `onToggleFavorito: () => void`.
- `Descubrir.tsx`: `handleToggleFavorito(petId)` — actualiza optimistamente solo ese elemento de `mascotas` (`.map`, no lo quita del array), error de red atrapado en silencio (mismo criterio que `handleSwipe`). Prop pasada a `<SwipeCard>`.
- Tests nuevos: `SwipeCard.test.tsx` (fixture `es_favorito: false` + 3 casos: corazón vacío/lleno con aria-label correcto, click en el botón dispara `onToggleFavorito` sin disparar `onSwipe`); `Descubrir.test.tsx` (mock extendido con `marcarFavorito`/`desmarcarFavorito`, fixture con `es_favorito: false`, caso de que favoritear no remueve la carta actual del DOM).
- Verificado: `npx vitest run` → **66/66 en verde** (62 previos + 4 nuevos); `npx tsc -b` sin errores; `npm run lint` (oxlint) y `npx prettier --check src/web` limpios; `bash init.sh` completo en verde (**188 API + 66 frontend**). Detalle completo en `changes.md` (2026-08-04). No se tocó `MascotaDetalle.tsx` ni se creó `Favoritos.tsx` (paso 4), no se marcó la feature como `done`.

**Paso 4 — Frontend: ficha de mascota + pantalla `/favoritos` (COMPLETADO 2026-08-04, implementador)**
- `MascotaDetalle.tsx`: botón de favorito (`♥`/`♡`, `aria-label` dinámico) agregado en una fila junto al badge de afinidad en el header (no en la barra fija inferior, que se dejó intacta con sus 2 botones ✕/"Me interesa adoptar"). `toggleFavorito()` actualiza `pet` optimistamente vía `setPet({ ...pet, es_favorito: !pet.es_favorito })` y llama `marcarFavorito`/`desmarcarFavorito` según corresponda.
- `screens/Favoritos.tsx` (nuevo): mismo patrón estructural que `MisMatches.tsx` — skeleton `animate-pulse` (3 placeholders) mientras `favoritos === null`, estado vacío ("Aún no tienes favoritos" + link a `/descubrir`), grid de tarjetas con foto/nombre/badge de afinidad (condicionado a `pet.afinidad !== null`, porque `GET /api/users/{id}/favorites` no calcula afinidad) y link a `/mascota/:id`. Botón "Quitar de favoritos" visible directamente en la tarjeta, con `e.preventDefault()`/`e.stopPropagation()` en su `onClick` (está anidado dentro del `<Link>`) para no disparar la navegación; llama `desmarcarFavorito(getActiveUserId(), pet.id)` y filtra esa mascota del array local `favoritos`, sin modal de confirmación.
- `App.tsx`: import de `Favoritos`, ruta `<Route path="/favoritos" element={<Favoritos />} />` dentro de `<Route element={<RequiereHomeProfile />}>` (junto a `/descubrir`, `/mascota/:id`, `/matches`), `NavLink` "Favoritos" en `Nav()` entre "Descubrir" y "Mis matches".
- Tests nuevos: `src/web/src/screens/Favoritos.test.tsx` (5 casos: skeleton, vacío con link a `/descubrir`, listado con foto/nombre/afinidad, afinidad `null` sin romper el render, "Quitar de favoritos" llama a `desmarcarFavorito(1, 17)` y remueve la tarjeta del DOM); `src/web/src/screens/MascotaDetalle.test.tsx` (nuevo — no existía antes de este paso; 2 casos de toggle en ambas direcciones, verificando `marcarFavorito`/`desmarcarFavorito` llamados con `(1, 17)` y que el `aria-label`/glifo cambian tras la respuesta).
- Verificado: `npx vitest run` → **73/73 en verde** (66 previos + 7 nuevos: 5 de `Favoritos.test.tsx` + 2 de `MascotaDetalle.test.tsx`); `npx tsc -b` sin errores; `npm run lint` (oxlint) y `npx prettier --check .` limpios; `pytest tests/api -q` → 188/188 sin regresión (no se tocó backend en este paso); `bash init.sh` completo en verde de punta a punta: **188 tests de API + 73 de frontend**, lint/formato limpios en ambos lados.
- **Verificación explícita de la restricción central** (hecha por el implementador en este paso, no delegada al revisor): lectura línea por línea de `src/api/adopta_api/routers/favorites.py` — ningún `import` de `services/matching.py`, ningún `Swipe(...)` construido ni insertado; las únicas menciones a "matching"/"swipes" en ese archivo y en `models/favorite.py` son de docstring explicando la independencia (`grep -n "matching\|Swipe(" routers/favorites.py models/favorite.py` → 2 coincidencias, ambas en comentarios). `pytest tests/api/test_favorites.py -v` → 12/12 en verde, incluyendo los 2 tests de regresión críticos del Paso 2: `test_mascota_favoriteada_sigue_en_el_deck` y `test_marcar_favorito_no_crea_swipe_ni_match`.

## Cobertura de tests vs. `acceptance` de `13-favorites` (verificada por el implementador tras el Paso 4)

Las 6 líneas de `acceptance` de `feature_list.json`, repasadas una por una contra un test real:

1. **"Un usuario puede marcar una mascota como favorita desde el deck (Descubrir) o desde su ficha (MascotaDetalle), sin que eso cuente como un swipe: la mascota sigue apareciendo en el deck."** → Deck: `src/web/src/screens/Descubrir.test.tsx` (caso de favoritear sin remover la carta, Paso 3) + `src/web/src/components/SwipeCard.test.tsx` (botón no dispara `onSwipe`, Paso 3). Ficha: `src/web/src/screens/MascotaDetalle.test.tsx` (nuevo, 2 casos de toggle, Paso 4). "Sigue en el deck": `tests/api/test_favorites.py::test_mascota_favoriteada_sigue_en_el_deck` (Paso 2).
2. **"`POST .../favorites` es idempotente (200/201) y `DELETE .../favorites/{pet_id}` también (204 exista o no la fila)."** → `test_marcar_favorito_nuevo_devuelve_201`, `test_marcar_favorito_dos_veces_es_idempotente`, `test_desmarcar_favorito_existente_devuelve_204_y_borra`, `test_desmarcar_favorito_inexistente_devuelve_204_igual` (los 4 en `tests/api/test_favorites.py`, Paso 2).
3. **"`GET .../favorites` devuelve la lista completa de mascotas favoritas del usuario (`PetOut[]`), vacía si no tiene ninguna (200, no 404)."** → `test_listar_favoritos_devuelve_mascotas_con_es_favorito_true`, `test_listar_favoritos_sin_favoritos_devuelve_200_vacio`, `test_listar_favoritos_usuario_inexistente_devuelve_404` (Paso 2). En frontend, `Favoritos.test.tsx` cubre el consumo de esa lista (skeleton/vacío/listado, Paso 4).
4. **"Favoritear una mascota nunca crea un `Swipe` ni un `Match`, y nunca la excluye de `GET /api/pets?user_id=`."** → `test_marcar_favorito_no_crea_swipe_ni_match` + `test_mascota_favoriteada_sigue_en_el_deck` (`tests/api/test_favorites.py`, Paso 2). **Verificado también por lectura de código en el Paso 4** (no solo confiando en el test): `routers/favorites.py` no importa `services/matching.py` ni construye/inserta `Swipe(...)` en ninguno de sus 3 endpoints; `_pet_out`/`listar_mascotas` siguen excluyendo del deck exclusivamente por `Swipe.pet_id` (`routers/pets.py`, sin tocar en este paso), `Favorite` no aparece en esa cláusula de exclusión.
5. **"Existe una pantalla `/favoritos` (dentro del guard de `HomeProfile`) donde el usuario revisa sus favoritos y puede quitarlos directamente desde la lista, sin entrar a la ficha."** → `src/web/src/screens/Favoritos.test.tsx` (nuevo, Paso 4): listado con foto/nombre/afinidad y el caso "Quitar de favoritos" llama `desmarcarFavorito` y remueve la tarjeta sin navegar. Guard confirmado por lectura de `App.tsx`: la ruta `/favoritos` está dentro de `<Route element={<RequiereHomeProfile />}>`.
6. **"`PetOut` expone `es_favorito` (bool, default `false`) calculado sin N+1 cuando se pasa `user_id`, igual que ya ocurre con `afinidad`."** → `test_obtener_mascota_no_favoriteada_devuelve_es_favorito_false` + `test_listar_favoritos_devuelve_mascotas_con_es_favorito_true` (Paso 2). Sin N+1: verificado por lectura de código en el Paso 2 (`favoritos = set(...)` precalculado una sola vez en `listar_mascotas`/`obtener_mascota`, pasado a cada `_pet_out`), no reverificado por lectura en el Paso 4 porque `routers/pets.py` no se tocó en este paso.

Sin huecos encontrados: las 6 líneas tienen al menos un test directo, y la línea 4 (la restricción central de la feature) fue reverificada por lectura de código en este paso, no solo citada. No fue necesario implementar nada adicional para cerrar cobertura.

**Paso 5 — Cierre del revisor (agente independiente, NO el líder ni el implementador)**
- `bash init.sh` completo en verde (backend + frontend), corrido en esa sesión (no heredado).
- Confirmar explícitamente, **no solo vía test automatizado**, que favoritear una mascota NO crea `Swipe`/`Match` ni la excluye del deck — leer `routers/favorites.py` línea por línea y correr manualmente el recorrido de abajo.
- Confirmar que `_pet_out`/`listar_mascotas`/`obtener_mascota` calculan `es_favorito` sin N+1 (lectura de código, no solo tests pasando).
- Recorrido manual en navegador real (`bash dev.sh`): en `/descubrir`, favoritear una mascota con el corazón (sin que se dispare el gesto de swipe ni desaparezca la carta); abrir su ficha y confirmar que el corazón aparece activo; ir a `/favoritos` y confirmar que aparece ahí; quitarla desde la lista y confirmar que desaparece; volver a `/descubrir` y confirmar que la mascota sigue en el deck (nunca fue swipeada).
- Confirmar programáticamente que ningún otro item de `feature_list.json` quedó `in_progress`.
- Resetear `data/app.db` con `python3 scripts/seed.py` después de la verificación manual.
- Solo entonces `status` → `done` en `feature_list.json`, con el mismo detalle de verificación que features anteriores documentado en `progress/current.md` (tabla acceptance↔test completa).

## Verificación end-to-end esperada

- `bash init.sh` en verde tras cada paso (backend y frontend por separado durante implementación; completo al cierre).
- Recorrido manual en navegador real, detallado en el Paso 5.
- Resetear `data/app.db` con `python3 scripts/seed.py` después de cualquier verificación manual que haya mutado datos.

---

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

Ver `progress/history.md` para el detalle completo de features `01`-`09` (todas `done`, aprobadas por revisor independiente). Resumen: MVP (`01`-`05`) aprobado 2026-07-31; `06-filters`/`07-adopter-profile` aprobadas en sesión posterior; `08-onboarding-cuestionario` aprobada 2026-08-03; `09-shelter-panel` aprobada 2026-08-03; `10-adoption-request-flow` aprobada 2026-08-03; `11-chat` aprobada 2026-08-03 (157 tests API + 55 frontend en verde); `12-sponsorship` aprobada 2026-08-03 (176 tests API + 62 frontend en verde). `13-favorites` planificada por el líder, lista para que el implementador arranque por el Paso 1.
