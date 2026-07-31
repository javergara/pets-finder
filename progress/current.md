# Estado actual

**Fase activa:** 7 — MVP local con datos artificiales
**Feature en progreso:** `01-foundations-data` (backend completo; frontend pendiente en el siguiente paso)

## Hecho en esta fase (backend)
- Modelos SQLAlchemy: `User`, `HomeProfile`, `Shelter`, `Pet`, `Swipe`, `Match` (sin columna de afinidad en `Match`, ADR 0003).
- Schemas Pydantic In/Out por entidad.
- `services/affinity.py`: `calcular_afinidad(pet, home)` pura, ponderación de `docs/product-research.md` §5, reglas duras (niños/gatos). **Probada** con 4 tests (alta afinidad, baja afinidad, 2 reglas duras).
- `services/matching.py`: `registrar_swipe` — crea `Match` de inmediato en `like` (ADR 0002).
- Routers `pets`/`swipes`/`matches` + `main.py` (CORS, lifespan moderno — no `on_event` deprecado, media estático).
- `scripts/seed.py`: **corrido de verdad**, 3 refugios, 17 mascotas, 5 adoptantes con `HomeProfile` sintético diseñado para casos de alta/baja afinidad y ambas reglas duras. Fotos reales descargadas de `placedog.net`/`cataas.com` (17/17 esta vez, red disponible); fallback SVG local implementado y documentado en `.claude/skills/seed-data/SKILL.md` aunque no se ejercitó (no hubo fallo de red en esta corrida).
- 9 tests (`tests/api/`) todos en verde: persistencia (las 6 entidades), afinidad (4 casos), endpoints (listar/excluir swipeadas, swipe crea match, pass no crea match).
- `ruff`/`black` limpios sobre `src/api`, `tests/api`, `scripts` (ajustes: `target-version` a py310 para que coincida con el intérprete real, `B008` ignorado por ser el idiom de FastAPI, `E501` ignorado solo en `scripts/seed.py` para las historias de mascotas).
- Probado manualmente con `curl` contra el servidor real: `/health`, `GET /api/pets` (orden por afinidad correcto), `POST /api/swipes` (crea match), `GET /api/matches`, `/media/*` (fotos servidas). DB reseteada al estado limpio del seed después de la prueba.

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente. Stack: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local (ADR 0001). Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).
- Usuario demo: `id=1` (Ana Martínez), sembrado siempre primero por `scripts/seed.py`.

## Próximo paso
Frontend (`src/web`, Vite+React+TS+Tailwind): deck de swipe, ficha de mascota, modal de match, matches — pasos 7-8 del plan de esta feature (ver commits anteriores de esta sesión para el detalle del plan completo).
