# CLAUDE.md — Reencuentro

Guía maestra para retomar este proyecto. Si es tu primera vez aquí, lee esto completo antes de tocar código.

## Qué es esto

**Reencuentro** es una app de emergencia para reportar mascotas **perdidas** (dueño) y **encontradas** (rescatista) tras el terremoto del Eje Cafetero (Colombia, 10 de agosto de 2026), y ayudar a reunirlas. Zonas cubiertas: Armenia, Pereira, Manizales, Cali, Quibdó y Bogotá, más una vista "Todo Colombia". Decisiones de producto deliberadas: **contacto directo por WhatsApp/teléfono** (sin chat interno), **registro mínimo sin contraseña**, **coincidencias sin AI** (especie + zona + distancia + fecha), y estado **"reunido"** como métrica de esperanza. El detalle está en `docs/product-research.md` y el razonamiento del pivot en `docs/decisions/0005-pivot-reencuentro.md`.

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

## Estado actual (2026-08-12)

**Pivot en curso.** `01-pivot-fundaciones` in_progress: rama `adopta-v1` creada, borrado y rename hechos, API mínima (users) y web mínima (landing v1 + registro) en verde. Siguen `02-reportes-backend` … `11-despliegue` según `feature_list.json`. Ver `progress/current.md` para el detalle vivo.
