# 0006 — Persistencia en Supabase: Postgres + Storage (API sin estado)

## Estado
Aceptado.

## Contexto

El ADR 0005 §7 dejó el despliegue con SQLite + fotos en un disco persistente de Render, anotando la migración a Postgres/S3 como decisión futura. Al preparar el deploy real, el usuario pidió analizar opciones de persistencia integradas con Vercel y de fácil uso. Hallazgos: Vercel Postgres fue descontinuado (2025) y su reemplazo oficial es el **Vercel Marketplace** (Neon, Supabase, etc.); el disco de Render es pago y ata la API a un filesystem.

Opciones evaluadas: (A) Supabase — Postgres 500 MB + Storage 1 GB gratis en un solo proveedor, disponible en el Marketplace; (B) Neon + Cloudinary — dos cuentas; (C) mantener Render + disco. **El usuario eligió A.**

## Decisión

1. **Base de datos: Supabase Postgres.** El código ya leía `DATABASE_URL` del entorno; se añade `psycopg2-binary` y nada más — el modelo usa solo tipos portables (String/Float/Date/DateTime). En local sigue SQLite por defecto: cero cambios de comportamiento en dev y tests.
2. **Fotos: Supabase Storage** (bucket público `fotos`). `reencuentro_api/media.py` gana `supabase_configurado()` y `subir_a_supabase()` — un POST directo a la API REST de Storage con la `service_role` key (no se adopta el SDK supabase-py: el flujo es un solo request y `requests` ya era dependencia). Con `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` en el entorno, el endpoint de uploads y las fotos del seed suben al bucket y `foto_url` pasa a ser una URL pública absoluta; sin esas variables, todo va al filesystem local exactamente igual que antes. `mediaUrl()` del frontend deja pasar las URLs absolutas tal cual.
3. **API sin estado**: `render.yaml` pierde el disco — el servicio corre en el free tier de Render y cualquier redeploy es seguro. El montaje local `/media` se conserva para dev.
4. La config se lee **en el momento de la llamada** (no al importar) para que los tests la activen/desactiven con `monkeypatch.setenv`, y la subida usa `x-upsert: true` para que el seed sea re-ejecutable sin colisiones.

## Consecuencias

- Persistencia real gratis y gestionada (DB y fotos sobreviven cualquier redeploy); el único límite es el free tier (500 MB DB / 1 GB fotos), suficiente para la emergencia.
- El seed en producción (`drop_all` + `create_all` contra Postgres) se corre UNA vez desde la Shell de Render — re-correrlo borra reportes reales, advertido en `docs/deploy.md`.
- La `service_role` key vive solo en el backend (env var de Render), nunca en el frontend.
- El free tier de Render duerme tras inactividad (~30 s el primer request); si molesta, subir de plan o mover la API — la app ya no depende del filesystem, así que es portable.
