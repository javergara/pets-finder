# 0007 — API como funciones serverless en Vercel (se elimina Render)

## Estado
Aceptado.

## Contexto

El plan de despliegue (ADR 0006) dejaba la API FastAPI en el free tier de Render. Al intentar crear el Blueprint, Render exigió tarjeta de crédito — bloqueó el deploy del usuario, que no quiere registrar tarjetas. Como la feature 12 dejó la API **sin estado** (Postgres y fotos en Supabase), ya no hay ninguna razón técnica que ate la API a un servidor con filesystem.

## Decisión

**Un solo proyecto de Vercel sirve todo**: el build estático de `src/web` y la API FastAPI como función serverless Python.

- `api/index.py` (raíz) expone la `app` real de `reencuentro_api` (misma instancia, no una app paralela — verificado por test); `requirements.txt` raíz incluye el de `src/api`.
- `vercel.json` raíz: build del frontend (`src/web/dist`), rewrite de `/api/*` y `/health` a la función, y fallback SPA que excluye `/api`. Los rewrites de Vercel preservan la URL original, así que FastAPI enruta normal.
- **Same-origin**: el frontend llama a la API con rutas relativas en producción (base vacía) — desaparecen `VITE_API_BASE_URL` y el problema de CORS entre dominios (el middleware queda, inofensivo, para dev).
- El montaje local `/media` se vuelve condicional: en serverless el filesystem es de solo lectura y en producción todas las fotos son URLs absolutas de Supabase.
- `render.yaml` y el `vercel.json` de `src/web` se eliminan.

## Consecuencias

- **Cero tarjetas de crédito** en todo el stack (Vercel Hobby + Supabase free) y un solo dashboard; cada push a `main` despliega frontend y API juntos.
- Arranques en frío de la función Python (~1-2 s tras inactividad) — aceptable para una app de emergencia; sin el sueño de 15 min del free tier de Render.
- El seed contra producción se corre desde la máquina local con las env vars de Supabase (no hay Shell de servidor) — documentado en `docs/deploy.md`.
- `create_all` corre en cada cold start (lifespan); es idempotente sobre Postgres.
