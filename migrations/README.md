# migrations/

El SQL que se ejecutó **de verdad** contra la base de producción (Supabase Postgres), versionado para que se pueda auditar después qué esquema tiene prod y por qué (la auditoría de AD-09 depende de que esto esté completo).

**No es un runner y no hay Alembic.** Nadie aplica estos archivos automáticamente: son documentación ejecutable a mano en el **SQL Editor de Supabase**, con **autorización explícita del dueño** y siempre **ANTES del merge a `main`** — en producción está `SKIP_DB_CREATE_ALL=1`, así que ninguna tabla ni columna se crea sola en el deploy, y el auto-deploy sirve el código nuevo apenas se pushea (si el código consulta algo que aún no existe, cae la API entera, no solo la pantalla nueva). Introducir un runner exige un ADR nuevo.

Reglas: solo SQL **aditivo** (`create table if not exists`, `alter table ... add column if not exists`, columnas nuevas nullable o con default). Nunca `drop`, `truncate`, `drop column` ni renombres — producción tiene datos reales de gente que perdió a su mascota. Toda tabla nueva lleva `enable row level security`. Los `CHECK`/`UNIQUE` del modelo hay que transcribirlos a mano con el **mismo nombre**: es lo que más se olvida, y por eso cada migración tiene su test anti-drift en `tests/api/` (para `pets`, `tests/api/test_migracion_pets.py`).

Convención de nombre: `AD-0N-<tabla>.sql` (una por feature que cambia esquema).

## Verificación post-migración

Contra la DB de prod, después de ejecutar el `.sql` y antes de mergear:

```sql
-- la tabla existe y tiene RLS
select tablename, rowsecurity from pg_tables
 where schemaname = 'public' and tablename = 'pets';

-- las columnas llegaron con los tipos esperados
select column_name, data_type, is_nullable from information_schema.columns
 where table_schema = 'public' and table_name = 'pets' order by ordinal_position;

-- las constraints también (lo que más se olvida al transcribir a mano)
select conname from pg_constraint where conrelid = 'public.pets'::regclass;
```

Si falta una columna o una constraint, se arregla con otro `alter` aditivo — no se recrea la tabla.

## Índice

