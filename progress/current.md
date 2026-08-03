# Estado actual

**Fase activa:** backlog — `feature_list.json`
**Feature actual:** ninguna `in_progress`. `10-adoption-request-flow` → **`done`**, aprobada por el revisor (sesión independiente, 2026-08-03). Siguiente candidata sugerida: `11-chat` (requiere reabrir ADR 0001 de stack) o el resto del backlog (`12-sponsorship`, `13-guardar-para-despues`, `14-mapa-refugios`, ver `feature_list.json`).

## Veredicto del revisor — `10-adoption-request-flow` (2026-08-03, sesión independiente)

**APROBADA.** `bash init.sh` corrido en verde en esta sesión (140 tests API + 45 frontend, lint/formato limpios, `feature_list.json` válido). Verificación punto por punto:

1. Las 6 líneas de `acceptance` tienen test directo: matriz de transiciones válidas por endpoint con verificación en DB (`tests/api/test_shelters.py::test_transicion_valida_actualiza_estado_y_persiste`), matriz completa de 9 transiciones inválidas → 409 (`test_transicion_invalida_devuelve_409_y_no_muta_estado`), `validar_transicion`/`calcular_etiqueta_solicitud` con 30 tests puros sin DB (`tests/api/test_solicitudes_service.py`), no-filtrado de `motivo_descarte` sobre el JSON real de `GET /api/matches` (`test_get_matches_adoptante_no_expone_motivo_descarte`, confirmado corriendo el test aislado), matriz de habilitado/deshabilitado en `SolicitudDetalle.test.tsx` (`it.each` por estado + caso terminal), 5 estados de `MisMatches.test.tsx` (`it.each`).
2. **Matriz backend vs. frontend verificada línea por línea, leyendo ambos archivos yo mismo**: `TRANSICIONES_VALIDAS` (`services/solicitudes.py`) — `agendar-visita: {solicitado, en_revision}`, `pedir-informacion: {solicitado}`, `descartar: {solicitado, en_revision, visita_agendada}` — coincide EXACTAMENTE con `permiteAgendar`/`permitePedirInfo`/`permiteDescartar` en `SolicitudDetalle.tsx`. Sin discrepancias.
3. `grep motivo_descarte` confirma 0 apariciones en `schemas/match.py` (backend, lado adoptante) y en `types.ts` en `Match`/`MatchWithPet` (solo aparece en `DescartarIn`, que es el payload que el refugio *envía*, no algo que el adoptante recibe — correcto). El test explícito de la fila 3 existe y pasa aislado.
4. `docs/decisions/0002-mecanica-match-no-mutuo.md` sigue consistente: las transiciones son sobre `Match.estado` (la solicitud), nunca crean/destruyen el `Match`, tal como el ADR delega explícitamente a esta feature de backlog. El docstring de `routers/shelters.py` fue actualizado correctamente: documenta que los 3 `GET` siguen siendo solo lectura pero los 3 `POST` nuevos sí mutan `Match.estado`, citando el ADR.
5. `MisMatches.tsx` — copy de `cerrado` es `"● Solicitud cerrada"` (`text-muted`), neutro, sin motivo ni atribución de culpa al refugio. Verificado leyendo el archivo directamente.
6. Código sigue `docs/conventions.md`: estructura de carpetas correcta (`services/` para la lógica pura, `routers/` delgado con helpers `_cargar_match_o_404`/`_solicitud_detalle_out`), sufijo `In` en `DescartarIn`, `HTTPException(409, ...)` con mensaje en español vía `TransicionInvalidaError` capturada en el router.
7. `changes.md` tiene 4 entradas detalladas referenciando la feature (una por paso de implementación).
8. Ninguna otra feature quedó `in_progress` (confirmado programáticamente sobre `feature_list.json`).

