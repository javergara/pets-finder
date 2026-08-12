# 0009 — Crawler de redes sociales: reportes con fuente y metadata de origen

## Estado

Propuesto (PR de Javier Torres — pendiente de aceptación del dueño del proyecto).

## Contexto

Tras el sismo, la mayoría de los reportes de mascotas perdidas/encontradas se
publican en redes (Instagram, Facebook) y nunca llegan a la plataforma: la
difusión está fragmentada justo cuando el matching necesita densidad de datos.
La idea: un crawler que tome publicaciones de redes (hoy: pantallazos), extraiga
los campos con un LLM y las publique como reportes, para que las coincidencias
sin AI de siempre (especie + zona + distancia + fecha, ADR 0005) también corran
sobre lo que la gente publica fuera de la app.

## Decisión

1. **Procedencia en el modelo**: `Report.fuente` (`"manual"` default | `"crawl"`)
   y `Report.crawl_metadata` (JSON). El schema del metadata es una **unión
   discriminada por `plataforma`**: base común (url_post, autor_handle, fecha_post,
   texto_original, modelo_extraccion, confianza, indice_mascota, total_mascotas)
   más los campos propios de cada plataforma. Hoy: `grupo` en Facebook (los
   posts viven en grupos tipo "Mascotas Perdidas Cali" — el nombre es señal de
   zona y camino para hallar el post) y `nombre_grupo` en WhatsApp (las cadenas
   no tienen URL; el grupo es la única pista de origen). Se llama `plataforma`
   y no "red" porque no todo origen es una red social: WhatsApp es mensajería,
   y un adaptador futuro podría ser un sitio de noticias. Las variantes son
   `extra="forbid"`: un campo en
   la variante equivocada es 422, no descarte silencioso. `JSON` de SQLAlchemy
   es portable (nativo en Postgres, TEXT en SQLite) — es la única excepción a la
   regla tácita de tipos simples en los modelos.
2. **Teléfono opcional solo en crawl**: los posts no siempre traen teléfono; el
   contacto es la publicación original. Regla dura en el schema: un reporte
   `crawl` sin teléfono exige `url_post` o `autor_handle` (algún camino de
   contacto), y `manual` mantiene el teléfono obligatorio de siempre. La UI del
   detalle muestra "Ver publicación original" en vez de WhatsApp/llamada, más
   una línea de procedencia con advertencia de extracción automática.
3. **El crawler es un proceso independiente** (`crawler/`), organizado como
   **pipelines de crawling**: cada pipeline es una forma distinta de obtener
   publicaciones — la primera es la de pantallazos (recibe uno o una carpeta
   de ellos, aportados a mano); candidatas futuras: un bot que reciba
   forwards/DMs, APIs oficiales, scraping donde los ToS lo permitan. Todas
   convergen en el mismo extractor → publicador. La API en Vercel es serverless
   (segundos de timeout — ADR 0007) y no puede crawlear: el crawler corre
   aparte (manual hoy, cron después) y publica por el **POST /api/reports
   público** — un solo camino de escritura, misma validación que el formulario.
   La independencia es de EJECUCIÓN, no de contrato: el crawler corre desde el
   checkout del repo e importa `ReportIn` y las zonas de la API como fuente de
   verdad (validación local con los mismos mensajes del backend, cero copias
   que se desincronicen). Sus dependencias de terceros sí viven aparte, en
   `crawler/requirements.txt`, jamás en las de la API.
4. **Usuario sistema**: los reportes crawleados pertenecen a un usuario real
   registrado para eso (p. ej. `crawler@petfinder-col.com`), con su id en la env
   var `CRAWLER_USER_ID`. Quien entre con ese email administra los reportes
   crawleados con las herramientas de autor que ya existen (editar, reunido,
   eliminar). Limitación conocida y aceptada: sin auth real (ADR 0005 §4),
   cualquiera puede publicar como el crawler; mitigación futura si duele: header
   secreto exigido cuando `fuente=crawl`.
