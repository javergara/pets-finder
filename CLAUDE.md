# CLAUDE.md — Reencuentro

Guía maestra para retomar este proyecto. Si es tu primera vez aquí, lee esto completo antes de tocar código.

## Qué es esto

**Reencuentro** (marca visible en producción: **Pet Finder Col**) es una app de emergencia para reportar mascotas **perdidas** (dueño) y **encontradas** (rescatista) tras el terremoto del Eje Cafetero (Colombia, 10 de agosto de 2026), y ayudar a reunirlas. **Está viva en producción: <https://petfinder-col.com>** (Vercel + Supabase, auto-deploy con cada push a `main`). Zonas cubiertas: Armenia, Pereira, Manizales, Cali, Quibdó y Bogotá, más una vista "Todo Colombia". Decisiones de producto deliberadas: **contacto directo por WhatsApp/teléfono** (sin chat interno), **registro mínimo sin contraseña** (entrar-o-registrar por email), **coincidencias sin AI** (especie + zona + distancia + fecha), y estado **"reunido"** como métrica de esperanza. El detalle está en `docs/product-research.md` y el razonamiento del pivot en `docs/decisions/0005-pivot-reencuentro.md` (+ ADRs 0006-0008 del deploy real: Supabase, serverless en Vercel, Leaflet).

> **Historia**: este repo fue antes **Adopta**, una app de adopción de mascotas tipo swipe (15 features completas, release 1.0.0). Todo ese trabajo vive íntegro en la rama git **`adopta-v1`** (tag `adopta-v1.0.0`) para retomarlo a futuro — nunca borres ni reescribas esa rama. Para consultar código de esa era: `git show adopta-v1:ruta/al/archivo`.

## Cómo levantarlo en local

```bash
bash init.sh   # una vez (o cuando cambien dependencias): venv, seed, lint, tests — debe quedar en verde
bash dev.sh    # levanta API (FastAPI, :8000) + web (Vite, :5173) juntas, Ctrl+C detiene ambas
```

Abrir `http://localhost:5173/` — landing de emergencia con los dos CTAs ("Perdí a mi mascota" / "Encontré una mascota"). No hay login: el usuario activo es el seed `id=1` (Ana Martínez, ver `scripts/seed.py`), o el que se registre en `/registro`.

Para resetear los datos a un estado limpio: `python3 scripts/seed.py` (determinista, mismo resultado siempre, funciona sin red).

## Mapa del repo

- **`AGENTS.md`** — el mapa real de divulgación progresiva: qué agente/skill usar para cada tarea. Empieza ahí para trabajo día a día.
- **`feature_list.json`** — alcance del pivot: 11 features (`01-pivot-fundaciones` … `11-despliegue`). Regla dura: máximo un item `in_progress`.
- **`CHECKPOINTS.md`** — qué significa "terminado". Fuente de verdad del revisor.
- **`docs/product-research.md`** — problema, referentes reales (Patitas a Salvo, PawBoost, Love Lost), decisiones de mecánica.
- **`docs/architecture.md`** + **`docs/decisions/`** — arquitectura y ADRs. El 0001 (stack) sigue vigente; el 0005 documenta el pivot completo.
- **`docs/conventions.md`** — estilo de código, estructura de carpetas, tests, commits.
- **`design/design-system.md`** — tokens visuales (semántica del pivot: perdido=`danger`, encontrado=`forest`).
- **`.claude/agents/`** — líder/implementador/revisor/investigador/diseñador. **`.claude/skills/`** — seed-data, db-migrations, run-verification, update-memory.
- **`progress/current.md`** (estado vivo) y **`progress/history.md`** (bitácora) — leer `current.md` antes de cualquier trabajo no trivial.
- **`memory/memory.md`** — gotchas y decisiones de proceso.
- **`src/api/reencuentro_api/`** — FastAPI + SQLAlchemy (`{models,schemas,services,routers}`). **`src/web/`** — React + Vite + TS + Tailwind v4.
- **`tests/api/`** (pytest) y **`src/web/src/**/*.test.{ts,tsx}`** (Vitest).
- **`data/media/`** — `seed/` (fotos del seed, regenerables) y `uploads/` (fotos subidas por usuarios). Ambas gitignored.

## Reglas de trabajo (resumen — el detalle vive en cada doc referenciado)

- Una feature a la vez en `feature_list.json`; `init.sh` y el pre-commit lo rechazan si no.
- Patrón líder→implementador→revisor (`AGENTS.md`): el revisor corre `init.sh` de verdad y aprueba o rechaza — nunca se autoaprueba una feature.
- Estado en disco: `progress/current.md` antes/después de cada paso no trivial. Nada importante vive solo en el chat.
- Conventional Commits, un commit por unidad lógica de trabajo. Ramas `main`/`develop` (+ `adopta-v1` intocable).
- Cada `acceptance` de `feature_list.json` necesita un test real que lo cubra antes de dar la feature por terminada.
- Al editar `feature_list.json`: reemplazo de texto puntual, nunca `json.dump` (ver `memory/memory.md`).

## Estado actual (2026-08-12, fin del día)

**19 features en `done` y la app desplegada en producción: <https://petfinder-col.com>.** Cada feature aprobada por un revisor independiente que corrió `bash init.sh` de verdad (70 tests de API + 64 de web, todo en verde). Arquitectura de producción (ADRs 0006-0008, guía completa en `docs/deploy.md`): un solo proyecto Vercel gratuito sirve el frontend estático y la API FastAPI como función serverless (`api/index.py`), con Postgres (pooler :6543) y Storage de fotos en Supabase free; dominio `petfinder-col.com` comprado en GoDaddy apuntando a Vercel; auto-deploy con cada push a `main`.

Funcionalidad viva: reportar perdida/encontrada con foto (comprimida en el navegador) y pin en mapa real (Leaflet+OSM), listado con filtros por características (raza/color/tamaño) y fotos lazy, detalle con contacto directo por WhatsApp, eliminar reporte (solo el autor), mapa por zona + Todo Colombia, coincidencias sin AI, reunidos con franja de esperanza, registro entrar-o-registrar con lista de ciudades de Colombia, UI móvil sin desbordes, marca visible **Pet Finder Col** con favicon propio.

**Backlog pendiente: features `20`-`25` en `todo` en `feature_list.json`** (fotos huérfanas del bucket, compartir con vista previa, alertas por zona, moderación, AI de fotos — cada una con su nota de ADR — y el checklist operativo `25-ops-produccion-pendientes` que ejecuta el dueño en los dashboards). Para retomar: mismo patrón líder→implementador→revisor, una feature a la vez.

⚠️ Reglas duras de producción: **NUNCA correr `scripts/seed.py` contra la DB de producción** (hace `drop_all`); toda escritura a prod requiere autorización explícita del usuario; si un deploy trae columnas/tablas nuevas, migrar prod (ALTER aditivo) ANTES de mergear a `main`.
