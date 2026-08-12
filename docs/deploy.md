# Despliegue — Reencuentro

Arquitectura: **frontend estático en Vercel** + **API FastAPI en Render con disco persistente**. La API no puede ir en serverless: SQLite (`data/app.db`) y las fotos subidas (`data/media/uploads/`) viven en disco (ADR 0005 §7).

```
Navegante ──▶ Vercel (src/web, build de Vite)
                 │  fetch a VITE_API_BASE_URL
                 ▼
              Render (src/api, uvicorn) ──▶ disco persistente en data/
                 └─ /media (fotos seed + uploads) y SQLite
```

## 0. Prerrequisito: repo en GitHub

Vercel y Render despliegan desde GitHub. Al publicar el repo, **pushear todo el archivo del proyecto**:

```bash
git remote add origin git@github.com:TU_USUARIO/reencuentro.git
git push -u origin main develop adopta-v1 --tags   # adopta-v1 y adopta-v1.0.0 incluidos: respaldo remoto de la era Adopta
```

## 1. API en Render

1. En [render.com](https://render.com): **New → Blueprint**, apuntando al repo. Render lee `render.yaml` (raíz) y crea el servicio `reencuentro-api` con:
   - `rootDir: src/api`, build `pip install -r requirements.txt`, start `uvicorn reencuentro_api.main:app --host 0.0.0.0 --port $PORT`.
   - **Disco persistente de 1 GB montado en `/opt/render/project/src/data`** — exactamente el `data/` de la raíz del checkout, donde `models/base.py` y `media.py` resuelven sus rutas. Sobrevive deploys.
   - `healthCheckPath: /health`.
2. Ajustar la env var `CORS_ORIGINS` al dominio real de Vercel (paso 2) — sin barra final, separando por comas si hay varios.
3. **Seed inicial** (una sola vez, o cuando se quiera resetear la demo): en la Shell del servicio en Render:
   ```bash
   cd /opt/render/project/src && python scripts/seed.py
   ```
   El seed funciona sin depender de red externa (fallback SVG). En producción real con reportes de usuarios, **no volver a correrlo**: hace `drop_all`.

## 2. Frontend en Vercel

1. En [vercel.com](https://vercel.com): **Add New → Project**, importar el repo.
2. **Root Directory: `src/web`** (Vercel detecta Vite automáticamente: build `npm run build`, output `dist/`). El `src/web/vercel.json` ya trae el rewrite SPA (toda ruta → `index.html`) para que `/reporte/18` o `/mapa` funcionen al recargar.
3. Env var del proyecto: `VITE_API_BASE_URL` = URL pública de Render (p. ej. `https://reencuentro-api.onrender.com`), **sin barra final**. Es la única configuración que el frontend necesita (`src/web/src/api/client.ts` cae a `http://127.0.0.1:8000` en local).
4. Deploy. Volver al paso 1.2 y poner el dominio que asignó Vercel en `CORS_ORIGINS` de Render.

## 3. Verificación post-deploy

1. `https://<api>.onrender.com/health` → `{"status":"ok"}`.
2. `https://<api>.onrender.com/api/reports` → JSON con los reportes del seed.
3. Abrir el dominio de Vercel: la landing carga con la franja de reencuentros (si esto falla con la API sana, revisar `CORS_ORIGINS`).
4. Flujo completo: registrarse → reportar con foto y pin → verlo en `/reportes` y `/mapa` → redeploy de la API (Manual Deploy en Render) → **el reporte y su foto siguen ahí** (el disco persiste).

## Variables de entorno (resumen)

| Dónde | Variable | Valor |
|---|---|---|
| Render | `DATABASE_URL` | `sqlite:////opt/render/project/src/data/app.db` (ya en render.yaml) |
| Render | `CORS_ORIGINS` | dominio(s) de Vercel, separados por comas |
| Render | `PYTHON_VERSION` | `3.10.17` (la versión contra la que apunta ruff/black) |
| Vercel | `VITE_API_BASE_URL` | URL pública de la API en Render |

## Cuándo esto deja de alcanzar

Si el tráfico crece (SQLite es un solo archivo, un solo proceso): migrar a Postgres (Neon/Render Postgres) + storage S3-compatible para las fotos. Es un ADR nuevo (el 0005 §7 lo deja anotado), no un ajuste de configuración.