5. **Extracción pantallazo → LlamaExtract**: la extracción es stateless con
   el SDK v2 (paquete `llama-cloud`; el paquete `llama-cloud-services` y su API
   de agentes quedaron deprecados en mayo de 2026) — el esquema viaja en cada
   request, sin estado que sincronizar en LlamaCloud. Schema-first con LlamaExtract
   (`crawler/schema.py` es a la vez el esquema y el prompt: las descripciones
   de los campos son las instrucciones), que resuelve reintentos/validación y
   devuelve confianza. Motivo decisivo además del fit técnico: Javier trabaja
   en LlamaIndex y el proyecto tiene **créditos ilimitados de LlamaExtract** —
   costo cero real para Pet Finder Col, coherente con el resto del stack free.
   Alternativa considerada: llamada directa a un modelo multimodal con salida
   estructurada — menos dependencia, pero reimplementa el ciclo de validación
   y sí costaría por token; se reevalúa si LlamaExtract estorba. Como mínimo
   casi siempre es extraíble el `autor_handle` — con eso ya hay camino de
   contacto.
6. **Multi-mascota**: un pantallazo puede traer varias mascotas. El extractor
   devuelve una lista: una entrada por animal individualizable, o UNA entrada
   colectiva si es un grupo genérico ("rescatamos 15 perritos" — igual que ya
   hace la gente a mano). N mascotas → N reportes que comparten foto, zona,
   fecha y `url_post`, distinguidos por `indice_mascota`.
7. **Dedup en dos capas**. (a) A nivel de extracción, local al crawler: un post
   ya visto no se re-extrae nunca (el LLM no es determinista: re-extraer
   duplicaría reportes y pagaría créditos dos veces). Clave: `url_post` o
   sha256 del pantallazo; estado en JSONL gitignored. (b) A nivel de creación,
   garantizado por el servidor: `Report.idempotency_id` (columna con índice
   único; el crawler manda `<clave_post>#<indice_mascota>`) hace el POST
   idempotente — repetirlo devuelve el reporte existente con 200 en vez de
   duplicar, incluso si una corrida murió a mitad de publicar y se reintenta,
   e incluso ante requests concurrentes (la carrera la resuelve el índice
   único, no un check-then-act).
8. **Geo aproximada**: los posts no traen coordenadas; el pin cae en el centro
   de la zona resuelta desde la ciudad extraída (mismo fallback del formulario
   web). Ciudad fuera de las 6 zonas → "Otro" + `ciudad_texto`. El matching se
   degrada con elegancia: pierde señal de distancia, conserva especie+zona+fecha.
   TODO futuro: geocodificar `barrio` + `ciudad_texto` con un servicio real
   (p. ej. Google Geocoding API) para pins precisos y distancia con señal de
   verdad en el matching. Queda como TODO y no como decisión porque exige key
   con facturación — la misma razón por la que el mapa descartó Google Maps
   (ADR 0008); evaluar también Nominatim (OSM), gratis con rate limits.

## Consecuencias

- **Migración de producción ANTES de mergear a `main`** (regla del repo):

  ```sql
  ALTER TABLE reports ADD COLUMN fuente VARCHAR(20) NOT NULL DEFAULT 'manual';
  ALTER TABLE reports ADD COLUMN crawl_metadata JSON;
  ALTER TABLE reports ADD COLUMN idempotency_id VARCHAR(300);
  CREATE UNIQUE INDEX ux_reports_idempotency_id ON reports (idempotency_id);
  ALTER TABLE reports ALTER COLUMN telefono_contacto DROP NOT NULL;
  ```

  Aditiva y retrocompatible: los reportes existentes quedan `manual` con su
  teléfono intacto. El `DROP NOT NULL` no pierde datos.
- Crear el usuario sistema en producción (registro normal con
  `crawler@petfinder-col.com`) y anotar su id como `CRAWLER_USER_ID`.
- Reportes crawleados de baja calidad son el spam que la feature 23 (moderación)
  del backlog quiere manejar — el crawler empieza en dry-run por defecto y con
  volumen manual precisamente por eso.
- Fricción legal/ToS: el pantallazo manual evita scraping automatizado contra
  los ToS de las plataformas; si esto escala a crawling real, esa decisión
  merece su propio ADR.
- Costo: cero mientras corra con los créditos de LlamaExtract de Javier (env
  var `LLAMA_CLOUD_API_KEY` suya). Si el proyecto algún día necesita una key
  propia, el dedup ya limita el gasto (nada se extrae dos veces).
