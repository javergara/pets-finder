# Cómo desplegar el módulo de adopción (AD-03 … AD-08) en producción

> Para Javier (dueño del repo y único con acceso a Supabase y Vercel).
> Este documento existe porque **el merge a `main` está bloqueado hasta que ejecutes cuatro sentencias SQL a mano**, y porque el orden entre esas sentencias y el merge no es una formalidad: al revés, tumba `/adoptar` entero en producción.
>
> Es el hermano operativo de `docs/revision-modulo-adopcion.md` (que cubrió AD-01+AD-02 y funcionó). Aquel decía *cómo revisar*; este dice *cómo desplegar*.

---

## TL;DR — lo único que no puede salir mal

**Ejecuta las cuatro migraciones en Supabase ANTES de mergear, en este orden:**

```bash
pbcopy < migrations/AD-03-swipes.sql          # 1
pbcopy < migrations/AD-03-home-profiles.sql   # 2
pbcopy < migrations/AD-05-matches.sql         # 3
pbcopy < migrations/AD-07-favorites.sql       # 4
```

Una por una: copiar → Supabase → proyecto de producción → **SQL Editor** → **New query** → pegar → **Run**. Respuesta esperada en las cuatro: `Success. No rows returned`.
*(Si el proyecto aparece pausado, dale antes a "Restore"/"Resume": el plan gratuito lo pausa tras una semana sin actividad.)*

Después, las tres consultas de verificación de la sección 3. **Solo entonces**, el merge.

En producción está `SKIP_DB_CREATE_ALL=1`: ninguna tabla se crea sola y el auto-deploy sirve el código nuevo apenas se pushea. Si mergeas primero, `/adoptar` responde error en producción hasta que migres.

---

## 0. En qué estado está producción hoy (medido el 2026-08-16, solo lecturas)

Esto no es un supuesto: son `curl` de solo lectura contra `petfinder-col.com`, hechos al preparar este documento.

| Comprobación | Hoy | Qué significa |
|---|---|---|
| `GET /health` | `200 {"status":"ok"}` | La API está viva |
| `GET /api/pets` | `200 []` | La tabla `pets` está migrada (AD-01) y **no hay ni una mascota publicada todavía** |
| `GET /api/pets/adopciones` | `200 {"total":0,"recientes":[]}` | Cero adopciones registradas |
| `GET /api/pets/deck` | `422` con `int_parsing` sobre `pet_id` | La ruta del deck **no existe**: hoy `deck` lo captura `GET /api/pets/{pet_id}` |
| `GET /api/solicitudes` | `404 {"detail":"Not Found"}` | El router de solicitudes no está desplegado |
| `GET /api/users/1/home-profile` | `404 {"detail":"Not Found"}` | Idem, perfil de hogar |
| `GET /api/users/1/favorites` | `404 {"detail":"Not Found"}` | Idem, favoritos |
| `/adoptar/mascota/1` con user-agent de WhatsApp | `200` con el `index.html` estático y og tags genéricos | El rewrite de bots de AD-08 **no está**. El de reportes sí: `/reporte/1` con el mismo user-agent llega a la API (`404 "El reporte 1 no existe"`) |
| Bundle `/assets/index-CtFTkjan.js` | contiene `"Dar en adopción"`, **no** contiene `"Mis favoritas"` ni `"mascotas rescatadas que buscan hogar"` | AD-02 está desplegado; AD-03…AD-08 no |

**Consecuencia práctica**: el catálogo de adopción en producción está vacío. Cualquier mascota que publiques durante la prueba de la sección 6 será la única, y se verá.

---

## 1. Antes de tocar producción (5 minutos, sin riesgo)

```bash
git fetch origin && git checkout feat/adoptar && git pull
bash init.sh
```

Debe imprimir **`Todo en verde.`** y salir 0, con **738 tests de Python + 487 de web**. La línea base al abrir el módulo era 174 + 148.

Y el build de producción, que es lo único que typechequea el frontend (`init.sh` corre `oxlint` pero **no** `tsc -b`):

```bash
cd src/web && npm run build     # tsc -b + vite build, debe salir 0
```

Dos cosas que puedes dar por comprobadas porque son un comando, no una promesa:

```bash
# Cero dependencias nuevas en todo el módulo: sin salida.
git diff origin/main...feat/adoptar -- src/web/package.json src/web/package-lock.json requirements.txt pyproject.toml

# Cero variables de entorno nuevas: sin salida.
git diff origin/main...feat/adoptar -- src/api api | grep "^[+-].*os\.environ"
```

---

## 2. Las cuatro migraciones, una por una

Cada archivo es **puramente aditivo**: `create table if not exists`, índices, una constraint y `enable row level security`. Ninguno lleva `drop`, `truncate`, `delete` ni `alter` sobre tablas existentes — solo las referencian por clave foránea. Ninguno puede modificar ni borrar una fila que ya exista: tus reportes importados y tus organizaciones no se tocan. Y como llevan `if not exists`, re-ejecutar uno no rompe nada.

Que no son una transcripción a ojo del modelo lo garantizan los cuatro tests anti-drift (`tests/api/test_migracion_{pets,swipes,matches,favorites}.py`), que comparan cada `.sql` contra su `__table__` columna a columna y exigen que viajen el RLS y las constraints **con su nombre**. El revisor de AD-07 los verificó rompiendo el SQL de ocho formas distintas: ocho rojos.

### 2.1 — `AD-03-swipes.sql`

Crea `public.swipes` (5 columnas), 2 índices, `uq_swipe_user_pet` y RLS. Es el registro de "me interesa / ahora no" del deck.

```sql
select column_name, data_type, is_nullable from information_schema.columns
 where table_schema = 'public' and table_name = 'swipes' order by ordinal_position;
```

### 2.2 — `AD-03-home-profiles.sql`

Crea `public.home_profiles` (13 columnas, **PK = `user_id`**, sin `id` propio) y RLS. Es el cuestionario de hogar: la fila existiendo *es* la señal de "cuestionario completo".

```sql
select column_name, data_type, is_nullable from information_schema.columns
 where table_schema = 'public' and table_name = 'home_profiles' order by ordinal_position;
```

`presupuesto_mensual_cop` tiene que salir **nullable**. Si sale `NOT NULL`, cada guardado sin ese dato fallará: pedir un presupuesto mensual en plena emergencia añade fricción y por eso es opcional.

### 2.3 — `AD-05-matches.sql`

Crea `public.matches` (9 columnas) — las **solicitudes de adopción**; conserva el nombre `matches` porque es el del ADR 0002 —, 2 índices, `uq_match_user_pet` y RLS.

```sql
select column_name, data_type, is_nullable from information_schema.columns
 where table_schema = 'public' and table_name = 'matches' order by ordinal_position;
```

`mensaje`, `telefono_contacto`, `motivo_descarte` y `actualizado_en` tienen que salir **nullable**. Un `NOT NULL` de más aquí rompe **todo** swipe-derecha que no venga con mensaje, que es la mayoría.

### 2.4 — `AD-07-favorites.sql`

Crea `public.favorites` (4 columnas), 2 índices, `uq_favorite_user_pet` y RLS. Es el "guardar para después".

```sql
select column_name, data_type, is_nullable from information_schema.columns
 where table_schema = 'public' and table_name = 'favorites' order by ordinal_position;
```

---

## 3. La verificación conjunta (antes de mergear)

**1. Las cinco tablas del módulo, con RLS.** Cinco filas, todas con `rowsecurity = t`:

```sql
select tablename, rowsecurity
  from pg_tables
 where schemaname = 'public'
   and tablename in ('pets', 'swipes', 'home_profiles', 'matches', 'favorites')
 order by tablename;
```

**2. El CHECK de AD-01 sigue vivo.** Es lo que garantiza que una mascota cuelgue de una organización **o** de un rescatista, nunca de ambos ni de ninguno:

```sql
select conname
  from pg_constraint
 where conrelid = 'public.pets'::regclass
   and conname = 'ck_pets_publicador_exclusivo';
```

**3. Los tres `UNIQUE` nuevos.** Tres filas:

```sql
select conname, conrelid::regclass as tabla
  from pg_constraint
 where contype = 'u'
   and conname in ('uq_swipe_user_pet', 'uq_match_user_pet', 'uq_favorite_user_pet')
 order by conname;
```

No son cosméticos: son la **idempotencia real** de las tres escrituras del módulo. En serverless dos requests del mismo dedo corren de verdad a la vez y los dos pueden ver vacío su `select` previo; sin el `UNIQUE`, un doble toque crea dos filas.