**Nota de proceso (autocrítica):** durante esta revisión ejecuté por error `git checkout -- feature_list.json`, lo que descartó temporalmente el trabajo previo del líder (status `in_progress` + las 6 líneas de `acceptance`) antes de mi propio cambio a `status: done`. Se detectó de inmediato por el diff resultante (mostraba `todo`→`done` y `acceptance: []`→6 líneas en un solo diff) y se reconstruyó con una edición quirúrgica de texto que reproduce exactamente el contenido perdido (verificado contra el JSON impreso al inicio de esta sesión y contra el texto ya citado en este mismo archivo). El diff final contra HEAD es mínimo y correcto (confirmado con `git diff feature_list.json`), pero quede registrado el incidente.

**Verificación manual en navegador real**: ya realizada en la sesión de implementación (no repetida por mí, según instrucción) — solicitud generada por like real, 3 acciones probadas en secuencia desde `/refugio` con la matriz de habilitado/deshabilitado coincidiendo en cada paso, reflejo correcto en `/matches` sin exponer el motivo, sin errores de consola, `data/app.db` reseteado al final.


## Plan — `10-adoption-request-flow`: acciones del refugio sobre la solicitud

**Documento de diseño aprobado por el usuario (base de este plan, NO reabrir las decisiones ya tomadas ahí):**
`/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md`

### Contexto verificado por el líder en esta sesión (no confiar solo en el documento — se releyó el código real)

- `src/api/adopta_api/routers/shelters.py`: los 3 `GET` de la feature 09 existen tal cual se documentaba. El docstring del módulo (líneas 1-7) dice explícitamente *"Ningún endpoint de este router muta `Match.estado`... las transiciones... son de la feature de backlog `10-adoption-request-flow`"* — hay que actualizarlo cuando esta feature deje de ser cierto eso.
- `src/api/adopta_api/services/solicitudes.py`: `calcular_etiqueta_solicitud(estado, creado_en, ahora=None)` es pura, sin I/O. Confirmado el gap: agrupa `solicitado`/`en_revision` bajo la misma rama de "días transcurridos" — no hay rama propia para `en_revision`. El docstring del módulo (líneas 1-15) documenta "5 valores" agrupando ambos estados en una sola viñeta — hay que actualizarlo a 6 ramas distintas.
- `src/api/adopta_api/models/match.py`: confirmado, NO tiene columna `motivo_descarte`. Columnas actuales: `id, user_id, pet_id, shelter_id, estado (String(20), default="solicitado"), creado_en`.
- `src/web/src/screens/SolicitudDetalle.tsx`: confirmado, termina (líneas 54-57) con el párrafo literal *"Agendar visita, pedir más información y descartar con motivo estarán disponibles en una próxima entrega."* — sin botones de acción. El resto de la pantalla (cabecera, cuestionario de hogar, "Sobre mí") no cambia.
- `src/web/src/screens/MisMatches.tsx`: confirmado el mapeo binario actual (líneas 59-65): solo distingue `estado === 'visita_agendada'` ("● Visita agendada", `text-forest`) de todo lo demás ("● Esperando refugio", `text-ochre`). No cubre `en_revision`, `adoptado`, `cerrado`.
- `tests/api/test_shelters.py`: confirmado el test que se rompe con el fix de `calcular_etiqueta_solicitud` — `test_listar_solicitudes_ordenada_con_afinidad_y_etiqueta` (línea 185) crea un match con `estado="en_revision"` reciente y espera hoy `etiqueta == "Cuestionario nuevo"`; tras el fix pasará a `"En revisión"` sin importar los días. También `test_calcular_etiqueta_en_revision_viejo_es_sin_responder_con_dias_exactos` (líneas 286-292) hoy espera `"Sin responder · 5 días"` para `en_revision` viejo; tras el fix debe esperar `"En revisión"`. Ambos se actualizan en el paso 1, no se dejan rotos.
- `schemas/shelter.py`: `SolicitudOut`/`SolicitudDetalleOut` confirmados sin `motivo_descarte`. `schemas/match.py` (`MatchWithPetOut`, lado adoptante) confirmado sin `motivo_descarte` — así debe quedar tras la feature también.
- `feature_list.json`: `acceptance` de `10-adoption-request-flow` estaba vacío, ahora tiene las 6 líneas de la sección 4 del documento de diseño (idénticas, sin editorializar). `status` → `in_progress`. Validado con `python3 scripts/validate_feature_list.py feature_list.json` (exit 0).

