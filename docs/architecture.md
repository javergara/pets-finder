# Arquitectura — Reencuentro

> La arquitectura de la era Adopta vive en la rama `adopta-v1`. Este documento describe el estado tras el pivot (ADR 0005) y la **fase 2** (módulo de adopción, features `AD-01`…`AD-08`), portada a mano desde esa rama.
>
> **Regla de este documento**: si una afirmación no se puede comprobar con un comando (`ls`, `grep`, `git log`), no se escribe. `CHECKPOINTS.md` declara inválida la documentación que describe lo que el código no hace, y este archivo llegó a decir que el mapa era un lienzo CSS propio dos ADRs después de migrar a Leaflet.

## 1. Stack

Sin cambios respecto al ADR 0001: **FastAPI + SQLAlchemy** (`src/api/reencuentro_api/`), **React + Vite + TypeScript + Tailwind v4** (`src/web/`). **SQLite en local, Postgres de Supabase en producción** (ADR 0006). Un comando de arranque (`bash dev.sh`), todo reproducible en local sin credenciales de terceros.

Dependencias de la API — `src/api/requirements.txt`, todas pineadas y verificadas contra el runtime CPython 3.14 de Vercel:

| Paquete | Para qué | Justificación |
| --- | --- | --- |
| `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic` | el stack base | ADR 0001 |
| `python-multipart` | el multipart de `POST /api/uploads` | ADR 0005 |
| `psycopg[binary]` | driver Postgres **v3** (`postgresql+psycopg://`, `models/base.py`). No es `psycopg2`: no publica wheels para el runtime de Vercel | ADR 0006 |
| `requests` | HTTP saliente: subir fotos al Storage de Supabase (`media.py`) y enviar correo por la API de Resend (`services/notificaciones.py`) | ADRs 0006 y 0011 |
| `httpx` | **solo tests**: lo exige `fastapi.testclient.TestClient` (`tests/api/conftest.py`). Ningún módulo de `src/` lo importa | — |

Dependencias del frontend — `src/web/package.json`, más allá de React / React Router / Tailwind:

| Paquete | Para qué | Justificación |
| --- | --- | --- |
| `leaflet` + `@types/leaflet` | mapa real con tiles de OpenStreetMap (`components/MapaLienzo.tsx`) | ADR 0008 |
| `qrcode` + `@types/qrcode` | QR del cartel imprimible (`lib/cartel.ts`) | feature 44, sin ADR propio |
| `react-easy-crop` | recorte de la foto antes de comprimirla y subirla (`components/FotoUpload.tsx`) | feature 35, sin ADR propio |

⚠️ `CHECKPOINTS.md` pide **un ADR por dependencia nueva**; `qrcode` y `react-easy-crop` entraron con su porqué escrito solo en `changes.md`. Es deuda conocida, no un olvido silencioso.

Fuera de la función serverless, dos procesos independientes con sus **propios** `requirements.txt` (que a propósito no se mezclan con el de la API): `embeddings/` (torch, vectores de fotos, ADR 0012) y `crawler/` (llama-cloud, ADR 0010).

## 2. Modelo de datos

**14 modelos** en `src/api/reencuentro_api/models/` (`grep -c __tablename__ models/*.py`), un archivo por entidad. `base.py` no es un modelo: tiene el `DeclarativeBase` y la resolución de `DATABASE_URL`.

**Cuenta (transversal a los tres dominios)**

- **`User`** (`users`) — quien reporta, quien publica en adopción y quien adopta. Registro liviano sin contraseña.

**Emergencia (el pivot, features 01-46)**

