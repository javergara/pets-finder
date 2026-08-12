# Despliegue — Reencuentro

Arquitectura (ADR 0006): **frontend estático en Vercel** + **API FastAPI sin estado en Render (free tier)** + **persistencia en Supabase** (Postgres para la base de datos, Storage para las fotos). Todo el tier gratuito.

```
Navegante ──▶ Vercel (src/web, build de Vite)          ← auto-deploy con cada push a main
                 │  fetch a VITE_API_BASE_URL
                 ▼
              Render (src/api, uvicorn, SIN disco)     ← auto-deploy con cada push a main
                 ├─ DATABASE_URL ──▶ Supabase Postgres (500 MB gratis)
                 └─ fotos ──▶ Supabase Storage, bucket público "fotos" (1 GB gratis)
```

En dev local nada de esto aplica: sin las env vars de Supabase, la app usa SQLite + filesystem exactamente como siempre (`bash dev.sh`).

## 0. Prerrequisito: repo en GitHub

Vercel y Render despliegan desde GitHub. Al publicar el repo, **pushear todo el archivo del proyecto**:

```bash
git remote add origin git@github.com:TU_USUARIO/reencuentro.git
git push -u origin main develop adopta-v1 --tags   # adopta-v1 y adopta-v1.0.0 incluidos: respaldo remoto de la era Adopta
```

## 1. Supabase (la persistencia)

1. Crear el proyecto: desde el dashboard de Vercel → **Storage → Marketplace → Supabase** (o directo en [supabase.com](https://supabase.com), gratis).
2. **Base de datos**: en Settings → Database, copiar el **connection string del pooler** (modo *Transaction*, puerto 6543): `postgresql://postgres.xxxx:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres`. Será el `DATABASE_URL` de Render.
3. **Fotos**: en Storage → New bucket → nombre **`fotos`**, marcado como **Public bucket** (las fotos de reportes son públicas por diseño).
4. En Settings → API copiar: la **URL del proyecto** (`https://xxxx.supabase.co`) y la **`service_role` key** (⚠️ solo para el backend — nunca en Vercel ni en el código).

## 2. API en Render

1. En [render.com](https://render.com): **New → Blueprint**, apuntando al repo. Render lee `render.yaml` y crea `reencuentro-api` (free tier, **sin disco** — la API es sin estado). Al crearlo pide los valores `sync: false`:
   - `DATABASE_URL`: el connection string del pooler (paso 1.2).
   - `SUPABASE_URL` y `SUPABASE_SERVICE_KEY`: del paso 1.4.
   - `CORS_ORIGINS`: el dominio de Vercel (paso 3) — se puede poner un placeholder y corregirlo después.
2. **Seed inicial** (⚠️ UNA sola vez — hace `drop_all`: re-correrlo contra producción borra los reportes reales): en la Shell del servicio:
   ```bash
   cd /opt/render/project/src && python scripts/seed.py
   ```
   Con las env vars presentes, el seed crea el esquema en Postgres y sube las fotos al bucket (URLs públicas absolutas).

## 3. Frontend en Vercel

1. En [vercel.com](https://vercel.com): **Add New → Project**, importar el repo.
2. **Root Directory: `src/web`** (Vite autodetectado; `src/web/vercel.json` ya trae el rewrite SPA para que `/reporte/18` o `/mapa` funcionen al recargar).
3. Env var: `VITE_API_BASE_URL` = URL pública de Render (p. ej. `https://reencuentro-api.onrender.com`), **sin barra final**.
4. Deploy. Con el dominio asignado, volver a Render y fijar `CORS_ORIGINS` (sin barra final, comas si hay varios). Desde aquí, **cada push a `main` redespliega frontend y API automáticamente**.

## 4. Verificación post-deploy

1. `https://<api>.onrender.com/health` → `{"status":"ok"}` (el primer request tras inactividad tarda ~30 s: el free tier duerme).
2. `https://<api>.onrender.com/api/reports` → JSON del seed, con `foto_url` absolutas de `supabase.co`.
3. Abrir el dominio de Vercel: la landing carga con la franja de reencuentros y las fotos (si la API está sana pero esto falla, revisar `CORS_ORIGINS`).
4. Flujo completo: registrarse → reportar con foto y pin → verlo en `/reportes` y `/mapa` → **Manual Deploy en Render** → el reporte y su foto siguen ahí (viven en Supabase, no en el servicio).

## Variables de entorno (resumen)

| Dónde | Variable | Valor |
|---|---|---|
| Render | `DATABASE_URL` | connection string del **pooler** de Supabase (puerto 6543) |
| Render | `SUPABASE_URL` | `https://xxxx.supabase.co` |
| Render | `SUPABASE_SERVICE_KEY` | `service_role` key (Settings → API) — solo backend |
| Render | `SUPABASE_BUCKET` | `fotos` (ya en render.yaml) |
| Render | `CORS_ORIGINS` | dominio(s) de Vercel, separados por comas |
| Render | `PYTHON_VERSION` | `3.10.17` (ya en render.yaml) |
| Vercel | `VITE_API_BASE_URL` | URL pública de la API en Render |

## Cuándo esto deja de alcanzar

Los límites del free tier de Supabase (500 MB de DB, 1 GB de fotos) cubren de sobra la emergencia. Si el proyecto crece: subir el plan de Supabase (mismo código) y/o mover la API del free tier de Render para eliminar el arranque en frío. Nada de eso requiere cambios de arquitectura — la API ya es sin estado (ADR 0006).
