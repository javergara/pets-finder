# Estado actual

**Fase activa:** backlog — `feature_list.json`
**Feature actual:** `09-shelter-panel` → **`done`**, aprobada por revisor independiente (sesión fresca, sin memoria de la implementación) el 2026-08-03.

## Veredicto del revisor — `09-shelter-panel` (APROBADA)

`bash init.sh` corrido de punta a punta en esta sesión: verde completo (81 tests de API, 33 de frontend, lint/formato limpios, `feature_list.json` válido con 0 `in_progress` tras el cierre).

Cobertura acceptance ↔ test verificada una por una:
1. `GET /api/shelters/{id}` perfil+métricas+404 → `test_obtener_refugio_calcula_metricas`, `test_obtener_refugio_inexistente_devuelve_404`.
2. `GET /api/shelters/{id}/solicitudes` lista+orden+etiqueta+404+vacío → `test_listar_solicitudes_*` (4 tests).
3. `GET /api/shelters/{id}/solicitudes/{match_id}` detalle+404 cruzado → `test_obtener_solicitud_*` (4 tests, incluye el caso de dos refugios distintos).
4. `POST /api/pets` éxito+defaults+404 → 3 tests nuevos en `test_endpoints.py`.
5. `/refugio` cabecera+métricas+tabla, detalle sin botones de acción → `PanelRefugio.test.tsx` (2), `SolicitudDetalle.test.tsx` (2).
6. Ningún endpoint muta `Match.estado` → verificado por grep independiente del revisor (ver abajo), no automatizable como test positivo.

**Verificación ADR 0002 (crítica), hecha por el revisor de cero, sin confiar en el reporte del implementador:** lectura completa de `src/api/adopta_api/routers/shelters.py` y del diff de `src/api/adopta_api/routers/pets.py`, más `grep -n "\.estado" ...` sobre ambos archivos y sobre `services/solicitudes.py`. Todas las apariciones de `estado` son lecturas: comparaciones de filtro (`Match.estado == "visita_agendada"`, `Pet.estado == "disponible"`), copia a un campo de salida de schema (`estado=match.estado`), o paso de valor de solo lectura a la función pura `calcular_etiqueta_solicitud(match.estado, ...)`. **Cero asignaciones de escritura a `Match.estado`** en todo el diff de la feature. `POST /api/pets` no crea ni toca ningún `Match`, solo inserta un `Pet` nuevo. Consistente con ADR 0002.

Otros puntos verificados directamente:
- `SolicitudDetalle.tsx` (frontend) leído completo: no tiene botones "Agendar visita" / "Pedir más información" / "Descartar con motivo" — en su lugar un párrafo explícito: *"Agendar visita, pedir más información y descartar con motivo estarán disponibles en una próxima entrega."*
- `apadrinamientos_recaudados_cop` es `0` fijo hardcodeado en el router (no existe `Sponsorship`), mismo patrón ya aprobado en `07-adopter-profile`.
- `adopciones_cerradas` reusa `shelter.adopciones_cerradas` directo, sin recalcularlo contando matches.
- `schemas/shelter.py` y `schemas/pet.py::PetIn` siguen la convención de sufijos `In`/`Out`. `HTTPException` con mensajes en español (`"El refugio {id} no existe"`, etc.). Sin `except Exception` genérico en ninguno de los archivos nuevos/tocados.
- `changes.md` tiene una entrada por cada uno de los 6 pasos de implementación, referenciando la feature.
- `App.tsx`: rutas `/refugio`, `/refugio/publicar`, `/refugio/solicitudes/:matchId` montadas correctamente fuera de `<Route element={<RequiereHomeProfile />}>` (ese guard es exclusivo del lado adoptante).
- `python3 scripts/validate_feature_list.py feature_list.json` en verde tras el cambio de `status` a `done`.
- Verificación manual en navegador real ya documentada por el implementador (no repetida por el revisor, no hacía falta): `/refugio` con datos del seed, like real que aparece como solicitud nueva, detalle sin botones, publicación de mascota nueva funcionando end-to-end.

**Nota operativa de esta sesión de revisión:** al editar `feature_list.json` se ejecutó por error un `git checkout -- feature_list.json`, que descartó momentáneamente el cambio no comprometido del líder (status `in_progress` + `acceptance` de 6 líneas). Se reconstruyó manualmente el bloque completo a partir del contenido ya leído en esta misma sesión (idéntico texto de `acceptance`) y se aplicó directamente el estado final `done`. Verificado con `validate_feature_list.py` y un `git diff` limpio y mínimo (solo cambia `status` y agrega las 6 líneas de `acceptance` de `09-shelter-panel`, sin tocar el resto del archivo). Lección para próximas sesiones: nunca usar `git checkout --` sobre archivos con cambios sin commitear, ni siquiera para "empezar de cero" en una edición — usar edición directa del archivo.

**Siguiente trabajo sugerido:** `10-adoption-request-flow` (depende de `09-shelter-panel`, ahora `done`) — implementa las transiciones de `Match.estado` y las acciones "Agendar visita" / "Pedir información" / "Descartar con motivo" que esta feature dejó explícitamente fuera de alcance.

## Historial de cierres anteriores

Ver `progress/history.md` para el detalle completo de features `01`-`08` (todas `done`, aprobadas por revisor independiente). Resumen: MVP (`01`-`05`) aprobado 2026-07-31; `06-filters`/`07-adopter-profile` aprobadas en sesión posterior; `08-onboarding-cuestionario` aprobada 2026-08-03; `09-shelter-panel` aprobada 2026-08-03 (6 pasos de implementación + cierre de revisor, 81 tests API + 33 frontend en verde). Sin feature en progreso tras este cierre.
