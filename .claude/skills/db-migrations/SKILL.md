---
name: db-migrations
description: Cambia el esquema de datos sin romper producción — local con create_all + seed, prod con SQL aditivo y RLS en Supabase antes del merge a main. Usar antes de tocar cualquier archivo en src/api/reencuentro_api/models/.
---

# db-migrations

## Cuándo usar
Al añadir o modificar una entidad del modelo de datos (`User`, `Report`, `Sighting`, `Organizacion`, `Necesidad`, `Suscripcion`, `ReportFoto`, `AvisoAyuda`, `RadarAviso`, `Pet`…), o cualquier columna nueva sobre una tabla que ya existe.

**Producción tiene datos reales** (reportes de gente que perdió a su mascota, incluidos los 204 importados del Drive de Cali). Nada de lo que se haga aquí puede borrarlos.

## Cómo — local y tests

El esquema no vive en ningún archivo de migración: sale de los modelos vía `Base.metadata.create_all`.

1. Cambia o crea el modelo en `src/api/reencuentro_api/models/`.
2. **Regístralo en `src/api/reencuentro_api/models/__init__.py`** (import + `__all__`) **y asegúrate de que su router lo importe**. Si nadie importa el módulo, la clase nunca se registra en `Base.metadata` y la tabla no se crea — sin error, solo ausencia.
3. **En cada archivo de test que use el modelo, impórtalo a nivel de módulo** (no dentro de la función). El fixture `db_session` de `tests/api/conftest.py` hace `create_all` con lo que haya registrado en ese instante: si el import ocurre tarde, aparece un `no such table` **intermitente**, que sale o no según el orden de colección de pytest.
4. `python3 scripts/seed.py` recrea los datos locales (`drop_all` + `create_all`, determinista y sin red). Es la forma de ver el esquema nuevo con datos.
5. Corre `pytest tests/api/` (o `bash init.sh`) para confirmar que las queries existentes siguen funcionando con el esquema nuevo.

## Cómo — producción (Supabase Postgres)

En prod está `SKIP_DB_CREATE_ALL=1`: **ninguna tabla ni columna se crea sola en el deploy**. Y el auto-deploy sirve el código nuevo apenas se pushea a `main`; si ese código consulta algo que no existe todavía en la DB, **la API entera falla**, no solo la pantalla nueva.

1. Escribe el SQL **aditivo** en `migrations/<FEATURE>-<slug>.sql`: solo `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (columnas nuevas siempre nullable o con default, para no romper las filas existentes). **Nunca `DROP`, `TRUNCATE`, `DROP COLUMN` ni renombres.**
2. Toda tabla nueva lleva `ALTER TABLE <tabla> ENABLE ROW LEVEL SECURITY;`, igual que el resto de las tablas de prod (el acceso real va por la service key del backend, no por el cliente).
3. Presenta el SQL al dueño y **espera autorización explícita**. Sin ese "sí", no se ejecuta nada contra prod.
4. Ejecútalo en el **SQL Editor de Supabase**, **ANTES del merge a `main`**. El orden es: migrar → verificar → recién ahí mergear/pushear.
5. Documenta el cambio en `changes.md` (qué tabla/columna, por qué, y que la migración ya se aplicó).

**`scripts/seed.py` JAMÁS se corre contra producción** — hace `drop_all` y se lleva por delante todos los datos reales. Regla dura, sin excepciones.

## Verificación post-migración

Contra la DB de prod, después de ejecutar el `.sql` y antes de mergear:

- La tabla existe y tiene RLS:
  ```sql
  select tablename, rowsecurity from pg_tables where schemaname = 'public' and tablename = '<tabla>';
  select column_name, data_type, is_nullable from information_schema.columns
   where table_schema = 'public' and table_name = '<tabla>' order by ordinal_position;
  ```
- Los `CHECK` y `UNIQUE` declarados en el modelo también llegaron (es lo que más se olvida al transcribir el modelo a SQL a mano):
  ```sql
  select conname, contype, pg_get_constraintdef(oid) from pg_constraint
   where conrelid = '<tabla>'::regclass;
  ```

Si falta una columna o una constraint, se arregla con otro `ALTER` aditivo — no se recrea la tabla.

## Qué no hacer

- **No borres `data/app.db` como "migración"** (lo decía la versión vieja de esta skill): el reflejo correcto es `python3 scripts/seed.py`, y ese reflejo aplicado a prod destruye datos reales.
- No introduzcas Alembic ni otro runner de migraciones sin un ADR nuevo. `migrations/` es **documentación auditable del SQL que se ejecutó a mano**, no un runner: nadie lo aplica automáticamente.
- No mergees a `main` con la migración pendiente "para probar en prod". El deploy es inmediato y la caída también.
- No cambies el tipo de una columna existente ni la hagas `NOT NULL` de golpe: eso no es aditivo. Si hace falta, es un plan aparte (columna nueva → backfill → dejar de leer la vieja) y se discute con el dueño.
