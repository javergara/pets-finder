# Estado actual

**Fase activa:** 7 — MVP local con datos artificiales (COMPLETA, aprobada por el revisor)
**Feature en progreso:** ninguna — las 5 features MVP (`01-05`) están en `done`

## Hecho tras el rechazo del revisor (segunda revisión)
1. **`services/deck.py`** nuevo: `ordenar_deck()` inserta mascotas difíciles de ubicar (senior >84 meses, tag "necesita experiencia", o publicadas hace >90 días) cada 4-5 tarjetas en el deck, sin perder ni duplicar ninguna. `routers/pets.py::listar_mascotas` la usa en vez de un sort plano. 6 tests en `tests/api/test_deck.py` (incluye caso explícito de alternancia 4/5 y verificación de que ninguna mascota se pierde/duplica).
2. `tests/api/test_endpoints.py`: 3 tests nuevos y reales para `GET /api/pets/{id}` (con afinidad+refugio, sin `user_id`, 404 en mascota inexistente).
3. `src/web/src/screens/MisMatches.test.tsx` nuevo: cubre estado vacío (mensaje + enlace a `/descubrir`) y estado con datos (afinidad, estado del match).

## Veredicto del revisor (segunda pasada)
**APROBADO.** Los 3 gaps de la primera revisión están genuinamente corregidos (código + test, no solo archivos):
- `bash init.sh` corrido en esta sesión, termina en verde: deps, seed (17 mascotas/3 refugios/5 adoptantes), ruff/black/oxlint/prettier limpios, **18 tests de API + 5 de web, todos pasan**, `feature_list.json` válido.
- Leído `services/deck.py` y `test_deck.py` línea por línea: la inserción cada 4-5 tarjetas es un algoritmo real (alternancia de intervalo 4/5) con test que verifica posiciones múltiplo de 4 o 5 y ausencia de pérdida/duplicación — no un stub.
- Leído `test_endpoints.py`: 3 tests reales para `GET /api/pets/{id}` (éxito con afinidad, sin afinidad, 404).
- Leído `MisMatches.test.tsx`: el test de estado vacío hace mock de `listarMatches` devolviendo `[]` y verifica el mensaje y el enlace a Descubrir — cobertura directa del acceptance 3 de `04-matches`.
- ADR 0002 (match no mutuo) y ADR 0003 (afinidad al vuelo) siguen respetados: no hay endpoint de "aceptar match", el score se calcula en `services/affinity.py` sin persistirse. Sin lenguaje de descarte en `src/web/src/screens` ni en routers (grep limpio).
- `changes.md` ya tiene entrada referenciando la corrección y el commit `ee4c325`.

**Acción tomada:** marcadas `01-foundations-data`, `02-swipe-deck`, `03-pet-profile`, `04-matches`, `05-affinity-score` como `status: "done"` en `feature_list.json` (diff mínimo, solo el campo `status`, resto del archivo intacto). Validado con `python3 scripts/validate_feature_list.py feature_list.json` (pasa, sin `in_progress` restante).

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente. Stack: React+Vite+TS+Tailwind (v4) / FastAPI+SQLAlchemy / SQLite local. Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).
- Usuario demo: `id=1` (Ana Martínez).

## Próximo paso
Fase 7 (MVP) cerrada con las 5 features `done`. Continuar con la **Fase 8 — Verificación** (`plan.md`): correr `bash init.sh` en verde con evidencia capturada en `docs/verification.md` (salida real de comandos, no descripción), y probar el flujo end-to-end en navegador (cargar deck, deslizar a la derecha, ver el match en Mis Matches, abrir su ficha) antes de pasar a la Fase 9 (cierre).
