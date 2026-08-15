-- AD-01 — mascotas en adopción. Aditivo: no toca ninguna tabla existente.
--
-- Estado: ESCRITO, NO EJECUTADO. Se aplica en el SQL Editor de Supabase con
-- autorización explícita del dueño y ANTES del merge a `main` (en prod está
-- SKIP_DB_CREATE_ALL=1: nada se crea solo, y el auto-deploy es inmediato).
--
-- Tipos elegidos para coincidir con lo que emite `create_all` de SQLAlchemy:
-- `serial` (no `identity`), `json` (no `jsonb`) y `timestamp without time zone`.
-- Sin `DEFAULT` de DB a propósito: los defaults los pone Python (modelo/schemas);
-- duplicarlos aquí crearía dos fuentes de verdad que se separan con el tiempo.
-- `report_id` va desde ya (puente con reportes "encontrada" de AD-02) para no
-- migrar la misma tabla dos veces.
create table if not exists public.pets (
    id                serial primary key,
    organizacion_id   integer references public.organizaciones (id),
    user_id           integer references public.users (id),
    report_id         integer unique references public.reports (id),
    nombre            varchar(80)   not null,
    especie           varchar(20)   not null,
    raza              varchar(80),
    sexo              varchar(10)   not null,
    edad_meses        integer       not null,
    tamano            varchar(20)   not null,
    energia           varchar(20)   not null,
    fotos             json          not null,
    historia          varchar(2000) not null,
    tags              json          not null,
    esterilizado      boolean       not null,
    vacunas_al_dia    boolean       not null,
    microchip         boolean       not null,
    desparasitado     boolean       not null,
    apto_ninos        boolean       not null,
    apto_perros       boolean       not null,
    apto_gatos        boolean       not null,
    zona              varchar(40)   not null,
    ciudad_texto      varchar(80),
    barrio            varchar(80),
    lat               double precision,
    lng               double precision,
    telefono_contacto varchar(20),
    estado            varchar(20)   not null,
    publicado_en      timestamp without time zone not null,
    adoptado_en       timestamp without time zone,
    constraint ck_pets_publicador_exclusivo
        check ((organizacion_id is null) <> (user_id is null))
);
create index if not exists ix_pets_organizacion_id on public.pets (organizacion_id);
create index if not exists ix_pets_user_id         on public.pets (user_id);
create index if not exists ix_pets_zona            on public.pets (zona);
create index if not exists ix_pets_estado          on public.pets (estado);
alter table public.pets enable row level security;
