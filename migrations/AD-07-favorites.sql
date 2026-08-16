-- AD-07 — favoritos ("guardar para después"). Aditivo: no toca ninguna tabla
-- existente.
--
-- Estado: ESCRITO, NO EJECUTADO. Se aplica en el SQL Editor de Supabase con
-- autorización explícita del dueño y ANTES del merge a `main` (en prod está
-- SKIP_DB_CREATE_ALL=1: nada se crea solo, y el auto-deploy es inmediato).
--
-- ⚠️ ORDEN DE DESPLIEGUE — este archivo es el **cuarto** de una cola de la que
-- todavía no se ha ejecutado ninguno:
--   1. `AD-03-swipes.sql`
--   2. `AD-03-home-profiles.sql`
--   3. `AD-05-matches.sql`
--   4. `AD-07-favorites.sql`  ← este
-- `favorites.pet_id` referencia `public.pets`, que ya existe en producción desde
-- `AD-01-pets.sql` (ejecutada el 2026-08-15), así que esta tabla no depende de
-- las tres anteriores para crearse; el orden se respeta igual porque es el del
-- despliegue del módulo entero y porque quien ejecute la ventana no debería
-- tener que decidir cuáles saltarse. Contra una base sin `public.pets` este
-- `create table` falla por la clave foránea y no crea nada.
--
-- Tipos elegidos para coincidir con lo que emite `create_all` de SQLAlchemy:
-- `serial` (no `identity`) y `timestamp without time zone`. Sin `DEFAULT` de DB
-- a propósito: el `creado_en` lo pone Python (`datetime.now(timezone.utc)` en el
-- modelo); un `default now()` aquí crearía dos fuentes de verdad para la misma
-- fecha, que se separan en cuanto una de las dos cambie de criterio.
--
-- ⚠️ `user_id` es el ADOPTANTE que MIRA y guarda la mascota, **no** quien la
-- publicó (ese es `pets.user_id`). Las dos son claves foráneas a `public.users`,
-- así que ninguna base de datos avisa si se cruzan.
--
-- `uq_favorite_user_pet` es **nuevo** respecto a `adopta-v1`, que resolvía la
-- idempotencia solo con un select previo en el router. Mismo criterio que
-- `uq_suscripcion_report_email`: con Postgres y concurrencia real, dos toques al
-- corazón corren de verdad a la vez y los dos pueden ver ese select vacío — la
-- garantía va en la base de datos, no en el código.
--
-- Sin columna de estado: la existencia de la fila es la señal, y quitar un
-- favorito borra su fila (única escritura destructiva del módulo, sobre datos
-- propios de quien la pide, y jamás desde este archivo).
create table if not exists public.favorites (
    id        serial primary key,
    user_id   integer not null references public.users (id),
    pet_id    integer not null references public.pets (id),
    creado_en timestamp without time zone not null,
    constraint uq_favorite_user_pet unique (user_id, pet_id)
);
create index if not exists ix_favorites_user_id on public.favorites (user_id);
create index if not exists ix_favorites_pet_id  on public.favorites (pet_id);
alter table public.favorites enable row level security;
