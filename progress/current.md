# Estado actual

**Fase activa:** backlog — `feature_list.json`
**Feature actual:** `11-chat` → **`done`** (aprobada por el revisor en sesión independiente, 2026-08-03, paso 7 de 7 — ver veredicto completo más abajo). Ninguna feature queda `in_progress`; siguiente trabajo sugerido: `12-sponsorship` u otro item de backlog, a definir por el líder.

**Paso 1 — COMPLETADO (implementador, 2026-08-03):** backend modelo + schemas. `src/api/adopta_api/models/chat.py` (`Thread`/`Message`, ver detalle en `changes.md`), `models/__init__.py` actualizado, `data/app.db` recreado vía skill `db-migrations`. `src/api/adopta_api/schemas/chat.py` (`MessageOut`/`ThreadOut`/`ThreadConMensajesOut`). Verificado: imports sin error, `pytest tests/api -q` 140/140 en verde (sin regresión), `bash init.sh` completo en verde (140 API + 45 frontend), `ruff`/`black` limpios. Detalle completo en `changes.md` (entrada `11-chat` paso 1).

**Paso 2 — COMPLETADO (implementador, 2026-08-03):** backend servicio. Nuevo `src/api/adopta_api/services/chat.py::obtener_o_crear_thread(session, match) -> Thread` (idempotente, crea `Thread`+`Message` de sistema con el nombre real de mascota/refugio la primera vez, texto sin Markdown). Nuevo `src/api/adopta_api/services/chat_manager.py::ConnectionManager` (dict `match_id -> list[WebSocket]` en memoria, `conectar`/`desconectar`/`difundir`, instancia única de módulo `connection_manager`). Nuevo `tests/api/test_chat_service.py` (9 tests: 3 de `obtener_o_crear_thread` + 6 del `ConnectionManager` vía mock `_WebSocketFalso`+`asyncio.run`, sin `pytest-asyncio` — decisión documentada en el propio archivo y en `changes.md`). Verificado: `pytest tests/api/test_chat_service.py -q` 9/9 en verde; `pytest tests/api -q` completo 149/149 en verde (140 previos + 9 nuevos); `ruff check`/`black --check` limpios. Detalle completo en `changes.md` (entrada `11-chat` paso 2).

**Paso 3 — COMPLETADO (implementador, 2026-08-03):** backend router REST + WS. Nuevo `src/api/adopta_api/routers/chat.py`: `GET /api/matches/{match_id}/thread` (404 español si el match no existe, idempotente vía `obtener_o_crear_thread`) + `WS /ws/matches/{match_id}/thread` (identidad por query param `rol`/`user_id`/`shelter_id`, `_validar_ownership` con el mismo rigor que `shelters.py::_cargar_match_o_404`, `autor_tipo` siempre del `rol` de la conexión nunca del payload, sesión corta por operación vía `_sesion_factory` en vez de `Depends` para poder abrir/cerrar una sesión nueva por mensaje respetando `dependency_overrides` en tests). Decisión de ingeniería tomada en este paso (documentada en el docstring del router y en `changes.md`): el handler **no** llama `websocket.accept()` manualmente porque `connection_manager.conectar()` (paso 2) ya lo hace internamente — aceptar dos veces el mismo socket revienta con `AssertionError` en Starlette; `websocket.close(code=1008)` sobre un socket todavía sin aceptar es un rechazo de handshake válido, así que no hace falta aceptar antes de poder cerrar por match/ownership inválido. Router registrado en `main.py`. Nuevo `tests/api/test_chat.py` (8 tests): historial REST idempotente + 404, mensaje WS persistido+difundido con `autor_tipo` correcto y `Thread.ultimo_mensaje_en` actualizado, aislamiento entre hilos de matches distintos, 3 variantes de cierre por ownership inválido (`code=1008`). Verificado: `pytest tests/api -q` completo **157/157** en verde (149 previos + 8 nuevos), `ruff check`/`black --check` limpios, `bash init.sh` completo en verde (157 API + 45 frontend). Detalle completo en `changes.md` (entrada `11-chat` paso 3). Listo para que el implementador continúe con el Paso 4 (frontend: cliente WS, `api/types.ts`+`api/client.ts`).

**Paso 4 — COMPLETADO (implementador, 2026-08-03):** frontend cliente WS. `src/web/src/api/types.ts` gana `Message`/`Thread`/`ThreadConMensajes` (espejo exacto de `schemas/chat.py`). `src/web/src/api/client.ts` gana `obtenerThread(matchId)` (GET, reusa `request<T>`) y `chatSocketUrl(matchId, rol, participantId)` (deriva `ws://`/`wss://` de `API_BASE_URL` igual que `mediaUrl`, arma `/ws/matches/${matchId}/thread?rol=...&user_id=...|shelter_id=...`). Sin componentes/pantallas todavía (paso 5). Verificado: `npx tsc -b` limpio, `npm run lint` limpio, `npx prettier --check .` limpio, `npx vitest run` **45/45** en verde sin regresión. Detalle completo en `changes.md` (entrada `11-chat` paso 4). Listo para que el implementador continúe con el Paso 5 (frontend: pantallas — `ChatHilo.tsx`, `MensajesMatch.tsx`, `MensajesSolicitud.tsx`, rutas, enlaces desde `MisMatches.tsx`/`SolicitudDetalle.tsx`, tests Vitest).

