# Reencuentro

App de emergencia para reportar mascotas **perdidas** y **encontradas** tras el terremoto del Eje Cafetero (Colombia, 10 de agosto de 2026), y ayudar a reunirlas con sus familias. Zonas: Armenia, Pereira, Manizales, Cali, Quibdó y Bogotá — con vista de todo Colombia.

Proyecto construido con un flujo de *harness engineering* — ver [`AGENTS.md`](AGENTS.md) para el mapa de reglas y [`CLAUDE.md`](CLAUDE.md) para retomar el trabajo.

> La versión anterior de este proyecto (**Adopta**, app de adopción de mascotas, 15 features completas) vive íntegra en la rama git `adopta-v1` (tag `adopta-v1.0.0`) para retomarla a futuro.

## Estado

Release **2.0.0**: la app funciona de punta a punta en local (ver [`docs/verification.md`](docs/verification.md)). Ver [`progress/current.md`](progress/current.md) para el estado vivo y [`feature_list.json`](feature_list.json) para el alcance.

## Local

```bash
bash init.sh   # una vez: venv, deps, seed, lint, tests
bash dev.sh    # API :8000 + web :5173
```

## Deploy

Frontend estático en **Vercel** (`src/web`, con `vercel.json` para el rewrite SPA) + API sin estado en **Render free** (`render.yaml`) + persistencia en **Supabase** (Postgres + Storage para las fotos, ADR 0006). Todo en tier gratuito, con auto-deploy en cada push a `main`. Guía paso a paso: [`docs/deploy.md`](docs/deploy.md).