### Decisiones ya tomadas en el documento de diseño (NO reabrir)

- `Match.motivo_descarte: str | None`, `String(500)`, nullable — vía skill `db-migrations` (sin Alembic en este proyecto: borrar `data/app.db`, recrear con `scripts/seed.py`).
- Matriz de transiciones válidas (función pura `validar_transicion(estado_actual, accion) -> None`, `class TransicionInvalidaError(Exception)`):
  - `agendar-visita`: válido desde `{solicitado, en_revision}`
  - `pedir-informacion`: válido solo desde `{solicitado}` (si ya está en `en_revision` → 409, no no-op)
  - `descartar`: válido desde `{solicitado, en_revision, visita_agendada}`
  - Estados terminales (`adoptado`, `cerrado`): ninguna acción válida → 409 siempre
  - Router captura `TransicionInvalidaError` → `HTTPException(409, str(exc))`
- 3 endpoints nuevos en `routers/shelters.py`: `POST /api/shelters/{shelter_id}/solicitudes/{match_id}/agendar-visita`, `.../pedir-informacion`, `.../descartar` (body `DescartarIn{motivo: str}` con `min_length=1` + validator que rechaza whitespace-only).
- Helpers a extraer en el router: `_cargar_match_o_404(session, shelter_id, match_id) -> Match` y `_solicitud_detalle_out(session, match) -> SolicitudDetalleOut` (la lógica de 404 y de construir `SolicitudDetalleOut` ya se repite en 2 endpoints existentes; con 3 nuevos que la necesitan, se factoriza).
- `SolicitudDetalleOut` NO gana `motivo_descarte` en esta pasada — el refugio no ve de vuelta el motivo que acaba de escribir (contrato mínimo, decisión explícita del documento).
- `schemas/match.py` (lado adoptante) NO cambia — `motivo_descarte` nunca se expone al adoptante (`docs/product-research.md`: "el motivo no se muestra al adoptante en crudo"). Se verifica con un test explícito de no-filtrado.
- Frontend `SolicitudDetalle.tsx`: si `estado` es terminal (`adoptado`/`cerrado`) → nota neutra sin botones; si no → 3 botones siempre visibles pero `disabled` (atenuados, no ocultos) según constantes `PERMITE_AGENDAR`/`PERMITE_PEDIR_INFO`/`PERMITE_DESCARTAR` que deben replicar EXACTAMENTE la matriz del backend. "Descartar" abre formulario inline (textarea + Confirmar/Cancelar, patrón ya usado en `PublicarMascota.tsx`), botón de confirmar deshabilitado si el texto está vacío/solo espacios. Tras éxito: `setSolicitud(resultado)` con la respuesta del endpoint (sin refetch). Error 409 → banner con el mensaje de `ApiError`.
- Frontend `MisMatches.tsx`: mapeo `ESTADO_COPY` de los 5 estados (`solicitado`, `en_revision`, `visita_agendada`, `adoptado`, `cerrado`), con `cerrado` en copy neutro ("Solicitud cerrada", `text-muted`, nunca lenguaje que culpe al refugio), fallback defensivo `ESTADO_COPY[match.estado] ?? ESTADO_COPY.solicitado`.

### Pasos de implementación (secuenciales, cada uno verificable de forma independiente)

**Paso 0 — Líder (COMPLETADO en esta sesión):** `10-adoption-request-flow` → `in_progress`, `acceptance` escrito en `feature_list.json`, este plan.

**Paso 1 — Backend: modelo + validación + etiqueta — HECHO (2026-08-03, implementador)**

