# Reencuentro

App de emergencia para reportar mascotas **perdidas** y **encontradas** tras el terremoto del Eje Cafetero (Colombia, 10 de agosto de 2026), y ayudar a reunirlas con sus familias. Zonas: Armenia, Pereira, Manizales, Cali, Quibdó y Bogotá — con vista de todo Colombia.

Proyecto construido con un flujo de *harness engineering* — ver [`AGENTS.md`](AGENTS.md) para el mapa de reglas y [`CLAUDE.md`](CLAUDE.md) para retomar el trabajo.

> La versión anterior de este proyecto (**Adopta**, app de adopción de mascotas, 15 features completas) vive íntegra en la rama git `adopta-v1` (tag `adopta-v1.0.0`) para retomarla a futuro.

## Estado

Release **2.1.0** — **en producción: <https://petfinder-col.com>** (marca visible: **Pet Finder Col**), con auto-deploy en cada push a `main`. 19 features en `done` con revisor independiente (70 tests de API + 64 de web); backlog `20`-`25` en `todo`. Ver [`progress/current.md`](progress/current.md) para el estado vivo y [`feature_list.json`](feature_list.json) para el alcance.

## Local

```bash
bash init.sh   # una vez: venv, deps, seed, lint, tests
bash dev.sh    # API :8000 + web :5173
```

## Deploy

**Todo en Vercel + Supabase, sin tarjetas** (ADRs 0006-0007): un solo proyecto Vercel sirve el frontend estático y la API FastAPI como función serverless (`api/index.py`), con Postgres + Storage de fotos en Supabase. Auto-deploy en cada push a `main`. Guía paso a paso: [`docs/deploy.md`](docs/deploy.md).
