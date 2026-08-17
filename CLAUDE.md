# CLAUDE.md — Reencuentro

Guía maestra para retomar este proyecto. Si es tu primera vez aquí, lee esto completo antes de tocar código.

## Qué es esto

**Reencuentro** (marca visible en producción: **Pet Finder Col**) es, ante todo, una app de **emergencia**: reportar mascotas **perdidas** (dueño) y **encontradas** (rescatista) tras el terremoto del Eje Cafetero (Colombia, 10 de agosto de 2026), y ayudar a reunirlas. **Está viva en producción: <https://petfinder-col.com>** (Vercel + Supabase, auto-deploy con cada push a `main`). Zonas cubiertas: Armenia, Pereira, Manizales, Cali, Quibdó, Bogotá y Medellín, más una vista "Todo Colombia". Decisiones de producto deliberadas: **contacto directo por WhatsApp/teléfono** (sin chat interno), **registro mínimo sin contraseña** (entrar-o-registrar por email), **coincidencias explicables** (especie + zona + distancia + fecha; desde el ADR 0012 se les suma el parecido visual de la foto, calculado fuera de la API y sin mandar nada a terceros — la heurística sigue siendo la base y el orden no cambia sin vectores), y estado **"reunido"** como métrica de esperanza. El detalle está en `docs/product-research.md` y el razonamiento del pivot en `docs/decisions/0005-pivot-reencuentro.md` (+ ADRs 0006-0008 del deploy real: Supabase, serverless en Vercel, Leaflet).

Sobre esa base hay una **fase 2: adopción** (`/adoptar`, features `AD-01`…`AD-08`) — las mascotas que nadie reclama necesitan hogar, y ese es el final del arco de la emergencia, no un producto distinto. Catálogo con filtros, deck de swipe con afinidad calculada al vuelo, perfil de hogar, solicitudes con estados y favoritos. **El orden importa y está codificado**: los dos CTAs de la landing siguen siendo "Perdí a mi mascota" y "Encontré una mascota"; "Adoptar" es un enlace **terciario** en la landing y el 8.º de la nav, detrás de los caminos de emergencia — hay tests que lo fijan (`LandingEmergencia.test.tsx`, `App.test.tsx`). La comunicación de una solicitud también es WhatsApp directo, sin chat interno (**ADR 0013**), y la mecánica hereda los ADRs 0002 (el match **no es mutuo**) y 0003 (afinidad sin caché). El porqué de la fase 2 está en `docs/product-research.md` §11 y el contexto del portado en `docs/integracion-adopcion.md`.

> **Historia**: este repo fue antes **Adopta**, una app de adopción de mascotas tipo swipe (15 features completas, release 1.0.0). Todo ese trabajo vive íntegro en la rama git **`adopta-v1`** (tag `adopta-v1.0.0`) — **nunca borres ni reescribas esa rama**. Ojo con el matiz: el módulo de adopción **volvió** como fase 2 de Reencuentro, pero **portado a mano, archivo por archivo**, adaptando nombres, stack y decisiones (WhatsApp en vez del chat con WebSockets del ADR 0004, que no funciona en serverless). No hay merge ni cherry-pick desde `adopta-v1`, y la rama sigue igual de intocable que antes: es el archivo histórico, no una fuente de la que se mergea. Para consultar código de esa era: **`git show origin/adopta-v1:ruta/al/archivo`** o `git show adopta-v1.0.0:ruta/al/archivo` — `git show adopta-v1:…` a secas **falla** con `invalid object name` salvo que alguien haya creado la rama local, y este repo no la trae.

## Cómo levantarlo en local

```bash
bash init.sh   # una vez (o cuando cambien dependencias): venv, seed, lint, tests — debe quedar en verde
bash dev.sh    # levanta API (FastAPI, :8000) + web (Vite, :5173) juntas, Ctrl+C detiene ambas
```

Abrir `http://localhost:5173/` — landing de emergencia con los dos CTAs ("Perdí a mi mascota" / "Encontré una mascota"). No hay login: el usuario activo es el seed `id=1` (Ana Martínez, ver `scripts/seed.py`), o el que se registre en `/registro`.

Para resetear los datos a un estado limpio: `python3 scripts/seed.py` (determinista, mismo resultado siempre, funciona sin red).

## Mapa del repo