- **`Report`** (`reports`) — el corazón de la app. Un solo modelo para ambos tipos (`tipo: perdido|encontrado`, ADR 0005 §2): especie, descripción, `foto_url`, zona + `lat`/`lng` (pin), `fecha_evento`, `telefono_contacto`, `estado: activo|reunido`. Campos condicionales: `nombre_mascota` (solo perdido), `situacion: conmigo|vista` (solo encontrado). `embedding` (384 dims en JSON) lo escribe el worker, no la API.
- **`ReportFoto`** (`report_fotos`) — hasta 2 fotos extra por reporte; `Report.foto_url` sigue siendo la principal.
- **`Sighting`** (`sightings`) — "la vi por aquí", **sin autoría ni cuenta**: en una emergencia cada fricción es una pista perdida.
- **`Suscripcion`** (`suscripciones`) — "avísame si hay novedades de este reporte"; el correo es la identidad y el `token` es la baja en un click.
- **`RadarAviso`** (`radar_avisos`) — pareja (perdido, candidato) ya avisada por el radar diario; evita reavisar lo mismo.

**Red de apoyo (features 32-33, 42)**

- **`Organizacion`** (`organizaciones`) — acopio, fundación, tienda o veterinaria, con dirección física obligatoria. `como_donar` es texto libre: **la app no procesa pagos**.
- **`Necesidad`** (`necesidades`) — pedido concreto de una organización; se cierra como "cubierta".
- **`AvisoAyuda`** (`avisos_ayuda`) — ayuda puntual entre vecinos ("necesito" / "ofrezco"), que no es una organización con sede.

**Adopción — fase 2 (features `AD-01`…`AD-08`)**

- **`Pet`** (`pets`) — mascota publicada en adopción. `ck_pets_publicador_exclusivo` obliga a que publique **o** un usuario **o** una organización, nunca los dos.
- **`HomeProfile`** (`home_profiles`) — perfil de hogar del adoptante, input de la afinidad. **PK = `user_id`**: hay como máximo uno por persona y la existencia de la fila *es* la señal.
- **`Swipe`** (`swipes`) — "me interesa" / "ahora no" sobre una carta del deck (`uq_swipe_user_pet`).
- **`Match`** (`matches`) — **la solicitud de adopción**. La tabla conserva el nombre histórico, pero en la API, el copy y las pantallas se llama siempre "solicitud". Se crea sola con el swipe-derecha: el match **no es mutuo** (ADR 0002).
- **`Favorite`** (`favorites`) — "guardar para después" (`uq_favorite_user_pet`), **independiente** de swipe y solicitud.

⚠️ **Colisión de `user_id`, la trampa del portado**: en `pets` es quien **publica**; en `swipes`, `matches` y `favorites` es quien **mira**. Confundirlas muestra el deck de una persona a otra. Hay tests dedicados en `tests/api/` para las tres.

### Migraciones: sí las hay, y `seed.py` NUNCA toca producción

**`migrations/` contiene el SQL versionado que se ejecuta a mano en el SQL Editor de Supabase** (`ls migrations/`: 5 `.sql` + `README.md`). No hay Alembic ni runner automático — introducirlo exige un ADR. Reglas: solo SQL **aditivo** (`create table if not exists`, `add column if not exists`, columnas nuevas nullable o con default), nunca `drop`/`truncate`/renombres, y **toda tabla nueva lleva `enable row level security`**.

Cada migración tiene su **anti-drift** en `tests/api/` — cuatro hoy, que comparan el `.sql` contra el modelo ORM (columnas, tipos, `UNIQUE`/`CHECK` **con su nombre exacto**, RLS): `test_migracion_pets.py`, `test_migracion_swipes.py`, `test_migracion_matches.py`, `test_migracion_favorites.py`, con el parser compartido en `tests/api/soporte_migraciones.py`.

⚠️ **Estado hoy: de las 5 migraciones, solo `AD-01-pets.sql` está ejecutada en producción. Las cuatro de adopción están escritas y SIN EJECUTAR**, en este orden obligatorio: `AD-03-swipes.sql` → `AD-03-home-profiles.sql` → `AD-05-matches.sql` → `AD-07-favorites.sql`. El estado por archivo vive en la tabla de `migrations/README.md`.