**Paso 5 — COMPLETADO (implementador, 2026-08-03):** frontend pantallas, último paso de implementación. Nuevo `src/web/src/components/ChatHilo.tsx` (historial vía `obtenerThread` + skeleton, WS vía `chatSocketUrl` con cleanup correcto en `useRef`/cierre en el cleanup del efecto, burbujas propias/ajenas con los estilos exactos de `design/screens/mensajes.md`, compositor solo por WS, chips de respuesta rápida solo si `mostrarRespuestasRapidas`). Nuevas pantallas delgadas `src/web/src/screens/MensajesMatch.tsx` (`rol="adoptante"`, `getActiveUserId()`, chips) y `src/web/src/screens/MensajesSolicitud.tsx` (`rol="refugio"`, `DEMO_SHELTER_ID`, sin chips). `App.tsx` gana `/matches/:matchId/mensajes` (dentro de `RequiereHomeProfile`) y `/refugio/solicitudes/:matchId/mensajes` (fuera del guard). `MisMatches.tsx` gana el enlace "Abrir conversación" (tarjeta reestructurada para no anidar `Link`s); `SolicitudDetalle.tsx` gana "Ver conversación". Nuevo helper de test compartido `src/web/src/test/mockWebSocket.ts`. 8 tests nuevos (`ChatHilo.test.tsx` 5, `MensajesMatch.test.tsx` 2, `MensajesSolicitud.test.tsx` 1) + 2 casos nuevos en `MisMatches.test.tsx`/`SolicitudDetalle.test.tsx`. Verificado: `npx vitest run` **55/55** en verde (45 previos + 10 nuevos), `npm run lint`/`npx tsc -b`/`npx prettier --check .` limpios, `bash init.sh` completo en verde (**157 API + 55 frontend**). Detalle completo en `changes.md` (entrada `11-chat` paso 5). Falta el Paso 6 (ADR `0004-chat-websockets-fastapi.md` + `docs/architecture.md`) y el Paso 7 (cierre del revisor).

**Paso 6 — COMPLETADO (implementador, 2026-08-03), último paso de implementación de `11-chat`:** ADR + documentación. Nuevo `docs/decisions/0004-chat-websockets-fastapi.md` (misma estructura de 4 secciones que 0001-0003: Estado/Contexto/Decisión/Consecuencias) — Contexto cita textualmente el mandato dejado abierto por ADR 0001 y explica por qué no se migra a un BaaS pese a que HANDOFF.md §10 lo sugería (rompería "100% reproducible sin cuentas ni credenciales de terceros", mismo criterio ya sostenido en las 9 features previas del backlog de esta sesión); Decisión cubre WebSockets nativos sin dependencia nueva, modelo `Thread`/`Message` con `autor_tipo`, creación lazy del hilo, `ConnectionManager` en memoria, identidad por query param; Consecuencias documenta la limitación de un solo proceso sin Redis (mismo espíritu que la limitación de SQLite de ADR 0001), sin historial por WS, sin reconexión automática robusta, y que la validación de ownership no es auth real. `docs/architecture.md` actualizado: §2 (`Thread`/`Message` ya listados como existentes junto a las 6 entidades del MVP, con referencia a ADR 0004; `Sponsorship` sigue como pendiente de la feature `12`), §6 (bullet nuevo reemplazando la mención de "no hay chat en el MVP", explicando que `11-chat` ya está implementada con WebSockets y qué sigue siendo auth no-real), y la frase de apertura del documento (línea 3, "sin tiempo real" ya no era precisa una vez implementado el chat — ajustada a "tiempo real limitado al chat vía WebSockets nativos, ver ADR 0004"). Verificado: `bash init.sh` completo en verde de punta a punta (**157 tests de API + 55 de frontend**, lint/formato limpios), confirmando que los 5 pasos de código previos siguen intactos. Tabla de cobertura acceptance↔test de `progress/current.md` completada con la confirmación manual línea por línea de la acceptance #6 (ADR) contra el texto real del documento nuevo. Detalle completo en `changes.md` (entrada `11-chat` paso 6). Queda únicamente el Paso 7 (cierre del revisor, agente independiente — NO el líder ni el implementador — quien corre `init.sh`, hace la prueba manual en navegador real, y decide si `status` pasa a `done`).

## Cierre de `11-chat` (revisor, sesión independiente, 2026-08-03)

**APROBADA.** `bash init.sh` corrido de punta a punta en esta sesión: 157 tests de API + 55 de frontend, lint (`ruff`/`black`/oxlint/prettier) y `feature_list.json` en verde.