- **`AGENTS.md`** — el mapa real de divulgación progresiva: qué agente/skill usar para cada tarea. Empieza ahí para trabajo día a día.
- **`feature_list.json`** — el alcance real y el único que valida `init.sh`: **55 items** hoy (`python3 -c "import json;print(len(json.load(open('feature_list.json'))['items']))"`), del pivot (`01-pivot-fundaciones` …) a la fase 2 (`AD-01` … `AD-09`). Regla dura: **máximo un item `in_progress`**.
- **`feature_list_adopcion.json`** — el **backlog fuente** de la fase 2 (9 items, `AD-01` … `AD-09`). No lo valida `init.sh`: al arrancar una tarea se copia el item a `feature_list.json`, y el revisor marca `done` en **los dos**. Lee antes `docs/integracion-adopcion.md`.
- **`CHECKPOINTS.md`** — qué significa "terminado". Fuente de verdad del revisor.
- **`docs/product-research.md`** — problema, referentes reales (Patitas a Salvo, PawBoost, Love Lost), decisiones de mecánica.
- **`docs/architecture.md`** + **`docs/decisions/`** — arquitectura y ADRs. El 0001 (stack) sigue vigente; el 0005 documenta el pivot completo.
- **`docs/conventions.md`** — estilo de código, estructura de carpetas, tests, commits.
- **`design/design-system.md`** — tokens visuales (semántica del pivot: perdido=`danger`, encontrado=`forest`).
- **`.claude/agents/`** — líder/implementador/revisor/investigador/diseñador. **`.claude/skills/`** — seed-data, db-migrations, run-verification, update-memory.
- **`progress/current.md`** (estado vivo) y **`progress/history.md`** (bitácora) — leer `current.md` antes de cualquier trabajo no trivial.
- **`memory/memory.md`** — gotchas y decisiones de proceso.
- **`src/api/reencuentro_api/`** — FastAPI + SQLAlchemy (`{models,schemas,services,routers}`; 14 modelos, 12 servicios, 12 routers). **`src/web/`** — React + Vite + TS + Tailwind v4.
- **`migrations/`** — el SQL **aditivo** que se ejecuta **a mano** en el SQL Editor de Supabase, versionado (`AD-0N-<tabla>.sql` + `README.md` con el estado de cada uno). No hay Alembic ni runner. Cada migración lleva su anti-drift en `tests/api/test_migracion_*.py`. En producción está `SKIP_DB_CREATE_ALL=1`: **nada de esquema se crea solo en el deploy**.
- **`tests/api/`** (pytest) y **`src/web/src/**/*.test.{ts,tsx}`** (Vitest).
- **`data/media/`** — `seed/` (fotos del seed, regenerables) y `uploads/` (fotos subidas por usuarios). Ambas gitignored.

## Reglas de trabajo (resumen — el detalle vive en cada doc referenciado)

- Una feature a la vez en `feature_list.json`; `init.sh` y el pre-commit lo rechazan si no.
- Patrón líder→implementador→revisor (`AGENTS.md`): el revisor corre `init.sh` de verdad y aprueba o rechaza — nunca se autoaprueba una feature.
- Estado en disco: `progress/current.md` antes/después de cada paso no trivial. Nada importante vive solo en el chat.
- Conventional Commits, un commit por unidad lógica de trabajo. Ramas `main`/`develop`, `feat/adoptar` (la fase 2, hoy sin mergear) y **`adopta-v1` intocable**.
- Cada `acceptance` de `feature_list.json` necesita un test real que lo cubra antes de dar la feature por terminada. Si un acceptance **no se puede** cubrir con un test (p. ej. layout: jsdom no tiene motor de layout), se dice **con todas las letras** en el paquete del revisor, con la medición que sí se hizo — nunca se presenta como cubierto.
- Al editar `feature_list.json`: reemplazo de texto puntual, nunca `json.dump` (ver `memory/memory.md`).

## Estado actual (2026-08-17)

**51 items en `done` de los 55 de `feature_list.json`**, cada uno aprobado por un revisor independiente que corrió `bash init.sh` de verdad. Última corrida: **753 tests de Python + 487 de web, `Todo en verde.`** (`init.sh` no typechequea el frontend: `npx tsc -b --force` o `npm run build` van aparte, a mano).

**Lo que está en producción** (`main`, <https://petfinder-col.com>) es el **dominio de emergencia + la red de apoyo**: reportar perdida/encontrada con varias fotos (comprimidas y recortadas en el navegador) y pin en mapa real (Leaflet+OSM), listado con filtros por características, búsqueda por descripción, avistamientos sin registro, detalle con contacto directo por WhatsApp, cartel imprimible con QR, alertas por correo y radar diario de coincidencias, reunidos con franja de esperanza, landings por zona con og tags, directorio de organizaciones y tablero de ayuda entre vecinos. Arquitectura (ADRs 0006-0008, guía en `docs/deploy.md`): un solo proyecto Vercel gratuito sirve el frontend estático y la API FastAPI como función serverless (`api/index.py`), con Postgres (pooler :6543) y Storage de fotos en Supabase free; dominio comprado en GoDaddy; auto-deploy con cada push a `main`.

**Lo que está en la rama `feat/adoptar` y NO en producción**: el módulo de adopción completo (`AD-01`…`AD-08` en `done`, **`AD-09-migraciones-y-deploy` en `in_progress`** — el item de cierre que despliega y verifica en prod).

✅ **El merge de `feat/adoptar` a `main` está DESBLOQUEADO desde el 2026-08-17**: las cuatro migraciones que faltaban ya corrieron en Supabase, en su orden — `AD-03-swipes.sql` → `AD-03-home-profiles.sql` → `AD-05-matches.sql` → `AD-07-favorites.sql`. El dueño lo verificó contra `pg_class`/`pg_constraint`: RLS activo en las cinco tablas del módulo y las cuatro constraints con su nombre exacto. Detalle por archivo en `migrations/README.md`.

⚠️ La regla que lo motivó **no se relaja**: con `SKIP_DB_CREATE_ALL=1` en producción no hay red de seguridad, así que **cualquier** cambio de esquema futuro se migra **antes** de mergear. Si el código llega antes que las tablas, cae la API entera, no solo las pantallas nuevas.

**Backlog del dominio de emergencia**: `22-alertas-por-zona`, `23-moderacion-reportes` y `25-ops-produccion-pendientes` (el checklist que ejecuta el dueño en los dashboards) siguen en `todo`. Para retomar cualquier cosa: mismo patrón líder→implementador→revisor, una feature a la vez.

⚠️ Reglas duras de producción: **NUNCA correr `scripts/seed.py` contra la DB de producción** (hace `drop_all` y allí hay datos reales de gente que perdió a su mascota); toda escritura a prod requiere autorización explícita del usuario; si un deploy trae columnas/tablas nuevas, migrar prod (**ALTER aditivo, con RLS en toda tabla nueva**) **ANTES** de mergear a `main`.