⚠️ **`scripts/seed.py` hace `drop_all` + `create_all`: es exclusivamente para la SQLite de desarrollo.** Correrlo contra producción borraría datos reales de gente que perdió a su mascota. En local es el reset determinista de siempre (skill `db-migrations`); en producción, el esquema solo cambia por un `.sql` de `migrations/` ejecutado a mano y con autorización explícita del dueño.

## 3. Servicios

`src/api/reencuentro_api/services/` tiene **12 módulos**: 11 de lógica pura (sin I/O ni FastAPI, testeables sin levantar la app) y `db.py`, que es solo la dependencia de sesión de SQLAlchemy.

**Emergencia**

- `geo.py` — distancia haversine entre dos coordenadas; base de todo lo demás.
- `ciudades.py` — fuente de verdad de las zonas (bounding box + centro): Armenia, Pereira, Manizales, Cali, Quibdó, Bogotá, Medellín + `COLOMBIA` (nacional). **Duplicada a mano en `src/web/src/lib/ciudades.ts` — mantener en sync** (checkpoint explícito en `CHECKPOINTS.md`).
- `coincidencias.py` — ordena candidatos del tipo opuesto por cercanía (distancia + penalización por fecha) **más el parecido visual de las fotos** (ADR 0012), que solo suma y nunca resta. Los vectores los calcula el worker `embeddings/`, un proceso aparte: torch no cabe en la función serverless. Sin vector, el orden es idéntico al anterior al ADR 0012.
- `busqueda.py` — "busca a tu mascota" (feature 38): parecido explicable sin AI; lo que se deja en blanco no se compara.
- `radar.py` — qué parejas merecen correo en cada corrida diaria, sobre el mismo orden determinista de `coincidencias.py`.
- `notificaciones.py` — correo vía la API HTTP de Resend (ADR 0011). Sin `RESEND_API_KEY` es un no-op con log: la falta de credenciales nunca rompe un endpoint.
- `titulos.py` — `titulo_reporte(report)` y `titulo_pet(pet)`, ambos sobre el **modelo ORM**. Espejos de `lib/titulo.ts` y `lib/adopcion.ts::tituloMascota`; alimentan los og tags.

**Adopción**

- `afinidad.py` — compatibilidad adoptante ↔ mascota, calculada al vuelo y sin caché (ADR 0003); pesos y reglas duras portados intactos de la era Adopta.
- `descubrir.py` — orden del deck: afinidad descendente con inserción periódica de mascotas difíciles de ubicar, para que el propio score no las esconda.
- `filtros.py` — filtros del deck sobre `PetOut` (no sobre el ORM), calculando de paso `distancia_km`.
- `solicitudes.py` — etiqueta y matriz de transiciones de una solicitud (`solicitado` → `en_revision` / `visita_agendada` → `adoptado` / `cerrado`). **Cero imports fuera de `datetime`**, que es lo que permite recorrer la matriz entera sin levantar app ni base.

## 4. API

**12 routers** en `src/api/reencuentro_api/routers/`, montados en `main.py` en ese mismo orden.

**Emergencia**

- `users.py` — `POST /api/users`, `GET /api/users/{id}` (registro liviano y perfil) + el perfil de hogar (`GET/PUT /api/users/{id}/home-profile`, que es de adopción pero vive bajo `users`).
- `reports.py` — CRUD de reportes con filtros (`POST/GET /api/reports`, `GET/PUT/DELETE /api/reports/{id}`; `estado=activo` por defecto, solo el autor edita o elimina) + `GET /busqueda`, `GET /reunidos`, `GET /conteos`, `POST /{id}/reunido`, `GET /{id}/coincidencias`, avistamientos y suscripciones del reporte.
- `uploads.py` — `POST /api/uploads`: multipart, valida content-type (jpeg/png/webp) y tamaño (≤5 MB), nombre uuid derivado del content-type y **nunca del filename del cliente**.
- `suscripciones.py` — `GET /api/suscripciones/baja/{token}`: baja en un click desde el correo, devuelve HTML.
- `radar.py` — `GET/POST /api/radar`, protegido por `CRON_SECRET`; lo dispara el cron de `vercel.json` (`0 11 * * *`).