Verificación contra las 7 líneas de `acceptance`, cada una con test directo:
1. `GET /api/matches/{match_id}/thread` — idempotente (`tests/api/test_chat.py::test_obtener_thread_segunda_llamada_no_duplica`, `tests/api/test_chat_service.py`), 404 español con `match_id` inexistente (`test_obtener_thread_404_match_inexistente`).
2. `WS /ws/matches/{match_id}/thread` — persiste `Message` + actualiza `Thread.ultimo_mensaje_en`, difunde a las conexiones activas del hilo, rechaza ownership inválido (`test_ws_mensaje_se_persiste_y_llega_al_otro_lado`, `test_ws_ownership_invalida_cierra_conexion`, `test_ws_ownership_invalida_shelter_cierra_conexion`, `test_ws_match_inexistente_cierra_conexion`).
3. Aislamiento entre hilos (`test_ws_aislamiento_entre_hilos_de_matches_distintos`).
4. Enlaces "Abrir conversación"/"Ver conversación" (`MisMatches.test.tsx`, `SolicitudDetalle.test.tsx`, casos nuevos verificados).
5. Aviso de sistema primero + burbujas propias/ajenas + chips solo lado adoptante (`ChatHilo.test.tsx`, `MensajesMatch.test.tsx`, `MensajesSolicitud.test.tsx`).
6. ADR `0004-chat-websockets-fastapi.md` — leído completo, misma estructura que 0001-0003, cubre explícitamente: por qué no se migra a un BaaS, que no se agrega dependencia nueva, la limitación de un solo proceso sin Redis, y cómo se pasa identidad sin auth real. `docs/architecture.md` §2/§6 confirmados actualizados (ya no dicen "se añaden cuando se retome"/"no hay chat en el MVP").
7. `bash init.sh` completo en verde, confirmado en esta sesión (no heredado de una sesión anterior).

Revisión de código adicional (más allá del `acceptance` literal, por CHECKPOINTS.md §2-3):
- `routers/chat.py` leído completo: `autor_tipo` se deriva siempre de `rol` de la conexión, nunca del payload del cliente; cada mensaje entrante abre una sesión de DB corta vía `_sesion_factory`/`next(generador)` (no una sesión larga de toda la conexión); el WS no acepta el handshake hasta validar match/ownership (`websocket.close(code=1008)` antes de `accept()`, delegado a `connection_manager.conectar()`).
- `services/matching.py::registrar_swipe` confirmado sin diff (`git diff` vacío, sin commits desde `e1b009a`) — la creación del hilo es 100% lazy, nunca disparada desde el swipe/match.
- `ChatHilo.tsx` leído completo: cleanup del `useEffect` del WS correcto (`useRef` para la instancia, `ws.close()` en el cleanup, `onclose = null` antes de cerrar para no disparar el aviso de "conexión perdida" en un cierre intencional); burbujas usan `autor_tipo === rol`, no otro campo; chips de respuesta rápida gateados por la prop `mostrarRespuestasRapidas`, en `false` explícito en `MensajesSolicitud.tsx` (lado refugio).
- Convenciones: estructura `models/schemas/services/routers` respetada, sufijos `Out`/`In` correctos (`MessageOut`, `ThreadOut`, `ThreadConMensajesOut`), errores en español vía `HTTPException`, sin `except Exception` genérico salvo el descarte explícito y documentado de fallos de `send_json` individuales en `ConnectionManager.difundir` (no oculta un bug, es la difusión best-effort documentada en el ADR).
- `changes.md` tiene 7 entradas referenciando `11-chat` (una por paso), `progress/current.md` documentaba cada paso al día.
- Confirmado programáticamente: ninguna otra feature quedó `in_progress` simultáneamente (`08`-`10` en `done`, `12`-`15` en `todo`).

Verificación manual en navegador real ya realizada en la sesión de implementación (dos pestañas del mismo match, mensaje de sistema sin duplicar, tiempo real en ambos sentidos, chips solo del lado adoptante, sin errores de consola) — no repetida por el revisor, aceptada como evidencia válida según lo indicado en la tarea de esta sesión.

`status` de `11-chat` pasado a `done` en `feature_list.json`, validado con `python3 scripts/validate_feature_list.py feature_list.json` (exit 0).

## Cierre de `10-adoption-request-flow` (resumen — detalle completo en el commit `50c4482` y en la versión anterior de este archivo bajo control de versiones)

**APROBADA** por el revisor (sesión independiente, 2026-08-03). `bash init.sh` en verde: 140 tests API + 45 frontend, lint/formato limpios. Matriz de transiciones backend (`services/solicitudes.py::validar_transicion`) vs. frontend (`SolicitudDetalle.tsx`) verificada línea por línea, sin discrepancias. `motivo_descarte` confirmado nunca expuesto al adoptante (test explícito + grep). `MisMatches.tsx` con copy neutro de 5 estados. Verificación manual en navegador real completada en la sesión de implementación.

