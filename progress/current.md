# Estado actual

**Fase activa:** 7 — MVP local con datos artificiales (gaps del revisor corregidos; pendiente segunda revisión)
**Feature en progreso:** `01-foundations-data` (backend + frontend completos; corregidos los 3 gaps de la primera revisión)

## Hecho tras el rechazo del revisor
1. **`services/deck.py`** nuevo: `ordenar_deck()` inserta mascotas difíciles de ubicar (senior >84 meses, tag "necesita experiencia", o publicadas hace >90 días) cada 4-5 tarjetas en el deck, sin perder ni duplicar ninguna. `routers/pets.py::listar_mascotas` ahora lo usa en vez de un sort plano. 6 tests nuevos en `tests/api/test_deck.py`.
2. `tests/api/test_endpoints.py`: 3 tests nuevos para `GET /api/pets/{id}` (con afinidad, sin user_id, 404).
3. `src/web/src/screens/MisMatches.test.tsx` nuevo: estado vacío (enlace a Descubrir) y estado con matches (afinidad + estado mostrados).

**Verificado:** `bash init.sh` completo en verde — 18 tests de API (antes 9) + 5 de web (antes 3), ruff/black/oxlint/prettier limpios.

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente. Stack: React+Vite+TS+Tailwind (v4) / FastAPI+SQLAlchemy / SQLite local. Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).
- Usuario demo: `id=1` (Ana Martínez).

## Próximo paso
Commitear estas correcciones y volver a invocar al **revisor** para la aprobación formal (marcar `01-05` como `done` en `feature_list.json` si corresponde) antes de pasar a la Fase 8.