Resultado: `src/api/adopta_api/models/match.py` (columna `motivo_descarte`), `src/api/adopta_api/services/solicitudes.py` (rama propia `en_revision` en `calcular_etiqueta_solicitud`, docstring de 6 ramas, `TransicionInvalidaError`/`validar_transicion`/`TRANSICIONES_VALIDAS`), nuevo `tests/api/test_solicitudes_service.py` (30 tests unitarios puros), 2 asserts corregidos en `tests/api/test_shelters.py` (líneas ~185 y ~286-292, `en_revision` → `"En revisión"`). `data/app.db` recreado. `pytest tests/api/` 111/111 en verde, `ruff`/`black` limpios, `bash init.sh` completo en verde (111 API + 33 frontend). Detalle completo en `changes.md` (2026-08-03). Siguiente: Paso 2 (endpoints POST).

**Paso 2 — Backend: 3 endpoints POST — HECHO (2026-08-03, implementador)**

Resultado: `src/api/adopta_api/schemas/shelter.py` (`DescartarIn`), `src/api/adopta_api/routers/shelters.py` (helpers `_cargar_match_o_404`/`_solicitud_detalle_out`, `obtener_solicitud` refactorizado sobre ellos sin cambio de comportamiento, 3 `POST` nuevos `agendar-visita`/`pedir-informacion`/`descartar`, docstring del módulo actualizado citando ADR 0002), `tests/api/test_shelters.py` extendido (+29 tests: transiciones válidas por endpoint con verificación en DB, matriz de 9 transiciones inválidas → 409, `descartar` con motivo vacío/whitespace → 422 (3 variantes), 404 refugio/match/match-de-otro-refugio para los 3 endpoints, test crítico de no-filtrado de `motivo_descarte` en `GET /api/matches`). `pytest tests/api/` 140/140 en verde (111 previos + 29 nuevos), `ruff check`/`black --check` limpios, `bash init.sh` completo en verde (140 API + 33 frontend). Detalle completo en `changes.md` (2026-08-03). Siguiente: Paso 3 (frontend `SolicitudDetalle.tsx`).

**Paso 3 — Frontend: `SolicitudDetalle.tsx` — HECHO (2026-08-03, implementador)**

Resultado: `src/web/src/api/types.ts` (`DescartarIn`), `src/web/src/api/client.ts` (`agendarVisita`/`pedirInformacion`/`descartarSolicitud`, reusan `request<T>`/`SolicitudDetalle` existentes), `src/web/src/screens/SolicitudDetalle.tsx` (3 botones con constantes `permiteAgendar`/`permitePedirInfo`/`permiteDescartar` que replican exactamente `TRANSICIONES_VALIDAS` del backend, nota neutra sin botones en estado terminal, formulario inline de descarte con validación de texto vacío/whitespace, banner de error con `ApiError`), `src/web/src/screens/SolicitudDetalle.test.tsx` reescrito completo (9 tests: matriz habilitado/deshabilitado por estado, caso terminal, flujo agendar visita, flujo descartar con validación, banner de error). `npm test` 40/40 en verde (33 previos + 9 nuevos, sin restar cobertura de los 2 casos que ya existían), `npm run lint`/`npx tsc -b`/`npx prettier --check .` limpios, `bash init.sh` completo en verde (140 API + 40 frontend). Detalle completo en `changes.md` (2026-08-03). No se tocó `MisMatches.tsx`. Siguiente: Paso 4 (frontend `MisMatches.tsx`).

**Paso 4 — Frontend: `MisMatches.tsx` — HECHO (2026-08-03, implementador)**