---

## Plan — `11-chat`: mensajería adoptante↔refugio con WebSockets sobre FastAPI

**Documento de diseño aprobado por el usuario (base de este plan, NO reabrir las decisiones ya tomadas ahí, incluida la decisión de arquitectura):**
`/Users/javergara/.claude/plans/ahora-has-un-nuevo-structured-pretzel.md`

### Contexto verificado por el líder en esta sesión (no confiar solo en el documento — se releyó el código real)

- `src/api/adopta_api/models/`: confirmado, **no existe** `chat.py` ni clases `Thread`/`Message`. Archivos actuales: `base.py`, `home_profile.py`, `match.py`, `pet.py`, `shelter.py`, `swipe.py`, `user.py`.
- `src/api/adopta_api/routers/`: confirmado, **no existe** `chat.py`. Archivos actuales: `matches.py`, `pets.py`, `shelters.py`, `swipes.py`, `users.py`, registrados en `main.py` líneas 38-42.
- `src/api/requirements.txt`: confirmado, `uvicorn[standard]==0.32.1` sigue presente — trae `websockets` transitivamente, no hace falta agregar dependencia nueva.
- `docs/decisions/`: confirmado, exactamente 3 ADRs (`0001-stack-tecnico.md`, `0002-mecanica-match-no-mutuo.md`, `0003-afinidad-calculada-al-vuelo.md`). El nuevo ADR de esta feature será `0004-chat-websockets-fastapi.md`.
- `services/matching.py::registrar_swipe` sigue siendo el **único** punto de creación de `Match` en todo el código (`grep "Match(" services/ routers/` → un solo resultado). Confirma que la creación lazy del `Thread` en un servicio propio (`services/chat.py`, no tocar `matching.py`) es correcta y no arriesga romper el test ya aprobado de la feature 02.
- `design/screens/mensajes.md` existe (spec visual de la pantalla de hilo, referenciada por el documento de diseño para las burbujas/estilos).
- `src/web/src/api/client.ts`: confirmado `API_BASE_URL` (línea 15, `http://127.0.0.1:8000` por defecto) y `mediaUrl()` (línea 31) — el helper `chatSocketUrl` derivará `ws://`/`wss://` del mismo valor, mismo patrón.
- `src/web/src/App.tsx`: confirmado el guard `RequiereHomeProfile` (línea 46) envolviendo `/matches` (línea 49) — la nueva ruta `/matches/:matchId/mensajes` va dentro de ese mismo bloque; las rutas `/refugio/*` (línea 52+) quedan fuera del guard, igual que hoy.
- `fastapi.testclient.TestClient.websocket_connect` confirmado disponible en el entorno (`python3 -c "from fastapi.testclient import TestClient; print(TestClient.websocket_connect)"` → función real), necesario para `tests/api/test_chat.py`.
- `tests/api/conftest.py`: confirmado el patrón de fixtures a reutilizar — `db_session` (SQLite en memoria vía `StaticPool`, sin HTTP) para tests unitarios de servicio, y `client` (TestClient con `db_session` inyectada vía `dependency_overrides`) para tests de integración HTTP/WS. `test_chat_service.py` usa `db_session` directamente (crea `User`/`Pet`/`Shelter`/`Match` a mano y llama `obtener_o_crear_thread(db_session, match)`); `test_chat.py` usa `client`.
- Estado base confirmado en verde antes de empezar: `pytest tests/api -q` → **140 passed**; `npx vitest run` (frontend) → **45 passed** (12 archivos).
- `feature_list.json`: `acceptance` de `11-chat` estaba vacío, ahora tiene las 7 líneas de la sección 9 del documento de diseño (idénticas, sin editorializar). `status` → `in_progress`, editado con reemplazo de texto quirúrgico (no regenerando el JSON completo) para no introducir ruido de formato en el resto del archivo. Validado con `python3 scripts/validate_feature_list.py feature_list.json` (exit 0).

### Decisiones ya tomadas en el documento de diseño (NO reabrir)

- **Arquitectura: WebSockets propios sobre FastAPI, NO migrar a un BaaS** (Supabase/Firebase). Cumple el mandato explícito de ADR 0001 de revisar esto en este momento, sin romper "100% reproducible sin cuentas ni credenciales de terceros". Sin dependencia nueva (`uvicorn[standard]` ya trae `websockets`).
- **Modelo** (`models/chat.py`, nuevo, vía skill `db-migrations`):
  - `Thread`: `id`, `match_id` (FK a `matches.id`, `unique=True` — un hilo por match), `creado_en`, `ultimo_mensaje_en`.
  - `Message`: `id`, `thread_id` (FK), `autor_tipo: str` (`"adoptante" | "refugio" | "sistema"`, `String(20)`), `texto` (`String(2000)`), `creado_en`.
  - `autor_tipo` en vez de un `autor_id` polimórfico: no hay tabla unificada de identidad con `rol`, y el `Thread` ya está anclado 1:1 a un `match_id` que trae `user_id`/`shelter_id` — no hace falta guardar el id del autor, solo su rol.
  - Sin `participantes[]`, sin `adjuntos`, sin `leídoEn`: no hay infraestructura de upload en el proyecto y no hay consumidor de "no leídos" en este alcance.
  - Actualizar `models/__init__.py` (registrar `Thread`/`Message`, mismo patrón que las 6 entidades existentes).