**Red de apoyo**

- `organizaciones.py` — CRUD de organizaciones + sus necesidades (`/{id}/necesidades`, `POST /{id}/necesidades/{nid}/cubierta`).
- `avisos_ayuda.py` — CRUD de avisos entre vecinos + `POST /{id}/resuelto`.

**Adopción**

- `pets.py` — `POST/GET /api/pets`, `GET/PUT/DELETE /api/pets/{id}`, `GET /api/pets/deck` (el deck ordenado) y `GET /api/pets/adopciones` (la franja de resumen).
- `swipes.py` — `POST /api/swipes`: registra la decisión y, en el swipe-derecha, crea la solicitud en el mismo request.
- `solicitudes.py` — `GET /api/solicitudes`, `GET /api/solicitudes/{id}` y las cuatro transiciones (`agendar-visita`, `pedir-informacion`, `descartar`, `aprobar`).
- `favoritos.py` — `POST/GET /api/users/{id}/favorites`, `DELETE /api/users/{id}/favorites/{pet_id}`. **Segundo router con prefijo `/api/users`**: va después de `users` y sus rutas tienen un segmento más, así que no compite con `/{user_id}`.

**Vistas HTML para bots**

- `paginas.py` — **va siempre último** porque registra rutas de raíz sin prefijo: `GET /reporte/{id}` (ADR 0009), `GET /adoptar/mascota/{pet_id}` (AD-08) y una ruta por zona (`/cali`, `/armenia`, …, generadas en un bucle sobre `SLUG_ZONAS`). Devuelven HTML con og tags, `html.escape` en todo, `og:image` omitido si no hay foto y 404 en español.

**Estáticos**: `/media` desde `data/media/` (`seed/` regenerable + `uploads/`), montado solo si el directorio existe — en serverless el filesystem es de solo lectura y todas las fotos son URLs absolutas de Supabase.

⚠️ **Regla de orden**: cualquier ruta literal (`/api/reports/reunidos`, `/api/pets/deck`) se registra **antes** que su ruta dinámica (`/{report_id}`, `/{pet_id}`) o queda eclipsada y responde 422. Está comentada en `main.py` y es una lección heredada, no teórica.

## 5. Frontend

Pantallas (`src/web/src/screens/`, ruteadas en `App.tsx`):

- **Emergencia**: landing (`/`), registro (`/registro`), reportar (`/reportar/perdido|encontrado`, un componente con campos condicionales), buscar por descripción (`/buscar`), listado (`/reportes`), detalle (`/reporte/:id`), editar (`/reporte/:id/editar`), mapa (`/mapa`), mis reportes (`/mis-reportes`).
- **Red de apoyo**: `/ayudar` (directorio + pestaña de comunidad), `/ayudar/registrar`, `/ayudar/publicar-aviso`, `/organizacion/:id`.
- **Adopción (9 rutas bajo `/adoptar`)**: catálogo (`/adoptar`), publicar (`/adoptar/publicar`), deck de swipe (`/adoptar/descubrir`), cuestionario de hogar (`/adoptar/mi-hogar`), mis solicitudes (`/adoptar/mis-solicitudes`), detalle de solicitud (`/adoptar/solicitud/:id`), mis favoritas (`/adoptar/mis-favoritas`), ficha (`/adoptar/mascota/:id`) y editar (`/adoptar/mascota/:id/editar`). Solo el catálogo se anuncia en la nav; a las interiores se llega desde él.
- **Landings de zona** (feature 46): una ruta por slug de `SLUGS_ZONA` (`/cali`, `/armenia`, `/pereira`, `/manizales`, `/quibdo`, `/bogota`, `/medellin`), espejo del `SLUG_ZONAS` del backend.

