-- AD-03 — swipes del deck de descubrimiento. Aditivo: no toca ninguna tabla
-- existente.
--
-- Estado: ESCRITO, NO EJECUTADO. Se aplica en el SQL Editor de Supabase con
-- autorización explícita del dueño y ANTES del merge a `main` (en prod está
-- SKIP_DB_CREATE_ALL=1: nada se crea solo, y el auto-deploy es inmediato).
--
-- ⚠️ ORDEN DE DESPLIEGUE: **AD-01/AD-02 primero**. `swipes.pet_id` referencia
-- `public.pets`, que crea `AD-01-pets.sql` (AD-02 no trae migración propia):
-- ejecutar este archivo contra una base sin esa tabla falla por la clave foránea
-- y no crea nada. El otro archivo de esta misma ventana es
-- `AD-03-home-profiles.sql`; el orden entre esos dos es indistinto.
--
-- Tipos elegidos para coincidir con lo que emite `create_all` de SQLAlchemy:
-- `serial` (no `identity`) y `timestamp without time zone`. Sin `DEFAULT` de DB
-- a propósito: los defaults los pone Python (modelo/schemas); duplicarlos aquí
-- crearía dos fuentes de verdad que se separan con el tiempo.
--
-- ⚠️ `user_id` es el ADOPTANTE que mira el deck, **no** quien publicó la mascota
-- (ese es `pets.user_id`). Las dos son claves foráneas a `public.users`, así que
-- ninguna base de datos avisa si se cruzan.
--
-- `uq_swipe_user_pet` es la garantía real de la idempotencia de
-- `POST /api/swipes`: en serverless dos requests del mismo dedo corren de verdad
-- a la vez y los dos pueden ver vacío el select previo.
create table if not exists public.swipes (
    id        serial primary key,
    user_id   integer     not null references public.users (id),
    pet_id    integer     not null references public.pets (id),
    direccion varchar(10) not null,
    creado_en timestamp without time zone not null,
    constraint uq_swipe_user_pet unique (user_id, pet_id)
);
create index if not exists ix_swipes_user_id on public.swipes (user_id);
create index if not exists ix_swipes_pet_id  on public.swipes (pet_id);
alter table public.swipes enable row level security;
