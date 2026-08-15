# 0002 — El match no es mutuo (regla de negocio de backend, no solo de copy)

## Estado
Aceptado.

## Contexto
`design/prototypes/HANDOFF.md` §1 establece que, a diferencia de un Tinder genérico, el match en Adopta **no requiere aceptación de la otra parte**: cuando el adoptante desliza a la derecha ("Me interesa"), el match se crea de inmediato. El refugio no decide si existe el match; decide si acepta o rechaza la **solicitud de adopción**, un paso posterior. El cuestionario de hogar (`HomeProfile`) es obligatorio y es el input del cálculo de afinidad, no un formulario opcional de perfil.

Si esto se tratara solo como una decisión de copy/UI, sería fácil implementar por error un flujo de "doble consentimiento" (like del adoptante + aprobación del refugio para crear el match), que es el patrón por defecto en cualquier app de dating y el que un desarrollador asumiría sin este ADR.

## Decisión
- La tabla `Swipe` (dirección `like`/`pass`) es independiente de la tabla `Match`. Un `Swipe` con dirección `like` **crea un `Match` de forma automática y síncrona** en el mismo request (`POST /api/swipes`), sin ninguna acción del refugio.
- El estado inicial de un `Match` es `solicitado`; transiciones posteriores (`en_revision`, `visita_agendada`, `adoptado`, `cerrado`) las controla el refugio a través de la feature de backlog `10-adoption-request-flow`, y son sobre la **solicitud**, no sobre la existencia del match.
- La API expone `GET /api/matches?user_id=` mostrando todos los matches creados por like, sin filtrar por si el refugio "aceptó" — porque no hay tal aceptación de match.
- El score de afinidad requiere un `HomeProfile` existente para el usuario; en el MVP esto se resuelve con `HomeProfile` sintético sembrado (feature `01`), ya que el flujo interactivo de cuestionario (feature `08`) es backlog. La API no debe asumir que `HomeProfile` es opcional: es una relación 1:1 obligatoria con `User` en el modelo de datos.

## Consecuencias
- Los tests de `04-matches` deben verificar explícitamente que un `like` crea el match **sin ningún paso adicional** (no debe existir un endpoint de "aceptar match" — solo de aceptar/rechazar solicitud, en backlog).
- El copy de la UI (deck, ficha, modal de match) usa siempre "Me interesa" / "Ahora no", nunca "rechazar" — la capa de presentación respeta la misma decisión que la capa de datos.

## Nota de vigencia tras el pivot (2026-08-15)

Esta decisión **sigue vigente y no se re-litiga** (`docs/integracion-adopcion.md`): el match no es mutuo, y no existe ni existirá un endpoint de "aceptar match". Lo que cambia es el vocabulario y una premisa que el pivot volvió falsa:

- El `Shelter` de aquella era es hoy **`Organizacion`** (y una mascota también puede colgar de un **rescatista individual**, que en la era Adopta no existía).
- **La tabla sigue llamándose `matches`** —es el nombre de las migraciones del backlog— pero en la API, en el copy y en las pantallas se llama siempre **"solicitud"**. Un lector que busque "match" en el producto no lo va a encontrar: está en el esquema, no en la interfaz.
- Los estados persistidos son exactamente **`solicitado` / `en_revision` / `visita_agendada` / `adoptado` / `cerrado`**. **Nunca `aprobado` ni `descartado`**: esas dos palabras solo viven en la prosa del backlog y en los nombres de las acciones HTTP (`POST /api/solicitudes/{id}/aprobar`, `/descartar`), que llevan a `adoptado` y `cerrado` respectivamente. Inventar un estado `aprobado` haría caer `calcular_etiqueta_solicitud` al branch de "solicitado" en silencio.
- **El párrafo que declara obligatorio el `HomeProfile` queda superado.** Aquí el deck (`GET /api/pets/deck`) responde **200 con `afinidad: null`** cuando quien mira no tiene perfil de hogar, en vez del 404 de la era Adopta. Dos motivos: lo exige literalmente el acceptance de `AD-04` ("sin perfil el deck sigue funcionando"), y un guard bloqueante contradice la **cuenta liviana sin contraseña** del ADR 0005 — pedir un cuestionario de 6 pasos antes de dejar ver una sola mascota es justo la fricción que el pivot eliminó. El perfil de hogar es un **mejorador opcional** de la experiencia: con él aparecen el score y sus razones; sin él, el deck ordena igual y la UI invita a completarlo sin bloquear.
- Se implementa en la feature **`AD-05`**; `AD-03` solo trae el swipe (tabla `swipes` y `POST /api/swipes`), y `SwipeOut.solicitud` viaja en `null` hasta entonces.

Este ADR se restauró a `main` el 2026-08-15 (paso 1 de `AD-03`) porque el pivot lo dejó únicamente en la rama `adopta-v1`, y el checkpoint 3 de `CHECKPOINTS.md` exige poder verificar que el código es consistente con el ADR que lo gobierna. El `0004-chat-websockets-fastapi.md` **no se restaura**: queda superado por el ADR 0012 (WhatsApp directo), que se escribe en `AD-06`.
