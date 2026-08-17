-- AD-03 — perfil de hogar del adoptante. Aditivo: no toca ninguna tabla
-- existente.
--
-- Estado: ESCRITO, NO EJECUTADO. Se aplica en el SQL Editor de Supabase con
-- autorización explícita del dueño y ANTES del merge a `main` (en prod está
-- SKIP_DB_CREATE_ALL=1: nada se crea solo, y el auto-deploy es inmediato).
--
-- ⚠️ ORDEN DE DESPLIEGUE: **AD-01/AD-02 primero**, igual que el otro archivo de
-- esta ventana (`AD-03-swipes.sql`, que sí depende de `public.pets`). Esta tabla
-- solo referencia `public.users`, pero viaja con el mismo deploy: si el código
-- del deck llega a prod sin ella, `GET /api/pets/deck` responde 500 para
-- cualquiera que mande `adoptante_id` — no falla una tarjeta, falla la pantalla.
--
-- La tabla se adelanta de AD-04 a AD-03 por una razón de código:
-- `calcular_afinidad(pet, home)` no existe sin ella y el deck la consulta.
-- **AD-04 se queda sin migración propia** (solo schemas, endpoints y wizard).
--
-- Tipos elegidos para coincidir con lo que emite `create_all` de SQLAlchemy:
-- `json` (no `jsonb`). Sin `DEFAULT` de DB a propósito: los defaults los pone
-- Python (modelo/schemas); duplicarlos aquí crearía dos fuentes de verdad.
--
-- `user_id` es la **llave primaria**, sin `id` propio: hay como máximo un perfil
-- por persona y la fila existiendo *es* la señal de "cuestionario completo" (el
-- upsert de AD-04 se apoya en eso).
--
-- `presupuesto_mensual_cop` va **nullable** por decisión de producto: pedir un
-- presupuesto mensual en COP en plena emergencia añade fricción, y quien no lo
-- dé conserva el resto de su perfil (`services/afinidad.py` degrada a
-- solo-experiencia). Crearla `not null` haría fallar cada guardado sin ese dato.
create table if not exists public.home_profiles (
    user_id                 integer primary key references public.users (id),
    vivienda                varchar(40) not null,
    espacio_exterior        varchar(40) not null,
    personas_en_casa        integer     not null,
    tiene_ninos             boolean     not null,
    tiene_otros_perros      boolean     not null,
    tiene_otros_gatos       boolean     not null,
    horas_fuera_dia         integer     not null,
    experiencia_previa      varchar(40) not null,
    presupuesto_mensual_cop integer,
    preferencia_especies    json        not null,
    preferencia_tamanos     json        not null,
    preferencia_energia     varchar(20) not null
);
alter table public.home_profiles enable row level security;
