# Estado actual

**Fase activa:** post-MVP — cola de `feature_list.json`
**Feature en progreso:** ninguna. `06-filters` fue revisada y **aprobada** (2026-08-03), `status: done` en `feature_list.json`.
**Siguiente sugerida:** `07-adopter-profile` (plan ya existe en `/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md`, sección "Feature `07-adopter-profile`").

## Veredicto de revisión — `06-filters` (APROBADA)

Revisor independiente, sesión fresca sin memoria de la implementación. Verificación hecha de cero, no se confió en las notas del implementador.

- `bash init.sh` corrido de verdad en esta sesión: **verde de punta a punta** — seed determinista (5 usuarios/17 mascotas, sin duplicar en corridas repetidas), `ruff`/`black`/`oxlint`/`prettier`/`tsc -b` limpios, **50 tests de API + 15 de frontend**, todos en verde.
- Cobertura de `acceptance` vs. tests, verificada leyendo el código de los tests (no solo el conteo):
  - "`GET /api/pets` acepta query params de filtro y devuelve solo coincidencias" → `tests/api/test_filters.py` (12 tests de integración: un test por dimensión + combinación + default implícito + 2 tests de coordenadas faltantes) + `tests/api/test_filters_service.py` (15 unitarios) + `tests/api/test_geo.py` (5 unitarios). Todos pasan.
  - "El contador 'N perfiles cerca de ti' se actualiza al cambiar filtros" → `src/web/src/screens/Descubrir.test.tsx` (contador refleja longitud del array mockeado; clic en chip dispara refetch y el contador cambia).
  - "Botón 'Restablecer filtros' vuelve al estado por defecto (15 km)" → `FiltrosPanel.test.tsx` (dispara `onReset`) + `Descubrir.test.tsx` (tras reset, `listarMascotas` se llama con `FILTROS_DEFAULT`, `distanciaKm: 15`).
- Consistencia con el diseño aprobado (`ahora-has-un-nuevo-structured-pretzel.md`, sección `06-filters`), verificada leyendo el código real, no las notas:
  - `services/geo.py` es un archivo nuevo, separado de `deck.py`, función pura `distancia_km` (solo `math`, sin imports del resto de la app).
  - `services/filters.py` es independiente de la regla dura: `services/affinity.py` **no fue tocado** (`git diff` confirmado, cero cambios), los toggles `apto_*` conviven con la regla dura sin fusionarse.
  - `edad_categoria`/`EDAD_CATEGORIA_RANGOS` importa `EDAD_MESES_SENIOR` de `services/deck.py` (`from .deck import EDAD_MESES_SENIOR`) — no redefine el 84.
  - Coordenadas faltantes no excluyen por distancia: confirmado en código (`aplicar_filtros` solo evalúa el filtro de distancia si ambos lados tienen lat/lng) y en test real (`test_distancia_no_excluye_cuando_falta_lat_lng_del_usuario` y `..._de_la_mascota` en `tests/api/test_filters.py`, ambos pasan).
  - Default `distancia_km=15.0` está también en el backend (`routers/pets.py`, default del query param), verificado además por `test_default_distancia_15km_implicito`.
- `docs/conventions.md`: estructura de carpetas respetada (`services/` para lógica pura, `routers/` delgado, `components/` presentacional sin fetch propio en `FiltrosPanel.tsx`), nombres consistentes (`snake_case`/`PascalCase`/sufijo `Out`), sin manejo de excepciones genéricas nuevo.
- ADR 0003 (afinidad al vuelo): los filtros tampoco se persisten — se calculan y aplican en cada request de `GET /api/pets`, sin columna nueva de filtro guardado. Consistente.
- `changes.md` tiene 6 entradas fechadas 2026-08-03 referenciando cada paso de `06-filters` (aunque el trabajo está sin commitear todavía — ver nota abajo).
- Ninguna otra feature quedó `in_progress` en simultáneo (`06-filters` era la única, confirmado con `feature_list.json` y `scripts/validate_feature_list.py`, exit 0).
- El implementador no había marcado la feature como `done` — lo hizo este revisor tras la verificación.

**Nota operativa:** todo el trabajo de `06-filters` (backend + frontend + tests + `changes.md`) está en el working tree, **sin commitear**. `feature_list.json` fue actualizado por este revisor a `status: done`. Queda pendiente que alguien con permiso de commit (líder/implementador) cree el/los commit(s) Conventional Commits correspondientes — el revisor no comitea código de producto, solo deja el estado verificado en disco.

## Después de esta feature

No arrancar `07-adopter-profile` hasta commitear `06-filters`. El plan completo de `07-adopter-profile` ya existe en `/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md` para cuando toque planificarla.

## Nota operativa
Si quedan servidores de `bash dev.sh` corriendo en segundo plano de una sesión anterior, deténlos (Ctrl+C o `pkill`) antes de correr `init.sh`/tests para evitar conflictos de puerto.