**El mapa usa Leaflet con tiles de OpenStreetMap** desde el **ADR 0008**. El componente sigue llamándose `components/MapaLienzo.tsx` por el lienzo CSS/SVG que reemplazó, pero su primera línea es `import L from 'leaflet'` — **el nombre es la única cosa que queda del diseño anterior, y `lib/mapa.ts` ya no existe**. Los colores de los pines se duplican como hex en el componente porque Leaflet pinta SVG y no lee clases de Tailwind.

El contacto es directo: `wa.me` + `tel:` (`lib/contacto.ts`), sin chat interno, tanto en los reportes como en las solicitudes de adopción (ADR 0013). Compartir por WhatsApp usa `navigator.share` con fallback a `clipboard` (`/reporte/:id` y `/adoptar/mascota/:id`), y quien recibe el link ve la vista previa que sirve `routers/paginas.py`.

## 6. Autenticación y sesión

Igual que en la era Adopta: ninguna real. `localStorage` guarda `reencuentro_active_user_id` (`lib/session.ts`); el backend recibe la identidad como parte del payload/query. `hasActiveUser()` distingue "nunca se registró" del fallback al `DEMO_USER_ID = 1`, y es lo que usan las pantallas para mandar a `/registro` en vez de actuar como el usuario semilla. Suficiente para el MVP de emergencia; si el proyecto crece, se decide auth real con un ADR nuevo.

## 7. Despliegue

Frontend estático y API **serverless** en un solo proyecto de Vercel (entry `api/index.py`, ADR 0007); persistencia en **Supabase** — Postgres vía `DATABASE_URL` (en local sigue SQLite) y fotos en Storage vía `media.py::subir_a_supabase` cuando `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` están configuradas (ADR 0006). Auto-deploy con cada push a `main`. Guía completa en `docs/deploy.md`.

Variables de entorno que leen los módulos (`grep -rn "os.environ.get" src/api api`): `DATABASE_URL` (o `POSTGRES_URL`/`POSTGRES_PRISMA_URL`), `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (con `SUPABASE_SERVICE_ROLE_KEY` como alias de respaldo, `media.py`), `SUPABASE_BUCKET`, `CORS_ORIGINS`, `SITE_URL`, `RESEND_API_KEY`, `RESEND_FROM`, `CRON_SECRET` y `SKIP_DB_CREATE_ALL`.

**`SKIP_DB_CREATE_ALL=1` está puesto en producción** (feature 19). Con esa variable el arranque **se salta `Base.metadata.create_all`**: recorta el arranque en frío del serverless, y a cambio **ninguna tabla ni columna se crea sola en el deploy**. Sin la variable (dev y tests), `create_all` sigue creando el esquema como siempre, dentro de un `try` que deja la app sirviendo `/health` aunque falle.

⚠️ **Flujo obligatorio para cualquier cambio de esquema — el `ALTER` aditivo va ANTES del merge a `main`:**

1. Escribir el `.sql` aditivo en `migrations/` (`AD-0N-<tabla>.sql`) y su test anti-drift en `tests/api/`.
2. Pedir **autorización explícita del dueño** y ejecutarlo a mano en el SQL Editor de Supabase, en el orden de la cola.
3. Verificar contra prod (las tres consultas de `migrations/README.md`: tabla + RLS, columnas, constraints) y actualizar el estado en su tabla.
4. **Solo entonces**, mergear a `main`.

El orden no es burocracia: el auto-deploy sirve el código nuevo apenas se pushea y `SKIP_DB_CREATE_ALL=1` no crea nada de red de seguridad, así que si el código llega antes que las tablas **cae la API entera**, no solo la pantalla nueva.

⚠️ **Hoy hay cuatro migraciones en esa cola sin ejecutar** (ver §2): el merge de `feat/adoptar` a `main` está bloqueado hasta que corran.
