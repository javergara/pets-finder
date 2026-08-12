# 0001 — Stack técnico del MVP

## Estado
Aceptado. **Adenda (2026-08-12, pivot Reencuentro — ADR 0005):** el stack sigue vigente tal cual tras el pivot; el paquete se renombró `adopta_api` → `reencuentro_api` y las referencias a features de adopción de este ADR son históricas (esa era vive en la rama `adopta-v1`).

## Contexto
`design/prototypes/HANDOFF.md` §10 (spec de diseño preexistente) recomienda React+TS+Vite+Tailwind en el frontend y Supabase/Firebase para auth/DB/storage/**chat en tiempo real**. El proceso de harness engineering que gobierna este proyecto (`plan.md`) por defecto pide un stack local reproducible sin dependencias cloud: FastAPI+SQLAlchemy+SQLite, con un solo comando de arranque.

El alcance del MVP (`feature_list.json`, items `01`-`05`) es: fundaciones de datos, deck de swipe, ficha de mascota, matches (creados de forma no-mutua) y score de afinidad. **No incluye** mensajería en tiempo real (item `11`, backlog) ni autenticación real (item `08`, backlog) — que son las dos razones por las que HANDOFF.md sugería un BaaS.

## Decisión
- **Frontend:** React + TypeScript + Vite + TailwindCSS (coincide con la recomendación de HANDOFF.md).
- **Backend:** FastAPI + SQLAlchemy (Python).
- **Base de datos:** SQLite, archivo local `data/app.db`.
- **Gestos de swipe:** Pointer Events crudos, reutilizando el comportamiento ya implementado en `design/prototypes/Adopta Web App.dc.html`, sin añadir una librería de gestos nueva.
- **Arranque:** un solo comando local (`dev.sh`), sin contenedores.

No se adopta Supabase/Firebase por ahora.

## Consecuencias
- El MVP es 100% reproducible sin cuentas ni credenciales de terceros — alineado con el requisito de `init.sh` de verificar todo localmente.
- Cuando se retome la feature `11-chat` (backlog), esta decisión debe revisarse: implementar WebSockets propios sobre FastAPI, o migrar persistencia/realtime a un BaaS como sugiere HANDOFF.md. Se documentará como un nuevo ADR en ese momento, no se decide preventivamente ahora.
- SQLite es adecuado para el volumen de datos de un MVP con seed sintético; si el proyecto pasa a producción con datos reales concurrentes, se reconsiderará (Postgres u otro).
