# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Added
- **`24-ai-matching-fotos`** (ADR 0012): las coincidencias suman **parecido visual** de las fotos sobre la heurística explicable de siempre. Modelos abiertos (Apache 2.0) que corren en el worker `embeddings/` fuera de la API — costo $0 y las fotos no salen a ningún tercero. Chip "foto muy parecida"/"foto parecida" junto a las razones de la 37, nunca un porcentaje. El parecido solo suma y nunca resta, así que sin vectores el orden es idéntico al anterior.
  - Motivo medido: 234 de los 260 reportes de producción comparten el mismo pin (el crawler los ubica en el centro de la zona), y el **89% de los pares candidatos empataba** bajo la heurística de distancia. La foto es la única señal que quedaba.
  - Pendiente antes de desplegar: migración aditiva (`embedding`, `embedding_modelo`) y backfill del worker.

### Fixed
- `init.sh` corría `pytest tests/api`, así que los tests de `tests/crawler` (y los nuevos de `tests/embeddings`) nunca se ejecutaban ahí. Ahora corre `pytest` a secas, respetando `testpaths`.
- La recencia de las tarjetas del listado se aseveraba con una redacción que dependía del reloj de pared ("hace X" → "ayer"), y rompía la suite al día siguiente.
- `dev.sh` asumía `.venv/bin/activate` (Linux) y no arrancaba en Windows; ahora detecta el intérprete y respeta `DATABASE_URL` si viene del entorno.

Backlog restante (requiere decisiones del dueño): `22-alertas-por-zona` (ADR de mecanismo; la 39 ya cubre las alertas por reporte), `23-moderacion-reportes` (alcance) y el checklist operativo `25-ops-produccion-pendientes` (+ crear la cuenta de Resend y sus env vars para que los correos de la 39 salgan de verdad).

## [3.0.0] - 2026-08-17 — **desplegado en producción**

Fase 2 del producto: **el módulo de adopción** (`/adoptar`), que cierra el arco de la emergencia con la mascota que nadie reclama. Cubre las ocho features `AD-01`…`AD-08` de `feature_list_adopcion.json`.