| Archivo | Feature | Qué hace | Estado |
| --- | --- | --- | --- |
| `AD-01-pets.sql` | AD-01 | Crea `public.pets` (+ 4 índices, `ck_pets_publicador_exclusivo`, RLS) | ✅ **EJECUTADA en producción** (2026-08-15, por el dueño del repo, junto con el merge del PR #6). Verificado: `GET /api/pets` responde 200 en petfinder-col.com |
| `AD-03-swipes.sql` | AD-03 | Crea `public.swipes` (+ 2 índices, `uq_swipe_user_pet`, RLS) | Escrito, **pendiente de ejecutar** — va **después** de `AD-01-pets.sql`: su `pet_id` referencia `public.pets` |
| `AD-03-home-profiles.sql` | AD-03 | Crea `public.home_profiles` (PK = `user_id`, RLS) | Escrito, **pendiente de ejecutar** — la tabla se adelanta de AD-04 porque el deck la consulta; **AD-04 no trae migración** |
| `AD-05-matches.sql` | AD-05 | Crea `public.matches` — las solicitudes de adopción — (+ 2 índices, `uq_match_user_pet`, RLS) | Escrito, **pendiente de ejecutar** — va **después** de los dos de AD-03: el swipe-derecha inserta en `swipes` y en `matches` en el mismo request |
| `AD-07-favorites.sql` | AD-07 | Crea `public.favorites` — el "guardar para después" — (+ 2 índices, `uq_favorite_user_pet`, RLS) | Escrito, **pendiente de ejecutar** — va **después** de `AD-05-matches.sql`, cuarta y última de la cola; su `pet_id` referencia `public.pets`, que ya existe en producción |

Anti-drift de las tablas de AD-03, AD-05 y AD-07: `tests/api/test_migracion_swipes.py`, `tests/api/test_migracion_matches.py` y `tests/api/test_migracion_favorites.py` (el parser de `create table` que comparten los cuatro anti-drift vive en `tests/api/soporte_migraciones.py`).

⚠️ **La cabecera de `AD-01-pets.sql` quedó rancia**: sigue diciendo "ESCRITO, NO EJECUTADO" aunque se ejecutó el 2026-08-15. **El estado real es el de la tabla de arriba**, no el del comentario. Re-ejecutar ese archivo sería inocuo (`create table if not exists`), pero conviene arreglar la línea; no se toca aquí para no meter un cambio de contenido en un `.sql` ya aplicado dentro de un trabajo que es solo de documentación.

## Cierre del módulo (AD-09)

Auditoría preparada para la ventana de migración del módulo de adopción. **Nada de esta sección se ha ejecutado**: requiere autorización explícita del dueño y acceso al SQL Editor de Supabase. La guía operativa completa, para quien va a darle a Run, es **`docs/despliegue-modulo-adopcion.md`**.

### El orden obligatorio, y por qué

```
1. AD-03-swipes.sql
2. AD-03-home-profiles.sql
3. AD-05-matches.sql
4. AD-07-favorites.sql
```

`pets` ya está en producción desde AD-01 (2026-08-15), así que las cuatro pendientes son las de arriba y ninguna otra.

**El orden es el del módulo, no una cadena de dependencias.** La única dependencia técnica real de las cuatro es `public.pets`, que ya existe: las cuatro tablas cuelgan de `users` y/o de `pets`, y **ninguna referencia a otra de la cola**. Medido y anotado por el implementador de AD-07: `favorites` tiene como única FK externa `public.pets` (más `users`), así que **no depende técnicamente de las tres anteriores** — contra una base con `pets` se crearía sola sin problema.

Se respeta igual, por dos razones que no son técnicas y sí operativas:

1. **Es el orden en que el código las necesita cuando el deploy llegue.** El swipe-derecha de AD-05 inserta en `swipes` y en `matches` **en el mismo request**; el deck de AD-03 consulta `home_profiles` en cuanto alguien manda `adoptante_id`. Si la ventana se interrumpe a la mitad, este orden deja la base en el estado más parecido a "el módulo hasta la feature N", no en un estado mixto raro.
2. **Quien ejecuta la ventana no debería tener que decidir cuáles se puede saltar.** Una lista numerada de cuatro sentencias que se corren en orden no tiene ambigüedad; una con notas al pie de "esta se puede adelantar" sí.

Y una que sí es técnica: contra una base **sin** `public.pets` los tres `create table` con `pet_id` fallan por la clave foránea y no crean nada. Esa condición ya está satisfecha en producción, pero no en una base nueva (staging, una copia local en Postgres): allí `AD-01-pets.sql` va primero.

### Verificación post-migración (pegar tal cual en el SQL Editor)

Las tres consultas se corren **después de las cuatro** y **antes** del merge a `main`.

**1. Las cinco tablas del módulo existen y tienen RLS.** Tienen que salir **cinco filas**, todas con `rowsecurity = t`:

```sql
select tablename, rowsecurity
  from pg_tables
 where schemaname = 'public'
   and tablename in ('pets', 'swipes', 'home_profiles', 'matches', 'favorites')
 order by tablename;
```

**2. El CHECK de AD-01 sigue ahí.** Es el que garantiza que una mascota cuelgue de una organización **o** de un rescatista, nunca de ambos ni de ninguno. Si desapareciera, dev y producción divergirían en silencio:

```sql
select conname
  from pg_constraint
 where conrelid = 'public.pets'::regclass
   and conname = 'ck_pets_publicador_exclusivo';
```

**3. Los tres `UNIQUE` nuevos, con su nombre exacto.** Tienen que salir **tres filas**. Son la garantía real de idempotencia de las tres escrituras del módulo (swipe, solicitud, favorito): en serverless dos requests del mismo dedo corren de verdad a la vez y los dos pueden ver vacío su `select` previo, así que la garantía vive en la base, no en el código:

```sql
select conname, conrelid::regclass as tabla
  from pg_constraint
 where contype = 'u'
   and conname in ('uq_swipe_user_pet', 'uq_match_user_pet', 'uq_favorite_user_pet')
 order by conname;
```

Si falta una columna, una constraint o el RLS, se arregla con otro `alter` **aditivo** — no se recrea la tabla.

### El aviso que más importa

**Con `SKIP_DB_CREATE_ALL=1` en producción no hay red de seguridad.** Ninguna tabla ni columna se crea sola en el deploy, y el auto-deploy sirve el código nuevo apenas se pushea a `main`.

Si el código llega antes que las tablas, **lo que cae no es "una pantalla nueva": es el módulo entero**. Los modelos declaran las columnas y SQLAlchemy emite el `SELECT` completo, así que **toda** petición que toque una tabla ausente responde 500, no un vacío elegante: el catálogo con `adoptante_id`, la ficha, el deck, el swipe, las solicitudes, el perfil de hogar y los favoritos. `/adoptar` queda inservible de punta a punta mientras la ventana no se cierre.

**Precisión honesta sobre el radio de daño, porque el matiz cambia la urgencia y no al revés:**

- **Tabla nueva que falta** (este caso, las cuatro): revienta todo lo que la consulte. Medido con `grep -rl "Swipe\|Match\|Favorite\|HomeProfile" src/api/reencuentro_api/`: los cuatro modelos solo se nombran en `models/`, `schemas/swipe.py`, `services/{afinidad,solicitudes}.py` y los routers `pets`, `swipes`, `solicitudes`, `favoritos` y `users` — **`routers/reports.py` y `routers/organizaciones.py` no aparecen**, así que los flujos de emergencia (`/reportes`, `/mapa`, `/ayudar`) no dependen de esta ventana. Ojo con el matiz de `routers/pets.py`: `GET /api/pets` **anónimo** no toca `favorites` (sin `adoptante_id`, `_ids_favoritos` devuelve `set()` sin ir a la base), pero **con** `adoptante_id` sí, y ahí revienta.
- **Columna nueva que falta sobre una tabla existente** (el caso de las features 15 y 24, no el de hoy): ahí sí **cae todo lo que lea esa tabla**, porque el `SELECT` lo emite el modelo con la columna dentro. Ese es el escenario que dejó la regla "migrar antes de mergear" escrita en `memory/memory.md` (2026-08-12), y por eso la regla no se relaja aunque hoy el radio sea menor.

Por eso el orden es siempre **migrar → verificar (las tres consultas de arriba) → mergear**, nunca al revés.
