# Arquitectura — Adopta

Ver decisiones individuales justificadas en `docs/decisions/`. Este documento explica cómo encajan las piezas y por qué esta forma es "buen trabajo" técnico para el alcance actual (MVP local, sin autenticación real; tiempo real limitado al chat vía WebSockets nativos, ver ADR 0004).

## 1. Vista general

```
┌─────────────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│  src/web (React + Vite) │ ───────────────────────▶ │  src/api (FastAPI)       │
│  deck de swipe, ficha,  │ ◀─────────────────────── │  routers → services →    │
│  matches, perfil        │                          │  modelos SQLAlchemy      │
└─────────────────────────┘                          └────────────┬─────────────┘
                                                                    │
                                                          ┌─────────▼─────────┐
                                                          │  SQLite            │
                                                          │  data/app.db       │
                                                          └────────────────────┘
                     scripts/seed.py ──▶ puebla data/app.db con datos deterministas
                     (mascotas, refugios, adoptantes, fotos con fallback offline)
```

Monorepo de dos paquetes (`src/api`, `src/web`) más `scripts/` y `data/`, en vez de repos separados: para un MVP de una sola persona/agente iterando rápido, un repo único con un comando de arranque reduce fricción (ver ADR 0001) sin costo real, ya que no hay equipos distintos por servicio todavía.

## 2. Backend (`src/api`)

FastAPI + SQLAlchemy, capas:

- **`models/`** — entidades SQLAlchemy: `User`, `HomeProfile`, `Shelter`, `Pet`, `Swipe`, `Match` (alcance MVP), más `Thread`/`Message` (`models/chat.py`, feature `11-chat`, ver ADR 0004). `Sponsorship` se añade cuando se retome la feature de backlog `12`.
- **`schemas/`** — Pydantic, entrada/salida de la API, separados de los modelos de DB para no filtrar detalles de persistencia al contrato HTTP.
- **`services/`** — lógica de negocio pura, testeable sin FastAPI ni DB real: en particular `affinity.py` (score adoptante↔mascota, ver ADR 0003) y `matching.py` (crear Match al registrar un Swipe con dirección `like`, ver ADR 0002).
- **`routers/`** — endpoints HTTP delgados que llaman a `services/`, sin lógica de negocio propia.

Elegir "servicios puros" en vez de lógica embebida en los routers es lo que permite testear la fórmula de afinidad y la regla de match-no-mutuo con tests unitarios rápidos (sin levantar la API ni la DB), que es exactamente lo que pide `feature_list.json` en los criterios de aceptación de `05-affinity-score`.

## 3. Frontend (`src/web`)

React + TypeScript + Vite + Tailwind. Los tokens de color/tipografía de `design/prototypes/HANDOFF.md` §3 se mapean 1:1 a `tailwind.config` (mismo nombre de token: `forest`, `ink`, `muted`, etc.) para que el `design-system.md` de la Fase 6 sea la fuente de verdad tanto del diseño como del código — evita que diseño e implementación diverjan con el tiempo.

Gestos de swipe: Pointer Events crudos (como en el prototipo `.dc.html` existente, que ya resuelve arrastre + umbral + sellos + `prefers-reduced-motion`) en vez de añadir una librería de gestos nueva — reutiliza el comportamiento ya validado en el prototipo en lugar de reimplementarlo con una dependencia distinta.

## 4. Datos y seed

SQLite en `data/app.db` (gitignored). `scripts/seed.py` es la única forma de poblar datos: determinista (semilla fija), reproducible, y **nunca falla por falta de red** — si no puede descargar fotos usa placeholders locales generados (ver Fase 7). Esto es lo que permite que `init.sh` corra en cualquier máquina sin depender de servicios externos disponibles en el momento de la verificación.

La afinidad **no se persiste**: se calcula al vuelo en cada request (ver ADR 0003). Es intencional — con el volumen de datos de un MVP el costo de recalcular es insignificante, y evita el problema de invalidación de caché cuando cambia el `HomeProfile` o el `Pet`.

## 5. Arranque local (un solo comando)

`init.sh` prepara el entorno (venv, dependencias, seed) y lo verifica; un script separado (`dev.sh`, documentado en `CLAUDE.md` al cierre) levanta `uvicorn` (API, puerto 8000) y `vite` (web, puerto 5173) en paralelo con un solo comando, matando ambos procesos con una única señal de interrupción. No se usa Docker para el MVP: añade una capa de indirección (build de imágenes, red entre contenedores) que no aporta nada mientras todo corre en un solo equipo de desarrollo; se reconsiderará si el proyecto pasa a desplegarse.

## 6. Qué queda fuera (y por qué no es deuda técnica todavía)

- **Autenticación real** — el MVP identifica al "adoptante activo" por un usuario semilla fijo (ver Fase 7); no hay login. Introducir auth ahora sin que exista todavía el flujo de onboarding (feature `08`, backlog) sería construir infraestructura para una pantalla que no existe.
- **Autenticación real en el chat** — la feature `11-chat` ya está implementada con WebSockets nativos sobre FastAPI/Starlette (`routers/chat.py`, `services/chat_manager.py::ConnectionManager` en memoria), sin migrar a un BaaS (ver ADR 0004, que revisa el mandato dejado abierto por ADR 0001). La identidad de cada conexión WS se pasa por query param y se valida contra el `Match`, con el mismo nivel de rigor que el resto de la API sin auth real — no es autenticación real, sigue siendo deuda pendiente de un login real (feature `08` la resolvió solo para el registro, no para sesiones).
- **Migraciones formales** — con un esquema que cambia junto con datos semilla desechables, se usa `SQLAlchemy.metadata.create_all` vía el skill `db-migrations` en vez de Alembic; se reconsiderará si el esquema necesita evolucionar sobre datos reales persistentes.