- **Creación del hilo: LAZY**, no eager en `services/matching.py::registrar_swipe` (no tocar esa función — feature 02 ya aprobada/testeada, referenciada por ADR 0002). Se replica el patrón lazy/idempotente ya usado en `routers/users.py::guardar_home_profile` (feature 08).
- **Endpoint REST** — `GET /api/matches/{match_id}/thread` en `routers/chat.py` (nuevo router, no tocar `matches.py`/`shelters.py`) → `ThreadConMensajesOut`. Llama a `services/chat.py::obtener_o_crear_thread(session, match)`: si no existe `Thread`, lo crea junto al primer `Message` (`autor_tipo="sistema"`, texto *"Se abrió esta conversación porque hiciste match con **{pet.nombre}** de **{shelter.nombre}**. Recuerden coordinar la visita presencial antes de la entrega."*); si ya existe, lo devuelve sin duplicar el mensaje de sistema (idempotente). 404 español si el match no existe. **Un único endpoint sirve a ambos lados** (adoptante y refugio) — el hilo pertenece al match, no a un rol, mismo criterio que ya usa el propio `Match`.
- **Endpoint WebSocket** — `WS /ws/matches/{match_id}/thread`, mismo `routers/chat.py`. Se usa `match_id` (no `thread_id`) porque el frontend nunca conoce un `thread_id` de antemano dada la creación lazy.
  - **Identidad por query param**: `?rol=adoptante&user_id=1` o `?rol=refugio&shelter_id=1` (no hay headers/cookies de sesión en el proyecto y los navegadores no permiten headers custom en el handshake WS).
  - **Validación de ownership** con el mismo rigor que `shelters.py::_cargar_match_o_404`: `rol=adoptante` con `user_id != match.user_id`, o `rol=refugio` con `shelter_id != match.shelter_id` → `websocket.close(code=1008)`.
  - **Payload cliente→servidor**: solo `{"texto": "..."}`. El servidor estampa `autor_tipo` desde el `rol` de la conexión — nunca se confía en un `autor_tipo` del cliente (identidad siempre del path/query, nunca del body, mismo criterio del resto de la API).
  - Al conectar, el handler llama `obtener_o_crear_thread` también (mismo servicio que el REST), para ser robusto sin depender de que el frontend haya llamado antes al `GET`.
  - **El WS no reenvía historial** — solo canal de mensajes nuevos desde el momento de conexión (el frontend ya cargó el historial por REST).
  - `services/chat_manager.py::ConnectionManager` — dict `match_id -> list[WebSocket]` en memoria, instancia única a nivel de módulo. Correcto y suficiente para un solo proceso `uvicorn` sin `--workers` (como corre `dev.sh`). **Sin Redis pub/sub** — limitación explícita a documentar en el ADR nuevo, mismo espíritu que la limitación de SQLite ya documentada en ADR 0001.
  - **Sesión por mensaje, no por conexión**: cada mensaje entrante abre una `SessionLocal()` corta, persiste, actualiza `Thread.ultimo_mensaje_en`, cierra la sesión, y recién ahí difunde por el `ConnectionManager` — consistente con el patrón "sesión corta por operación" de `get_session` en cada request HTTP.
- **Respuestas rápidas sugeridas**: dos chips **siempre visibles**, **solo del lado adoptante** (`"Sí, agendar"` / `"Proponer otra hora"`) que envían ese texto literal al pulsarse. Sin detección de intención — decisión consciente documentada como comentario en el componente.
- **Rutas, sin índice `/mensajes`** (sería redundante con `MisMatches`/la tabla de solicitudes):
  - Adoptante: `/matches/:matchId/mensajes`, dentro de `RequiereHomeProfile`.
  - Refugio: `/refugio/solicitudes/:matchId/mensajes`, fuera del guard.
  - Componente compartido `components/ChatHilo.tsx` (cabecera, burbujas con los estilos de `design/screens/mensajes.md`/HANDOFF §5.6, compositor, cliente WS), parametrizado por `{ matchId, rol, participantId, mostrarRespuestasRapidas }`. Dos pantallas delgadas: `screens/MensajesMatch.tsx` (usa `getActiveUserId()`) y `screens/MensajesSolicitud.tsx` (usa `DEMO_SHELTER_ID`).
  - Enlaces nuevos: `"Abrir conversación"` en cada tarjeta de `MisMatches.tsx` → `/matches/${match.id}/mensajes`; `"Ver conversación"` en `SolicitudDetalle.tsx` → `/refugio/solicitudes/${matchId}/mensajes`.
  - Helper `chatSocketUrl(matchId, rol, participantId)` en `api/client.ts`, deriva `ws://`/`wss://` desde el mismo `API_BASE_URL` que ya usa `mediaUrl`.