Si falta algo, se arregla con otro `alter` aditivo. **Nunca se recrea la tabla.**

---

## 4. Por qué el orden importa, y qué pasa si se salta

**El orden es el del módulo, no una cadena de dependencias.** Conviene que lo sepas para no asustarte si algo sale a destiempo:

- Las cuatro tablas solo dependen de `public.users` y de `public.pets`, **que ya existen**. Ninguna referencia a otra de la cola.
- `favorites` en particular **no depende técnicamente de las tres anteriores** (medido por el implementador de AD-07: su única FK externa es a `public.pets`).
- Contra una base **sin** `pets`, en cambio, los tres `create table` con `pet_id` fallan por la clave foránea y no crean nada. En producción esa condición ya está satisfecha; en una base nueva (staging o una copia local en Postgres) habría que correr antes `AD-01-pets.sql`.

Entonces, ¿por qué respetar el orden? Porque **es el orden en que el código las necesita** si la ventana se interrumpe a la mitad: el deck consulta `home_profiles` en cuanto alguien manda `adoptante_id`, y el swipe-derecha escribe en `swipes` y en `matches` **en el mismo request**. Ejecutadas en orden, una interrupción deja la base en un estado que se parece a "el módulo hasta la feature N". En desorden, deja un estado mixto que hay que reconstruir leyendo `information_schema`.

**Qué pasa si mergeas antes de migrar** (el error caro):

- **Cae el módulo entero, no "una pantalla nueva"**. Los modelos declaran las columnas y SQLAlchemy emite el `SELECT` completo, así que toda petición que toque una tabla ausente responde 500: catálogo con `adoptante_id`, ficha, deck, swipe, solicitudes, perfil de hogar y favoritos.
- **Los flujos de emergencia no dependen de esta ventana**, y eso sí está medido: `grep -rl "Swipe\|Match\|Favorite\|HomeProfile" src/api/reencuentro_api/` no devuelve `routers/reports.py` ni `routers/organizaciones.py`. `/reportes`, `/mapa` y `/ayudar` seguirían en pie.
- ⚠️ **Ojo con el matiz de `GET /api/pets`**: anónimo no toca `favorites` y sobreviviría; **con `adoptante_id`** (que es como lo llama el catálogo de cualquiera que tenga cuenta) sí la consulta, y ahí revienta.
- La regla no se relaja aunque hoy el radio sea menor: cuando lo que falta es una **columna** sobre una tabla existente (features 15 y 24), cae **todo** lo que lea esa tabla. Es el escenario que dejó escrita la regla en `memory/memory.md` (2026-08-12).

---

## 5. Mergear y comprobar que el deploy existió de verdad

Con las cuatro tablas creadas y verificadas, mergea `feat/adoptar`. Después:

```bash
curl -s https://petfinder-col.com/health                                  # {"status":"ok"}
curl -s https://petfinder-col.com/api/pets | head                         # JSON, no error
curl -s https://petfinder-col.com/api/pets/deck | head                    # 200 con lista, ya NO el 422 de int_parsing
curl -s -o /dev/null -w '%{http_code}\n' https://petfinder-col.com/api/solicitudes   # 422 (el guard de "uno de tres filtros"), ya no 404
curl -s "https://petfinder-col.com/api/users/1/favorites?solicitante_id=1"          # detail EN ESPAÑOL, ya no {"detail":"Not Found"}
curl -s "https://petfinder-col.com/api/users/1/home-profile?solicitante_id=1"       # idem: español = la ruta existe
curl -s -A "WhatsApp/2.23" https://petfinder-col.com/adoptar/mascota/1 | head       # JSON 404 en español o el HTML con og propios, ya no el index.html genérico
```

**Cada uno de esos valores "antes" está medido hoy** (sección 0), así que el cambio de respuesta es la prueba de que el deploy trajo el código nuevo, no una impresión.

En los dos de `users/1`, lo que discrimina es **el idioma del `detail`**, no el status: hoy responden `{"detail":"Not Found"}` (la ruta no existe); con el código nuevo responderán en español (`"El usuario 1 no existe"` o `"Todavía no completaste el perfil de hogar de tu cuenta"`). Dato medido hoy y que sorprende: **en producción no hay ningún usuario con `id = 1`** (`GET /api/users/1` → `404 {"detail":"El usuario 1 no existe"}`), pese a que varios comentarios del repo dan por hecho que el `DEMO_USER_ID = 1` es "una persona real en producción". Si vas a probar con otro id, cámbialo en los dos `curl`.

