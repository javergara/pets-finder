# Despliegue — Reencuentro

Arquitectura (ADRs 0006 + 0007): **todo en Vercel + Supabase, sin tarjetas de crédito**. Un solo proyecto de Vercel sirve el frontend estático y la API FastAPI como función serverless; la persistencia (Postgres + fotos) vive en Supabase. Cada push a `main` redespliega todo automáticamente.

```
Navegante ──▶ Vercel (un solo proyecto, plan Hobby gratis)
                 ├─ estático: build de src/web (Vite)
                 └─ /api/* ──▶ función serverless Python (api/index.py → FastAPI)
                                  ├─ DATABASE_URL ──▶ Supabase Postgres (500 MB gratis)
                                  └─ fotos ──▶ Supabase Storage, bucket "fotos" (1 GB gratis)
```

En dev local nada cambia: `bash dev.sh` (SQLite + filesystem, la web apunta a `http://127.0.0.1:8000`).

> Repo remoto: `git@github.com:javergara/pets-finder.git`, con rama por defecto `main`. Si se re-publica en otro remoto, pushear también el archivo de la era Adopta: `git push -u origin main develop adopta-v1 --tags`.

## 1. Supabase (la persistencia)

1. Crear el proyecto: desde el dashboard de Vercel → **Storage → Marketplace → Supabase** (o directo en [supabase.com](https://supabase.com), gratis, sin tarjeta).
2. **Base de datos**: en Settings → Database, copiar el **connection string del pooler** (modo *Transaction*, puerto 6543): `postgresql://postgres.xxxx:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres`.
3. **Fotos**: Storage → New bucket → nombre **`fotos`**, marcado como **Public bucket**.
4. En Settings → API copiar: la **URL del proyecto** (`https://xxxx.supabase.co`) y la **`service_role` key** (⚠️ secreta — solo va en env vars del servidor, nunca en el código).

## 2. Proyecto en Vercel

1. [vercel.com](https://vercel.com) → **Add New → Project** → importar `pets-finder`.
2. **Root Directory: dejar la raíz del repo** (no `src/web` — el `vercel.json` de la raíz ya define el build del frontend y la función de la API). Framework preset: **Other**.
3. **Environment Variables** (las cuatro, para Production y Preview):

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | connection string del **pooler** (paso 1.2) |
   | `SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `SUPABASE_SERVICE_KEY` | `service_role` key |
   | `SUPABASE_BUCKET` | `fotos` |

   No hace falta `VITE_API_BASE_URL` (la web llama a `/api` en el mismo dominio) ni `CORS_ORIGINS` (same-origin).
4. **Deploy**. Desde aquí, cada push a `main` redespliega frontend y API juntos.

## 3. Seed inicial (desde tu máquina)

⚠️ **UNA sola vez** — hace `drop_all`: re-correrlo contra producción borra los reportes reales.

```bash
source .venv/bin/activate
DATABASE_URL="postgresql://...pooler.supabase.com:6543/postgres" \
SUPABASE_URL="https://xxxx.supabase.co" \
SUPABASE_SERVICE_KEY="eyJ..." \
python scripts/seed.py
```

Crea el esquema en Postgres y sube las 17 fotos del seed al bucket (URLs públicas absolutas).

## 4. Verificación post-deploy

1. `https://tu-proyecto.vercel.app/health` → `{"status":"ok"}` (primer request tras inactividad: ~1-2 s de arranque en frío de la función).
2. `https://tu-proyecto.vercel.app/api/reports` → JSON del seed con `foto_url` de `supabase.co`.
3. Abrir la landing: franja de reencuentros con fotos. Navegar a `/reportes` y `/mapa`, recargar en una ruta interna (el rewrite SPA debe responder la app, no un 404).
4. Flujo completo: registrarse → reportar con foto y pin → verlo en el listado/mapa → un **Redeploy** en Vercel → el reporte y su foto siguen ahí (viven en Supabase).

## Límites del tier gratuito (estimados para esta app)

- **Reportes/usuarios**: cientos de miles (una fila pesa <1 KB de los 500 MB de Postgres) — no es el cuello de botella.
- **Fotos**: ~300-500 con fotos de celular típicas (1 GB de Storage). **Este es el límite real.**
- **Tráfico de fotos**: ~10 GB/mes de egress en Supabase; 100 GB/mes de bandwidth en Vercel Hobby.
- ⚠️ **El proyecto Supabase se pausa tras 1 semana sin actividad** — se reactiva con un click en su dashboard.
- Si despega: comprimir imágenes en el upload (multiplica la capacidad ×10, mejora futura anotada) o Supabase Pro ($25/mes: 8 GB DB + 100 GB fotos).