Resultado: `src/web/src/screens/MisMatches.tsx` (constante `ESTADO_COPY` con los 5 estados de `Match.estado` — `solicitado`/`en_revision`/`visita_agendada`/`adoptado`/`cerrado` —, reemplaza el ternario binario previo; fallback defensivo `ESTADO_COPY[match.estado] ?? ESTADO_COPY.solicitado` para cualquier valor inesperado), `src/web/src/screens/MisMatches.test.tsx` extendido con `it.each` de los 5 estados (verifica texto y clase de color de cada badge). `npx vitest run src/screens/MisMatches.test.tsx` 7/7 en verde (2 previos + 5 nuevos). `npm test` 45/45 en verde (40 previos + 5 nuevos), `npm run lint`/`npx tsc -b`/`npx prettier --check .` limpios. `bash init.sh` completo en verde (140 API + 45 frontend) — feature `10-adoption-request-flow` completa en sus 4 pasos de implementación. Detalle completo en `changes.md` (2026-08-03). Siguiente: Paso 5 (cierre del revisor, agente independiente).

<!-- Plan original del paso, conservado para referencia: -->
- `models/match.py`: agregar `motivo_descarte: Mapped[str | None] = mapped_column(String(500), nullable=True)`.
- Skill `db-migrations`: borrar `data/app.db`, recrear con `python3 scripts/seed.py`.
- `services/solicitudes.py`:
  - Corregir `calcular_etiqueta_solicitud`: rama `estado == "en_revision"` → `"En revisión"`, ANTES de la rama de días (que queda exclusiva de `"solicitado"`).
  - Actualizar el docstring del módulo (documentaba 5 ramas agrupadas, ahora son 6 distintas).
  - Nueva función pura `validar_transicion(estado_actual: str, accion: str) -> None` + `class TransicionInvalidaError(Exception)`, matriz exacta de la sección "Decisiones ya tomadas" arriba.
- Nuevo `tests/api/test_solicitudes_service.py`: matriz completa de `validar_transicion` (cada acción × cada estado, válidos e inválidos) + las 6 ramas de `calcular_etiqueta_solicitud` (agregar caso `en_revision` reciente y viejo, ambos → `"En revisión"`).
- Actualizar en `tests/api/test_shelters.py` los 2 asserts rotos identificados arriba (línea 185 y bloque 286-292) para reflejar que `en_revision` siempre etiqueta `"En revisión"`.
- Verificación: `pytest tests/api/test_solicitudes_service.py tests/api/test_shelters.py -q` en verde.

**Paso 2 — Backend: 3 endpoints POST**
- `schemas/shelter.py`: agregar `DescartarIn` (validator `motivo_no_vacio`, ver documento de diseño §1.3).
- `routers/shelters.py`: helpers `_cargar_match_o_404` y `_solicitud_detalle_out`; los 3 `POST` (`agendar-visita`, `pedir-informacion`, `descartar`); actualizar el docstring del módulo (ya no es cierto que ningún endpoint mute `Match.estado` — documentar exactamente cuáles sí y por qué está permitido aquí, referenciando ADR 0002).
- Extender `tests/api/test_shelters.py`: cada transición válida por endpoint con verificación en DB; `descartar` con motivo vacío/whitespace → 422; cada transición inválida de la matriz → 409; 404 refugio inexistente / match inexistente / match de otro refugio para los 3 endpoints; test explícito de no-filtrado de `motivo_descarte` en `GET /api/matches`.
- Verificación: `pytest tests/api -q` completo en verde (81 tests previos + los nuevos).

**Paso 3 — Frontend: `SolicitudDetalle.tsx`**
- `api/types.ts`: `DescartarIn { motivo: string }`.
- `api/client.ts`: `agendarVisita(shelterId, matchId)`, `pedirInformacion(shelterId, matchId)`, `descartarSolicitud(shelterId, matchId, motivo)` — `POST`, reusan `request<T>`/`ApiError`.
- `screens/SolicitudDetalle.tsx`: reemplazar el párrafo de "próxima entrega" por los 3 botones + lógica de estado terminal + formulario inline de descarte, según diseño arriba.
- Reescribir `SolicitudDetalle.test.tsx` completo: casos por estado (`solicitado`, `en_revision`, `visita_agendada`, terminal) verificando botones habilitados/deshabilitados vía `getByRole`; flujo de descartar (formulario, validación cliente, mock de `descartarSolicitud`, actualización de pantalla tras éxito).
- Verificación: `npx vitest run src/screens/SolicitudDetalle.test.tsx` en verde.