✅ **En producción desde el 2026-08-17** (<https://petfinder-col.com>), por el PR #7. Las cuatro migraciones que faltaban se ejecutaron **antes** del merge, en su orden obligatorio —`AD-03-swipes.sql` → `AD-03-home-profiles.sql` → `AD-05-matches.sql` → `AD-07-favorites.sql`—, verificadas contra `pg_class`/`pg_constraint`: RLS en las cinco tablas del módulo y las cuatro constraints con su nombre exacto. Ese orden no era una formalidad: con `SKIP_DB_CREATE_ALL=1` no hay red de seguridad, y si el código hubiera llegado antes que las tablas **caía la API entera**, no solo las pantallas nuevas.

Verificado tras el deploy con GET de solo lectura: `/api/pets/deck` (que consulta `swipes` y `home_profiles`), `/api/users/{id}/favorites`, `/api/solicitudes` en sus tres formas y `/api/users/{id}/home-profile` responden **200 o su 4xx de dominio, cero 500**, y el dominio de emergencia (`/api/reports`, `/api/organizaciones`) sigue intacto.

Es un **mayor** y no un menor porque abre una segunda fase de producto encima de la app de emergencia (cinco tablas, nueve rutas `/adoptar`, la nav crece a ocho enlaces) y porque desplegarlo exigió una acción manual en la base de datos antes del merge. La emergencia no cede el primer plano: la adopción entra detrás de los dos CTAs de siempre, y hay tests que lo fijan.

Suite al desplegar: **753 tests de Python + 493 de web**, `bash init.sh` en verde (al cerrar `AD-08` eran 738 + 487; los 15 de Python llegaron con el arreglo del 500 al despublicar y los 6 de web con la feature 48). Al abrir `AD-01` eran 174 + 148 (ese tramo incluye también trabajo ajeno al módulo: feature 47 y los PRs 4 y 5).

### Added
- **`AD-01-modelo-pet-y-catalogo`** *(ya en producción desde 2.5.0)*: modelo `Pet` con **publicador exclusivo** (`ck_pets_publicador_exclusivo`: organización XOR rescatista, nunca ambos ni ninguno), catálogo público `/adoptar` con filtros multivalor (especie, tamaño, energía) y zona, ficha `/adoptar/mascota/:id` con galería, historia, convivencia y checklist de salud, y resumen `GET /api/pets/adopciones`. Mirar nunca pide cuenta.
- **`AD-02-publicar-en-adopcion`** *(ya en producción desde 2.5.0)*: publicar por **tres caminos** — rescatista (`/adoptar/publicar`), organización (`?organizacion=` + pestaña `?tab=adopcion` en su ficha) y **el puente** desde un reporte de "encontrada" que sigue contigo, que precarga el formulario y **hereda las fotos del reporte sin volver a subirlas**. Editar y despublicar (`PUT`/`DELETE /api/pets/{id}`, solo autor), y 409 al eliminar un reporte que ya tiene mascota publicada.
- **`AD-03-deck-swipe-y-afinidad`**: deck `/adoptar/descubrir` — una mascota a la vez, con arrastre, teclado y botones; `POST /api/swipes` idempotente (`uq_swipe_user_pet`) y `GET /api/pets/deck` con orden determinista e inserción de las difíciles de ubicar. **Afinidad explicable calculada al vuelo** (ADR 0003), siempre con sus razones en texto ("Encaja con tus 6 horas fuera al día"), nunca un porcentaje suelto. Tablas `swipes` y `home_profiles`.
- **`AD-04-perfil-de-hogar`**: cuestionario de 6 pasos en `/adoptar/mi-hogar` con `PUT`/`GET /api/users/{id}/home-profile` (upsert que responde 200 siempre; el 403 va **antes** del 404 para no delatar quién contestó su cuestionario). **No bloquea el deck**: sin perfil se ve todo, sin porcentaje y con una invitación no bloqueante — un muro contradiría la cuenta liviana del ADR 0005.
- **`AD-05-solicitudes-de-adopcion`**: el swipe-derecha crea la solicitud (`uq_match_user_pet`, **match no mutuo**, ADR 0002). `GET /api/solicitudes` responde tres preguntas con una sola forma ("las que envié", "las de mi fundación", "las que recibí") y quien publica agenda visita, pide información, descarta con motivo privado o **aprueba** — aprobar cierra la mascota y las demás solicitudes en una sola query. Pantallas `/adoptar/mis-solicitudes` y `/adoptar/solicitud/:id`. Tabla `matches`.
- **`AD-06-comunicacion-solicitud`** (ADR 0013): la conversación se lleva **por WhatsApp**, con mensaje precargado distinto por estado y por lado (quien pide / quien publica). Cero infraestructura nueva: sin WebSockets, sin tabla de mensajes, sin endpoints. Candado de no-regresión: un test recorre `src/api/reencuentro_api/**/*.py` y falla si reaparece `WebSocket`, `websockets` o `ConnectionManager`.
- **`AD-07-favoritos`**: "guardar para después" con corazón en la tarjeta, el deck y la ficha, más la lista `/adoptar/mis-favoritas`. `POST`/`GET`/`DELETE /api/users/{id}/favorites` con `uq_favorite_user_pet`; **guardar no crea swipe ni solicitud y no saca la carta del deck**. `es_favorito` se llena en catálogo, ficha y deck con **una sola consulta constante**, y el tráfico anónimo no paga nada. Tabla `favorites`.
- **`AD-08-integracion-transversal`**: `/adoptar` entra en la nav (octavo enlace, **detrás** de la emergencia) y en la landing como enlace terciario sin borde; **vista previa al compartir una ficha** en WhatsApp (`GET /adoptar/mascota/{id}` sirviendo og tags a bots + rewrite por user-agent, gemelo del de reportes); cruce desde la Comunidad de `/ayudar`; filtros plegados en móvil, medidos en Chrome real a 360×740 y 360×640.
- **Esquema — cinco tablas nuevas**: `pets` (AD-01, **ya migrada** el 2026-08-15), `swipes` y `home_profiles` (AD-03), `matches` (AD-05) y `favorites` (AD-07). Las cuatro últimas se **ejecutaron el 2026-08-17**, en ese orden y antes del merge. Cada `.sql` tiene su test anti-drift (`tests/api/test_migracion_*.py`, cuatro) que lo compara columna a columna contra el modelo y exige que viajen el RLS y las constraints con su nombre.
- **Cero dependencias nuevas en todo el módulo**: `git diff origin/main...feat/adoptar -- src/web/package.json src/web/package-lock.json requirements.txt pyproject.toml` no devuelve **nada**.

### Removed
- **Apadrinamiento** (era la feature `12-sponsorship` de Adopta 1.0): **recortado a propósito**, no olvidado. Sin pasarela de pagos real solo registraría una intención en una tabla, y `Organizacion.como_donar` ya cubre esa intención con información más útil (a quién, para qué, por qué medio). No hay tabla `sponsorships` en el módulo, ni acceptance que la pida: el item `AD-07` se copió a `feature_list.json` sin ella.
- **Chat interno** (era la feature `11-chat`, ADR 0004): **no vuelve**. Su `ConnectionManager` en memoria de un solo proceso no es "poco escalable" en el serverless de Vercel (ADR 0007) — **no funciona ni una vez**: no hay proceso persistente entre requests ni conexión que sobreviva a la respuesta. El **ADR 0013 supera al 0004** y decide WhatsApp directo, que es la misma regla que el ADR 0005 §3 ya fijó para la emergencia. No hay tabla `mensajes` ni ninguna dependencia de WebSockets.

### Changed
- `docs/architecture.md` **reescrito contra el código**, tras medir siete afirmaciones falsas (dependencias del pivot, 2 modelos listados de 14, "sin migraciones formales" cuando `migrations/` existe con 5 `.sql`, el mapa "de lienzo propio" que usa Leaflet desde el ADR 0008, `lib/mapa.ts` que ya no existe). `CLAUDE.md`, `AGENTS.md` y `docs/product-research.md` (§11 nuevo) también reflejan ya la fase 2 y el recorte del apadrinamiento.
- `CLAUDE.md` y `AGENTS.md` mandaban leer la era Adopta con `git show adopta-v1:ruta`, que **falla en este working tree** (`fatal: invalid object name`): no hay rama local, solo `origin/adopta-v1` y el tag. Corregido en los dos.

### Fixed
- El deck estaba **muerto con ratón y con dedo**: `setPointerCapture` en el `pointerdown` hacía que Chrome redirigiera el `click` al contenedor y nunca al botón. La captura se pide ahora en el primer `pointermove` de más de 8 px. jsdom no podía verlo (allí `setPointerCapture` ni existe); lo encontró el recorrido manual en Chrome.
- La cabecera del catálogo **desbordaba a 360px** (`shrink-0` y `flex-wrap` anulándose: 729px de ancho contra 360 de viewport). Medido por CDP antes y después.
- Con solo un tramo de edad activo y cero resultados, el catálogo decía "Todavía no hay mascotas publicadas" en vez de "ninguna coincide con estos filtros": `hayFiltros` no miraba `filtros.edad`. Se arregla con `contarFiltrosActivos` como fuente única.

### Sin cambios, y es una garantía
- **La rama `adopta-v1` sigue intocable**: `origin/adopta-v1` y el tag `adopta-v1.0.0` siguen en `cde337f`. El módulo **volvió portado a mano**, sin merge ni cherry-pick desde esa rama — los modelos portados (`pet.py`, `swipe.py`, `favorite.py`) no coinciden con su original. Para consultar la era Adopta: `git show origin/adopta-v1:ruta/al/archivo`.

## [2.5.0] - 2026-08-15

Jornada de colaboración: dos PRs externos integrados, módulo de adopción desplegado y dos fuentes de datos importadas.

### Added
- **Módulo de adopción (AD-01+AD-02, de un colaborador)**: catálogo público /adoptar, ficha con galería y checklist de salud, publicar por 3 caminos (organización, rescatista, y el puente "¿nadie la reclamó? dala en adopción" desde un reporte encontrado). Tabla `pets` con publicador exclusivo (CHECK) migrada.
- **`47-entrenadores`**: quinto tipo de la Red de Apoyo — vitrina con WhatsApp y "Cómo apoyar".
- **Sistema de deduplicación `dedup/` (PR 4, Javier Torres)**: detección por clusters con canónico cronológico, guarda anti-pérdida y juez LLM opcional que solo anota — herramienta de operador, nada se borra solo.
- **Coincidencias visuales (feature 24 / ADR 0012, PR 5, Juan Andrés Ruiz)**: parecido de fotos con modelos locales (recorte YOLOS + DINOv2 de identidad animal, costo $0, fotos nunca salen a terceros), bandas "alto/medio" sin porcentajes, la zona deja de ser filtro duro, guarda antifraude de misma-imagen. Columnas `reports.embedding`/`embedding_modelo` migradas; worker `embeddings/` corre fuera del serverless.
- **Datos**: 35 casos del export "Recupera Tu Mascota" (16 del Centro de Bienestar Animal) + 11 veterinarias de Cali + 16 fundaciones damnificadas.

### Fixed
- `init.sh` ahora corre TODOS los testpaths (crawler y dedup quedaban fuera: 45 tests invisibles al harness).

## [2.4.0] - 2026-08-14

Lote del benchmark Patas en Cali (product-research §10) — 3 features revisadas y desplegadas.

### Added
- **`40-seguridad-y-contacto-multicanal`**: avisos de seguridad anti-estafas al publicar y al contactar, botón de cámara directa en móvil, e Instagram/Facebook opcionales como canales de contacto de los reportes.
- **`41-fotos-multiples`**: hasta 3 fotos por reporte (tabla `report_fotos`) con galería de miniaturas en el detalle; la principal sigue mandando en tarjetas/mapa/og.
- **`42-tablero-ayuda-p2p`**: /ayudar con pestañas Lugares/Comunidad — avisos de ayuda entre personas (necesito/ofrezco: hogar de paso, transporte, alimento, salud, rescate) con WhatsApp directo y cierre "Resuelto 💚" (tabla `avisos_ayuda`).

## [2.3.0] - 2026-08-13

Jornada del benchmark encontradogs.co (product-research §9) — 5 features nuevas revisadas y desplegadas, más la primera ingesta masiva del crawler.

### Added
- **`35-marca-recorte-y-visibilidad`**: logos oficiales de `design/logo/` (favicon isotipo, wordmark en nav y landing, apple-touch-icon), recorte de foto al subir (react-easy-crop + `recortarImagen`, proporciones Original/Cuadrada/Horizontal), accesos "Ver reportes"/"Ver mapa" como botones en la landing y pestaña "Centros de ayuda".
- **`36-titulo-descriptivo`**: los reportes sin nombre se titulan con sus atributos ("Perro mediano café") en tarjetas, detalle, mapa y og tags.
- **`37-coincidencias-explicables`**: cada coincidencia dice por qué ("mismo perro", "misma zona", "a 0.6 km", "mismo color") sin cambiar el motor de orden.
- **`38-busqueda-por-descripcion`**: pantalla /buscar — describe a tu mascota y la app rankea por parecido explicable sin AI (pesos por zona/color/tamaño + solapamiento de señas; el porcentaje es relativo a los criterios dados).
- **`39-alertas-por-reporte`** (ADR 0011): "🔔 Avísame si hay novedades" — suscripción por correo a un reporte (tabla `suscripciones`), aviso en avistamientos y reencuentros vía Resend (no-op sin credenciales) y baja en un click.
- **SEO/compartir**: og tags + imagen social 1200x630 + robots.txt del sitio raíz (el link ya no sale pelado en WhatsApp/Instagram).
- **Ingesta Cali**: 204 reportes reales importados del Drive comunitario "ANIMALES PERDIDOS - CALI" vía el pipeline del crawler (solo extraviados/encontrados con foto, 5 duplicados detectados y saltados).

## [2.2.0] - 2026-08-12

Cierre del backlog ejecutable en la misma jornada del lanzamiento: 30 features en `done`, todas revisadas y desplegadas.

### Added
- **`26-zona-medellin`**: Medellín (Valle de Aburrá) como séptima zona con mapa propio + test comparativo permanente de sync backend↔frontend de las zonas.
- **`27-vista-reencuentros`**: filtro "Reunidas 💚" navegable en el listado (entrada desde la franja de la landing), badge celebratorio y capa "solo reencuentros" en el mapa.
- **`28-avistamientos`**: "la vi por aquí" — pistas georreferenciadas de terceros (sin cuenta) sobre reportes perdidos, con pins ocre y lista cronológica (tabla `sightings`).
- **`32-red-de-apoyo`** + **`33-necesidades-ayuda`**: sección /ayudar con centros de acopio, fundaciones, tiendas y veterinarias (mapa + directorio + Cómo donar), y necesidades concretas con "Quiero ayudar" por WhatsApp y "Cubierta 💚" (tablas `organizaciones` y `necesidades`).
- **`34-contadores-y-recencia`**: conteos en vivo por tipo (`/api/reports/conteos`) en listado y landing, y recencia relativa ("hace 2 horas") en tarjetas y detalle.
- **`21-compartir-reporte`** (ADR 0009): botón Compartir (Web Share API + fallback copiar) y vista previa real en WhatsApp — og tags por reporte servidos solo a bots vía rewrite por user-agent.
- **`30-busqueda-y-paginacion`**: búsqueda por texto libre (`q`) sobre nombre/señas/barrio/ciudad, paginación limit/offset con orden estable y total en `X-Total-Count`, campo Buscar y "Cargar más".
- **`31-pin-mi-ubicacion`**: geolocalización del navegador para el pin al reportar (con autoselección de zona y sugerencia de corrección) y para centrar el mapa.
- **`29-editar-reporte-completo`**: pantalla /reporte/:id/editar con foto, características, fecha, barrio y pin corregibles (solo autor).
- **`20-fotos-huerfanas-storage`**: al eliminar un reporte u organización su foto se borra del bucket/disco (tolerante a fallos; seed y hosts ajenos intocables).

### Changed
- Sin zona/ciudad preseleccionada en los formularios ("Selecciona la zona/ciudad" + mapa nacional) — antes todo defaulteaba a Armenia.
- Benchmarks documentados en product-research §6-8 (Reúne Mascotas, Encuentra tu Peludo).

## [2.1.0] - 2026-08-12

Deploy real: la app queda **viva en producción en <https://petfinder-col.com>** (Vercel + Supabase, todo free tier, dominio de GoDaddy), con auto-deploy en cada push a `main`, y el pulido post-lanzamiento pedido por el usuario.

### Added
- **`12-persistencia-supabase`** (ADR 0006): Postgres + Storage de Supabase como persistencia gratuita — API sin estado, fotos al bucket con URL pública absoluta, fallback local intacto para dev.
- **`13-api-vercel-serverless`** (ADR 0007): la API corre como función serverless en el mismo proyecto de Vercel (`api/index.py`) — cero tarjetas de crédito (Render eliminado tras exigirla), same-origin sin CORS ni `VITE_API_BASE_URL`, auto-deploy total con cada push a `main`.
- **`14-mapa-leaflet`** (ADR 0008): mapa real con Leaflet + OpenStreetMap (gratis, sin API key) en `/mapa`, el detalle y el formulario — pins por color, click con lat/lng reales, equivalente accesible por pin; se elimina la interpolación propia (`lib/mapa.ts`).
- **`15-caracteristicas-busqueda`**: raza (catálogo por especie), color y tamaño como selects predefinidos al reportar + filtros exactos en el listado y chips en tarjetas/detalle; columnas nullable nuevas en `Report` con migración aditiva de producción (ALTER + backfill, sin drop).
- **`16-mobile-ui`**: auditoría visual real a 390px y fix del desborde horizontal (la nav empujaba todas las rutas); nav deslizable en móvil.
- **`17-registro-ciudades-lista`**: la ciudad del registro es un select — las 6 zonas con mapa primero y las 32 capitales departamentales + ciudades grandes de Colombia después.
- **`18-eliminar-reporte`**: `DELETE /api/reports/{id}` solo-autor (204/403/404) + borrado con confirmación en dos pasos en el detalle.
- **`19-optimizacion-carga-y-tab`**: compresión de fotos en el navegador (máx 1280px JPEG) antes de subir, `loading="lazy"` en las tarjetas, `SKIP_DB_CREATE_ALL=1` para recortar el cold start serverless, título de pestaña `petfinder-col` y favicon propio (huella, tokens del design system).

### Changed
- **Entrar-o-registrar**: `POST /api/users` con un email existente devuelve la cuenta (200) en vez de 409 — fix del bug real de producción "no puedo volver a entrar"; emails normalizados a minúsculas.
- **Marca visible**: "Reencuentro" → **"Pet Finder Col"** en la nav y en el mensaje precargado de WhatsApp (el nombre interno del proyecto no cambia).

### Fixed
- El letrero de la landing ya no dice "Eje Cafetero": el alcance es todo el país.
- Fotos sin recorte: el detalle y el preview de subida muestran la imagen completa (`object-contain`), y las tarjetas muestran la mascota entera dentro del marco 4:3.
- Favicon con cache-bust (`?v=2`): el rayo por defecto de Vercel quedaba clavado en la caché de favicon de los navegadores.
- Env vars de producción leídas con `.strip()` (una `SUPABASE_URL` pegada con espacio rompía las URLs de las fotos) y compatibilidad `POSTGRES_URL`/`SUPABASE_SERVICE_ROLE_KEY`.

## [2.0.0] - 2026-08-12

Pivot completo del producto tras el terremoto del Eje Cafetero (2026-08-10): de **Adopta** (adopción de mascotas) a **Reencuentro** (reporte y reunificación de mascotas perdidas/encontradas). Ver ADR 0005. Verificación end-to-end en `docs/verification.md`: 51 tests de API + 56 de web en verde, recorrido completo en navegador real.

### Removed
- **Todo el producto de adopción** (features `01`-`15` de la era Adopta): modelos (`HomeProfile`, `Shelter`, `Pet`, `Swipe`, `Match`, `Sponsorship`, `Favorite`, `Thread`, `Message`), servicios (afinidad, deck, matching, solicitudes, chat WebSocket), routers, las 14 pantallas, el sistema de diseño por pantalla y los prototipos. **Nada se perdió**: la era Adopta vive íntegra en la rama `adopta-v1` (tag `adopta-v1.0.0`).
- ADRs 0002-0004 (match no-mutuo, afinidad al vuelo, chat WebSockets): su objeto ya no existe en el árbol; se conservan en la rama.

### Added
- **`01-pivot-fundaciones`**: rama de archivo `adopta-v1` + tag; paquete renombrado `adopta_api` → `reencuentro_api`; harness completo actualizado (feature_list con 11 features nuevas, CLAUDE/AGENTS/CHECKPOINTS, ADR 0005, product-research y architecture reescritos); API mínima (registro liviano + perfil) y web mínima (landing de emergencia + registro con `?volver=`); media movida a `data/media/{seed,uploads}`.
- **`02-reportes-backend`**: modelo único `Report` (perdido|encontrado con validación condicional), `services/ciudades.py` (Armenia, Pereira, Manizales, Cali, Quibdó, Bogotá + bounding box nacional), CRUD con filtros, seed determinista de 17 reportes con par de coincidencia obvia y 2 reunidos.
- **`03-upload-fotos`**: `POST /api/uploads` multipart seguro (uuid, extensión del content-type, ≤5 MB por chunks) + `FotoUpload` con preview; rutas de media unificadas en `reencuentro_api/media.py` tras un 404 real encontrado por el revisor.
- **`04-reportar-ui`**: formulario único con campos condicionales, pin por click sobre el mapa propio (interpolación invertible por zona), selector con "Otro lugar de Colombia", gate de registro con `?volver=`, landing de emergencia con los 2 CTAs gigantes.
- **`05-listado-reportes`**: galería `/reportes` con filtros; `ReporteCard` hereda el diseño visual de las tarjetas de mascota de `adopta-v1`.
- **`06-detalle-contacto`**: `/reporte/:id` con mini-mapa y contacto directo — `wa.me` con mensaje precargado y `tel:`, teléfono normalizado a +57.
- **`07-mapa-reportes`**: `/mapa` con vista "Todo Colombia" y por zona, pins danger/forest con leyenda, sin librerías de mapas.
- **`08-coincidencias`**: heurística explicable sin AI (tipo opuesto + especie + zona, orden por distancia con penalización de 0.5 km/día) y sección en el detalle.
- **`09-reunidos`**: marcar reencuentro (solo autor, 403/409), `/mis-reportes` con edición, franja de esperanza con contador en la landing.
- **`10-verificacion-final`**: evidencia completa en `docs/verification.md`; merge `develop` → `main`.

### Changed
- `Registro.tsx` ahora soporta `?volver=` (para volver al formulario de reporte tras registrarse) y solo acepta rutas internas como destino.
- Clave de sesión en localStorage: `adopta_active_user_id` → `reencuentro_active_user_id` (+ helper `hasActiveUser()`).

## [1.0.0] - 2026-08-04

Backlog completo: las 15 features de `feature_list.json` en `done`. Sesión continua sobre el MVP (`0.1.0`), cerrando post-MVP (`06`-`07`) y todo el backlog (`08`-`15`).

### Added
- **`06-filters`**: filtros de descubrimiento (especie, tamaño, energía, edad, convivencia, distancia) sobre `GET /api/pets`, aplicados al instante; `services/geo.py` (haversine) y `User.lat/lng`.
- **`07-adopter-profile`**: `GET /api/users/{id}` con perfil, resumen de `HomeProfile` y métricas agregadas; pantalla "Mi perfil".
- **`08-onboarding-cuestionario`**: registro liviano sin contraseña, cuestionario de hogar interactivo de 6 pasos (reemplaza el `HomeProfile` sintético), guard `RequiereHomeProfile` que bloquea el deck hasta completarlo.
- **`09-shelter-panel`**: panel del refugio de solo lectura (perfil, métricas, cola de solicitudes con el cuestionario del adoptante adjunto) y publicación de mascotas nuevas.
- **`10-adoption-request-flow`**: acciones del refugio sobre la solicitud (agendar visita, pedir más información, descartar con motivo obligatorio y privado) con una matriz de transiciones de estado validada.
- **`11-chat`**: mensajería en tiempo real adoptante↔refugio por match, sobre WebSockets nativos de FastAPI (ver ADR 0004 — sin migrar a un BaaS externo).
- **`12-sponsorship`**: apadrinamiento de mascotas (niveles de donación, lista de "necesitan apoyo ahora"), sin pasarela de pago real — registro de compromiso en base de datos.
- **`13-favorites`**: guardar mascotas para revisar después sin que cuente como swipe (independiente de `Swipe`/`Match`).
- **`14-shelter-map`**: mapa de refugios con lienzo propio en CSS/SVG (interpolación de `lat`/`lng`), sin tiles externos ni dependencias nuevas.
- **`15-public-landing`**: landing pública de marketing en `/` (reemplaza el redirect a `/descubrir`), con el copy del prototipo original `Adopta Landing.dc.html`.
- ADR 0004 (`docs/decisions/0004-chat-websockets-fastapi.md`): WebSockets sobre FastAPI en vez de un BaaS para el chat en tiempo real.

### Changed
- `UserMetricsOut.apadrinamientos` y `ShelterMetricsOut.apadrinamientos_recaudados_cop` (antes fijos en `0`, features `07`/`09`) ahora reflejan datos reales de `Sponsorship`.
- `App.tsx` reestructurado con un layout `AppLayout` (`Nav`+`Outlet`) para que la landing pública en `/` no muestre la navegación interna de la app.

## [0.1.0] - 2026-07-31

Primer MVP funcional en local, con datos artificiales.

### Added
- Sistema de harness engineering completo: `AGENTS.md`, `CHECKPOINTS.md`, `init.sh`, `.claude/agents` (líder/implementador/revisor/investigador/diseñador), `.claude/skills` (seed-data, db-migrations, run-verification, update-memory, match-scoring), hooks de validación de `feature_list.json` y de formato post-edit.
- Investigación de producto (`docs/product-research.md`) y arquitectura (`docs/architecture.md` + ADRs 0001-0003) a partir del diseño preexistente de Adopta.
- Sistema de diseño formalizado (`design/design-system.md`, `design/screens/*.md`) para las 11 pantallas del producto.
- Backend (FastAPI + SQLAlchemy + SQLite): modelo de datos (`User`, `HomeProfile`, `Shelter`, `Pet`, `Swipe`, `Match`), cálculo de compatibilidad adoptante↔mascota con reglas duras de incompatibilidad, creación de match no-mutuo al hacer like, orden del deck con inserción de mascotas difíciles de ubicar, seed determinista con 17 mascotas/3 refugios/5 adoptantes y descarga de fotos con fallback offline.
- Frontend (React + Vite + TypeScript + Tailwind v4): deck de descubrimiento con gesto de swipe (arrastre + equivalentes de teclado/botón), ficha de mascota, modal de match, listado de matches.
- `dev.sh`: comando único para levantar API + web en local.
- 18 tests de backend (pytest) y 5 de frontend (Vitest + Testing Library), todos en verde. Evidencia completa en `docs/verification.md`.

### Fixed
- Tag inexistente en la config de pre-commit de `mirrors-prettier` (`v3.3.3` → `v3.1.0`).
- Deprecación de `on_event` de FastAPI, migrado a `lifespan`.
- `target-version` de ruff/black desalineado con el intérprete real (3.11 asumido → 3.10 real).