### El poll del bundle por string marcador

Los `curl` de arriba prueban la API. El frontend se comprueba buscando en el bundle servido un string que **hoy no existe** — el enlace de la landing que añadió AD-08:

```bash
until ASSET=$(curl -s https://petfinder-col.com/ | grep -o '/assets/[A-Za-z0-9._-]*\.js' | head -1); \
      curl -s "https://petfinder-col.com$ASSET" | grep -q "mascotas rescatadas que buscan hogar"; do \
  echo "esperando el deploy…"; sleep 20; \
done; echo "desplegado"
```

Verificado hoy contra producción: el bundle actual (`/assets/index-CtFTkjan.js`) **no** contiene ese texto, así que el `grep` solo puede pasar con el código nuevo. `"Mis favoritas"` sirve igual de marcador (también ausente hoy) si prefieres apuntar a AD-07.

⚠️ **Verifica que el deployment existió de verdad, no lo des por hecho.** El auto-deploy de `main` **ya falló en silencio una vez**: durante días los pushes a `main` no creaban ningún deployment (ni siquiera "Canceled"), mientras los previews de rama sí. Está documentado en `memory/memory.md` (2026-08-12) y se resolvió **reconectando la GitHub App** en Vercel → Settings → Git; el workaround mientras tanto es Deployments → "…" → Create Deployment → `main` → Deploy to Production. Si el poll de arriba lleva varios minutos sin cambiar, es esto y no una caché.

---

## 6. El recorrido manual en producción (cierra el acceptance 2)

El acceptance pide *"el flujo completo funciona en producción con un caso real de prueba, documentado con evidencia en `progress/`"*. Recorrido sugerido, con dos cuentas (una publica, otra adopta) — recuerda que **el catálogo de producción está vacío hoy**, así que lo que publiques será lo único visible:

| # | Qué | Dónde | Qué deberías ver |
|---|---|---|---|
| 1 | Nav y landing | `/` | "Adoptar" como octavo enlace de la nav, **detrás** de la emergencia, y el enlace de texto sin borde en la landing |
| 2 | Publicar | `/adoptar/publicar` (cuenta A) | La mascota aparece en `/adoptar` con su foto |
| 3 | Compartir | ficha de esa mascota | El botón de compartir; pegar la URL en WhatsApp debe mostrar **foto y nombre**, no el link pelado |
| 4 | Perfil de hogar | `/adoptar/mi-hogar` (cuenta B) | El cuestionario guarda y al volver al deck aparece el `% afín` con sus razones en texto |
| 5 | Deck | `/adoptar/descubrir` (cuenta B) | Una carta a la vez; el corazón guarda **sin** sacar la carta |
| 6 | Solicitud | "Me interesa" (cuenta B) | La solicitud aparece en `/adoptar/mis-solicitudes` |
| 7 | Contacto | `/adoptar/solicitud/:id` | El botón de WhatsApp con el mensaje precargado del estado — **basta con comprobar el enlace; no hace falta enviar el mensaje** |
| 8 | Gestión | cuenta A | Agendar visita / pedir información / aprobar, y que el estado cambie de los dos lados |
| 9 | Favoritos | `/adoptar/mis-favoritas` (cuenta B) | La mascota guardada, y quitarla la saca de la lista |
| 10 | Móvil | cualquiera a 360px | Los filtros arrancan plegados y no hay scroll horizontal |

### La limpieza: por la API, nunca por SQL — y hay un tope que tienes que decidir antes de empezar

Regla del repo: los datos de prueba se borran **por la API**, jamás con un `delete from` en el SQL Editor. Un `delete` a mano contra una base con datos reales de gente que perdió a su mascota es exactamente el riesgo que estas guías existen para no correr.

Lo que la API de hoy sí puede deshacer:

```bash
# quitar un favorito
curl -X DELETE "https://petfinder-col.com/api/users/<ID_B>/favorites/<ID_PET>"

# despublicar la mascota de prueba (solo quien la publicó)
curl -X DELETE "https://petfinder-col.com/api/pets/<ID_PET>?user_id=<ID_A>"
```

⚠️ **Lo que la API de hoy NO puede deshacer, y conviene saberlo antes de swipear:**