**Paso 4 — Frontend: `MisMatches.tsx`**
- Reemplazar el mapeo binario por `ESTADO_COPY` de 5 estados (ver diseño arriba).
- Extender `MisMatches.test.tsx` con un caso por cada uno de los 5 estados.
- Verificación: `npx vitest run src/screens/MisMatches.test.tsx` en verde.

**Paso 5 — Cierre del revisor (agente independiente, NO el líder ni el implementador)**
- `bash init.sh` completo en verde (backend + frontend).
- Verificar la matriz de transiciones línea por línea: `validar_transicion` (backend) vs. constantes `PERMITE_*` (frontend) — deben coincidir exactamente.
- `grep` para confirmar que `motivo_descarte` nunca aparece en `schemas/match.py` ni en `types.ts` del lado adoptante, ni en la respuesta JSON real de `GET /api/matches`.
- Confirmar que el copy de `cerrado` en `MisMatches.tsx` no culpa al refugio (lenguaje neutro).
- Recorrido manual en navegador real (`bash dev.sh`): como adoptante, generar solicitud nueva (like); como refugio (`/refugio`), probar las 3 acciones en distintos momentos (agendar visita → luego pedir info debe fallar/estar deshabilitado; descartar otra solicitud con motivo); volver a `/matches` como adoptante y confirmar reflejo del estado sin ver el motivo. Resetear `data/app.db` con `python3 scripts/seed.py` después.
- Solo entonces `status` → `done` en `feature_list.json`, con el mismo detalle de verificación que features anteriores documentado en `progress/current.md`.

### Tabla de cobertura acceptance ↔ test (revisada por el implementador tras el paso 4; el revisor la confirma en el paso 5)

Las 6 líneas de `acceptance` de `10-adoption-request-flow` en `feature_list.json`, una por una:

| # | Acceptance (texto literal, resumido) | Tests que la cubren | Estado |
|---|---|---|---|
| 1 | El refugio puede agendar visita / pedir información / descartar con motivo vía 3 endpoints `POST` nuevos; ninguna acción muta el match en estado terminal o transición inválida — 409 en español | `tests/api/test_shelters.py`: una transición válida por endpoint con verificación en DB, matriz completa de 9 transiciones inválidas → 409 (incluye ambos estados terminales), motivo vacío/whitespace → 422 (3 variantes) (paso 2) | Cubierta |
| 2 | La validación de la matriz de transiciones vive en una función pura y testeada (`services/solicitudes.py::validar_transicion`), no en el router; `calcular_etiqueta_solicitud` distingue `en_revision` de `solicitado` con etiqueta propia | `tests/api/test_solicitudes_service.py`: 30 tests unitarios sin DB/HTTP — matriz completa `validar_transicion` (cada acción × cada estado) + las 6 ramas de `calcular_etiqueta_solicitud` incluyendo `en_revision` reciente y viejo (paso 1) | Cubierta |
| 3 | `motivo_descarte` se persiste en `Match.motivo_descarte` pero nunca se expone en `GET /api/matches` (lado adoptante) ni en `schemas/match.py` — verificado con test explícito | `tests/api/test_shelters.py::test_get_matches_adoptante_no_expone_motivo_descarte` (línea 468): crea un match `cerrado` con `motivo_descarte` no nulo, llama `GET /api/matches` y hace `assert "motivo_descarte" not in elemento` sobre el JSON crudo — no solo confía en el tipo de schema. `grep motivo_descarte src/api/adopta_api/schemas/match.py` y `grep motivo_descarte src/web/src/api/types.ts` (lado adoptante) confirman 0 resultados — el campo nunca existió en esos contratos, no se "filtra" activamente porque nunca estuvo (paso 2) | Cubierta |
| 4 | `SolicitudDetalle.tsx` muestra los 3 botones de acción con habilitado/deshabilitado según la matriz de transiciones válidas para el estado actual, y un formulario con motivo obligatorio para descartar | `src/web/src/screens/SolicitudDetalle.test.tsx` reescrito: matriz habilitado/deshabilitado por estado (`solicitado`, `en_revision`, `visita_agendada`), nota neutra sin botones en estado terminal, flujo de agendar visita, flujo de descartar con validación de texto vacío/whitespace, banner de error 409 (paso 3) | Cubierta |
| 5 | `MisMatches.tsx` (lado adoptante) refleja los 5 estados posibles de un match con copy propio para cada uno, sin exponer el motivo de descarte y sin lenguaje que culpe al refugio | `src/web/src/screens/MisMatches.test.tsx`, `it.each` de los 5 estados (`solicitado` → "Esperando refugio", `en_revision` → "En revisión", `visita_agendada` → "Visita agendada", `adoptado` → "Adopción cerrada", `cerrado` → "Solicitud cerrada"), verifica texto y clase de color de cada badge (paso 4). Ver nota debajo sobre "sin motivo"/"sin culpar" | Cubierta |
| 6 | `bash init.sh` pasa completo (backend + frontend) incluyendo los tests nuevos de transición, 409, 404 cruzado entre refugios y los 5 estados visuales | Corrida del implementador tras el paso 4: 140 tests API + 45 tests frontend, lint/formato limpios. Pendiente confirmación independiente del revisor en el paso 5 | Verificada por implementador, pendiente de revisor |