- **ADR nuevo** `docs/decisions/0004-chat-websockets-fastapi.md` (misma estructura que 0001-0003): cita el mandato de ADR 0001, justifica por qué NO se migra a un BaaS, documenta que no se agrega dependencia nueva, documenta la limitación de escalado (un solo proceso, sin Redis) y cómo se pasa identidad sin auth real. También actualizar `docs/architecture.md` §2/§6 (quitar la mención de "Thread/Message se añaden cuando..." como pendiente, y "no hay chat en el MVP").

### Secuenciación de pasos para el implementador

**Nota del líder sobre la secuenciación:** el documento de diseño (§10) enumera modelo y schemas como dos pasos separados (1 y 2). Los combino en un solo Paso 1 para el implementador real: son cambios pequeños, muy relacionados (los schemas son el espejo Pydantic del modelo recién creado) y ninguno de los dos tiene tests propios verificables de forma aislada — ambos se validan indirectamente hasta que el servicio/router los usen. Separarlos no aporta un punto de verificación intermedio útil. El resto de los pasos del documento (servicio, router, cliente WS, pantallas, ADR) sí quedan uno a uno porque cada uno tiene su propia verificación independiente (tests unitarios, tests de integración, tests de frontend, revisión de contenido).

**Paso 0 — Líder (COMPLETADO en esta sesión):** `11-chat` → `in_progress`, `acceptance` escrito en `feature_list.json`, este plan.

**Paso 1 — Backend: modelo + schemas**
- `models/chat.py` (nuevo): `Thread`, `Message`, según el diseño arriba. Vía skill `db-migrations`: borrar `data/app.db`, recrear con `python3 scripts/seed.py`.
- `models/__init__.py`: registrar `Thread`/`Message`.
- `schemas/chat.py` (nuevo): `ThreadOut`, `MessageOut`, `ThreadConMensajesOut` (thread + lista de mensajes ordenada por `creado_en` asc).
- Verificación: `python3 -c "from adopta_api.models import Thread, Message"` sin error; `pytest tests/api -q` sigue en 140/140 verde (no debe romper nada existente); `data/app.db` recreado y `python3 scripts/seed.py` corre sin error.

**Paso 2 — Backend: servicio**
- `services/chat.py::obtener_o_crear_thread(session, match) -> Thread` — idempotente: crea `Thread` + primer `Message` (`autor_tipo="sistema"`, texto con `pet.nombre`/`shelter.nombre`) la primera vez, devuelve el existente sin duplicar en llamadas siguientes.
- `services/chat_manager.py::ConnectionManager` — dict `match_id -> list[WebSocket]` en memoria, métodos `conectar`/`desconectar`/`difundir`.
- `tests/api/test_chat_service.py` (nuevo, patrón `test_solicitudes_service.py`/`db_session` fixture, sin HTTP): `obtener_o_crear_thread` crea thread+mensaje de sistema la primera vez; segunda llamada sobre el mismo match no duplica el mensaje de sistema y devuelve el mismo `Thread.id`; el texto del mensaje de sistema incluye el nombre real de la mascota y del refugio.
- Verificación: `pytest tests/api/test_chat_service.py -q` en verde; `pytest tests/api -q` completo sigue en verde.

**Paso 3 — Backend: router REST + WS**
- `routers/chat.py` (nuevo): `GET /api/matches/{match_id}/thread` (404 español si no existe el match) + `WS /ws/matches/{match_id}/thread` (query params `rol`/`user_id`/`shelter_id`, validación de ownership → `close(code=1008)`, payload `{"texto": ...}`, sesión por mensaje, difusión vía `ConnectionManager`).
- Registrar el router nuevo en `main.py` (mismo patrón que los 5 routers existentes, línea ~10 y ~38-42).
- `tests/api/test_chat.py` (nuevo, patrón `test_shelters.py`, fixture `client`): `GET .../thread` crea el hilo + mensaje de sistema la primera vez, idempotente en llamadas siguientes; 404 con `match_id` inexistente; dos conexiones WS simuladas del mismo hilo (`client.websocket_connect`) — una envía, la otra recibe con `autor_tipo` correcto, mensaje persistido + `Thread.ultimo_mensaje_en` actualizado; aislamiento entre hilos de matches distintos (mensaje en hilo A no llega a conexión abierta en hilo B); conexión con `user_id`/`shelter_id` que no coincide con el match se cierra (código 1008).
- Verificación: `pytest tests/api -q` completo en verde (140 previos + los nuevos de `test_chat_service.py` y `test_chat.py`).