- **No hay endpoint para borrar un swipe ni una solicitud.** `routers/swipes.py` solo expone `POST`; `routers/solicitudes.py` expone `GET` y las cuatro acciones, ninguna destructiva.
- Y como `swipes.pet_id` y `matches.pet_id` son claves foráneas **sin `ON DELETE`** (comprobado: `grep -i "on delete" migrations/*.sql` no devuelve nada), en Postgres el `DELETE` de la mascota que ya tiene un swipe o una solicitud **debería fallar por integridad referencial**, y `despublicar_mascota` no lo contempla: borra la fila directamente.
  **Esto está predicho por el esquema, no medido.** No hay Postgres en este working tree y **SQLite no fuerza las claves foráneas**, así que la suite no puede verlo — el mismo género de trampa que ya documenta `memory/memory.md` (2026-08-15).
- Tampoco hay `DELETE` de usuarios: la cuenta de prueba se queda.

**Decide antes de empezar el paso 5**, porque después no hay vuelta atrás por la API:

1. **Recorrido en dos mascotas**: una para publicar/compartir/editar/despublicar (se borra limpia, 204) y otra —la del deck— asumiendo que sus filas se quedan. Es lo menos malo con la API de hoy.
2. **Dejarlo escrito**: marcar la mascota de prueba como `adoptado` por la API la saca del catálogo público, pero **suma +1 al contador de adopciones logradas**, que hoy está en 0 y se ve en `/adoptar`. Un final feliz falso en un producto cuya métrica es la esperanza no es un detalle cosmético.
3. **Autorizar explícitamente un borrado por SQL** de esas filas concretas, sabiendo que contradice la regla de arriba (`delete from matches/swipes where pet_id = X`, y luego la mascota). Es tu llamada, no la del agente.

La cuarta salida —que `DELETE /api/pets/{id}` limpie sus filas hijas o responda 409 como hace `eliminar_reporte` con el puente— **es código nuevo y no entra en AD-09**: queda anotada para que el líder decida si es una feature aparte.

---

## 7. Qué NO entra en este despliegue

- **Apadrinamiento**: recortado por decisión de producto. Sin pasarela de pagos solo registraría una intención, y `Organizacion.como_donar` ya la cubre mejor. No existe tabla `sponsorships` ni la va a haber en este release.
- **Chat interno**: no vuelve. El `ConnectionManager` en memoria del ADR 0004 no funciona **ni una vez** en el serverless de Vercel; el ADR 0013 lo supera y decide WhatsApp directo. No existe tabla `mensajes`.
- **Búsqueda por descripción sobre mascotas en adopción**: `/buscar` sigue siendo solo de reportes. Está anotado como backlog en `docs/product-research.md` §11, fuera de alcance a propósito.
- **Filtro por distancia en el catálogo**: las mascotas nacen sin `lat`/`lng` (el formulario no pide pin), así que ese filtro nacería muerto. Anotado desde la revisión de AD-01+AD-02.

---

## 8. Deuda conocida que viaja con este release

| Qué | Dónde | Gravedad |
|---|---|---|
| La UI es la única barrera de autoría (consecuencia del ADR 0005: sin contraseñas) | `progress/current.md` | Merece ADR propio; no lo abre este módulo |
| `init.sh` no corre `tsc -b`: la exhaustividad de tipos la aplica el build de Vercel | `memory/memory.md` (2026-08-16) | Baja; se compensa corriendo `npm run build` antes de mergear |
| `ya_solicitada` sigue en `false` en toda la app (deuda de AD-05) | docstring de `obtener_mascota` | Baja, cosmética |
| Filtros inalcanzables al cruzar el breakpoint en escritorio (encoger < 1024px, plegar, ensanchar) | `progress/current.md` (AD-08 paso 7) | Baja; no ocurre en un móvil real |
| `qrcode` y `react-easy-crop` entraron sin ADR | `CHECKPOINTS.md`, `docs/architecture.md` §1 | Deuda documental, ya anotada |
| Prettier local (3.9.6) ≠ el del pre-commit (v3.1.0) | ensucia diffs ajenos | Un `chore:` de una línea |

---

**Si algo de esto no te cuadra, dilo antes de darle a Run.** El módulo no tiene prisa; la base de datos de producción sí tiene reportes reales de gente buscando a su mascota.
