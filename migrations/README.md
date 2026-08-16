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
| `AD-01-pets.sql` | AD-01 | Crea `public.pets` (+ 4 índices, `ck_pets_publicador_exclusivo`, RLS) | Escrito, **pendiente de ejecutar** con autorización del dueño |
| `AD-03-swipes.sql` | AD-03 | Crea `public.swipes` (+ 2 índices, `uq_swipe_user_pet`, RLS) | Escrito, **pendiente de ejecutar** — va **después** de `AD-01-pets.sql`: su `pet_id` referencia `public.pets` |
| `AD-03-home-profiles.sql` | AD-03 | Crea `public.home_profiles` (PK = `user_id`, RLS) | Escrito, **pendiente de ejecutar** — la tabla se adelanta de AD-04 porque el deck la consulta; **AD-04 no trae migración** |

Anti-drift de las dos tablas de AD-03: `tests/api/test_migracion_swipes.py` (el parser de `create table` que comparten los dos anti-drift vive en `tests/api/soporte_migraciones.py`).
