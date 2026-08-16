-- AD-05 — solicitudes de adopción. Aditivo: no toca ninguna tabla existente.
--
-- Estado: ESCRITO, NO EJECUTADO. Se aplica en el SQL Editor de Supabase con
-- autorización explícita del dueño y ANTES del merge a `main` (en prod está
-- SKIP_DB_CREATE_ALL=1: nada se crea solo, y el auto-deploy es inmediato).
--
-- ⚠️ ORDEN DE DESPLIEGUE: **`AD-03-swipes.sql` y `AD-03-home-profiles.sql`
-- primero** (a esta fecha siguen sin ejecutar, igual que este archivo), y este
-- después. Dos motivos: `matches.pet_id` referencia `public.pets` —que crea
-- `AD-01-pets.sql`, ya aplicado— y, sobre todo, el swipe-derecha inserta la fila
-- de `matches` en el **mismo request** que la de `swipes`. Si el código llega a
-- prod y falta cualquiera de las dos tablas, `POST /api/swipes` responde 500 y
-- no falla una tarjeta: falla el deck entero.
--
-- La tabla conserva el nombre `matches` porque es el de las migraciones del
-- backlog y el del ADR 0002; en la API y en el producto se llama siempre
-- **"solicitud"**.
--
-- Tipos elegidos para coincidir con lo que emite `create_all` de SQLAlchemy:
-- `serial` (no `identity`) y `timestamp without time zone`. Ese último no es un
-- descuido: es lo que obliga a `calcular_etiqueta_solicitud` a normalizar el
-- `creado_en` naive también en Postgres. Sin `DEFAULT` de DB a propósito: los
-- defaults los pone Python (modelo/schemas), empezando por `estado`; duplicarlos
-- aquí crearía dos fuentes de verdad que se separan con el tiempo.
--
-- ⚠️ `user_id` es el ADOPTANTE que pidió la mascota, **no** quien la publicó
-- (ese es `pets.user_id`). Las dos son claves foráneas a `public.users`, así que
-- ninguna base de datos avisa si se cruzan.
--
-- No hay `shelter_id` ni `organizacion_id`: el publicador se resuelve por join a
-- `pets`, para no repetir aquí el XOR de `ck_pets_publicador_exclusivo` ni
-- quedar rancio si una mascota cambia de dueño. Tampoco hay columna de afinidad
-- (ADR 0003: se calcula al vuelo).
--
-- `mensaje`, `telefono_contacto`, `motivo_descarte` y `actualizado_en` van
-- **nullable**: los tres primeros porque el adoptante puede swipear sin escribir
-- nada y el motivo solo existe si se descartó; el último porque es nulo hasta
-- que el publicador ejecuta su primera acción. Crear cualquiera `not null`
-- rompería el swipe-derecha en producción.
--
-- `uq_match_user_pet` es la garantía real de la idempotencia que pide el
-- acceptance ("una solicitud por user+pet"): en serverless dos requests del
-- mismo dedo corren de verdad a la vez y los dos pueden ver vacío el select
-- previo.
create table if not exists public.matches (
    id                serial primary key,
    user_id           integer     not null references public.users (id),
    pet_id            integer     not null references public.pets (id),
    estado            varchar(20) not null,
    mensaje           varchar(500),
    telefono_contacto varchar(20),
    motivo_descarte   varchar(500),
    creado_en         timestamp without time zone not null,
    actualizado_en    timestamp without time zone,
    constraint uq_match_user_pet unique (user_id, pet_id)
);
create index if not exists ix_matches_user_id on public.matches (user_id);
create index if not exists ix_matches_pet_id  on public.matches (pet_id);
alter table public.matches enable row level security;
