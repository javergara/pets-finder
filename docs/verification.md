# Verificación — Adopta MVP

Evidencia real de la Fase 8 (`plan.md`). Todo lo de abajo se corrió de verdad en esta sesión, no es una descripción de lo que "debería" pasar (ver `CHECKPOINTS.md`, "qué NO es un checkpoint válido").

## `bash init.sh` — resultado completo

Corrido el 2026-07-31 desde la raíz del repo, sin modificaciones previas al working tree:

```
== 1. Dependencias del sistema ==
  ✓ python3 encontrado (Python 3.10.17)
  ✓ node encontrado (v22.21.0)
  ✓ npm encontrado (10.9.4)

== 2. feature_list.json ==
  ✓ feature_list.json válido

== 3. Entorno Python (.venv) ==
  ✓ .venv ya existe
  ✓ dependencias de desarrollo instaladas
  ✓ dependencias de la API instaladas

== 4. Pre-commit hook ==
  ✓ hook de pre-commit instalado

== 5. Datos semilla (SQLite) ==
Seed completo: 3 refugios, 17 mascotas, 5 adoptantes.
Usuario demo (id=1): Ana Martínez
  ✓ seed corrido, data/app.db poblado

== 6. Frontend (src/web) ==
  ✓ dependencias de src/web instaladas

== 7. Lint ==
All checks passed!
  ✓ ruff sin errores
All done! ✨ 🍰 ✨
23 files would be left unchanged.
  ✓ black: formato correcto
  ✓ lint sin errores

== 8. Tests ==
============================= test session starts ==============================
platform darwin -- Python 3.10.17, pytest-8.3.3, pluggy-1.6.0
collected 18 items

tests/api/test_affinity.py ....                                          [ 22%]
tests/api/test_deck.py ......                                            [ 55%]
tests/api/test_endpoints.py .......                                      [ 94%]
tests/api/test_persistence.py .                                          [100%]

============================== 18 passed in 0.29s ===============================
  ✓ tests de API pasan

 Test Files  2 passed (2)
      Tests  5 passed (5)
  ✓ tests de web pasan

== Resultado ==
Todo en verde.
```

## Cobertura de tests por feature (`feature_list.json`, todas `status: done`)

| Feature | Tests | Archivo |
|---|---|---|
| `01-foundations-data` | Persistencia de las 6 entidades | `tests/api/test_persistence.py` |
| `02-swipe-deck` | Swipe like crea match, pass no crea match, mascota excluida tras swipe, teclado/botón equivalentes al gesto | `tests/api/test_endpoints.py`, `src/web/src/components/SwipeCard.test.tsx` |
| `03-pet-profile` | `GET /api/pets/{id}` con afinidad+refugio, sin `user_id`, 404 | `tests/api/test_endpoints.py` |
| `04-matches` | Match aparece en `/api/matches`, estado vacío con enlace a Descubrir, estado con datos | `tests/api/test_endpoints.py`, `src/web/src/screens/MisMatches.test.tsx` |
| `05-affinity-score` | Alta afinidad, baja afinidad, 2 reglas duras (niños/gatos), inserción de mascotas difíciles cada 4-5 tarjetas (6 tests) | `tests/api/test_affinity.py`, `tests/api/test_deck.py` |

Total: **18 tests de API + 5 de frontend**, todos en verde.

## Verificación manual end-to-end en navegador

Corrida con `bash dev.sh` (API en `:8000`, web en `:5173`) y Chrome real (no solo `curl`):

1. `http://localhost:5173/` redirige a `/descubrir` y carga el deck con fotos reales descargadas (`placedog.net`/`cataas.com`), ordenado por afinidad (94% afín primero).
2. Click en `♥` (Me interesa) → `POST /api/swipes` crea el match de inmediato → aparece el modal "Nuevo match" con foto, nombre y tiempo de respuesta del refugio (ADR 0002: sin paso de aprobación del refugio para el match).
3. "Ver mis matches" → `/matches` muestra la mascota con su score de afinidad y estado "Esperando refugio".
4. Click en la tarjeta → `/mascota/:id` muestra historia, salud y cuidados, tarjeta del refugio, y la explicación de afinidad (nunca el número solo, ver ADR 0003).
5. Sin errores en la consola del navegador durante todo el flujo.
6. Después de la prueba, `data/app.db` se resembró (`python3 scripts/seed.py`) para dejar el estado limpio — el swipe de prueba no queda en el estado semilla del repo.

## Reglas de negocio verificadas contra el código (no solo documentadas)

- **ADR 0002 (match no mutuo):** `services/matching.py::registrar_swipe` crea el `Match` en el mismo request que el `Swipe` con dirección `like`, sin ningún endpoint de "aceptar match". Confirmado por revisor independiente (dos pasadas, ver `progress/history.md`).
- **ADR 0003 (afinidad al vuelo):** no existe columna de afinidad en `models/match.py`; `services/affinity.py` se invoca en cada request desde `routers/pets.py` y `routers/matches.py`.
- **Sin lenguaje de descarte:** grep de "rechazar"/"nope"/"descartar" sobre `src/web/src/screens` y `src/web/src/components` sin coincidencias — el copy usa "Ahora no"/"Me interesa" consistentemente.

## Qué queda fuera de esta verificación (documentado, no un olvido)

- Features `06`-`15` de `feature_list.json` (post-MVP/backlog): no implementadas, no verificadas — fuera del alcance de este MVP por diseño (ver `docs/product-research.md` §7).
- No hay pruebas de carga ni de concurrencia — SQLite + datos semilla no lo requieren para este alcance (ver `docs/architecture.md` §6).