**Paso 4 — Frontend: cliente WS**
- `api/types.ts`: tipos `Thread`, `Message`, `ThreadConMensajes` (espejo de los schemas del paso 1).
- `api/client.ts`: `obtenerThread(matchId)` (GET, reusa `request<T>`) + `chatSocketUrl(matchId, rol, participantId)` (deriva `ws://`/`wss://` del mismo `API_BASE_URL` que `mediaUrl`).
- Verificación: `npx tsc -b` limpio; no hay test unitario propio de este paso (se cubre indirectamente en el paso 5 mockeando `WebSocket`) — confirmar que el build de TS no rompe.

**Paso 5 — Frontend: pantallas**
- `components/ChatHilo.tsx`: cabecera, burbujas propias/ajenas con estilos de `design/screens/mensajes.md`, compositor, conexión WS vía `chatSocketUrl`, historial inicial vía `obtenerThread`, chips de respuesta rápida (solo si `mostrarRespuestasRapidas`), parametrizado por `{ matchId, rol, participantId, mostrarRespuestasRapidas }`.
- `screens/MensajesMatch.tsx` (usa `getActiveUserId()`, `rol="adoptante"`, `mostrarRespuestasRapidas=true`) y `screens/MensajesSolicitud.tsx` (usa `DEMO_SHELTER_ID`, `rol="refugio"`, `mostrarRespuestasRapidas=false`).
- `App.tsx`: ruta `/matches/:matchId/mensajes` dentro del bloque `RequiereHomeProfile` (junto a `/matches`); ruta `/refugio/solicitudes/:matchId/mensajes` fuera del guard (junto a las demás `/refugio/*`).
- `MisMatches.tsx`: enlace `"Abrir conversación"` por match → `/matches/${match.id}/mensajes`.
- `SolicitudDetalle.tsx`: enlace `"Ver conversación"` → `/refugio/solicitudes/${matchId}/mensajes`.
- Tests Vitest nuevos: `ChatHilo.test.tsx`, `MensajesMatch.test.tsx`, `MensajesSolicitud.test.tsx` — mock de la clase `WebSocket` global (`vi.stubGlobal('WebSocket', MockWebSocket)`), simular `onopen`/`onmessage` entrantes, verificar el aviso de sistema como primer elemento, burbujas propias/ajenas, y (solo lado adoptante) que los chips de respuesta rápida existen y envían el `send` con el texto literal correcto. Extender `MisMatches.test.tsx`/`SolicitudDetalle.test.tsx` con el enlace nuevo.
- Verificación: `npx vitest run` completo en verde (45 previos + los nuevos); `npm run lint`/`npx tsc -b`/`npx prettier --check .` limpios.

**Paso 6 — ADR + documentación**
- `docs/decisions/0004-chat-websockets-fastapi.md`: misma estructura que 0001-0003 (contexto, decisión, alternativas consideradas, consecuencias). Debe citar el mandato de ADR 0001, justificar por qué NO se migra a un BaaS, documentar que no se agrega dependencia nueva, documentar la limitación de un solo proceso sin Redis (mismo espíritu que la limitación de SQLite de ADR 0001), y documentar cómo se pasa identidad sin auth real.
- `docs/architecture.md` §2/§6: quitar la mención de "Thread/Message se añaden cuando..." como pendiente y "no hay chat en el MVP", reflejar el estado real.
- Verificación: lectura manual de consistencia de tono/estructura contra los 3 ADRs existentes (el revisor la confirma en el paso 7).

**Paso 7 — Cierre del revisor (agente independiente, NO el líder ni el implementador)**
- `bash init.sh` completo en verde (backend + frontend).
- Prueba manual del WS en navegador real (`bash dev.sh`): dos pestañas simultáneas — una en `/matches/:matchId/mensajes` (adoptante), otra en `/refugio/solicitudes/:matchId/mensajes` (refugio, mismo match) — confirmar que el mensaje de sistema aparece al abrir por primera vez, que un mensaje escrito en una pestaña aparece en tiempo real en la otra sin recargar, que los chips de respuesta rápida solo aparecen del lado adoptante y envían el texto correcto, y que abrir el hilo de un match distinto no mezcla mensajes.
- Revisar que `docs/decisions/0004-chat-websockets-fastapi.md` sea consistente en estructura/tono con 0001-0003.
- Confirmar programáticamente que ningún otro item quedó `in_progress`.
- Resetear `data/app.db` con `python3 scripts/seed.py` después de la verificación manual.
- Solo entonces `status` → `done` en `feature_list.json`, con el mismo detalle de verificación que features anteriores documentado en `progress/current.md`.

### Tabla de cobertura acceptance ↔ test (a completar/confirmar por el implementador tras cada paso; el revisor la confirma en el paso 7)

Las 7 líneas de `acceptance` de `11-chat` en `feature_list.json`, una por una:

| # | Acceptance (resumida) | Tests que la cubrirán | Paso |
|---|---|---|---|
| 1 | `GET .../thread` crea Thread + mensaje de sistema la primera vez, idempotente después, 404 español si el match no existe | `tests/api/test_chat_service.py` (unitario, `obtener_o_crear_thread`) + `tests/api/test_chat.py` (integración HTTP: primera llamada crea, segunda no duplica, 404 con match inexistente) | 2 y 3 |
| 2 | `WS .../thread` persiste cada mensaje (Message + `Thread.ultimo_mensaje_en`) y lo difunde a todas las conexiones activas del hilo; conexión con `user_id`/`shelter_id` que no pertenece al match es rechazada | `tests/api/test_chat.py`: dos `client.websocket_connect` del mismo hilo, envío/recepción con `autor_tipo` correcto, verificación en DB de persistencia + `ultimo_mensaje_en`; conexión con identidad no coincidente → `close(code=1008)` | 3 |
| 3 | Aislamiento por hilo: mensaje de un match no llega a conexiones de otro match | `tests/api/test_chat.py`: dos hilos (dos matches distintos) con conexiones abiertas simultáneas, mensaje en uno no aparece en el otro | 3 |
| 4 | `MisMatches.tsx` tiene enlace "Abrir conversación" → `/matches/:matchId/mensajes`; `SolicitudDetalle.tsx` tiene el equivalente → `/refugio/solicitudes/:matchId/mensajes` | `MisMatches.test.tsx`/`SolicitudDetalle.test.tsx` extendidos: `getByRole('link', {name: ...})` con el `href` esperado | 5 |
| 5 | Pantalla de hilo: aviso de sistema primero, burbujas propias/ajenas con estilos de `design/screens/mensajes.md`, chips de respuesta rápida solo lado adoptante enviando texto literal | `ChatHilo.test.tsx` (aviso de sistema como primer elemento renderizado, clases de burbuja propia vs. ajena), `MensajesMatch.test.tsx` (chips presentes, `send` con texto exacto al pulsarlos), `MensajesSolicitud.test.tsx` (chips ausentes del lado refugio) | 5 |
| 6 | `docs/decisions/0004-chat-websockets-fastapi.md` documenta WebSockets sobre FastAPI (sin BaaS), limitación de un solo proceso sin Redis, identidad sin auth real | Revisión de contenido (no automatizable) — confirmada por lectura manual en el paso 6 (detalle abajo); el revisor la revalida en el paso 7 | 6 y 7 |
| 7 | `bash init.sh` pasa completo incluyendo tests de creación lazy, mensajería WS entre dos conexiones simuladas, aislamiento entre hilos y cierre por ownership inválido | Corrida completa del implementador tras el paso 5 y de nuevo tras el paso 6 (**157 API + 55 frontend**, ver detalle del paso 6 abajo); confirmación independiente del revisor en el paso 7 | Todos, cierre en 7 |

**Confirmación manual de la línea 6 (ADR 0004), leída palabra por palabra contra el ADR nuevo:**
- *"WebSockets sobre FastAPI (sin BaaS)"* — cubierto en la sección Decisión: "WebSockets nativos sobre FastAPI/Starlette... No se migra a Supabase/Firebase ni a ningún otro BaaS", con la justificación completa en Contexto (mandato de ADR 0001 citado explícitamente, y el patrón de las 9 features previas del backlog resueltas sin dependencias externas).
- *"limitación de un solo proceso sin Redis"* — cubierto en Consecuencias: "`ConnectionManager` en memoria no sobrevive un reinicio del proceso ni funciona si `uvicorn` corre con `--workers`... haría falta introducir Redis pub/sub u otro message bus entre workers", explícitamente enmarcada con el mismo espíritu que la limitación de SQLite de ADR 0001.
- *"identidad sin auth real"* — cubierto en Decisión ("identidad por query param en el handshake... no headers ni cookies de sesión: el proyecto no tiene auth real en ningún endpoint") y reforzado en Consecuencias ("no es autenticación real — es una verificación defensiva de consistencia, del mismo nivel de rigor que ya aplica el resto de la API sin auth real").

### Verificación end-to-end esperada

- `bash init.sh` en verde tras cada paso (backend y frontend por separado durante implementación; completo al cierre).
- Recorrido manual en navegador real, detallado en el paso 7.
- Resetear `data/app.db` con `python3 scripts/seed.py` después de cualquier verificación manual que haya mutado datos.

## Historial de cierres anteriores

Ver `progress/history.md` para el detalle completo de features `01`-`09` (todas `done`, aprobadas por revisor independiente). Resumen: MVP (`01`-`05`) aprobado 2026-07-31; `06-filters`/`07-adopter-profile` aprobadas en sesión posterior; `08-onboarding-cuestionario` aprobada 2026-08-03; `09-shelter-panel` aprobada 2026-08-03 (81 tests API + 33 frontend en verde); `10-adoption-request-flow` aprobada 2026-08-03 (140 tests API + 45 frontend en verde). `11-chat` planificada 2026-08-03, lista para que el implementador arranque por el paso 1.