**Nota explícita sobre "sin exponer el motivo de descarte" y "sin lenguaje que culpe al refugio" en `MisMatches.tsx` (línea 5):** esto está garantizado en dos niveles independientes, no solo por elección de copy:
- **A nivel de tipos:** `MatchWithPet` (`src/web/src/api/types.ts`, línea 120) y `Match` (backend, `schemas/match.py`, lado adoptante) no incluyen el campo `motivo_descarte` en absoluto — el frontend adoptante no tiene forma de acceder a ese dato aunque quisiera, porque nunca llega en la respuesta HTTP (confirmado por el test de la fila 3 de esta tabla). No hace falta "ocultar" nada en `MisMatches.tsx`: el dato simplemente no existe en el objeto `match` con el que trabaja el componente.
- **A nivel de copy:** las 5 entradas de `ESTADO_COPY` fueron elegidas explícitamente en el documento de diseño de este plan (línea 36 arriba) para no usar lenguaje de descarte/rechazo ni atribuir la decisión al refugio. En particular `cerrado` → `"Solicitud cerrada"` (no "Rechazada por el refugio" ni similar) — el mismo término neutro (`"cerrado"`) que ya usa `calcular_etiqueta_solicitud` del lado refugio, así que el copy es consistente entre ambos lados de la feature. No hay test automatizado que verifique "ausencia de lenguaje ofensivo" (es una propiedad de contenido, no de comportamiento), pero sí hay 5 tests (`it.each`) que fijan el texto exacto de cada estado — si alguien cambiara el copy de `cerrado` a algo que culpe al refugio, el test de esa fila fallaría inmediatamente.

### Verificación end-to-end esperada

- `bash init.sh` en verde tras cada paso (backend y frontend por separado durante implementación; completo al cierre).
- Recorrido manual en navegador real, detallado en el paso 5.
- Resetear `data/app.db` con `python3 scripts/seed.py` después de cualquier verificación manual que haya mutado datos.

## Historial de cierres anteriores

Ver `progress/history.md` para el detalle completo de features `01`-`09` (todas `done`, aprobadas por revisor independiente). Resumen: MVP (`01`-`05`) aprobado 2026-07-31; `06-filters`/`07-adopter-profile` aprobadas en sesión posterior; `08-onboarding-cuestionario` aprobada 2026-08-03; `09-shelter-panel` aprobada 2026-08-03 (81 tests API + 33 frontend en verde). `10-adoption-request-flow` planificada 2026-08-03, lista para que el implementador arranque por el paso 1.
